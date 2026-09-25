"""Bounded execution policies, iteration guards, and decision limits."""

from app.agent.state import AgentState

MAX_STEPS: int = 6
MAX_TOOL_RETRIES: int = 2
MAX_VALIDATION_RETRIES: int = 2
MAX_ITERATIONS: int = 16


def has_more_steps(state: AgentState) -> bool:
    """Evaluate whether the plan has remaining unexecuted steps."""
    plan = state.get("plan")
    if not plan:
        return False

    steps = plan.get("steps", [])
    current_index = state.get("current_step_index", 0)

    # Respect MAX_STEPS upper boundary
    if current_index >= min(len(steps), MAX_STEPS):
        return False

    return True


def is_iteration_limit_exceeded(state: AgentState) -> bool:
    """Guard against infinite agent loops."""
    iteration = state.get("iteration", 0)
    max_iter = state.get("max_iterations", MAX_ITERATIONS)
    return iteration >= max_iter


def can_retry_tool(state: AgentState) -> bool:
    """Check if tool execution retry quota has not been exhausted."""
    retries = state.get("tool_retries", 0)
    max_retries = state.get("max_tool_retries", MAX_TOOL_RETRIES)
    return retries < max_retries


def can_retry_validation(state: AgentState) -> bool:
    """Check if validation failure replan/retry quota remains."""
    retries = state.get("validation_retries", 0)
    max_retries = state.get("max_validation_retries", MAX_VALIDATION_RETRIES)
    return retries < max_retries


def needs_research_retry(state: AgentState) -> bool:
    """Determine whether a research retry is warranted and permitted."""
    validation = state.get("validation")
    if not validation:
        return False

    is_insufficient = (
        validation.get("status") == "insufficient"
        or validation.get("is_valid") is False
        or validation.get("evidence_coverage", 1.0) < 0.8
    )

    return is_insufficient and can_retry_validation(state) and not is_iteration_limit_exceeded(state)

