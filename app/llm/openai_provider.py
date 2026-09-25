"""OpenAI and OpenAI-compatible LLM Provider using httpx."""

import json
from typing import Any, Optional, Type, TypeVar
import httpx
from pydantic import BaseModel
from app.core.config import get_settings
from app.core.errors import LLMInvalidOutputException, LLMTimeoutException
from app.llm.base import LLMProvider

T = TypeVar("T", bound=BaseModel)


class OpenAICompatibleProvider(LLMProvider):
    """Integrates with OpenAI and OpenAI-compatible inference endpoints."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 60.0,
    ) -> None:
        settings = get_settings()
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.base_url = (base_url or settings.OPENAI_BASE_URL).rstrip("/")
        self.model = model or settings.OPENAI_MODEL
        self.timeout = timeout

    async def generate_text(
        self, prompt: str, system: Optional[str] = None, temperature: float = 0.2
    ) -> str:
        url = f"{self.base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
        except httpx.TimeoutException as e:
            raise LLMTimeoutException(f"OpenAI request timed out: {e}")
        except Exception as e:
            raise LLMInvalidOutputException(f"OpenAI API invocation error: {e}")

    async def generate_structured(
        self,
        prompt: str,
        schema: Type[T],
        system: Optional[str] = None,
        temperature: float = 0.1,
    ) -> T:
        url = f"{self.base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        schema_json = json.dumps(schema.model_json_schema())
        messages = [
            {
                "role": "system",
                "content": (
                    (system or "You are an expert systems engineer.")
                    + f"\nOutput ONLY raw valid JSON conforming to this schema:\n{schema_json}"
                ),
            },
            {"role": "user", "content": prompt},
        ]

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "response_format": {"type": "json_object"},
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                raw_text = data["choices"][0]["message"]["content"].strip()
                parsed = json.loads(raw_text)
                return schema.model_validate(parsed)
        except httpx.TimeoutException as e:
            raise LLMTimeoutException(f"OpenAI request timed out: {e}")
        except Exception as e:
            raise LLMInvalidOutputException(f"OpenAI structured parse error: {e}")
