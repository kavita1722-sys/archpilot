"""Tests for EvidenceService extraction from search and fetch results."""

import pytest
from app.schemas.evidence import EvidenceItem
from app.services.evidence_service import EvidenceService


def test_sequential_evidence_ids():
    """Verify evidence IDs follow sequential EV-001 format."""
    service = EvidenceService()
    assert service.next_evidence_id() == "EV-001"
    assert service.next_evidence_id() == "EV-002"
    assert service.next_evidence_id() == "EV-003"


def test_extract_evidence_from_search():
    """Verify conversion of search results to validated EvidenceItem records."""
    service = EvidenceService()
    raw_results = [
        {
            "title": "Qdrant Vector Database Sizing Guide",
            "url": "https://qdrant.tech/documentation/guides/quantization/",
            "snippet": "Scalar quantization reduces memory requirements by 4x. Float32 vectors are compressed to int8.",
            "source": "web",
        },
        {
            "title": "PostgreSQL pgvector Performance Benchmarks",
            "url": "https://github.com/pgvector/pgvector",
            "snippet": "HNSW index benchmarks demonstrate sub-50ms p99 query latency on 1M vectors.",
            "source": "web",
        },
    ]

    items = service.extract_evidence_from_search(raw_results, query="qdrant memory quantization")

    assert len(items) == 2
    for it in items:
        assert isinstance(it, EvidenceItem)
        assert it.id.startswith("EV-")
        assert it.title
        assert it.url.startswith("https://")
        assert it.claim
        assert it.excerpt
        assert it.relevance >= 0.8
        assert it.confidence >= 0.8
        assert it.status == "verified"


def test_extract_evidence_from_fetch():
    """Verify conversion of URL fetch output to a validated EvidenceItem."""
    service = EvidenceService()
    fetch_data = {
        "url": "https://docs.aws.amazon.com/privatelink/",
        "title": "AWS PrivateLink Architecture Overview",
        "content": (
            "AWS PrivateLink establishes private connectivity between Virtual Private Clouds (VPCs) "
            "and supported AWS services without exposing traffic to the public internet. "
            "This satisfies enterprise regulatory and data sovereignty standards."
        ),
    }

    item = service.extract_evidence_from_fetch(fetch_data, topic="privacy VPC")
    assert item is not None
    assert isinstance(item, EvidenceItem)
    assert item.id.startswith("EV-")
    assert "PrivateLink" in item.title
    assert item.source_type == "documentation"
    assert len(item.excerpt) > 20
