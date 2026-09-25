"""Safe, deterministic mathematical calculator tool without eval()."""

import ast
import math
import operator
import time
from typing import Any, Callable, Dict, Union
from app.core.logging import logger
from app.schemas.tool import CalculatorInput, ToolResult
from app.tools.base import BaseTool

# Supported binary operators
BINARY_OPERATORS: Dict[type, Callable[[Any, Any], Any]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

# Supported unary operators
UNARY_OPERATORS: Dict[type, Callable[[Any], Any]] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

# Allowed safe math functions
SAFE_FUNCTIONS: Dict[str, Callable[..., Any]] = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "ceil": math.ceil,
    "floor": math.floor,
    "sqrt": math.sqrt,
    "log": math.log,
    "log2": math.log2,
    "log10": math.log10,
    "exp": math.exp,
    "pow": pow,
}


def _safe_eval_node(node: ast.AST) -> Union[int, float]:
    """Recursively evaluate an AST expression node under strict safety constraints.

    Args:
        node: The parsed AST node.

    Returns:
        Evaluated numeric result.

    Raises:
        ValueError: For disallowed expressions or security violations.
        ZeroDivisionError: For division by zero.
    """
    if isinstance(node, ast.Expression):
        return _safe_eval_node(node.body)

    # Literals (int, float)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return node.value
        raise ValueError(f"Disallowed constant type: {type(node.value).__name__}")

    # Binary Operations (+, -, *, /, etc.)
    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in BINARY_OPERATORS:
            raise ValueError(f"Disallowed binary operator: {op_type.__name__}")

        left = _safe_eval_node(node.left)
        right = _safe_eval_node(node.right)

        # Safeguard against exponential CPU exhaustion (e.g. 9999 ** 999999)
        if op_type is ast.Pow:
            if abs(right) > 100:
                raise ValueError("Exponent value exceeds maximum security threshold (100).")
            if abs(left) > 1e12 and right > 10:
                raise ValueError("Base value too large for exponentiation.")

        op_func = BINARY_OPERATORS[op_type]
        return op_func(left, right)

    # Unary Operations (+x, -x)
    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in UNARY_OPERATORS:
            raise ValueError(f"Disallowed unary operator: {op_type.__name__}")
        operand = _safe_eval_node(node.operand)
        return UNARY_OPERATORS[op_type](operand)

    # Safe Function Calls (e.g. ceil, floor, round, sqrt)
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ValueError("Only direct named mathematical functions are supported.")
        func_name = node.func.id
        if func_name not in SAFE_FUNCTIONS:
            raise ValueError(f"Disallowed function call '{func_name}'. Allowed: {list(SAFE_FUNCTIONS.keys())}")

        args = [_safe_eval_node(arg) for arg in node.args]

        if func_name == "exp" and args and args[0] > 700:
            raise ValueError("Argument to exp() exceeds float capacity limit.")

        return SAFE_FUNCTIONS[func_name](*args)

    raise ValueError(f"Disallowed expression node type: {type(node).__name__}")


def evaluate_expression(expression: str) -> Union[int, float]:
    """Parse and evaluate a mathematical expression without eval().

    Args:
        expression: Mathematical string expression (e.g. '100000 * 15360').

    Returns:
        Numerical result.

    Raises:
        ValueError: For syntax errors or disallowed AST elements.
    """
    if not expression or not expression.strip():
        raise ValueError("Expression cannot be empty.")

    cleaned_expr = expression.strip()

    try:
        parsed = ast.parse(cleaned_expr, mode="eval")
    except SyntaxError as e:
        raise ValueError(f"Invalid mathematical syntax: {e}")

    result = _safe_eval_node(parsed)

    # Check for NaN / Infinity
    if isinstance(result, float) and (math.isnan(result) or math.isinf(result)):
        raise ValueError("Calculation resulted in NaN or Infinity.")

    # Convert integer floats like 150.0 to int 150 for clarity where exact
    if isinstance(result, float) and result.is_integer():
        return int(result)

    return result


class CalculatorTool(BaseTool):
    """Deterministic, safe calculator tool recording execution metrics."""

    name: str = "calculator"
    description: str = (
        "Perform deterministic arithmetic calculations (+, -, *, /, %, **, ceil, floor, round, sqrt, log)."
    )
    input_schema: type = CalculatorInput

    def execute(self, inputs: Dict[str, Any]) -> ToolResult:
        """Execute calculation and return structured ToolResult."""
        start_time = time.perf_counter()

        expression = inputs.get("expression", "")
        if not expression and "expr" in inputs:
            expression = inputs["expr"]

        try:
            val = evaluate_expression(str(expression))
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.info("Calculator executed '%s' = %s in %.2fms", expression, val, elapsed_ms)
            return ToolResult(
                tool_name=self.name,
                inputs={"expression": expression},
                output=val,
                duration_ms=round(elapsed_ms, 2),
                status="success",
                error=None,
            )
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.warning("Calculator failed for '%s': %s", expression, str(e))
            return ToolResult(
                tool_name=self.name,
                inputs={"expression": expression},
                output=None,
                duration_ms=round(elapsed_ms, 2),
                status="error",
                error=str(e),
            )
