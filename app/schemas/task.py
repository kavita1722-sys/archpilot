"""Schemas for engineering task input and normalized requirements."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    """Payload accepted to initiate an ArchPilot engineering decision run."""

    task: str = Field(
        ...,
        description="Clear engineering problem statement or architecture query.",
        min_length=5,
        max_length=4000,
        examples=["Design a cache tier for 500,000 requests/sec with 10KB average object size."],
    )
    constraints: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional technical constraints, e.g. latency, SLA, cost ceiling, cloud provider.",
    )


class TaskResponse(BaseModel):
    """Immediate response after submitting an engineering run."""

    run_id: str
    status: str
    task: str
    created_at: datetime


class NormalizedTask(BaseModel):
    """Normalized and structured interpretation of the user's task."""

    normalized_task: str = Field(
        ..., description="Standardized, disambiguated engineering problem statement."
    )
    domain: str = Field(
        ..., description="Engineering domain (e.g., Database Architecture, Caching, Sizing)."
    )
    extracted_constraints: Dict[str, Any] = Field(
        default_factory=dict, description="Normalized quantitative and architectural constraints."
    )
    target_metric: Optional[str] = Field(
        None, description="Primary metric to compute or optimize (e.g., Total RAM in GB, IOPS)."
    )
    requires_calculation: bool = Field(
        True, description="Whether deterministic quantitative calculations are necessary."
    )
    key_variables: List[str] = Field(
        default_factory=list, description="Variables identified for mathematical modeling."
    )
