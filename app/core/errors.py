"""Typed error taxonomy and domain exception definitions."""

from enum import Enum
from typing import Any, Optional


class ErrorCode(str, Enum):
    """Categorized domain error codes."""

    TASK_INVALID = "TASK_INVALID"
    PLAN_INVALID = "PLAN_INVALID"
    TOOL_NOT_ALLOWED = "TOOL_NOT_ALLOWED"
    TOOL_TIMEOUT = "TOOL_TIMEOUT"
    LLM_TIMEOUT = "LLM_TIMEOUT"
    LLM_INVALID_OUTPUT = "LLM_INVALID_OUTPUT"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    PERSISTENCE_ERROR = "PERSISTENCE_ERROR"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


class ArchPilotException(Exception):
    """Base domain exception with standardized error code and metadata."""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        details: Optional[dict[str, Any]] = None,
        status_code: int = 400,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}
        self.status_code = status_code

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to structured error response representation."""
        return {
            "code": self.code.value,
            "message": self.message,
            "details": self.details,
        }


class TaskInvalidException(ArchPilotException):
    def __init__(self, message: str, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(ErrorCode.TASK_INVALID, message, details, status_code=422)


class PlanInvalidException(ArchPilotException):
    def __init__(self, message: str, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(ErrorCode.PLAN_INVALID, message, details, status_code=422)


class ToolNotAllowedException(ArchPilotException):
    def __init__(self, message: str, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(ErrorCode.TOOL_NOT_ALLOWED, message, details, status_code=403)


class ToolTimeoutException(ArchPilotException):
    def __init__(self, message: str, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(ErrorCode.TOOL_TIMEOUT, message, details, status_code=504)


class LLMTimeoutException(ArchPilotException):
    def __init__(self, message: str, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(ErrorCode.LLM_TIMEOUT, message, details, status_code=504)


class LLMInvalidOutputException(ArchPilotException):
    def __init__(self, message: str, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(ErrorCode.LLM_INVALID_OUTPUT, message, details, status_code=502)


class ValidationFailedException(ArchPilotException):
    def __init__(self, message: str, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(ErrorCode.VALIDATION_FAILED, message, details, status_code=422)


class PersistenceException(ArchPilotException):
    def __init__(self, message: str, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(ErrorCode.PERSISTENCE_ERROR, message, details, status_code=500)
