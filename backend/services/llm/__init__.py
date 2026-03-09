"""LLM provider package — factory for creating the configured client.

Usage::

    from services.llm import create_llm_client
    llm = create_llm_client()          # returns a ``LLMProvider``
    response = llm.send_message(...)

To add a new provider:
  1. Create a class in this package that satisfies ``LLMProvider``.
  2. Add an ``elif`` branch in ``create_llm_client()`` below.
"""

from __future__ import annotations

from services.llm.protocol import LLMProvider


def create_llm_client() -> LLMProvider:
    """Factory — returns the LLM client configured by ``config.LLM_PROVIDER``."""
    import config

    if config.LLM_PROVIDER == "gemini":
        from services.llm.gemini import GeminiClient

        return GeminiClient()
    else:
        from services.llm.anthropic import AnthropicClient

        return AnthropicClient()


__all__ = ["LLMProvider", "create_llm_client"]
