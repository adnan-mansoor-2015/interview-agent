"""Application configuration — read from environment variables at import time."""

from __future__ import annotations

import os

# ── LLM Provider ────────────────────────────────────────────────────
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")  # "gemini" or "anthropic"

# Google Gemini Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_TEXT_MODEL = "gemini-2.5-flash"
GEMINI_VISION_MODEL = "gemini-2.5-flash"

# Gemini model fallback chains (tried in order on 429 RESOURCE_EXHAUSTED)
GEMINI_TEXT_MODEL_CHAIN = [
    "gemini-2.5-flash",      # Primary: thinking model, highest quality flash
    "gemini-2.0-flash",      # Fallback 1: fast, may have limited free-tier quota
    "gemini-1.5-flash",      # Fallback 2: older but reliable
    "gemini-1.5-pro",        # Fallback 3: higher quality, lower rate limits
]

GEMINI_VISION_MODEL_CHAIN = [
    "gemini-2.5-flash",      # Primary: supports vision + thinking
    "gemini-2.0-flash",      # Fallback 1: good vision support
    "gemini-1.5-flash",      # Fallback 2: older but reliable vision
    "gemini-1.5-pro",        # Fallback 3: best quality vision fallback
]

# Anthropic Configuration (fallback)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_TEXT_MODEL = "claude-sonnet-4-20250514"
ANTHROPIC_VISION_MODEL = "claude-3-5-sonnet-20241022"

MAX_TOKENS = 16384

# Redis Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
SESSION_TTL = 3600 * 24  # 24 hours

# Environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = ENVIRONMENT == "development"
