from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Categorized lifecycle events during agentic execution."""

    RUN_STARTED = "RUN_STARTED"
    TASK_NORMALIZED = "TASK_NORMALIZED"
    PLAN_CREATED = "PLAN_CREATED"
    STEP_STARTED = "STEP_STARTED"
    TOOL_CALLED = "TOOL_CALLED"
    TOOL_COMPLETED = "TOOL_COMPLETED"
    OBSERVATION_ADDED = "OBSERVATION_ADDED"
    EVIDENCE_COLLECTED = "EVIDENCE_COLLECTED"
    DECISION_RECORDED = "DECISION_RECORDED"
    STEP_COMPLETED = "STEP_COMPLETED"
    VALIDATION_COMPLETED = "VALIDATION_COMPLETED"
    VALIDATION_FAILED_RETRY = "VALIDATION_FAILED_RETRY"
    RESEARCH_STARTED = "RESEARCH_STARTED"
    FINALIZED = "FINALIZED"
    RUN_FAILED = "RUN_FAILED"


class ExecutionEvent(BaseModel):
    """Structured event capturing an immutable execution milestone."""

    id: str = Field(..., description="Unique event ID.")
    run_id: str = Field(..., description="Associated run ID.")
    event_type: EventType = Field(..., description="Type of event recorded.")
    step_id: Optional[int] = Field(None, description="Plan step id if applicable.")
    payload: Dict[str, Any] = Field(
        default_factory=dict, description="Metadata or structured data associated with event."
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="UTC timestamp of the event."
    )

