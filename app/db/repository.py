"""Data access repository for runs, steps, events, and results."""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.db.models import ExecutionEventModel, RunModel, StepModel, ToolEventModel


class RunRepository:
    """Encapsulates data persistence operations for agent runs."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def create_run(
        self, run_id: str, task: str, constraints: Optional[Dict[str, Any]] = None
    ) -> RunModel:
        """Create a new engineering run record in PENDING state."""
        run = RunModel(
            id=run_id,
            task=task,
            constraints_json=json.dumps(constraints or {}),
            status="PENDING",
            created_at=self._now(),
            updated_at=self._now(),
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def get_run(self, run_id: str) -> Optional[RunModel]:
        """Fetch a run by unique ID."""
        return self.db.query(RunModel).filter(RunModel.id == run_id).first()

    def list_runs(self, limit: int = 20, offset: int = 0) -> List[RunModel]:
        """List runs ordered by creation time descending."""
        return (
            self.db.query(RunModel)
            .order_by(RunModel.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def count_runs(self) -> int:
        """Count total runs."""
        return self.db.query(RunModel).count()

    def count_runs_by_status(self, status: str) -> int:
        """Count runs by status."""
        return self.db.query(RunModel).filter(RunModel.status == status).count()

    def update_run_status(
        self, run_id: str, status: str, error_message: Optional[str] = None
    ) -> Optional[RunModel]:
        """Update run lifecycle status."""
        run = self.get_run(run_id)
        if run:
            run.status = status
            if error_message:
                run.error_message = error_message
            run.updated_at = self._now()
            self.db.commit()
            self.db.refresh(run)
        return run

    def update_run_normalized_task(
        self, run_id: str, normalized_task: Dict[str, Any]
    ) -> Optional[RunModel]:
        """Save normalized task requirements."""
        run = self.get_run(run_id)
        if run:
            run.normalized_task_json = json.dumps(normalized_task)
            run.updated_at = self._now()
            self.db.commit()
            self.db.refresh(run)
        return run

    def update_run_plan(self, run_id: str, plan: Dict[str, Any]) -> Optional[RunModel]:
        """Save structured execution plan."""
        run = self.get_run(run_id)
        if run:
            run.plan_json = json.dumps(plan)
            run.updated_at = self._now()
            self.db.commit()
            self.db.refresh(run)
        return run

    def update_run_validation(
        self, run_id: str, validation: Dict[str, Any]
    ) -> Optional[RunModel]:
        """Save validation results."""
        run = self.get_run(run_id)
        if run:
            run.validation_json = json.dumps(validation)
            run.updated_at = self._now()
            self.db.commit()
            self.db.refresh(run)
        return run

    def update_run_final_result(
        self, run_id: str, final_result: Dict[str, Any]
    ) -> Optional[RunModel]:
        """Save final synthesized engineering decision."""
        run = self.get_run(run_id)
        if run:
            run.final_result_json = json.dumps(final_result)
            run.status = "COMPLETED"
            run.updated_at = self._now()
            self.db.commit()
            self.db.refresh(run)
        return run

    def add_step(
        self,
        run_id: str,
        step_index: int,
        objective: str,
        tool_name: str,
        inputs: Dict[str, Any],
        success_criteria: str,
    ) -> StepModel:
        """Record plan step in the database."""
        step = StepModel(
            id=str(uuid.uuid4()),
            run_id=run_id,
            step_index=step_index,
            objective=objective,
            tool_name=tool_name,
            inputs_json=json.dumps(inputs),
            status="PENDING",
            success_criteria=success_criteria,
            started_at=self._now(),
        )
        self.db.add(step)
        self.db.commit()
        self.db.refresh(step)
        return step

    def update_step_status(
        self, run_id: str, step_index: int, status: str
    ) -> Optional[StepModel]:
        """Update step progress status."""
        step = (
            self.db.query(StepModel)
            .filter(StepModel.run_id == run_id, StepModel.step_index == step_index)
            .first()
        )
        if step:
            step.status = status
            if status in ("COMPLETED", "FAILED", "SKIPPED"):
                step.completed_at = self._now()
            self.db.commit()
            self.db.refresh(step)
        return step

    def add_tool_event(
        self,
        run_id: str,
        tool_name: str,
        inputs: Dict[str, Any],
        output: Any,
        status: str,
        duration_ms: float,
        error: Optional[str] = None,
        step_id: Optional[int] = None,
    ) -> ToolEventModel:
        """Persist a tool invocation record."""
        event = ToolEventModel(
            id=str(uuid.uuid4()),
            run_id=run_id,
            step_id=step_id,
            tool_name=tool_name,
            inputs_json=json.dumps(inputs),
            output_json=json.dumps(output) if output is not None else None,
            status=status,
            duration_ms=duration_ms,
            error=error,
            timestamp=self._now(),
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def count_tool_events(self) -> int:
        """Count total tool executions across all runs."""
        return self.db.query(ToolEventModel).count()

    def add_execution_event(
        self,
        run_id: str,
        event_type: str,
        payload: Dict[str, Any],
        step_id: Optional[int] = None,
    ) -> ExecutionEventModel:
        """Persist an audit timeline event."""
        event = ExecutionEventModel(
            id=str(uuid.uuid4()),
            run_id=run_id,
            event_type=event_type,
            step_id=step_id,
            payload_json=json.dumps(payload),
            timestamp=self._now(),
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def get_events_for_run(self, run_id: str) -> List[ExecutionEventModel]:
        """Fetch all chronological timeline events for a run."""
        return (
            self.db.query(ExecutionEventModel)
            .filter(ExecutionEventModel.run_id == run_id)
            .order_by(ExecutionEventModel.timestamp.asc())
            .all()
        )

    def get_tool_events_for_run(self, run_id: str) -> List[ToolEventModel]:
        """Fetch all tool events recorded for a run."""
        return (
            self.db.query(ToolEventModel)
            .filter(ToolEventModel.run_id == run_id)
            .order_by(ToolEventModel.timestamp.asc())
            .all()
        )
