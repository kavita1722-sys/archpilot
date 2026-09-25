"""Tests for SearchProvider abstractions (MockSearchProvider and LiveSearchProvider)."""

import pytest
from app.schemas.tool import SearchResultItem
from app.tools.search_provider import LiveSearchProvider, MockSearchProvider


@pytest.mark.asyncio
async def test_mock_search_provider_returns_normalized_results():
    """Verify MockSearchProvider returns normalized SearchResultItem objects."""
    provider = MockSearchProvider()
    results = await provider.search("qdrant vector database memory", max_results=3)

    assert len(results) > 0
    assert len(results) <= 3
    for r in results:
        assert isinstance(r, SearchResultItem)
        assert r.title
        assert r.url.startswith("http")
        assert r.snippet
        assert r.source


@pytest.mark.asyncio
async def test_mock_search_provider_generic_fallback():
    """Verify MockSearchProvider generates relevant results for generic queries."""
    provider = MockSearchProvider()
    results = await provider.search("uncommon distributed algorithm", max_results=2)

    assert len(results) == 2
    for r in results:
        assert isinstance(r, SearchResultItem)
        assert "uncommon" in r.title.lower() or "benchmark" in r.title.lower()


@pytest.mark.asyncio
async def test_live_search_provider_missing_api_key_graceful_fallback():
    """Verify LiveSearchProvider gracefully falls back to mock results when API key is missing."""
    # Ensure without API key it doesn't crash, instead falling back safely
    provider = LiveSearchProvider(api_key=None)
    results = await provider.search("qdrant memory scaling", max_results=2)

    assert isinstance(results, list)
    assert len(results) > 0
    for r in results:
        assert isinstance(r, SearchResultItem)
