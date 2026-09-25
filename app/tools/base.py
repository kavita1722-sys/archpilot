"""Base abstraction for all ArchPilot registered tools."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Type
from pydantic import BaseModel
from app.schemas.tool import ToolResult


class BaseTool(ABC):
    """Abstract base class establishing standard lifecycle for agentic tools."""

    name: str
    description: str
    input_schema: Type[BaseModel]

    @abstractmethod
    def execute(self, inputs: Dict[str, Any]) -> ToolResult:
        """Execute the tool deterministically with provided inputs.

        Args:
            inputs: Dictionary containing arguments matching input_schema.

        Returns:
            ToolResult containing status, output, duration, and metadata.
        """
        pass
