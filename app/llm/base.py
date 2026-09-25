"""Abstract base interface for interchangeable LLM providers."""

from abc import ABC, abstractmethod
from typing import Optional, Type, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMProvider(ABC):
    """Abstract interface for LLM backends (Mock, Ollama, OpenAI-compatible)."""

    @abstractmethod
    async def generate_text(
        self, prompt: str, system: Optional[str] = None, temperature: float = 0.2
    ) -> str:
        """Generate unstructured textual completion.

        Args:
            prompt: User/instruction prompt.
            system: Optional system prompt context.
            temperature: Sampling temperature.

        Returns:
            Text response from model.
        """
        pass

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        schema: Type[T],
        system: Optional[str] = None,
        temperature: float = 0.1,
    ) -> T:
        """Generate structured response conforming to a Pydantic schema.

        Args:
            prompt: User/instruction prompt.
            schema: Pydantic model class defining the required schema.
            system: Optional system prompt context.
            temperature: Sampling temperature.

        Returns:
            Validated Pydantic instance.
        """
        pass
