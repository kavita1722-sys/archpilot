"""Tests for Pydantic schemas, validation rules, and constraints."""

import pytest
from pydantic import ValidationError
from app.core.security import validate_task_input
from app.schemas.plan import Plan, PlanStep, StepStatus
from app.schemas.result import FinalResult, ValidationResult
from app.schemas.task import NormalizedTask, TaskCreate
from app.schemas.tool import ToolResult


def test_task_create_valid():
    """Verify valid TaskCreate payload instantiation."""
    task = TaskCreate(
        task="Design a distributed cache tier for 500k RPS.",
        constraints={"p99_latency_ms": 10},
    )
    assert "cache" in task.task
    assert task.constraints["p99_latency_ms"] == 10


def test_task_create_validation_too_short():
    """Verify minimum length validation on task input."""
    with pytest.raises(ValidationError):
        TaskCreate(task="abc")


def test_security_validate_task_input_injection_patterns():
    """Verify security validation catches malicious injections."""
    with pytest.raises(Exception):
        validate_task_input("Do something; subprocess.Popen('calc.exe')")

    with pytest.raises(Exception):
        validate_task_input("Help me with __import__('os').system('ls')")


def test_plan_max_steps_constraint():
    """Verify Plan rejects more than 6 steps."""
    steps = [
        PlanStep(
            id=i,
            objective=f"Step {i}",
            tool="calculator",
            inputs={"expression": f"{i} + 1"},
            success_criteria=f"Done {i}",
        )
        for i in range(1, 8)  # 7 steps
    ]

    with pytest.raises(ValidationError) as exc:
        Plan(goal="Test goal", steps=steps)
    assert "exceeds maximum limit of 6 steps" in str(exc.value)


def test_plan_empty_steps_rejection():
    """Verify Plan requires at least one step."""
    with pytest.raises(ValidationError) as exc:
        Plan(goal="Test goal", steps=[])
    assert "at least 1 step" in str(exc.value)


def test_tool_result_schema():
    """Verify ToolResult schema structure."""
    tr = ToolResult(
        tool_name="calculator",
        inputs={"expression": "10 * 10"},
        output=100,
        duration_ms=1.2,
        status="success",
    )
    assert tr.status == "success"
    assert tr.output == 100
    assert tr.error is None
