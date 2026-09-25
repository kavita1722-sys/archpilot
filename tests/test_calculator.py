"""Tests for safe deterministic calculator evaluation."""

import pytest
from app.tools.calculator import CalculatorTool, evaluate_expression


def test_basic_arithmetic():
    """Verify addition, subtraction, multiplication, and division."""
    assert evaluate_expression("10 + 25") == 35
    assert evaluate_expression("100 - 45") == 55
    assert evaluate_expression("12 * 12") == 144
    assert evaluate_expression("100 / 4") == 25


def test_operator_precedence_and_parentheses():
    """Verify correct operator precedence and grouping."""
    assert evaluate_expression("2 + 3 * 4") == 14
    assert evaluate_expression("(2 + 3) * 4") == 20
    assert evaluate_expression("((100 - 20) / 4) + 10") == 30


def test_large_number_engineering_multiplication():
    """Verify deterministic calculations for capacity sizing (e.g. users * payload)."""
    # 100,000 * 15,360
    assert evaluate_expression("100000 * 15360") == 1536000000
    # Bytes to Gigabytes: 500000 * 10240 / (1024 * 1024 * 1024)
    res = evaluate_expression("500000 * 10240 / (1024 * 1024 * 1024)")
    assert round(res, 4) == round(500000 * 10240 / (1024**3), 4)


def test_safe_math_functions():
    """Verify allowlisted math functions work accurately."""
    assert evaluate_expression("ceil(14.2)") == 15
    assert evaluate_expression("floor(14.8)") == 14
    assert evaluate_expression("round(14.567)") == 15
    assert evaluate_expression("abs(-42)") == 42
    assert evaluate_expression("sqrt(144)") == 12
    assert evaluate_expression("min(10, 5, 20)") == 5
    assert evaluate_expression("max(10, 5, 20)") == 20


def test_division_by_zero():
    """Verify division by zero raises ZeroDivisionError."""
    with pytest.raises(ZeroDivisionError):
        evaluate_expression("100 / 0")


def test_calculator_tool_execution():
    """Verify CalculatorTool returns structured ToolResult."""
    tool = CalculatorTool()
    res = tool.execute({"expression": "100000 * 15360"})

    assert res.tool_name == "calculator"
    assert res.status == "success"
    assert res.output == 1536000000
    assert res.duration_ms >= 0.0
    assert res.error is None


def test_calculator_tool_error_handling():
    """Verify CalculatorTool catches errors and reports in ToolResult."""
    tool = CalculatorTool()
    res = tool.execute({"expression": "100 / 0"})

    assert res.tool_name == "calculator"
    assert res.status == "error"
    assert res.output is None
    assert "division by zero" in res.error.lower()
