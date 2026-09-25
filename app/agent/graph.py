"""LangGraph StateGraph assembly for the ArchPilot engineering agent."""

from typing import Any, Callable, Dict, Literal, Optional
from langgraph.graph import END, START, StateGraph
from app.agent.nodes import NodeHandler
from app.agent.policies import (
    has_more_steps,
    is_iteration_limit_exceeded,
    needs_research_retry,
)
from app.agent.state import AgentState
from app.core.logging import logger
from app.llm.base import LLMProvider
from app.schemas.event import EventType
from app.tools.registry import ToolRegistry


def route_after_select_next_step(state: AgentState) -> Literal["execute_tool", "validate"]:
    """Determine whether to execute tool or proceed to validation."""
    if state.get("current_step_id") is not None:
        return "execute_tool"
    return "validate"


def route_after_observe(state: AgentState) -> Literal["select_next_step", "validate"]:
    """Determine whether more steps remain or if workflow advances to validation."""
    if is_iteration_limit_exceeded(state):
        logger.warning("Iteration limit reached; routing directly to validate.")
        return "validate"

    # If research step just completed, return to validate
    if state.get("validation_retries", 0) > 0 and not state.get("research_queue"):
        # We just observed the outcome of a research retry
        return "validate"

    if has_more_steps(state):
        return "select_next_step"

    return "validate"


def route_after_validate(state: AgentState) -> Literal["research_step", "finalize"]:
    """Bounded research loop: if validation is insufficient and retries remain, do research."""
    if needs_research_retry(state):
        logger.info("Validation identified missing evidence; dispatching bounded research step.")
        return "research_step"
    return "finalize"


def create_agent_graph(
    llm: LLMProvider,
    tools: ToolRegistry,
    event_callback: Optional[Callable[[str, EventType, Dict[str, Any], Optional[int]], None]] = None,
):
    """Construct and compile the ArchPilot LangGraph workflow with Bounded Research Loop.

    Args:
        llm: LLMProvider instance.
        tools: ToolRegistry instance.
        event_callback: Optional callback for audit event persistence.

    Returns:
        Compiled LangGraph runnable.
    """
    handler = NodeHandler(llm=llm, tools=tools, event_callback=event_callback)
    workflow = StateGraph(AgentState)

    # Register workflow nodes
    workflow.add_node("normalize_task", handler.normalize_task)
    workflow.add_node("plan", handler.plan)
    workflow.add_node("select_next_step", handler.select_next_step)
    workflow.add_node("execute_tool", handler.execute_tool)
    workflow.add_node("observe", handler.observe)
    workflow.add_node("validate", handler.validate)
    workflow.add_node("research_step", handler.research_step)
    workflow.add_node("finalize", handler.finalize)

    # Connect initial edges
    workflow.add_edge(START, "normalize_task")
    workflow.add_edge("normalize_task", "plan")
    workflow.add_edge("plan", "select_next_step")

    # Conditional edge from select_next_step
    workflow.add_conditional_edges(
        "select_next_step",
        route_after_select_next_step,
        {
            "execute_tool": "execute_tool",
            "validate": "validate",
        },
    )

    # Edge from tool execution to observation
    workflow.add_edge("execute_tool", "observe")

    # Conditional edge from observe: loop to next step or proceed to validate
    workflow.add_conditional_edges(
        "observe",
        route_after_observe,
        {
            "select_next_step": "select_next_step",
            "validate": "validate",
        },
    )

    # Conditional edge from validate: bounded research retry or finalize
    workflow.add_conditional_edges(
        "validate",
        route_after_validate,
        {
            "research_step": "research_step",
            "finalize": "finalize",
        },
    )

    # Edge from research_step back to execute_tool
    workflow.add_edge("research_step", "execute_tool")

    # Finalize -> END
    workflow.add_edge("finalize", END)

    return workflow.compile()
