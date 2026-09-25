"""LangGraph node execution functions for the ArchPilot workflow."""

import copy
from typing import Any, Callable, Dict, Optional
from app.agent.policies import (
    MAX_STEPS,
    has_more_steps,
    is_iteration_limit_exceeded,
)
from app.agent.prompts import (
    FINALIZE_PROMPT,
    FINALIZE_SYSTEM,
    NORMALIZE_TASK_PROMPT,
    NORMALIZE_TASK_SYSTEM,
    PLAN_PROMPT,
    PLAN_SYSTEM,
    VALIDATION_PROMPT,
    VALIDATION_SYSTEM,
)
from app.agent.state import AgentState
from app.core.errors import PlanInvalidException
from app.core.logging import logger
from app.core.security import validate_task_input, verify_tool_allowed
from app.llm.base import LLMProvider
from app.schemas.event import EventType
from app.schemas.plan import Plan, StepStatus
from app.schemas.result import FinalResult, ValidationResult
from app.schemas.task import NormalizedTask
from app.tools.registry import ToolRegistry


class NodeHandler:
    """Encapsulates node execution logic with injected LLM and Tool Registry."""

    def __init__(
        self,
        llm: LLMProvider,
        tools: ToolRegistry,
        event_callback: Optional[Callable[[str, EventType, Dict[str, Any], Optional[int]], None]] = None,
    ) -> None:
        self.llm = llm
        self.tools = tools
        self.event_callback = event_callback

    def _emit(
        self,
        run_id: str,
        event_type: EventType,
        payload: Dict[str, Any],
        step_id: Optional[int] = None,
    ) -> None:
        if self.event_callback:
            try:
                self.event_callback(run_id, event_type, payload, step_id)
            except Exception as e:
                logger.error("Failed to emit event %s: %s", event_type, e)

    async def normalize_task(self, state: AgentState) -> Dict[str, Any]:
        """Node 1: Clean, disambiguate, and extract constraints from user task."""
        run_id = state.get("run_id", "unknown")
        raw_task = state.get("task", "")
        constraints = state.get("constraints", {})
        iteration = state.get("iteration", 0) + 1

        logger.info("[Node: normalize_task] Processing run %s", run_id)

        # Security validation on raw input
        cleaned_task = validate_task_input(raw_task)

        prompt = NORMALIZE_TASK_PROMPT.format(
            task=cleaned_task,
            constraints=constraints,
        )

        normalized: NormalizedTask = await self.llm.generate_structured(
            prompt=prompt,
            schema=NormalizedTask,
            system=NORMALIZE_TASK_SYSTEM,
        )

        self._emit(
            run_id=run_id,
            event_type=EventType.TASK_NORMALIZED,
            payload=normalized.model_dump(),
        )

        return {
            "task": cleaned_task,
            "normalized_task": normalized.model_dump(),
            "iteration": iteration,
            "status": "RUNNING",
        }

    async def plan(self, state: AgentState) -> Dict[str, Any]:
        """Node 2: Formulate structured multi-step plan using registered tools."""
        run_id = state.get("run_id", "unknown")
        normalized = state.get("normalized_task") or {}
        iteration = state.get("iteration", 0) + 1

        logger.info("[Node: plan] Creating plan for run %s", run_id)

        prompt = PLAN_PROMPT.format(
            normalized_task=normalized.get("normalized_task", state.get("task")),
            domain=normalized.get("domain", "General Engineering"),
            key_variables=normalized.get("key_variables", []),
            target_metric=normalized.get("target_metric", "Optimal Architecture"),
            constraints=state.get("constraints", {}),
        )

        plan_obj: Plan = await self.llm.generate_structured(
            prompt=prompt,
            schema=Plan,
            system=PLAN_SYSTEM,
        )

        # Enforce tool allowlist and max steps limit
        if len(plan_obj.steps) > MAX_STEPS:
            logger.warning("Truncating plan steps from %d to %d", len(plan_obj.steps), MAX_STEPS)
            plan_obj.steps = plan_obj.steps[:MAX_STEPS]

        for step in plan_obj.steps:
            verify_tool_allowed(step.tool, list(self.tools.allowed_tools))

        self._emit(
            run_id=run_id,
            event_type=EventType.PLAN_CREATED,
            payload=plan_obj.model_dump(),
        )

        first_step_id = plan_obj.steps[0].id if plan_obj.steps else None

        return {
            "plan": plan_obj.model_dump(),
            "current_step_index": 0,
            "current_step_id": first_step_id,
            "observations": [],
            "tool_events": [],
            "calculations": [],
            "iteration": iteration,
        }

    async def select_next_step(self, state: AgentState) -> Dict[str, Any]:
        """Node 3: Identify and prepare the next step to execute."""
        run_id = state.get("run_id", "unknown")
        plan_dict = state.get("plan") or {}
        steps = plan_dict.get("steps", [])
        current_index = state.get("current_step_index", 0)
        iteration = state.get("iteration", 0) + 1

        logger.info(
            "[Node: select_next_step] Step index %d of %d for run %s",
            current_index,
            len(steps),
            run_id,
        )

        if current_index < len(steps):
            active_step = steps[current_index]
            step_id = active_step.get("id")

            # Mark step as IN_PROGRESS
            updated_steps = copy.deepcopy(steps)
            updated_steps[current_index]["status"] = StepStatus.IN_PROGRESS.value
            plan_dict["steps"] = updated_steps

            self._emit(
                run_id=run_id,
                event_type=EventType.STEP_STARTED,
                payload={"step_id": step_id, "objective": active_step.get("objective")},
                step_id=step_id,
            )

            return {
                "plan": plan_dict,
                "current_step_id": step_id,
                "iteration": iteration,
            }

        return {
            "current_step_id": None,
            "iteration": iteration,
        }

    async def execute_tool(self, state: AgentState) -> Dict[str, Any]:
        """Node 4: Safely invoke registered tool matching the current step."""
        run_id = state.get("run_id", "unknown")
        plan_dict = state.get("plan") or {}
        steps = plan_dict.get("steps", [])
        current_index = state.get("current_step_index", 0)
        iteration = state.get("iteration", 0) + 1

        if current_index >= len(steps):
            logger.warning("No active step found for index %d", current_index)
            return {"iteration": iteration}

        active_step = steps[current_index]
        tool_name = active_step.get("tool", "")
        inputs = active_step.get("inputs", {})
        step_id = active_step.get("id")

        logger.info(
            "[Node: execute_tool] Invoking tool '%s' with inputs %s for step %s",
            tool_name,
            inputs,
            step_id,
        )

        self._emit(
            run_id=run_id,
            event_type=EventType.TOOL_CALLED,
            payload={"tool": tool_name, "inputs": inputs},
            step_id=step_id,
        )

        # Execute via registry
        tool_result = self.tools.execute(tool_name, inputs)

        self._emit(
            run_id=run_id,
            event_type=EventType.TOOL_COMPLETED,
            payload=tool_result.model_dump(),
            step_id=step_id,
        )

        # Record tool event and calculations
        tool_events = list(state.get("tool_events", []))
        tool_events.append(tool_result.model_dump())

        calculations = list(state.get("calculations", []))
        if tool_result.status == "success" and tool_result.output is not None:
            calculations.append({
                "step_id": step_id,
                "tool": tool_name,
                "inputs": inputs,
                "result": tool_result.output,
                "duration_ms": tool_result.duration_ms,
            })

        return {
            "tool_events": tool_events,
            "calculations": calculations,
            "iteration": iteration,
        }

    async def observe(self, state: AgentState) -> Dict[str, Any]:
        """Node 5: Ingest tool execution output as evidence observation."""
        run_id = state.get("run_id", "unknown")
        plan_dict = state.get("plan") or {}
        steps = plan_dict.get("steps", [])
        current_index = state.get("current_step_index", 0)
        iteration = state.get("iteration", 0) + 1

        if current_index >= len(steps):
            return {"iteration": iteration}

        active_step = steps[current_index]
        step_id = active_step.get("id")
        tool_events = state.get("tool_events", [])
        latest_event = tool_events[-1] if tool_events else None

        updated_steps = copy.deepcopy(steps)
        observations = list(state.get("observations", []))

        if latest_event and latest_event.get("status") == "success":
            updated_steps[current_index]["status"] = StepStatus.COMPLETED.value
            output_val = latest_event.get("output")
            obs_text = (
                f"Step {step_id} ({active_step.get('objective')}): "
                f"Computed value = {output_val} (took {latest_event.get('duration_ms')}ms)."
            )
            observations.append(obs_text)
        else:
            updated_steps[current_index]["status"] = StepStatus.FAILED.value
            err_msg = latest_event.get("error") if latest_event else "Unknown error"
            obs_text = f"Step {step_id} failed: {err_msg}"
            observations.append(obs_text)

        plan_dict["steps"] = updated_steps

        self._emit(
            run_id=run_id,
            event_type=EventType.OBSERVATION_ADDED,
            payload={"observation": obs_text, "step_id": step_id},
            step_id=step_id,
        )

        self._emit(
            run_id=run_id,
            event_type=EventType.STEP_COMPLETED,
            payload={"step_id": step_id, "status": updated_steps[current_index]["status"]},
            step_id=step_id,
        )

        return {
            "plan": plan_dict,
            "observations": observations,
            "current_step_index": current_index + 1,
            "tool_retries": 0,
            "iteration": iteration,
        }

    async def validate(self, state: AgentState) -> Dict[str, Any]:
        """Node 6: Critically review evidence completeness and math validity."""
        run_id = state.get("run_id", "unknown")
        iteration = state.get("iteration", 0) + 1
        plan_dict = state.get("plan") or {}

        logger.info("[Node: validate] Validating evidence for run %s", run_id)

        prompt = VALIDATION_PROMPT.format(
            task=state.get("task", ""),
            goal=plan_dict.get("goal", ""),
            observations="\n".join(state.get("observations", [])),
            calculations=state.get("calculations", []),
        )

        validation_obj: ValidationResult = await self.llm.generate_structured(
            prompt=prompt,
            schema=ValidationResult,
            system=VALIDATION_SYSTEM,
        )

        self._emit(
            run_id=run_id,
            event_type=EventType.VALIDATION_COMPLETED,
            payload=validation_obj.model_dump(),
        )

        return {
            "validation": validation_obj.model_dump(),
            "iteration": iteration,
        }

    async def finalize(self, state: AgentState) -> Dict[str, Any]:
        """Node 7: Synthesize comprehensive engineering decision deliverable."""
        run_id = state.get("run_id", "unknown")
        iteration = state.get("iteration", 0) + 1
        plan_dict = state.get("plan") or {}
        normalized = state.get("normalized_task") or {}

        logger.info("[Node: finalize] Finalizing decision for run %s", run_id)

        prompt = FINALIZE_PROMPT.format(
            task=state.get("task", ""),
            normalized_task=normalized.get("normalized_task", ""),
            assumptions=plan_dict.get("assumptions", []),
            observations="\n".join(state.get("observations", [])),
            calculations=state.get("calculations", []),
        )

        final_obj: FinalResult = await self.llm.generate_structured(
            prompt=prompt,
            schema=FinalResult,
            system=FINALIZE_SYSTEM,
        )

        # Merge actual collected calculations and observations into final object
        if state.get("observations"):
            final_obj.observations = state.get("observations", [])

        self._emit(
            run_id=run_id,
            event_type=EventType.FINALIZED,
            payload=final_obj.model_dump(),
        )

        return {
            "final_result": final_obj.model_dump(),
            "status": "COMPLETED",
            "iteration": iteration,
        }
