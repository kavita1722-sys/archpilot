"""Schemas for the Evidence Ledger and Evidence Filtering."""

from datetime import datetime, timezone
from typing import Literal, Optional
from pydantic import BaseModel, Field


class EvidenceItem(BaseModel):
    """An empirical evidence record grounded in external documentation or search."""

    id: str = Field(..., description="Unique evidence identifier (e.g., 'EV-001').")
    title: str = Field(..., description="Source title or document header.")
    url: str = Field(..., description="Canonical source URL or documentation link.")
    source_type: Literal["documentation", "web", "benchmark", "api", "specification"] = Field(
        default="web", description="Classification of the evidence source."
    )
    claim: str = Field(..., description="Specific technical claim supported by this evidence.")
    excerpt: str = Field(..., description="Verbatim or summarized relevant text snippet.")
    retrieved_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO timestamp when evidence was retrieved.",
    )
    relevance: float = Field(
        default=0.9, ge=0.0, le=1.0, description="Semantic relevance score (0.0 to 1.0)."
    )
    confidence: float = Field(
        default=0.85, ge=0.0, le=1.0, description="Verification confidence score (0.0 to 1.0)."
    )
    status: Literal["verified", "unverified", "contradicted"] = Field(
        default="verified", description="Evidence verification status."
    )


class EvidenceFilterResult(BaseModel):
    """Evaluation outcome assessing whether candidate evidence supports a claim."""

    evaluation: Literal["supporting", "contradicting", "insufficient"] = Field(
        ..., description="Evaluation outcome."
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Evaluator confidence in the assessment."
    )
    reasoning: str = Field(
        ..., description="Explicit analytical rationale explaining the assessment."
    )
