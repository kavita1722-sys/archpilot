"""Tests for workflow state transitions and bounded execution policies."""

from app.agent.policies import (
    MAX_STEPS,
    can_retry_tool,
    can_retry_validation,
    has_more_steps,
    is_iteration_limit_exceeded,
)
from app.agent.state import AgentState


def test_has_more_steps():
    """Verify has_more_steps accurately compares index with step count."""
    state: AgentState = {
        "plan": {
            "steps": [
                {"id": 1, "tool": "calculator"},
                {"id": 2, "tool": "calculator"},
            ]
        },
        "current_step_index": 0,
    }
    assert has_more_steps(state) is True

    state["current_step_index"] = 1
    assert has_more_steps(state) is True

    state["current_step_index"] = 2
    assert has_more_steps(state) is False


def test_has_more_steps_bounds_to_max_steps():
    """Verify has_more_steps enforces MAX_STEPS upper boundary."""
    state: AgentState = {
        "plan": {
            "steps": [{"id": i, "tool": "calculator"} for i in range(1, 10)]
        },
        "current_step_index": MAX_STEPS,
    }
    assert has_more_steps(state) is False


def test_iteration_limit_guard():
    """Verify loop termination guard prevents unbounded loops."""
    state: AgentState = {"iteration": 5, "max_iterations": 12}
    assert is_iteration_limit_exceeded(state) is False

    state["iteration"] = 12
    assert is_iteration_limit_exceeded(state) is True


def test_retry_policies():
    """Verify tool and validation retry counters adhere to limits."""
    state: AgentState = {
        "tool_retries": 1,
        "max_tool_retries": 2,
        "validation_retries": 2,
        "max_validation_retries": 2,
    }
    assert can_retry_tool(state) is True
    assert can_retry_validation(state) is False
