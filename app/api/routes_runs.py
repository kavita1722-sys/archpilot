"""API route handlers for managing engineering decision runs."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from app.api.dependencies import get_run_service
from app.schemas.result import FinalResult
from app.schemas.task import TaskCreate, TaskResponse
from app.services.run_service import RunService

router = APIRouter(prefix="/api/v1", tags=["Runs"])


@router.post(
    "/runs",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a new engineering task",
)
async def create_run(
    payload: TaskCreate,
    background_tasks: BackgroundTasks,
    sync: bool = Query(
        False, description="If True, execute synchronously before returning response."
    ),
    service: RunService = Depends(get_run_service),
) -> TaskResponse:
    """Accept an engineering task, initialize state, and trigger the agent workflow."""
    run = service.create_run(task=payload.task, constraints=payload.constraints)

    if sync:
        await service.execute_run(run.id)
        refreshed = service.get_run(run.id)
        return TaskResponse(
            run_id=run.id,
            status=refreshed["status"] if refreshed else "COMPLETED",
            task=run.task,
            created_at=run.created_at,
        )

    # Launch in background
    background_tasks.add_task(service.execute_run, run.id)

    return TaskResponse(
        run_id=run.id,
        status="PENDING",
        task=run.task,
        created_at=run.created_at,
    )


@router.get(
    "/runs/{run_id}",
    summary="Get execution status and state of a run",
    status_code=status.HTTP_200_OK,
)
async def get_run(
    run_id: str,
    service: RunService = Depends(get_run_service),
) -> Dict[str, Any]:
    """Retrieve full details of an engineering run, including normalized task and plan."""
    run_data = service.get_run(run_id)
    if not run_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run '{run_id}' not found.",
        )
    return run_data


@router.get(
    "/runs/{run_id}/events",
    summary="Get chronological timeline events for a run",
    status_code=status.HTTP_200_OK,
)
async def get_run_events(
    run_id: str,
    service: RunService = Depends(get_run_service),
) -> List[Dict[str, Any]]:
    """Retrieve the audit log of all state transitions and milestones."""
    run_data = service.get_run(run_id)
    if not run_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run '{run_id}' not found.",
        )
    return service.get_run_events(run_id)


@router.get(
    "/runs/{run_id}/tools",
    summary="Get tool execution telemetry for a run",
    status_code=status.HTTP_200_OK,
)
async def get_run_tool_events(
    run_id: str,
    service: RunService = Depends(get_run_service),
) -> List[Dict[str, Any]]:
    """Retrieve structured tool invocation telemetry (inputs, outputs, latency)."""
    run_data = service.get_run(run_id)
    if not run_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run '{run_id}' not found.",
        )
    return service.get_run_tool_events(run_id)


@router.get(
    "/runs/{run_id}/result",
    summary="Get the final synthesized engineering decision",
    status_code=status.HTTP_200_OK,
)
async def get_run_result(
    run_id: str,
    service: RunService = Depends(get_run_service),
) -> Dict[str, Any]:
    """Retrieve the final evidence-driven decision document."""
    run_data = service.get_run(run_id)
    if not run_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run '{run_id}' not found.",
        )

    result = service.get_run_result(run_id)
    if not result:
        if run_data["status"] in ("PENDING", "RUNNING"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Run '{run_id}' is still in status '{run_data['status']}'. Result not ready.",
            )
        elif run_data["status"] == "FAILED":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Run failed: {run_data.get('error_message')}",
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Final result not available for this run.",
        )
    return result


@router.get(
    "/runs/{run_id}/evidence",
    summary="Get Evidence Ledger items for a run",
    status_code=status.HTTP_200_OK,
)
async def get_run_evidence(
    run_id: str,
    service: RunService = Depends(get_run_service),
) -> List[Dict[str, Any]]:
    """Retrieve all evidence collected and verified in the Evidence Ledger."""
    run_data = service.get_run(run_id)
    if not run_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run '{run_id}' not found.",
        )
    return service.get_run_evidence(run_id)


@router.get(
    "/runs/{run_id}/decisions",
    summary="Get Decision Ledger items for a run",
    status_code=status.HTTP_200_OK,
)
async def get_run_decisions(
    run_id: str,
    service: RunService = Depends(get_run_service),
) -> List[Dict[str, Any]]:
    """Retrieve all structured architectural decisions from the Decision Ledger."""
    run_data = service.get_run(run_id)
    if not run_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run '{run_id}' not found.",
        )
    return service.get_run_decisions(run_id)


@router.get(
    "/runs",
    summary="List recent engineering runs",
    status_code=status.HTTP_200_OK,
)
async def list_runs(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: RunService = Depends(get_run_service),
) -> List[Dict[str, Any]]:
    """List historical engineering runs with status summaries."""
    return service.list_runs(limit=limit, offset=offset)


@router.get(
    "/metrics",
    summary="Get high-level system dashboard metrics",
    status_code=status.HTTP_200_OK,
)
async def get_metrics(
    service: RunService = Depends(get_run_service),
) -> Dict[str, int]:
    """Return aggregated metrics (total runs, completed, active, tool calls)."""
    return service.get_dashboard_metrics()
