"""FastAPI dependency injection providers."""

from typing import Generator
from fastapi import Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.llm.base import LLMProvider
from app.llm.factory import get_llm_provider
from app.services.run_service import RunService
from app.tools.registry import ToolRegistry, get_default_registry

_tool_registry = get_default_registry()


def get_tool_registry_dep() -> ToolRegistry:
    """Provide application-wide singleton ToolRegistry."""
    return _tool_registry


def get_llm_provider_dep() -> LLMProvider:
    """Provide configured LLMProvider."""
    return get_llm_provider()


def get_run_service(
    db: Session = Depends(get_db),
    llm: LLMProvider = Depends(get_llm_provider_dep),
    tools: ToolRegistry = Depends(get_tool_registry_dep),
) -> RunService:
    """Provide fully wired RunService."""
    return RunService(db=db, llm=llm, tools=tools)
