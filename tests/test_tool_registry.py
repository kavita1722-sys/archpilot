"""Tests for the ToolRegistry and security allowlist enforcement."""

import pytest
from app.core.errors import ToolNotAllowedException
from app.tools.calculator import CalculatorTool
from app.tools.registry import ToolRegistry


def test_tool_registry_registration():
    """Verify tool can be registered and retrieved."""
    registry = ToolRegistry(allowed_tools=["calculator"])
    tool = CalculatorTool()
    registry.register(tool)

    retrieved = registry.get("calculator")
    assert retrieved is not None
    assert retrieved.name == "calculator"
    assert registry.is_allowed("calculator") is True


def test_tool_registry_list_tools():
    """Verify list_tools exposes registered authorized metadata."""
    registry = ToolRegistry(allowed_tools=["calculator"])
    registry.register(CalculatorTool())

    tools_list = registry.list_tools()
    assert len(tools_list) == 1
    assert tools_list[0]["name"] == "calculator"
    assert "description" in tools_list[0]


def test_tool_registry_execute():
    """Verify registry safely dispatches to the tool."""
    registry = ToolRegistry(allowed_tools=["calculator"])
    registry.register(CalculatorTool())

    res = registry.execute("calculator", {"expression": "25 * 4"})
    assert res.status == "success"
    assert res.output == 100


def test_tool_registry_disallowed_tool():
    """Verify invoking a disallowed tool raises ToolNotAllowedException."""
    registry = ToolRegistry(allowed_tools=["calculator"])
    registry.register(CalculatorTool())

    with pytest.raises(ToolNotAllowedException) as exc_info:
        registry.execute("bash_shell", {"command": "ls"})

    assert "not authorized" in str(exc_info.value).lower()


def test_tool_not_on_allowlist():
    """Verify a registered tool not in the allowlist cannot be executed."""
    registry = ToolRegistry(allowed_tools=["web_search"])  # calculator NOT allowed
    registry.register(CalculatorTool())

    assert registry.is_allowed("calculator") is False
    with pytest.raises(ToolNotAllowedException):
        registry.execute("calculator", {"expression": "1 + 1"})
