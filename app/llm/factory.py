"""Factory for instantiating the configured LLM provider."""

from typing import Optional
from app.core.config import Settings, get_settings
from app.core.logging import logger
from app.llm.base import LLMProvider
from app.llm.mock import MockLLMProvider
from app.llm.ollama import OllamaProvider
from app.llm.openai_provider import OpenAICompatibleProvider


def get_llm_provider(settings: Optional[Settings] = None) -> LLMProvider:
    """Retrieve or instantiate an LLM provider based on runtime settings."""
    cfg = settings or get_settings()

    provider_type = cfg.LLM_PROVIDER.lower()
    logger.info("Initializing LLM provider: '%s'", provider_type)

    if provider_type == "mock":
        return MockLLMProvider()
    elif provider_type == "ollama":
        return OllamaProvider(
            base_url=cfg.OLLAMA_BASE_URL,
            model=cfg.OLLAMA_MODEL,
        )
    elif provider_type == "openai_compatible":
        return OpenAICompatibleProvider(
            api_key=cfg.OPENAI_API_KEY,
            base_url=cfg.OPENAI_BASE_URL,
            model=cfg.OPENAI_MODEL,
        )
    else:
        logger.warning(
            "Unknown LLM provider '%s', falling back to MockLLMProvider", provider_type
        )
        return MockLLMProvider()
