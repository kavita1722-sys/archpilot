"""Schemas defining structured engineering execution plans."""

from enum import Enum
from typing import Any, Dict, List
from pydantic import BaseModel, Field, field_validator


class StepStatus(str, Enum):
    """Execution status of an individual plan step."""

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class PlanStep(BaseModel):
    """An atomic, executable step inside an engineering plan."""

    id: int = Field(..., description="Step index (1-based sequence).")
    objective: str = Field(..., description="Goal and clear purpose of this step.")
    tool: str = Field(..., description="Name of registered tool to execute.")
    inputs: Dict[str, Any] = Field(
        default_factory=dict, description="Structured parameters passed to the tool."
    )
    success_criteria: str = Field(
        ..., description="Condition that determines whether this step succeeded."
    )
    status: StepStatus = Field(
        default=StepStatus.PENDING, description="Current progress status of the step."
    )


class Plan(BaseModel):
    """Structured plan composed of bounded, verifiable steps."""

    goal: str = Field(..., description="Overall goal and solution hypothesis.")
    assumptions: List[str] = Field(
        default_factory=list, description="Explicit technical assumptions made."
    )
    steps: List[PlanStep] = Field(
        default_factory=list,
        description="Sequential execution steps (maximum 6 steps).",
    )

    @field_validator("steps")
    @classmethod
    def validate_max_steps(cls, v: List[PlanStep]) -> List[PlanStep]:
        if len(v) > 6:
            raise ValueError(f"Plan step count ({len(v)}) exceeds maximum limit of 6 steps.")
        if len(v) == 0:
            raise ValueError("Plan must contain at least 1 step.")
        return v
