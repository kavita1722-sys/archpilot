"""Strongly typed state definition for the ArchPilot LangGraph workflow."""

from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict


class AgentState(TypedDict, total=False):
    """Execution state preserved across all LangGraph nodes."""

    # Run identification and inputs
    run_id: str
    task: str
    constraints: Dict[str, Any]

    # Normalized requirements
    normalized_task: Optional[Dict[str, Any]]

    # Structured plan
    plan: Optional[Dict[str, Any]]

    # Step execution tracking
    current_step_id: Optional[int]
    current_step_index: int  # 0-based pointer into plan.steps

    # Evidence, observations, and tool outcomes
    observations: List[str]
    tool_events: List[Dict[str, Any]]
    calculations: List[Dict[str, Any]]

    # Quality and validation
    validation: Optional[Dict[str, Any]]

    # Final engineering synthesis
    final_result: Optional[Dict[str, Any]]

    # Loop guardrails and bounded execution controls
    iteration: int
    max_iterations: int
    tool_retries: int
    max_tool_retries: int
    validation_retries: int
    max_validation_retries: int

    # Errors and status
    errors: List[str]
    status: str  # "RUNNING", "COMPLETED", "FAILED"
