"""Tests for Decision Ledger model schema and validation."""

import pytest
from pydantic import ValidationError
from app.schemas.decision import DecisionItem


def test_decision_item_valid():
    """Verify valid DecisionItem instantiation and properties."""
    decision = DecisionItem(
        id="DEC-001",
        question="Which vector database architecture should be selected?",
        recommendation="Deploy self-hosted Qdrant with int8 scalar quantization in private VPC.",
        supporting_evidence_ids=["EV-001", "EV-002"],
        constraints_addressed=["strict privacy", "constrained budget", "100k PDFs scale"],
        tradeoffs=[
            "Requires container operational management vs serverless SaaS, but eliminates per-token API costs.",
            "Int8 quantization trades 0.5% precision for 4x memory savings.",
        ],
        assumptions=[
            "100,000 PDFs yield ~2.5 million vectors",
            "Peak throughput bounded at 2.0 QPS",
        ],
        confidence=0.94,
    )

    assert decision.id == "DEC-001"
    assert "Qdrant" in decision.recommendation
    assert len(decision.supporting_evidence_ids) == 2
    assert "EV-001" in decision.supporting_evidence_ids
    assert len(decision.constraints_addressed) == 3
    assert len(decision.tradeoffs) == 2
    assert decision.confidence == 0.94


def test_decision_item_missing_required_fields():
    """Verify DecisionItem rejects missing mandatory fields."""
    with pytest.raises(ValidationError):
        # Missing question and recommendation
        DecisionItem(id="DEC-002")


def test_evidence_integrity_dangling_reference_detection():
    """Verify check_evidence_integrity detects non-existent evidence IDs without inventing them."""
    from app.services.evidence_service import EvidenceService
    from app.schemas.evidence import EvidenceItem

    service = EvidenceService()
    real_evidence = [
        EvidenceItem(
            id="EV-001",
            title="Qdrant Docs",
            url="https://qdrant.tech",
            claim="Scalar quantization reduces memory 4x",
            excerpt="Quantization reduces memory footprint.",
        )
    ]
    decisions = [
        DecisionItem(
            id="DEC-001",
            question="Which DB?",
            recommendation="Use Qdrant",
            supporting_evidence_ids=["EV-001", "EV-999"],  # EV-999 is dangling
        )
    ]

    result = service.check_evidence_integrity(decisions=decisions, evidence=real_evidence)
    assert result["is_valid"] is False
    assert len(result["dangling_references"]) == 1
    assert result["dangling_references"][0]["decision_id"] == "DEC-001"
    assert result["dangling_references"][0]["dangling_evidence_id"] == "EV-999"


def test_evidence_integrity_sanitization_does_not_invent_evidence():
    """Verify sanitize_decision_evidence_references drops invalid IDs without fabricating evidence."""
    from app.services.evidence_service import EvidenceService
    from app.schemas.evidence import EvidenceItem

    service = EvidenceService()
    real_evidence = [
        EvidenceItem(
            id="EV-001",
            title="Qdrant Docs",
            url="https://qdrant.tech",
            claim="Scalar quantization reduces memory 4x",
            excerpt="Quantization reduces memory footprint.",
        )
    ]
    decisions = [
        DecisionItem(
            id="DEC-001",
            question="Which DB?",
            recommendation="Use Qdrant",
            supporting_evidence_ids=["EV-001", "EV-GHOST"],
        )
    ]

    sanitized = service.sanitize_decision_evidence_references(decisions=decisions, evidence=real_evidence)
    assert len(sanitized) == 1
    assert sanitized[0].supporting_evidence_ids == ["EV-001"]
    assert "EV-GHOST" not in sanitized[0].supporting_evidence_ids
    # Ensure evidence ledger still only contains real evidence (not silently invented)
    assert len(real_evidence) == 1
    assert real_evidence[0].id == "EV-001"

