"""Schemas for agent validation and the final engineering decision report."""

from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field
from app.schemas.decision import DecisionItem
from app.schemas.evidence import EvidenceItem


class ValidationResult(BaseModel):
    """Quality and completeness evaluation of evidence, constraints, and calculations."""

    status: Literal["passed", "insufficient"] = Field(
        default="passed", description="Validation outcome."
    )
    is_valid: bool = Field(
        default=True, description="Backwards-compatible boolean flag indicating if validation passed."
    )
    score: float = Field(
        default=0.95, ge=0.0, le=1.0, description="Overall verification score."
    )
    evidence_coverage: float = Field(
        default=0.92, ge=0.0, le=1.0, description="Proportion of external claims backed by verified evidence."
    )
    constraint_coverage: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Proportion of user technical constraints addressed."
    )
    calculation_validity: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Verification score of deterministic calculations."
    )
    missing_items: List[str] = Field(
        default_factory=list, description="Missing technical constraints, evidence, or calculation items."
    )
    warnings: List[str] = Field(
        default_factory=list, description="Non-fatal warnings or identified architectural risks."
    )
    checks: List[Dict[str, Any]] = Field(
        default_factory=list, description="Checklist verification outcomes."
    )
    research_needed: Optional[str] = Field(
        None, description="Specific targeted query if research retry loop is required."
    )
    feedback: Optional[str] = Field(
        None, description="Actionable critique or instructions for bounded retry."
    )


class FinalResult(BaseModel):
    """The comprehensive 15-section engineering decision deliverable."""

    # 1. Executive Summary
    executive_summary: str = Field(
        ..., description="High-level synthesis and primary architectural decision."
    )

    # 2. Problem Definition
    problem_definition: str = Field(
        default="", description="Formal technical problem statement and operational boundaries."
    )

    # 3. Requirements
    requirements: List[str] = Field(
        default_factory=list, description="Extracted hard technical and operational constraints."
    )

    # 4. Assumptions
    assumptions: List[str] = Field(
        default_factory=list, description="Engineering assumptions (e.g. read/write ratio, chunk sizes)."
    )

    # 5. Recommended Architecture
    recommended_architecture: Union[Dict[str, Any], str] = Field(
        default_factory=dict, description="Detailed specification of the selected architecture."
    )

    # 6. Alternative Architecture A
    alternative_architecture_a: Union[Dict[str, Any], str] = Field(
        default_factory=dict, description="First viable competing architectural option."
    )

    # 7. Alternative Architecture B
    alternative_architecture_b: Union[Dict[str, Any], str] = Field(
        default_factory=dict, description="Second viable competing architectural option."
    )

    # 8. Architecture Comparison Matrix
    architecture_comparison: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Structured comparison matrix (Cost, Latency, Privacy, Scalability, Maintenance).",
    )

    # 9. Capacity Calculations
    capacity_calculations: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Deterministic calculations with formulas, inputs, results, and units.",
    )

    # 10. Evidence (with EV-xxx IDs)
    evidence: List[EvidenceItem] = Field(
        default_factory=list, description="Evidence items supporting claims and decisions."
    )

    # 11. Decisions (with DEC-xxx IDs)
    decisions: List[DecisionItem] = Field(
        default_factory=list, description="Explicit decision records linking evidence to trade-offs."
    )

    # 12. Trade-offs
    trade_offs: List[str] = Field(
        default_factory=list, description="Explicit technical and operational trade-offs accepted."
    )

    # 13. Risks & Mitigations
    risks: List[Union[Dict[str, Any], str]] = Field(
        default_factory=list, description="Identified failure modes, bottlenecks, and mitigations."
    )

    # 14. Implementation Roadmap
    implementation_roadmap: List[Union[Dict[str, Any], str]] = Field(
        default_factory=list, description="Step-by-step phased execution and rollout roadmap."
    )

    # 15. Metrics
    confidence: float = Field(
        default=0.92, ge=0.0, le=1.0, description="Overall confidence score for the recommendation."
    )
    evidence_coverage: float = Field(
        default=0.95, ge=0.0, le=1.0, description="Proportion of external claims backed by verified evidence."
    )

    # Backward compatibility fields for Phase 1
    plan_summary: str = Field(default="", description="Summary of execution plan.")
    actions_taken: List[Dict[str, Any]] = Field(
        default_factory=list, description="Tools executed."
    )
    observations: List[str] = Field(
        default_factory=list, description="Empirical observations."
    )
    calculations: List[Dict[str, Any]] = Field(
        default_factory=list, description="Deterministic calculations."
    )
    final_answer: str = Field(
        default="", description="Synthesized technical specification."
    )
    decision_trace: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Traceability chain: Decision -> Constraints -> Evidence -> Calculation -> Trade-off.",
    )
