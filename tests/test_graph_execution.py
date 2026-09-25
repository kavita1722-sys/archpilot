"""Tests for end-to-end LangGraph execution flow."""

import pytest
from app.agent.graph import create_agent_graph
from app.agent.state import AgentState
from app.llm.mock import MockLLMProvider
from app.schemas.event import EventType
from app.tools.registry import get_default_registry


@pytest.mark.asyncio
async def test_complete_graph_execution_end_to_end():
    """Verify full graph execution: START -> normalize -> plan -> tool -> observe -> validate -> finalize -> END."""
    llm = MockLLMProvider()
    tools = get_default_registry()

    recorded_events = []

    def mock_callback(run_id, event_type, payload, step_id):
        recorded_events.append((event_type, step_id))

    graph = create_agent_graph(llm=llm, tools=tools, event_callback=mock_callback)

    initial_state: AgentState = {
        "run_id": "test_run_123",
        "task": "Size persistent storage and bandwidth for 10M DAU photo sharing service.",
        "constraints": {"replication": 3},
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
        "max_iterations": 12,
        "tool_retries": 0,
        "max_tool_retries": 2,
        "validation_retries": 0,
        "max_validation_retries": 2,
        "errors": [],
        "status": "RUNNING",
    }

    final_state = await graph.ainvoke(initial_state)

    # State outcome assertions
    assert final_state["status"] == "COMPLETED"
    assert final_state["normalized_task"] is not None
    assert final_state["plan"] is not None

    steps = final_state["plan"]["steps"]
    assert len(steps) >= 1
    for step in steps:
        assert step["status"] == "COMPLETED"

    assert len(final_state["tool_events"]) >= len(steps)
    assert len(final_state["calculations"]) >= len(steps)
    assert len(final_state["observations"]) >= len(steps)

    assert final_state["validation"] is not None
    assert final_state["validation"]["is_valid"] is True

    final_result = final_state["final_result"]
    assert final_result is not None
    assert "executive_summary" in final_result
    assert "final_answer" in final_result
    assert len(final_result["decision_trace"]) > 0

    # Milestone events check
    event_types = [ev[0] for ev in recorded_events]
    assert EventType.TASK_NORMALIZED in event_types
    assert EventType.PLAN_CREATED in event_types
    assert EventType.STEP_STARTED in event_types
    assert EventType.TOOL_CALLED in event_types
    assert EventType.TOOL_COMPLETED in event_types
    assert EventType.OBSERVATION_ADDED in event_types
    assert EventType.VALIDATION_COMPLETED in event_types
    assert EventType.FINALIZED in event_types
