"""API tests validating REST endpoints, health probes, and execution lifecycle."""

from fastapi.testclient import TestClient


def test_health_live(client: TestClient):
    """Verify liveness probe returns 200 OK."""
    resp = client.get("/health/live")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "alive"
    assert "version" in data


def test_health_ready(client: TestClient):
    """Verify readiness probe confirms database connectivity."""
    resp = client.get("/health/ready")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ready"
    assert data["database"] == "connected"


def test_create_and_execute_run_sync(client: TestClient):
    """Verify creating and synchronously running an engineering task end-to-end."""
    payload = {
        "task": "Size memory and nodes for 500k RPS cache cluster.",
        "constraints": {"max_memory_overhead": 0.25},
    }

    # Execute with sync=True
    create_resp = client.post("/api/v1/runs?sync=true", json=payload)
    assert create_resp.status_code == 201
    run_meta = create_resp.json()
    run_id = run_meta["run_id"]
    assert run_meta["status"] in ("COMPLETED", "RUNNING")

    # Fetch Run state
    get_resp = client.get(f"/api/v1/runs/{run_id}")
    assert get_resp.status_code == 200
    run_data = get_resp.json()
    assert run_data["run_id"] == run_id
    assert run_data["status"] == "COMPLETED"
    assert run_data["plan"] is not None
    assert len(run_data["plan"]["steps"]) > 0

    # Fetch Events
    events_resp = client.get(f"/api/v1/runs/{run_id}/events")
    assert events_resp.status_code == 200
    events = events_resp.json()
    assert len(events) >= 5
    event_types = [e["event_type"] for e in events]
    assert "RUN_STARTED" in event_types
    assert "TASK_NORMALIZED" in event_types
    assert "FINALIZED" in event_types

    # Fetch Tools
    tools_resp = client.get(f"/api/v1/runs/{run_id}/tools")
    assert tools_resp.status_code == 200
    tool_events = tools_resp.json()
    assert len(tool_events) >= 1
    assert tool_events[0]["tool_name"] == "calculator"
    assert tool_events[0]["status"] == "success"

    # Fetch Final Result
    result_resp = client.get(f"/api/v1/runs/{run_id}/result")
    assert result_resp.status_code == 200
    result = result_resp.json()
    assert "executive_summary" in result
    assert "final_answer" in result
    assert len(result["decision_trace"]) > 0


def test_list_runs_and_metrics(client: TestClient):
    """Verify run listing and dashboard metrics endpoints."""
    # List runs
    list_resp = client.get("/api/v1/runs?limit=10")
    assert list_resp.status_code == 200
    runs = list_resp.json()
    assert isinstance(runs, list)

    # Metrics
    metrics_resp = client.get("/api/v1/metrics")
    assert metrics_resp.status_code == 200
    metrics = metrics_resp.json()
    assert "total_runs" in metrics
    assert "completed_runs" in metrics
    assert "tool_calls" in metrics


def test_get_nonexistent_run_returns_404(client: TestClient):
    """Verify 404 is returned for an invalid run ID."""
    resp = client.get("/api/v1/runs/nonexistent_12345")
    assert resp.status_code == 404


def test_create_run_invalid_task_returns_422(client: TestClient):
    """Verify validation error when task is too short."""
    resp = client.post("/api/v1/runs", json={"task": "hi"})
    assert resp.status_code == 422
