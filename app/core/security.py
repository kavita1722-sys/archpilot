"""Security guardrails, input validations, and execution safety checks."""

import re
from typing import Any, List
from app.core.config import get_settings
from app.core.errors import TaskInvalidException, ToolNotAllowedException


# Suspicious command injection / shell exploit patterns
DISALLOWED_PATTERNS = [
    r"__import__",
    r"subprocess\.",
    r"os\.system",
    r"shutil\.",
    r"eval\(",
    r"exec\(",
    r"open\(",
    r"/bin/(sh|bash|zsh)",
    r"cmd\.exe",
    r"powershell",
]


def validate_task_input(task: str) -> str:
    """Validate user task input against size limits and malicious payloads.

    Args:
        task: Raw string task submitted by the user.

    Returns:
        Sanitized and trimmed task string.

    Raises:
        TaskInvalidException: If input is empty, too long, or contains exploit attempts.
    """
    settings = get_settings()

    if not task or not task.strip():
        raise TaskInvalidException("Task description cannot be empty or whitespace.")

    cleaned_task = task.strip()

    if len(cleaned_task) > settings.MAX_TASK_LENGTH:
        raise TaskInvalidException(
            f"Task length ({len(cleaned_task)}) exceeds maximum allowable limit of {settings.MAX_TASK_LENGTH} characters."
        )

    # Check for direct exploit injection strings in the task prompt
    for pattern in DISALLOWED_PATTERNS:
        if re.search(pattern, cleaned_task, re.IGNORECASE):
            raise TaskInvalidException(
                "Task contains disallowed malicious code pattern or command injection syntax.",
                details={"pattern": pattern},
            )

    return cleaned_task


def verify_tool_allowed(tool_name: str, allowlist: List[str] | None = None) -> bool:
    """Verify that a tool name is permitted under the current security policy.

    Args:
        tool_name: Identifier of the requested tool.
        allowlist: Optional custom allowlist; defaults to settings.ALLOWED_TOOLS.

    Returns:
        True if permitted.

    Raises:
        ToolNotAllowedException: If tool is not on the allowed list.
    """
    settings = get_settings()
    allowed = allowlist or settings.ALLOWED_TOOLS

    if tool_name not in allowed:
        raise ToolNotAllowedException(
            f"Tool '{tool_name}' is not in the authorized tools allowlist: {allowed}",
            details={"requested_tool": tool_name, "allowed_tools": allowed},
        )
    return True
