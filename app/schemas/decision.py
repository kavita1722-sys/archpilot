"""Schemas for Decision Ledger items and architectural conclusions."""

from typing import List
from pydantic import BaseModel, Field


class DecisionItem(BaseModel):
    """An explicit architectural decision grounded in evidence and constrained by trade-offs."""

    id: str = Field(..., description="Unique decision identifier (e.g., 'DEC-001').")
    question: str = Field(..., description="Core architectural question or design dilemma.")
    recommendation: str = Field(..., description="Actionable, authoritative technical recommendation.")
    supporting_evidence_ids: List[str] = Field(
        default_factory=list,
        description="Referenced Evidence Ledger IDs (e.g., ['EV-001', 'EV-004']).",
    )
    constraints_addressed: List[str] = Field(
        default_factory=list,
        description="Project constraints satisfied (e.g., ['privacy', 'scale', 'budget']).",
    )
    tradeoffs: List[str] = Field(
        default_factory=list,
        description="Explicit trade-offs and compromises accepted by choosing this recommendation.",
    )
    assumptions: List[str] = Field(
        default_factory=list,
        description="Assumptions underpinning this recommendation.",
    )
    confidence: float = Field(
        default=0.85, ge=0.0, le=1.0, description="Architectural confidence score (0.0 to 1.0)."
    )
