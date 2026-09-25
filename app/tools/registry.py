"""Central Tool Registry enforcing security allowlists and execution policies."""

from typing import Any, Dict, List, Optional
from app.core.config import get_settings
from app.core.errors import ToolNotAllowedException
from app.core.logging import logger
from app.schemas.tool import ToolResult
from app.tools.calculator import CalculatorTool

from app.tools.base import BaseTool
from app.tools.url_fetch import UrlFetchTool
from app.tools.web_search import WebSearchTool


class ToolRegistry:
    """Manages available tools, validates allowlists, and coordinates tool execution."""

    def __init__(self, allowed_tools: Optional[List[str]] = None) -> None:
        self._tools: Dict[str, BaseTool] = {}
        settings = get_settings()
        self.allowed_tools = set(allowed_tools or settings.ALLOWED_TOOLS)

    def register(self, tool: BaseTool) -> None:
        """Register a new tool instance with the registry."""
        self._tools[tool.name] = tool
        logger.info("Registered tool: '%s' (%s)", tool.name, tool.description)

    def get(self, tool_name: str) -> Optional[BaseTool]:
        """Retrieve a registered tool by identifier."""
        return self._tools.get(tool_name)

    def is_allowed(self, tool_name: str) -> bool:
        """Check if a tool is permitted under active security allowlist."""
        return tool_name in self.allowed_tools and tool_name in self._tools

    def list_tools(self) -> List[Dict[str, Any]]:
        """Return metadata for all registered and authorized tools."""
        descriptors = []
        for name, tool in self._tools.items():
            if name in self.allowed_tools:
                descriptors.append({
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.input_schema.model_json_schema()
                    if hasattr(tool.input_schema, "model_json_schema")
                    else str(tool.input_schema),
                })
        return descriptors

    def execute(self, tool_name: str, inputs: Dict[str, Any]) -> ToolResult:
        """Safely invoke an authorized tool.

        Args:
            tool_name: Registered tool name.
            inputs: Tool input parameters.

        Returns:
            ToolResult containing execution outcome and telemetry.

        Raises:
            ToolNotAllowedException: If tool is unknown or not on the allowlist.
        """
        if not self.is_allowed(tool_name):
            raise ToolNotAllowedException(
                f"Tool '{tool_name}' is not authorized or not registered.",
                details={
                    "requested_tool": tool_name,
                    "registered_tools": list(self._tools.keys()),
                    "allowed_tools": list(self.allowed_tools),
                },
            )

        tool = self._tools[tool_name]
        return tool.execute(inputs)


def get_default_registry() -> ToolRegistry:
    """Create and configure the default ToolRegistry with baseline tools."""
    registry = ToolRegistry()
    registry.register(CalculatorTool())
    registry.register(WebSearchTool())
    registry.register(UrlFetchTool())
    return registry

