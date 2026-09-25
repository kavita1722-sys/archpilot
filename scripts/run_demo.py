"""Interactive terminal runner demonstrating the complete ArchPilot agentic loop."""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import SessionLocal, init_db
from app.llm.mock import MockLLMProvider
from app.services.run_service import RunService
from app.tools.registry import get_default_registry



async def main() -> None:
    print("=" * 70)
    print("ARCHPILOT: Evidence-Driven AI Engineering Decision Agent Demo")
    print("=" * 70)

    # Initialize SQLite database
    init_db()
    db = SessionLocal()

    llm = MockLLMProvider()
    tools = get_default_registry()
    service = RunService(db=db, llm=llm, tools=tools)

    sample_task = (
        "Estimate 1-year persistent storage, replication overhead, and peak ingress network bandwidth "
        "for a photo sharing platform with 10M daily active users uploading 3 photos/day at 500KB average size."
    )
    sample_constraints = {
        "retention_period": "1 year",
        "replication_factor": 3,
        "peak_traffic_multiplier": 3.0,
    }

    print(f"\n[1] Submitting Task: {sample_task[:80]}...")
    run = service.create_run(task=sample_task, constraints=sample_constraints)
    print(f"    Created Run ID: {run.id} (Status: {run.status})")

    print("\n[2] Executing Agentic Workflow (PLAN -> ACT -> OBSERVE -> VALIDATE -> RESPOND)...")
    final_state = await service.execute_run(run.id)

    print("\n[3] Execution Completed!")
    print(f"    Final Status: {final_state.get('status')}")
    print(f"    Steps Executed: {len(final_state.get('plan', {}).get('steps', []))}")
    print(f"    Calculations Verified: {len(final_state.get('calculations', []))}")

    print("\n[4] Traceability Chain:")
    final_result = final_state.get("final_result", {})
    for trace in final_result.get("decision_trace", []):
        print(f"    * Decision: {trace.get('decision')}")
        print(f"      - Constraint:  {trace.get('constraint')}")
        print(f"      - Evidence:    {trace.get('evidence')}")
        print(f"      - Calculation: {trace.get('calculation')}")
        print(f"      - Trade-off:   {trace.get('trade_off')}")

    print("\n[5] Executive Summary:")
    print(f"    {final_result.get('executive_summary')}")

    db.close()
    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
