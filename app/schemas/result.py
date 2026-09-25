"""Schemas for agent validation and the final engineering decision result."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ValidationResult(BaseModel):
    """Quality and completeness evaluation of the observations before finalizing."""

    is_valid: bool = Field(
        ..., description="True if evidence sufficiently answers the task criteria."
    )
    score: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence/completeness score between 0.0 and 1.0."
    )
    checks: List[Dict[str, Any]] = Field(
        default_factory=list, description="Detailed checklist verification outcomes."
    )
    feedback: Optional[str] = Field(
        None, description="Actionable critique or missing details if is_valid is False."
    )


class FinalResult(BaseModel):
    """The structured engineering decision deliverable."""

    executive_summary: str = Field(
        ..., description="High-level synthesis and primary architectural decision."
    )
    plan_summary: str = Field(
        ..., description="Recap of the systematic strategy followed by the agent."
    )
    actions_taken: List[Dict[str, Any]] = Field(
        default_factory=list, description="Step-by-step account of tools executed."
    )
    observations: List[str] = Field(
        default_factory=list, description="Collected empirical observations and evidence."
    )
    calculations: List[Dict[str, Any]] = Field(
        default_factory=list, description="Deterministic calculations and equations verified."
    )
    final_answer: str = Field(
        ..., description="Exhaustive, actionable engineering decision and specification."
    )
    trade_offs: List[str] = Field(
        default_factory=list, description="Identified technical trade-offs and compromises."
    )
    risks: List[str] = Field(
        default_factory=list, description="Operational, scaling, and architectural risks."
    )
    decision_trace: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Traceability chain: Decision -> Constraints -> Evidence -> Calculation -> Trade-off.",
    )
