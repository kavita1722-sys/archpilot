"""Tests for the MockLLMProvider generating domain-appropriate structured data."""

import pytest
from app.llm.mock import MockLLMProvider
from app.schemas.plan import Plan
from app.schemas.result import FinalResult, ValidationResult
from app.schemas.task import NormalizedTask


@pytest.mark.asyncio
async def test_mock_llm_text_generation():
    """Verify MockLLMProvider generates coherent engineering text."""
    provider = MockLLMProvider()
    res = await provider.generate_text("Summarize cache sizing recommendations.")
    assert len(res) > 20
    assert "ArchPilot" in res


@pytest.mark.asyncio
async def test_mock_llm_generate_normalized_task():
    """Verify MockLLMProvider produces valid NormalizedTask."""
    provider = MockLLMProvider()
    res: NormalizedTask = await provider.generate_structured(
        prompt="Design cache layer for 500k RPS",
        schema=NormalizedTask,
    )
    assert isinstance(res, NormalizedTask)
    assert res.requires_calculation is True
    assert len(res.key_variables) > 0


@pytest.mark.asyncio
async def test_mock_llm_generate_plan():
    """Verify MockLLMProvider produces valid bounded Plan with calculator steps."""
    provider = MockLLMProvider()
    plan: Plan = await provider.generate_structured(
        prompt="Calculate annual photo storage for 10M users",
        schema=Plan,
    )
    assert isinstance(plan, Plan)
    assert 1 <= len(plan.steps) <= 6
    for step in plan.steps:
        assert step.tool == "calculator"
        assert "expression" in step.inputs


@pytest.mark.asyncio
async def test_mock_llm_generate_validation_and_result():
    """Verify MockLLMProvider produces valid ValidationResult and FinalResult."""
    provider = MockLLMProvider()
    val: ValidationResult = await provider.generate_structured(
        prompt="Validate observations",
        schema=ValidationResult,
    )
    assert val.is_valid is True
    assert val.score >= 0.9

    res: FinalResult = await provider.generate_structured(
        prompt="Deliver final report",
        schema=FinalResult,
    )
    assert len(res.executive_summary) > 20
    assert len(res.calculations) > 0
    assert len(res.trade_offs) > 0
    assert len(res.decision_trace) > 0


def test_llm_factory_instantiation():
    """Verify get_llm_provider instantiates correct classes for mock, ollama, and openai_compatible."""
    from app.core.config import Settings
    from app.llm.factory import get_llm_provider
    from app.llm.ollama import OllamaProvider
    from app.llm.openai_provider import OpenAICompatibleProvider

    mock_prov = get_llm_provider(Settings(LLM_PROVIDER="mock"))
    assert isinstance(mock_prov, MockLLMProvider)

    ollama_prov = get_llm_provider(Settings(LLM_PROVIDER="ollama"))
    assert isinstance(ollama_prov, OllamaProvider)
    assert ollama_prov.base_url == "http://localhost:11434"
    assert ollama_prov.model == "llama3.2:latest"

    openai_prov = get_llm_provider(
        Settings(
            LLM_PROVIDER="openai_compatible",
            OPENAI_API_KEY="test-key",
            OPENAI_BASE_URL="https://custom.llm.endpoint/v1",
            OPENAI_MODEL="deepseek-chat",
        )
    )
    assert isinstance(openai_prov, OpenAICompatibleProvider)
    assert openai_prov.api_key == "test-key"
    assert openai_prov.base_url == "https://custom.llm.endpoint/v1"
    assert openai_prov.model == "deepseek-chat"

