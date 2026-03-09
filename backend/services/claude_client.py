"""Backward-compatible import shim.

All agents import ``claude_client`` from this module.  The actual
implementation now lives in ``services.llm`` — this file simply
re-exports the configured instance so existing imports keep working::

    from services.claude_client import claude_client
"""

from services.llm import create_llm_client

claude_client = create_llm_client()
