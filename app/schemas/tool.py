"""Schemas for tool inputs, invocations, and execution results."""

from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, Field


class CalculatorInput(BaseModel):
    """Input payload for the safe deterministic calculator tool."""

    expression: str = Field(
        ...,
        description="Safe mathematical expression (e.g. '100000 * 15360 / (1024 * 1024)').",
        examples=["500000 * 10240 / 1073741824"],
    )


class ToolCall(BaseModel):
    """Represents an agent's request to invoke a specific tool."""

    tool_name: str = Field(..., description="Registered name of the tool.")
    inputs: Dict[str, Any] = Field(
        default_factory=dict, description="Inputs required by the tool."
    )


class ToolResult(BaseModel):
    """Structured output recorded from tool execution."""

    tool_name: str
    inputs: Dict[str, Any]
    output: Any
    duration_ms: float
    status: Literal["success", "error"]
    error: Optional[str] = None
