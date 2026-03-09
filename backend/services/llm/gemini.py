"""Google Gemini LLM provider with automatic model fallback on rate limits."""

from __future__ import annotations

import logging
from typing import Any

import config

logger = logging.getLogger(__name__)


class GeminiClient:
    """Google Gemini API client using the ``google-genai`` SDK.

    Features:
    - Lazy SDK initialisation (imported on first call).
    - Automatic fallback through ``config.GEMINI_TEXT_MODEL_CHAIN`` when a
      model returns **429 RESOURCE_EXHAUSTED**.
    """

    def __init__(self) -> None:
        self._client: Any | None = None

    @property
    def client(self) -> Any:
        if self._client is None:
            from google import genai

            self._client = genai.Client(api_key=config.GEMINI_API_KEY)
        return self._client

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_rate_limit_error(exc: Exception) -> bool:
        """Return *True* if *exc* is a 429 / RESOURCE_EXHAUSTED error."""
        from google.genai.errors import ClientError

        if isinstance(exc, ClientError):
            if exc.code == 429:
                return True
            if getattr(exc, "status", "") == "RESOURCE_EXHAUSTED":
                return True
        return False

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
        """Send a text conversation with automatic model fallback."""
        model_chain = [model] if model else list(config.GEMINI_TEXT_MODEL_CHAIN)

        contents = [
            {
                "role": "user" if msg["role"] == "user" else "model",
                "parts": [{"text": msg["content"]}],
            }
            for msg in messages
        ]

        from google.genai import types

        last_exception: Exception | None = None
        for model_name in model_chain:
            try:
                logger.info("Attempting LLM call with model: %s", model_name)
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        max_output_tokens=max_tokens or config.MAX_TOKENS,
                        temperature=0.7,
                    ),
                )
                logger.info("LLM call succeeded with model: %s", model_name)
                return response
            except Exception as e:
                last_exception = e
                if self._is_rate_limit_error(e):
                    logger.warning("Rate limited on %s — trying next fallback…", model_name)
                    continue
                raise

        logger.error("All models in fallback chain exhausted.")
        raise last_exception  # type: ignore[misc]

    def send_message_with_image(
        self,
        system_prompt: str,
        text: str,
        image_base64: str,
        model: str | None = None,
    ) -> Any:
        """Send a text + image request with automatic model fallback."""
        model_chain = [model] if model else list(config.GEMINI_VISION_MODEL_CHAIN)

        from google.genai import types

        last_exception: Exception | None = None
        for model_name in model_chain:
            try:
                logger.info("Attempting vision call with model: %s", model_name)
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=[
                        {
                            "role": "user",
                            "parts": [
                                {"text": text},
                                {"inline_data": {"mime_type": "image/png", "data": image_base64}},
                            ],
                        }
                    ],
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        max_output_tokens=config.MAX_TOKENS,
                        temperature=0.7,
                    ),
                )
                logger.info("Vision call succeeded with model: %s", model_name)
                return response
            except Exception as e:
                last_exception = e
                if self._is_rate_limit_error(e):
                    logger.warning("Rate limited on vision model %s — trying next…", model_name)
                    continue
                raise

        logger.error("All vision models in fallback chain exhausted.")
        raise last_exception  # type: ignore[misc]

    def extract_text(self, response: Any) -> str:
        """Extract text from a Gemini response.

        Handles *thinking* models whose ``.text`` may be ``None`` when
        ``finish_reason`` is ``MAX_TOKENS``.
        """
        if response.text:
            return response.text
        if response.candidates:
            parts = response.candidates[0].content.parts
            if parts:
                for part in reversed(parts):
                    if hasattr(part, "text") and part.text:
                        return part.text
        return ""
