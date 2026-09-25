"""Web search tool executing authorized external queries."""

import asyncio
import time
from typing import Any, Dict, Optional
from app.core.logging import logger
from app.schemas.tool import ToolResult, WebSearchInput
from app.tools.base import BaseTool
from app.tools.search_provider import LiveSearchProvider, MockSearchProvider, SearchProvider


class WebSearchTool(BaseTool):
    """Registered tool enabling agents to research technical benchmarks and architecture patterns."""

    name: str = "web_search"
    description: str = (
        "Search technical engineering documentation, open-source benchmarks, and architecture guides."
    )
    input_schema: type = WebSearchInput

    def __init__(self, provider: Optional[SearchProvider] = None) -> None:
        self.provider = provider or LiveSearchProvider(fallback=MockSearchProvider())

    def execute(self, inputs: Dict[str, Any]) -> ToolResult:
        """Execute search synchronously (wrapping async provider)."""
        start_time = time.perf_counter()
        query = inputs.get("query", "").strip()
        max_results = int(inputs.get("max_results", 5))

        if not query:
            return ToolResult(
                tool_name=self.name,
                inputs=inputs,
                output=None,
                duration_ms=0.0,
                status="error",
                error="Search query cannot be empty.",
            )

        try:
            # Handle event loop in sync context if called synchronously
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Running inside existing event loop
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, self.provider.search(query, max_results))
                        results = future.result()
                else:
                    results = loop.run_until_complete(self.provider.search(query, max_results))
            except RuntimeError:
                results = asyncio.run(self.provider.search(query, max_results))

            elapsed_ms = (time.perf_counter() - start_time) * 1000
            serialized_results = [r.model_dump() for r in results]
            logger.info("WebSearch executed for '%s' returned %d results in %.2fms", query, len(results), elapsed_ms)

            return ToolResult(
                tool_name=self.name,
                inputs={"query": query, "max_results": max_results},
                output=serialized_results,
                duration_ms=round(elapsed_ms, 2),
                status="success",
                error=None,
            )
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.warning("WebSearch failed for '%s': %s", query, e)
            return ToolResult(
                tool_name=self.name,
                inputs={"query": query},
                output=None,
                duration_ms=round(elapsed_ms, 2),
                status="error",
                error=str(e),
            )
