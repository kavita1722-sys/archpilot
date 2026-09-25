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


class SearchResultItem(BaseModel):
    """Normalized search result item."""

    title: str = Field(..., description="Title of the search result.")
    url: str = Field(..., description="Canonical URL.")
    snippet: str = Field(..., description="Extracted relevant text summary.")
    source: str = Field(default="web", description="Origin provider or domain.")


class WebSearchInput(BaseModel):
    """Input schema for web search tool."""

    query: str = Field(..., description="Technical query string.", min_length=2)
    max_results: int = Field(default=5, ge=1, le=10, description="Max results to return.")


class UrlFetchInput(BaseModel):
    """Input schema for URL fetch tool."""

    url: str = Field(..., description="Web or documentation URL to inspect.")


class UrlFetchOutput(BaseModel):
    """Structured extraction from a fetched URL."""

    url: str
    title: str
    content: str
    content_length: int
    truncated: bool = False


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

