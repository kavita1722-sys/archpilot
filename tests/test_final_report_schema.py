"""Tests for FinalResult engineering report schema and 15-section completeness."""

import pytest
from app.schemas.decision import DecisionItem
from app.schemas.evidence import EvidenceItem
from app.schemas.result import FinalResult


def test_final_result_all_15_sections():
    """Verify FinalResult schema contains all 15 required engineering sections."""
    report = FinalResult(
        executive_summary="Executive summary synthesis for RAG architecture.",
        problem_definition="100,000 PDF document retrieval and generation under strict privacy constraints.",
        requirements=["Ingest 100k PDFs", "Support 20 concurrent users", "Enforce strict privacy", "Budget under $600/mo"],
        assumptions=["ASSUMPTION: 25 chunks per PDF", "ASSUMPTION: 1536-dim embedding vectors"],
        recommended_architecture={"name": "Self-Hosted Qdrant + vLLM", "isolation": "Private VPC"},
        alternative_architecture_a={"name": "PostgreSQL with pgvector"},
        alternative_architecture_b={"name": "AWS OpenSearch Serverless"},
        architecture_comparison=[
            {"dimension": "Privacy", "recommended": "100% Private VPC", "alt_a": "100% Private VPC", "alt_b": "Shared Cloud Host"},
            {"dimension": "Cost", "recommended": "$410/mo", "alt_a": "$380/mo", "alt_b": "$1,100/mo"},
        ],
        capacity_calculations=[
            {"metric": "Raw RAM", "formula": "2.5M * 1536 * 4 / 1024^3", "result": 14.31, "unit": "GB"},
            {"metric": "Quantized RAM", "formula": "14.31 / 4", "result": 3.58, "unit": "GB"},
        ],
        evidence=[
            EvidenceItem(
                id="EV-001",
                title="Qdrant Sizing",
                url="https://qdrant.tech/documentation/guides/quantization/",
                source_type="documentation",
                claim="Scalar quantization reduces memory by 4x.",
                excerpt="Float32 to Int8 quantization reduces memory footprint by 75%.",
                relevance=0.95,
                confidence=0.92,
                status="verified",
            )
        ],
        decisions=[
            DecisionItem(
                id="DEC-001",
                question="Which vector DB engine should be used?",
                recommendation="Deploy self-hosted Qdrant with scalar quantization in private VPC.",
                supporting_evidence_ids=["EV-001"],
                constraints_addressed=["strict privacy", "budget constraint"],
                tradeoffs=["Requires container management vs managed SaaS."],
                assumptions=["2.5M vectors fit in under 10GB RAM."],
                confidence=0.94,
            )
        ],
        trade_offs=["TRADE-OFF: Self-hosting saves money and protects privacy but requires operational maintenance."],
        risks=[{"risk": "GPU Out-Of-Memory during traffic bursts", "impact": "High", "mitigation": "Dynamic queuing with backpressure"}],
        implementation_roadmap=[{"phase": "Phase 1: Ingestion", "deliverables": ["Deploy Qdrant in VPC"]}],
        confidence=0.94,
        evidence_coverage=0.95,
    )

    # 1. Executive Summary
    assert report.executive_summary
    # 2. Problem Definition
    assert report.problem_definition
    # 3. Requirements
    assert len(report.requirements) == 4
    # 4. Assumptions
    assert len(report.assumptions) == 2
    # 5. Recommended Architecture
    assert report.recommended_architecture
    # 6. Alternative Architecture A
    assert report.alternative_architecture_a
    # 7. Alternative Architecture B
    assert report.alternative_architecture_b
    # 8. Architecture Comparison
    assert len(report.architecture_comparison) == 2
    # 9. Capacity Calculations
    assert len(report.capacity_calculations) == 2
    # 10. Evidence
    assert len(report.evidence) == 1
    assert report.evidence[0].id == "EV-001"
    # 11. Decisions
    assert len(report.decisions) == 1
    assert report.decisions[0].id == "DEC-001"
    # 12. Trade-offs
    assert len(report.trade_offs) == 1
    # 13. Risks
    assert len(report.risks) == 1
    # 14. Implementation Roadmap
    assert len(report.implementation_roadmap) == 1
    # 15. Confidence & Evidence Coverage
    assert report.confidence == 0.94
    assert report.evidence_coverage == 0.95
