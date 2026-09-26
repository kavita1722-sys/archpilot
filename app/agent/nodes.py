"""LangGraph node execution functions for the ArchPilot workflow."""

import copy
from typing import Any, Callable, Dict, List, Optional
from app.agent.policies import (
    MAX_STEPS,
    has_more_steps,
    is_iteration_limit_exceeded,
    needs_research_retry,
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
from app.schemas.decision import DecisionItem
from app.schemas.event import EventType
from app.schemas.evidence import EvidenceItem
from app.schemas.plan import Plan, StepStatus
from app.schemas.result import FinalResult, ValidationResult
from app.schemas.task import NormalizedTask
from app.services.evidence_service import EvidenceService
from app.tools.registry import ToolRegistry


class NodeHandler:
    """Encapsulates node execution logic with injected LLM, Tool Registry, and Evidence Pipeline."""

    def __init__(
        self,
        llm: LLMProvider,
        tools: ToolRegistry,
        event_callback: Optional[Callable[[str, EventType, Dict[str, Any], Optional[int]], None]] = None,
    ) -> None:
        self.llm = llm
        self.tools = tools
        self.event_callback = event_callback
        self.evidence_service = EvidenceService()

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
            target_metric=normalized.get("target_metric", "Recommended Architecture"),
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
            "evidence": [],
            "decisions": [],
            "research_queue": [],
            "validation_attempts": 0,
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
        """Node 4: Safely invoke registered tool matching the current step or research queue."""
        run_id = state.get("run_id", "unknown")
        research_queue = list(state.get("research_queue", []))
        plan_dict = state.get("plan") or {}
        steps = plan_dict.get("steps", [])
        current_index = state.get("current_step_index", 0)
        iteration = state.get("iteration", 0) + 1

        # Check if executing from dynamic research retry queue or scheduled plan
        if research_queue:
            active_step = research_queue[0]
            step_id = active_step.get("id", 99)
            tool_name = active_step.get("tool", "web_search")
            inputs = active_step.get("inputs", {})
            is_research_retry = True
        elif current_index < len(steps):
            active_step = steps[current_index]
            tool_name = active_step.get("tool", "")
            inputs = active_step.get("inputs", {})
            step_id = active_step.get("id")
            is_research_retry = False
        else:
            logger.warning("No active step or research queue item to execute.")
            return {"iteration": iteration}

        logger.info(
            "[Node: execute_tool] Invoking tool '%s' with inputs %s for step %s (research_retry=%s)",
            tool_name,
            inputs,
            step_id,
            is_research_retry,
        )

        self._emit(
            run_id=run_id,
            event_type=EventType.TOOL_CALLED,
            payload={"tool": tool_name, "inputs": inputs, "is_research_retry": is_research_retry},
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
            if tool_name == "calculator":
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
        """Node 5: Ingest tool execution output, extract evidence items, and update observations."""
        run_id = state.get("run_id", "unknown")
        research_queue = list(state.get("research_queue", []))
        plan_dict = state.get("plan") or {}
        steps = plan_dict.get("steps", [])
        current_index = state.get("current_step_index", 0)
        iteration = state.get("iteration", 0) + 1

        tool_events = state.get("tool_events", [])
        latest_event = tool_events[-1] if tool_events else None
        evidence_items = list(state.get("evidence", []))
        observations = list(state.get("observations", []))

        # Check whether we were executing a research retry step or plan step
        if research_queue:
            active_step = research_queue.pop(0)
            step_id = active_step.get("id", 99)
            is_research_retry = True
            objective = active_step.get("objective", "Targeted research")
        elif current_index < len(steps):
            active_step = steps[current_index]
            step_id = active_step.get("id")
            is_research_retry = False
            objective = active_step.get("objective", "")
        else:
            return {"iteration": iteration}

        updated_steps = copy.deepcopy(steps)

        if latest_event and latest_event.get("status") == "success":
            output_val = latest_event.get("output")
            tool_name = latest_event.get("tool_name")

            # Extract evidence if research tool was executed
            if tool_name == "web_search" and isinstance(output_val, list):
                extracted = self.evidence_service.extract_evidence_from_search(
                    output_val, query=str(latest_event.get("inputs", {}).get("query", ""))
                )
                for item in extracted:
                    evidence_items.append(item.model_dump())
                    self._emit(
                        run_id=run_id,
                        event_type=EventType.EVIDENCE_COLLECTED,
                        payload=item.model_dump(),
                        step_id=step_id,
                    )
            elif tool_name == "url_fetch" and isinstance(output_val, dict):
                extracted_item = self.evidence_service.extract_evidence_from_fetch(output_val)
                if extracted_item:
                    evidence_items.append(extracted_item.model_dump())
                    self._emit(
                        run_id=run_id,
                        event_type=EventType.EVIDENCE_COLLECTED,
                        payload=extracted_item.model_dump(),
                        step_id=step_id,
                    )

            if not is_research_retry and current_index < len(updated_steps):
                updated_steps[current_index]["status"] = StepStatus.COMPLETED.value

            obs_text = (
                f"Step {step_id} ({objective}): "
                f"Tool '{tool_name}' completed in {latest_event.get('duration_ms')}ms."
            )
            observations.append(obs_text)
        else:
            if not is_research_retry and current_index < len(updated_steps):
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
            payload={"step_id": step_id, "status": "COMPLETED" if latest_event and latest_event.get("status") == "success" else "FAILED"},
            step_id=step_id,
        )

        new_index = current_index if is_research_retry else current_index + 1

        return {
            "plan": plan_dict,
            "observations": observations,
            "evidence": evidence_items,
            "research_queue": research_queue,
            "current_step_index": new_index,
            "tool_retries": 0,
            "iteration": iteration,
        }

    async def validate(self, state: AgentState) -> Dict[str, Any]:
        """Node 6: Critically review evidence completeness, constraint coverage, and math validity."""
        run_id = state.get("run_id", "unknown")
        iteration = state.get("iteration", 0) + 1
        validation_attempts = state.get("validation_attempts", 0) + 1
        plan_dict = state.get("plan") or {}

        logger.info(
            "[Node: validate] Validating evidence in Validation Center for run %s (Attempt %d)",
            run_id,
            validation_attempts,
        )

        evidence_items = state.get("evidence", [])
        evidence_summary = "\n".join([
            f"- [{e.get('id', 'EV-???')}] ({e.get('source_type', 'web')}): {e.get('claim', '')} (Confidence: {e.get('confidence', 0.85)})"
            for e in evidence_items
        ]) or "No external evidence collected yet."

        prompt = VALIDATION_PROMPT.format(
            task=state.get("task", ""),
            constraints=state.get("constraints", {}),
            goal=plan_dict.get("goal", ""),
            observations="\n".join(state.get("observations", [])),
            calculations=state.get("calculations", []),
            evidence_summary=evidence_summary,
        )

        validation_obj: ValidationResult = await self.llm.generate_structured(
            prompt=prompt,
            schema=ValidationResult,
            system=VALIDATION_SYSTEM,
        )

        # Evidence integrity verification: check for dangling evidence references
        integrity_res = self.evidence_service.check_evidence_integrity(
            decisions=state.get("decisions", []),
            evidence=evidence_items,
        )
        has_integrity_check = any(c.get("name") == "Evidence Integrity" for c in validation_obj.checks)
        if not has_integrity_check:
            if integrity_res["is_valid"]:
                validation_obj.checks.append({
                    "name": "Evidence Integrity",
                    "passed": True,
                    "notes": "All referenced evidence IDs exist in Evidence Ledger; zero dangling references.",
                })
            else:
                dangling_notes = ", ".join([
                    f"{r['decision_id']} -> {r['dangling_evidence_id']}"
                    for r in integrity_res["dangling_references"]
                ])
                validation_obj.checks.append({
                    "name": "Evidence Integrity",
                    "passed": False,
                    "notes": f"Dangling evidence references detected: {dangling_notes}",
                })
                validation_obj.warnings.append(f"Dangling evidence citations detected: {dangling_notes}")

        self._emit(
            run_id=run_id,
            event_type=EventType.VALIDATION_COMPLETED,
            payload=validation_obj.model_dump(),
        )

        # If validation determines information is insufficient, notify retry
        if validation_obj.status == "insufficient" or not validation_obj.is_valid:
            self._emit(
                run_id=run_id,
                event_type=EventType.VALIDATION_FAILED_RETRY,
                payload={
                    "missing_items": validation_obj.missing_items,
                    "research_needed": validation_obj.research_needed,
                    "attempt": validation_attempts,
                },
            )

        return {
            "validation": validation_obj.model_dump(),
            "validation_attempts": validation_attempts,
            "iteration": iteration,
        }

    async def research_step(self, state: AgentState) -> Dict[str, Any]:
        """Node 6b: Bounded research retry step dispatched when validation detects gaps."""
        run_id = state.get("run_id", "unknown")
        validation = state.get("validation") or {}
        validation_retries = state.get("validation_retries", 0) + 1
        iteration = state.get("iteration", 0) + 1

        query = validation.get("research_needed")
        if not query:
            missing = validation.get("missing_items", [])
            query = missing[0] if missing else f"Technical sizing benchmarks for {state.get('task', '')[:50]}"

        logger.info(
            "[Node: research_step] Formulating targeted research query: '%s' (Retry %d)",
            query,
            validation_retries,
        )

        new_step = {
            "id": 100 + validation_retries,
            "objective": f"Targeted research to fill validation gap: {query[:60]}",
            "tool": "web_search",
            "inputs": {"query": query, "max_results": 4},
            "success_criteria": "Acquire verified external documentation or published benchmark evidence for missing constraints.",
            "status": StepStatus.PENDING.value,
        }

        self._emit(
            run_id=run_id,
            event_type=EventType.RESEARCH_STARTED,
            payload=new_step,
            step_id=new_step["id"],
        )

        return {
            "research_queue": [new_step],
            "validation_retries": validation_retries,
            "iteration": iteration,
        }

    async def finalize(self, state: AgentState) -> Dict[str, Any]:
        """Node 7: Synthesize comprehensive 15-Section Engineering Decision Report."""
        run_id = state.get("run_id", "unknown")
        iteration = state.get("iteration", 0) + 1
        plan_dict = state.get("plan") or {}
        normalized = state.get("normalized_task") or {}

        logger.info("[Node: finalize] Finalizing 15-Section Decision Report for run %s", run_id)

        evidence_items = state.get("evidence", [])
        evidence_ledger_str = "\n".join([
            f"{e.get('id')}: {e.get('title')} ({e.get('url')}) - Claim: {e.get('claim')} [Excerpt: {e.get('excerpt')[:150]}]"
            for e in evidence_items
        ]) or "No external evidence entries."

        prompt = FINALIZE_PROMPT.format(
            task=state.get("task", ""),
            normalized_task=normalized.get("normalized_task", ""),
            assumptions=plan_dict.get("assumptions", []),
            observations="\n".join(state.get("observations", [])),
            calculations=state.get("calculations", []),
            evidence_ledger=evidence_ledger_str,
        )

        final_obj: FinalResult = await self.llm.generate_structured(
            prompt=prompt,
            schema=FinalResult,
            system=FINALIZE_SYSTEM,
        )

        # Merge actual collected evidence items into FinalResult
        if evidence_items:
            final_obj.evidence = [EvidenceItem.model_validate(e) for e in evidence_items]

        # Enforce Evidence Integrity:
        # Ensure every supporting_evidence_id referenced by a DecisionItem exists in actual evidence ledger.
        # If an evidence ID does not exist, do not silently invent it; drop the dangling reference.
        known_evidence_ids = {
            str(e.get("id") or e.get("evidence_id"))
            for e in evidence_items
            if (e.get("id") or e.get("evidence_id"))
        }
        if not known_evidence_ids and final_obj.evidence:
            known_evidence_ids = {str(e.id) for e in final_obj.evidence if e.id}

        for dec in final_obj.decisions:
            valid_ids = []
            for ev_id in dec.supporting_evidence_ids:
                if str(ev_id) in known_evidence_ids:
                    valid_ids.append(str(ev_id))
                else:
                    logger.warning(
                        "Dangling evidence reference '%s' in decision %s not found in Evidence Ledger; dropped without fabricating evidence.",
                        ev_id,
                        dec.id,
                    )
            dec.supporting_evidence_ids = valid_ids

        # Ensure decisions exist and emit DECISION_RECORDED events
        for dec in final_obj.decisions:
            self._emit(
                run_id=run_id,
                event_type=EventType.DECISION_RECORDED,
                payload=dec.model_dump(),
            )

        if state.get("observations"):
            final_obj.observations = state.get("observations", [])

        self._emit(
            run_id=run_id,
            event_type=EventType.FINALIZED,
            payload=final_obj.model_dump(),
        )

        return {
            "final_result": final_obj.model_dump(),
            "decisions": [d.model_dump() for d in final_obj.decisions],
            "status": "COMPLETED",
            "iteration": iteration,
        }
