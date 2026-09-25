"""End-to-End test executing the canonical ArchPilot engineering challenge.

Canonical Task:
"Design a production-ready RAG architecture for 100,000 PDF documents, 20 concurrent users,
strict data privacy, and a constrained monthly infrastructure budget. Compare two viable architectures,
identify bottlenecks, calculate approximate storage and throughput requirements, and recommend an implementation roadmap."
"""

import pytest
from app.services.run_service import RunService

CANONICAL_RAG_TASK = (
    "Design a production-ready RAG architecture for 100,000 PDF documents, 20 concurrent users, "
    "strict data privacy, and a constrained monthly infrastructure budget. Compare two viable architectures, "
    "identify bottlenecks, calculate approximate storage and throughput requirements, and recommend an implementation roadmap."
)


@pytest.mark.asyncio
async def test_canonical_rag_task_e2e(db_session, mock_llm, tool_registry):
    """Execute the full canonical RAG engineering task and verify the entire intelligence pipeline."""
    service = RunService(db=db_session, llm=mock_llm, tools=tool_registry)

    # 1. Create Run
    run = service.create_run(
        task=CANONICAL_RAG_TASK,
        constraints={
            "document_volume": "100,000 PDFs",
            "concurrency": 20,
            "privacy": "strict_vpc",
            "budget": "<$600/month",
        },
    )
    assert run.id.startswith("run_")
    assert run.status == "PENDING"

    # 2. Execute Run through LangGraph
    final_state = await service.execute_run(run.id)

    # Verify execution status
    assert final_state["status"] == "COMPLETED"

    # 3. Verify Plan Formulated
    plan = final_state.get("plan")
    assert plan is not None
    assert len(plan["steps"]) >= 3
    tool_names = [s["tool"] for s in plan["steps"]]
    assert "calculator" in tool_names
    assert "web_search" in tool_names or "url_fetch" in tool_names

    # 4. Verify Tool Telemetry Recorded
    tool_events = service.get_run_tool_events(run.id)
    assert len(tool_events) >= 3
    executed_tools = {te["tool_name"] for te in tool_events}
    assert "calculator" in executed_tools

    # 5. Verify Evidence Collected in Ledger
    evidence_items = service.get_run_evidence(run.id)
    assert len(evidence_items) > 0
    for ev in evidence_items:
        assert ev["evidence_id"].startswith("EV-")
        assert ev["title"]
        assert ev["url"]
        assert ev["claim"]
        assert ev["excerpt"]
        assert ev["relevance"] > 0.0
        assert ev["confidence"] > 0.0

    # 6. Verify Validation Center
    validation = final_state.get("validation")
    assert validation is not None
    assert validation.get("status") == "passed"
    assert validation.get("evidence_coverage", 0.0) >= 0.8
    assert validation.get("constraint_coverage", 0.0) >= 0.8
    assert validation.get("calculation_validity", 0.0) >= 0.8

    # 7. Verify Decision Ledger
    decisions = service.get_run_decisions(run.id)
    assert len(decisions) > 0
    for dec in decisions:
        assert dec["decision_id"].startswith("DEC-")
        assert dec["question"]
        assert dec["recommendation"]
        assert len(dec["supporting_evidence_ids"]) > 0
        assert len(dec["constraints_addressed"]) > 0

    # 8. Verify Comprehensive 15-Section Final Result
    final_report = service.get_run_result(run.id)
    assert final_report is not None
    assert "executive_summary" in final_report
    assert "problem_definition" in final_report
    assert "requirements" in final_report
    assert "assumptions" in final_report
    assert "recommended_architecture" in final_report
    assert "alternative_architecture_a" in final_report
    assert "alternative_architecture_b" in final_report
    assert "architecture_comparison" in final_report
    assert "capacity_calculations" in final_report
    assert "evidence" in final_report
    assert "decisions" in final_report
    assert "trade_offs" in final_report
    assert "risks" in final_report
    assert "implementation_roadmap" in final_report
    assert final_report.get("confidence", 0.0) >= 0.85
    assert final_report.get("evidence_coverage", 0.0) >= 0.85


@pytest.mark.asyncio
async def test_canonical_rag_via_api(client):
    """Verify submitting canonical RAG task synchronously via API and querying evidence/decisions."""
    payload = {
        "task": CANONICAL_RAG_TASK,
        "constraints": {"budget": "constrained", "privacy": "strict"},
    }

    # Submit task synchronously
    response = client.post("/api/v1/runs?sync=true", json=payload)
    assert response.status_code == 201
    data = response.json()
    run_id = data["run_id"]
    assert run_id.startswith("run_")
    assert data["status"] == "COMPLETED"

    # Query evidence endpoint
    ev_resp = client.get(f"/api/v1/runs/{run_id}/evidence")
    assert ev_resp.status_code == 200
    evidence = ev_resp.json()
    assert len(evidence) > 0
    assert any(e["evidence_id"].startswith("EV-") for e in evidence)

    # Query decisions endpoint
    dec_resp = client.get(f"/api/v1/runs/{run_id}/decisions")
    assert dec_resp.status_code == 200
    decisions = dec_resp.json()
    assert len(decisions) > 0
    assert any(d["decision_id"].startswith("DEC-") for d in decisions)

    # Query result endpoint
    res_resp = client.get(f"/api/v1/runs/{run_id}/result")
    assert res_resp.status_code == 200
    res_json = res_resp.json()
    assert "executive_summary" in res_json
    assert "recommended_architecture" in res_json
    assert "capacity_calculations" in res_json
