"""Orchestration service bridging API requests, LangGraph agent, and persistence."""

import json
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.agent.graph import create_agent_graph
from app.agent.state import AgentState
from app.core.config import get_settings
from app.core.errors import ArchPilotException, ErrorCode
from app.core.logging import logger
from app.db.models import RunModel
from app.db.repository import RunRepository
from app.llm.base import LLMProvider
from app.llm.factory import get_llm_provider
from app.schemas.event import EventType
from app.tools.registry import ToolRegistry, get_default_registry


class RunService:
    """Coordinates execution of engineering decision runs with audit trails and DB persistence."""

    def __init__(
        self,
        db: Session,
        llm: Optional[LLMProvider] = None,
        tools: Optional[ToolRegistry] = None,
    ) -> None:
        self.db = db
        self.repo = RunRepository(db)
        self.llm = llm or get_llm_provider()
        self.tools = tools or get_default_registry()
        self.settings = get_settings()

    def create_run(self, task: str, constraints: Optional[Dict[str, Any]] = None) -> RunModel:
        """Initialize and persist a new run in PENDING status."""
        run_id = f"run_{uuid.uuid4().hex[:12]}"
        run = self.repo.create_run(run_id=run_id, task=task, constraints=constraints)

        self.repo.add_execution_event(
            run_id=run_id,
            event_type=EventType.RUN_STARTED.value,
            payload={"task": task, "constraints": constraints or {}},
        )
        return run

    async def execute_run(self, run_id: str) -> Dict[str, Any]:
        """Execute the LangGraph workflow for a specific run and persist milestones."""
        run = self.repo.get_run(run_id)
        if not run:
            raise ArchPilotException(
                code=ErrorCode.UNKNOWN_ERROR,
                message=f"Run '{run_id}' not found.",
                status_code=404,
            )

        self.repo.update_run_status(run_id=run_id, status="RUNNING")

        def event_callback(
            ev_run_id: str,
            event_type: EventType,
            payload: Dict[str, Any],
            step_id: Optional[int] = None,
        ) -> None:
            # Audit event persistence
            self.repo.add_execution_event(
                run_id=ev_run_id,
                event_type=event_type.value,
                payload=payload,
                step_id=step_id,
            )

            # Mirror to specific relational models based on milestone
            if event_type == EventType.TASK_NORMALIZED:
                self.repo.update_run_normalized_task(ev_run_id, payload)
            elif event_type == EventType.PLAN_CREATED:
                self.repo.update_run_plan(ev_run_id, payload)
                # Populate individual step records
                for step in payload.get("steps", []):
                    self.repo.add_step(
                        run_id=ev_run_id,
                        step_index=step.get("id", 1),
                        objective=step.get("objective", ""),
                        tool_name=step.get("tool", ""),
                        inputs=step.get("inputs", {}),
                        success_criteria=step.get("success_criteria", ""),
                    )
            elif event_type == EventType.STEP_COMPLETED:
                if step_id is not None:
                    self.repo.update_step_status(
                        ev_run_id, step_index=step_id, status=payload.get("status", "COMPLETED")
                    )
            elif event_type == EventType.TOOL_COMPLETED:
                self.repo.add_tool_event(
                    run_id=ev_run_id,
                    tool_name=payload.get("tool_name", "unknown"),
                    inputs=payload.get("inputs", {}),
                    output=payload.get("output"),
                    status=payload.get("status", "success"),
                    duration_ms=payload.get("duration_ms", 0.0),
                    error=payload.get("error"),
                    step_id=step_id,
                )
            elif event_type == EventType.VALIDATION_COMPLETED:
                self.repo.update_run_validation(ev_run_id, payload)
            elif event_type == EventType.FINALIZED:
                self.repo.update_run_final_result(ev_run_id, payload)

        app_graph = create_agent_graph(
            llm=self.llm,
            tools=self.tools,
            event_callback=event_callback,
        )

        initial_state: AgentState = {
            "run_id": run_id,
            "task": run.task,
            "constraints": json.loads(run.constraints_json or "{}"),
            "normalized_task": None,
            "plan": None,
            "current_step_id": None,
            "current_step_index": 0,
            "observations": [],
            "tool_events": [],
            "calculations": [],
            "validation": None,
            "final_result": None,
            "iteration": 0,
            "max_iterations": self.settings.MAX_ITERATIONS,
            "tool_retries": 0,
            "max_tool_retries": self.settings.MAX_TOOL_RETRIES,
            "validation_retries": 0,
            "max_validation_retries": self.settings.MAX_VALIDATION_RETRIES,
            "errors": [],
            "status": "RUNNING",
        }

        try:
            logger.info("Starting graph execution for run %s", run_id)
            final_state = await app_graph.ainvoke(initial_state)

            final_result = final_state.get("final_result")
            if final_result:
                self.repo.update_run_final_result(run_id, final_result)
            else:
                self.repo.update_run_status(run_id, status="COMPLETED")

            return final_state
        except Exception as e:
            logger.exception("Graph execution failed for run %s: %s", run_id, str(e))
            self.repo.update_run_status(run_id, status="FAILED", error_message=str(e))
            self.repo.add_execution_event(
                run_id=run_id,
                event_type=EventType.RUN_FAILED.value,
                payload={"error": str(e)},
            )
            raise

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get formatted summary of run."""
        run = self.repo.get_run(run_id)
        if not run:
            return None

        return {
            "run_id": run.id,
            "task": run.task,
            "constraints": json.loads(run.constraints_json or "{}"),
            "status": run.status,
            "normalized_task": json.loads(run.normalized_task_json)
            if run.normalized_task_json
            else None,
            "plan": json.loads(run.plan_json) if run.plan_json else None,
            "validation": json.loads(run.validation_json) if run.validation_json else None,
            "final_result": json.loads(run.final_result_json) if run.final_result_json else None,
            "error_message": run.error_message,
            "created_at": run.created_at.isoformat() if run.created_at else None,
            "updated_at": run.updated_at.isoformat() if run.updated_at else None,
        }

    def get_run_events(self, run_id: str) -> List[Dict[str, Any]]:
        """Fetch chronological execution events."""
        events = self.repo.get_events_for_run(run_id)
        return [
            {
                "id": ev.id,
                "event_type": ev.event_type,
                "step_id": ev.step_id,
                "payload": json.loads(ev.payload_json or "{}"),
                "timestamp": ev.timestamp.isoformat() if ev.timestamp else None,
            }
            for ev in events
        ]

    def get_run_tool_events(self, run_id: str) -> List[Dict[str, Any]]:
        """Fetch tool execution telemetry for run."""
        tool_events = self.repo.get_tool_events_for_run(run_id)
        return [
            {
                "id": te.id,
                "step_id": te.step_id,
                "tool_name": te.tool_name,
                "inputs": json.loads(te.inputs_json or "{}"),
                "output": json.loads(te.output_json) if te.output_json else None,
                "status": te.status,
                "duration_ms": te.duration_ms,
                "error": te.error,
                "timestamp": te.timestamp.isoformat() if te.timestamp else None,
            }
            for te in tool_events
        ]

    def get_run_result(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve final synthesized engineering decision."""
        run = self.repo.get_run(run_id)
        if not run or not run.final_result_json:
            return None
        return json.loads(run.final_result_json)

    def list_runs(self, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """List runs with high-level metadata."""
        runs = self.repo.list_runs(limit=limit, offset=offset)
        return [
            {
                "run_id": r.id,
                "task": r.task,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
            }
            for r in runs
        ]

    def get_dashboard_metrics(self) -> Dict[str, int]:
        """Aggregate high-level system metrics for the dashboard."""
        total = self.repo.count_runs()
        completed = self.repo.count_runs_by_status("COMPLETED")
        active = self.repo.count_runs_by_status("RUNNING") + self.repo.count_runs_by_status("PENDING")
        tool_calls = self.repo.count_tool_events()
        return {
            "total_runs": total,
            "completed_runs": completed,
            "active_runs": active,
            "tool_calls": tool_calls,
        }
