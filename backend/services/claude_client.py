"""
LLM Client abstraction — supports Google Gemini (default) and Anthropic Claude.
All agents use the same interface: send_message(), send_message_with_image(), extract_text().

Gemini client includes automatic model fallback: on 429 RESOURCE_EXHAUSTED,
it retries with the next model in the configured fallback chain.
"""
import base64
import logging
import config

logger = logging.getLogger(__name__)


class GeminiClient:
    """Google Gemini API client using the google-genai SDK.

    Supports automatic model fallback on 429 RESOURCE_EXHAUSTED errors.
    When a model hits its rate limit, the client automatically retries
    with the next model in the configured fallback chain.
    """

    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            from google import genai
            self._client = genai.Client(api_key=config.GEMINI_API_KEY)
        return self._client

    @staticmethod
    def _is_rate_limit_error(exc: Exception) -> bool:
        """Check if an exception is a 429 rate limit / RESOURCE_EXHAUSTED error."""
        from google.genai.errors import ClientError
        if isinstance(exc, ClientError):
            if exc.code == 429:
                return True
            if getattr(exc, 'status', '') == "RESOURCE_EXHAUSTED":
                return True
        return False

    def send_message(self, system_prompt: str, messages: list, model: str = None, max_tokens: int = None):
        """Send a message to Gemini with automatic model fallback on rate limits."""
        # Build the model chain to try
        if model:
            model_chain = [model]  # Explicit model — no fallback
        else:
            model_chain = list(config.GEMINI_TEXT_MODEL_CHAIN)

        # Build contents once (reused across retries)
        contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})

        from google.genai import types

        last_exception = None
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
                    logger.warning(
                        "Rate limited on model %s: %s. Trying next fallback...",
                        model_name, e,
                    )
                    continue
                else:
                    logger.error("Non-rate-limit error on model %s: %s", model_name, e)
                    raise

        # All models in the chain were rate limited
        logger.error("All models in fallback chain exhausted. Last error: %s", last_exception)
        raise last_exception

    def send_message_with_image(self, system_prompt: str, text: str, image_base64: str, model: str = None):
        """Send a message with an image to Gemini with automatic model fallback on rate limits."""
        # Build the model chain to try
        if model:
            model_chain = [model]  # Explicit model — no fallback
        else:
            model_chain = list(config.GEMINI_VISION_MODEL_CHAIN)

        from google.genai import types

        last_exception = None
        for model_name in model_chain:
            try:
                logger.info("Attempting vision LLM call with model: %s", model_name)
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=[{
                        "role": "user",
                        "parts": [
                            {"text": text},
                            {"inline_data": {"mime_type": "image/png", "data": image_base64}},
                        ],
                    }],
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        max_output_tokens=config.MAX_TOKENS,
                        temperature=0.7,
                    ),
                )
                logger.info("Vision LLM call succeeded with model: %s", model_name)
                return response
            except Exception as e:
                last_exception = e
                if self._is_rate_limit_error(e):
                    logger.warning(
                        "Rate limited on vision model %s: %s. Trying next fallback...",
                        model_name, e,
                    )
                    continue
                else:
                    logger.error("Non-rate-limit error on vision model %s: %s", model_name, e)
                    raise

        # All vision models in the chain were rate limited
        logger.error("All vision models in fallback chain exhausted. Last error: %s", last_exception)
        raise last_exception

    def extract_text(self, response):
        """Extract text from Gemini response.
        Handles thinking models where .text may be None when finish_reason is MAX_TOKENS."""
        if response.text:
            return response.text
        # Fallback: extract from candidates directly (thinking model / truncation)
        if response.candidates:
            parts = response.candidates[0].content.parts
            if parts:
                # Thinking models may have multiple parts — get the last non-thought text
                for part in reversed(parts):
                    if hasattr(part, 'text') and part.text:
                        return part.text
        return ""


class AnthropicClient:
    """Anthropic Claude API client (fallback)."""

    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            import anthropic
            self._client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        return self._client

    def send_message(self, system_prompt: str, messages: list, model: str = None, max_tokens: int = None):
        return self.client.messages.create(
            model=model or config.ANTHROPIC_TEXT_MODEL,
            max_tokens=max_tokens or config.MAX_TOKENS,
            system=system_prompt,
            messages=messages,
        )

    def send_message_with_image(self, system_prompt: str, text: str, image_base64: str, model: str = None):
        return self.client.messages.create(
            model=model or config.ANTHROPIC_VISION_MODEL,
            max_tokens=config.MAX_TOKENS,
            system=system_prompt,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": text},
                    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": image_base64}},
                ],
            }],
        )

    def extract_text(self, response):
        return response.content[0].text


# Create the right client based on config
if config.LLM_PROVIDER == "gemini":
    claude_client = GeminiClient()
else:
    claude_client = AnthropicClient()
