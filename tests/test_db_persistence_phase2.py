"""Tests for Phase 2 database persistence: Evidence, Decisions, and Final Reports."""

import pytest
from app.db.models import DecisionModel, EvidenceModel, FinalReportModel, RunModel
from app.db.repository import RunRepository
from app.services.run_service import RunService


def test_evidence_persistence(db_session):
    """Verify storing and retrieving items from the Evidence Ledger."""
    repo = RunRepository(db_session)
    run = repo.create_run(run_id="run_ev_test", task="Test Evidence Persistence")

    item = repo.add_evidence(
        run_id="run_ev_test",
        evidence_id="EV-001",
        title="PostgreSQL Documentation",
        url="https://postgresql.org/docs/",
        source_type="documentation",
        claim="PostgreSQL pgvector supports HNSW indexing with cosine similarity.",
        excerpt="The HNSW index provides high recall and fast approximate nearest neighbor search.",
        relevance=0.94,
        confidence=0.89,
        status="verified",
    )

    assert item.id is not None
    assert item.evidence_id == "EV-001"

    retrieved = repo.get_evidence_for_run("run_ev_test")
    assert len(retrieved) == 1
    assert retrieved[0].evidence_id == "EV-001"
    assert retrieved[0].relevance == 0.94
    assert retrieved[0].confidence == 0.89
    assert retrieved[0].status == "verified"


def test_decision_persistence(db_session):
    """Verify storing and retrieving items from the Decision Ledger."""
    repo = RunRepository(db_session)
    run = repo.create_run(run_id="run_dec_test", task="Test Decision Persistence")

    decision = repo.add_decision(
        run_id="run_dec_test",
        decision_id="DEC-001",
        question="Which storage engine should be used?",
        recommendation="Deploy self-hosted Qdrant inside private VPC.",
        supporting_evidence_ids=["EV-001", "EV-004"],
        constraints_addressed=["privacy", "scale", "cost"],
        tradeoffs=["Requires container ops vs SaaS."],
        assumptions=["2.5M vectors fit in RAM."],
        confidence=0.86,
    )

    assert decision.id is not None
    assert decision.decision_id == "DEC-001"

    decisions = repo.get_decisions_for_run("run_dec_test")
    assert len(decisions) == 1
    assert decisions[0].decision_id == "DEC-001"
    assert decisions[0].confidence == 0.86


def test_run_service_evidence_and_decisions_getters(db_session, mock_llm, tool_registry):
    """Verify RunService helper methods for fetching evidence and decisions."""
    service = RunService(db=db_session, llm=mock_llm, tools=tool_registry)
    run = service.create_run(task="Check Service Getters")

    # Add evidence via repo
    service.repo.add_evidence(
        run_id=run.id,
        evidence_id="EV-101",
        title="Test Benchmarks",
        url="https://benchmark.org",
        source_type="benchmark",
        claim="Memory footprint scales linearly.",
        excerpt="Linear scaling benchmark excerpt.",
        relevance=0.91,
        confidence=0.88,
    )

    # Add decision via repo
    service.repo.add_decision(
        run_id=run.id,
        decision_id="DEC-101",
        question="Which node type?",
        recommendation="EC2 m6i.xlarge",
        supporting_evidence_ids=["EV-101"],
        constraints_addressed=["RAM"],
        tradeoffs=["Cost"],
        assumptions=["Peak traffic"],
        confidence=0.90,
    )

    evidence_list = service.get_run_evidence(run.id)
    assert len(evidence_list) == 1
    assert evidence_list[0]["evidence_id"] == "EV-101"

    decisions_list = service.get_run_decisions(run.id)
    assert len(decisions_list) == 1
    assert decisions_list[0]["decision_id"] == "DEC-101"
    assert "EV-101" in decisions_list[0]["supporting_evidence_ids"]
