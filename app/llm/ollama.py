"""Ollama LLM Provider using direct local REST API integration."""

import json
from typing import Any, Optional, Type, TypeVar
import httpx
from pydantic import BaseModel
from app.core.config import get_settings
from app.core.errors import LLMInvalidOutputException, LLMTimeoutException
from app.core.logging import logger
from app.llm.base import LLMProvider

T = TypeVar("T", bound=BaseModel)


class OllamaProvider(LLMProvider):
    """Integrates with locally hosted Ollama instances."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 60.0,
    ) -> None:
        settings = get_settings()
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL
        self.timeout = timeout

    async def generate_text(
        self, prompt: str, system: Optional[str] = None, temperature: float = 0.2
    ) -> str:
        """Call Ollama /api/generate endpoint."""
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system or "",
            "stream": False,
            "options": {"temperature": temperature},
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                return data.get("response", "")
        except httpx.TimeoutException as e:
            raise LLMTimeoutException(f"Ollama request timed out after {self.timeout}s: {e}")
        except Exception as e:
            raise LLMInvalidOutputException(f"Ollama communication failure: {e}")

    async def generate_structured(
        self,
        prompt: str,
        schema: Type[T],
        system: Optional[str] = None,
        temperature: float = 0.1,
    ) -> T:
        """Call Ollama with format=schema.model_json_schema() and validate response against Pydantic schema."""
        url = f"{self.base_url}/api/generate"
        schema_dict = schema.model_json_schema()
        schema_json = json.dumps(schema_dict)
        enhanced_prompt = (
            f"{prompt}\n\n"
            f"You MUST output raw valid JSON matching this JSON Schema:\n{schema_json}\n"
            "Do NOT include any markdown code blocks, prefixes, or explanations outside the JSON."
        )

        payload = {
            "model": self.model,
            "prompt": enhanced_prompt,
            "system": system or "You are an expert systems engineer. Output strictly raw JSON.",
            "format": schema_dict,
            "stream": False,
            "options": {"temperature": temperature},
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                raw_text = data.get("response", "").strip()

                # Clean markdown backticks if returned
                if raw_text.startswith("```"):
                    lines = raw_text.splitlines()
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines and lines[-1].startswith("```"):
                        lines = lines[:-1]
                    raw_text = "\n".join(lines).strip()

                parsed_json = json.loads(raw_text)
                return schema.model_validate(parsed_json)
        except httpx.TimeoutException as e:
            raise LLMTimeoutException(f"Ollama request timed out after {self.timeout}s: {e}")
        except json.JSONDecodeError as e:
            raise LLMInvalidOutputException(
                f"Failed to parse Ollama JSON output: {e}. Raw response: {raw_text[:200]}"
            )
        except Exception as e:
            raise LLMInvalidOutputException(f"Ollama structured generation error: {e}")
