"""LLM provider protocol — the contract all LLM backends must satisfy."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class LLMProvider(Protocol):
    """Protocol that every LLM provider client must implement.

    To add a new provider (e.g. OpenAI, local Ollama):
      1. Create a new class in ``services/llm/`` that satisfies this Protocol.
      2. Register it in ``services/llm/__init__.py:create_llm_client()``.
    """

    def send_message(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
        model: str | None = None,
        max_tokens: int | None = None,
    ) -> Any:
        """Send a text conversation and return the provider-specific response."""
        ...

    def send_message_with_image(
        self,
        system_prompt: str,
        text: str,
        image_base64: str,
        model: str | None = None,
    ) -> Any:
        """Send a text + image request and return the provider-specific response."""
        ...

    def extract_text(self, response: Any) -> str:
        """Extract plain-text content from a provider-specific response object."""
        ...
