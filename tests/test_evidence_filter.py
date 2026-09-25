"""Tests for EvidenceFilter credibility evaluation (supporting, contradicting, insufficient)."""

import pytest
from app.schemas.evidence import EvidenceFilterResult, EvidenceItem
from app.services.evidence_service import EvidenceService


def test_evidence_filter_supporting():
    """Verify EvidenceFilter correctly identifies supporting evidence."""
    service = EvidenceService()
    candidate = EvidenceItem(
        id="EV-001",
        title="Qdrant Scalar Quantization Benchmarks",
        url="https://qdrant.tech/documentation/guides/quantization/",
        source_type="documentation",
        claim="Scalar quantization reduces vector RAM usage by up to 4x.",
        excerpt="Scalar quantization compresses vectors from float32 to int8, reducing RAM footprint by 75% with 99.4% recall.",
        relevance=0.95,
        confidence=0.92,
        status="verified",
    )

    result: EvidenceFilterResult = service.filter_evidence(
        claim="Scalar quantization compresses vector memory by 4x",
        candidate=candidate,
    )

    assert result.evaluation == "supporting"
    assert result.confidence >= 0.70
    assert "substantiates" in result.reasoning or "verified" in result.reasoning


def test_evidence_filter_contradicting():
    """Verify EvidenceFilter correctly flags contradictory evidence."""
    service = EvidenceService()
    candidate = EvidenceItem(
        id="EV-002",
        title="PostgreSQL pgvector Limits",
        url="https://example.com/pgvector-limits",
        source_type="documentation",
        claim="pgvector cannot support real-time clustering",
        excerpt="pgvector is not recommended for high concurrency workloads exceeding 10,000 QPS and cannot support sub-millisecond p99 latency.",
        relevance=0.90,
        confidence=0.88,
        status="verified",
    )

    result: EvidenceFilterResult = service.filter_evidence(
        claim="pgvector is recommended for high concurrency workloads exceeding 10,000 QPS",
        candidate=candidate,
    )

    assert result.evaluation == "contradicting"
    assert result.confidence >= 0.8
    assert "contradiction" in result.reasoning.lower() or "violation" in result.reasoning.lower()


def test_evidence_filter_insufficient():
    """Verify EvidenceFilter flags irrelevant evidence as insufficient."""
    service = EvidenceService()
    candidate = EvidenceItem(
        id="EV-003",
        title="General Web Design Principles",
        url="https://example.com/css-design",
        source_type="web",
        claim="Modern typography and CSS frameworks",
        excerpt="Use modern fonts like Inter and Outfit for responsive dashboards.",
        relevance=0.3,
        confidence=0.5,
        status="unverified",
    )

    result: EvidenceFilterResult = service.filter_evidence(
        claim="Qdrant scalar quantization compresses 1536 dimension vectors into RAM",
        candidate=candidate,
    )

    assert result.evaluation == "insufficient"
    assert "sufficient" in result.reasoning.lower()
