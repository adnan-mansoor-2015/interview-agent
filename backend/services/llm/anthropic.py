"""Anthropic Claude LLM provider."""

from __future__ import annotations

from typing import Any

import config


class AnthropicClient:
    """Anthropic Claude API client — used as a fallback provider."""

    def __init__(self) -> None:
        self._client: Any | None = None

    @property
    def client(self) -> Any:
        if self._client is None:
            import anthropic

            self._client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        return self._client

    # ------------------------------------------------------------------
    # Public interface (satisfies ``LLMProvider`` protocol)
    # ------------------------------------------------------------------

    def send_message(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
        model: str | None = None,
        max_tokens: int | None = None,
    ) -> Any:
        return self.client.messages.create(
            model=model or config.ANTHROPIC_TEXT_MODEL,
            max_tokens=max_tokens or config.MAX_TOKENS,
            system=system_prompt,
            messages=messages,
        )

    def send_message_with_image(
        self,
        system_prompt: str,
        text: str,
        image_base64: str,
        model: str | None = None,
    ) -> Any:
        return self.client.messages.create(
            model=model or config.ANTHROPIC_VISION_MODEL,
            max_tokens=config.MAX_TOKENS,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": text},
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_base64,
                            },
                        },
                    ],
                }
            ],
        )

    def extract_text(self, response: Any) -> str:
        return response.content[0].text
