"""Tests for validation routing and bounded research retry loops."""

import pytest
from app.agent.policies import needs_research_retry
from app.agent.state import AgentState
from app.schemas.result import ValidationResult


def test_needs_research_retry_when_insufficient():
    """Verify research retry is triggered when validation status is insufficient and quota remains."""
    state: AgentState = {
        "validation": {
            "status": "insufficient",
            "is_valid": False,
            "evidence_coverage": 0.60,
            "missing_items": ["vector database memory benchmarks"],
            "research_needed": "qdrant scalar quantization memory ratio",
        },
        "validation_retries": 0,
        "max_validation_retries": 2,
        "iteration": 5,
        "max_iterations": 16,
    }

    assert needs_research_retry(state) is True


def test_needs_research_retry_stops_at_max_retries():
    """Verify bounded research loop never exceeds MAX_VALIDATION_RETRIES (stops at 2)."""
    state: AgentState = {
        "validation": {
            "status": "insufficient",
            "is_valid": False,
            "evidence_coverage": 0.60,
        },
        "validation_retries": 2,  # Quota exhausted
        "max_validation_retries": 2,
        "iteration": 8,
        "max_iterations": 16,
    }

    assert needs_research_retry(state) is False


def test_needs_research_retry_passed_validation():
    """Verify research retry is NOT triggered when validation passes."""
    state: AgentState = {
        "validation": {
            "status": "passed",
            "is_valid": True,
            "evidence_coverage": 0.94,
        },
        "validation_retries": 0,
        "max_validation_retries": 2,
        "iteration": 5,
        "max_iterations": 16,
    }

    assert needs_research_retry(state) is False
