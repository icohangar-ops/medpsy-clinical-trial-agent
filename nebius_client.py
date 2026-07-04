"""
Nebius Token Factory client wrapper for MedPsy Clinical Trial Matching Agent.
Uses the Nebius OpenAI-compatible API.
"""

import os
import json
from typing import Optional

try:  # Optional at import time so offline/mock runs and CI need no live SDK.
    from openai import OpenAI
except Exception:  # pragma: no cover - only when openai isn't installed
    OpenAI = None  # type: ignore

try:
    from cubiczan_resilience import resilient
except Exception:  # pragma: no cover - package is a git dep; provide a no-op shim
    def resilient(*_args, **_kwargs):  # type: ignore
        """Fallback no-op decorator when cubiczan-resilience isn't installed."""
        def _decorator(fn):
            return fn

        # Support both @resilient and @resilient(timeout=...) usage.
        if _args and callable(_args[0]) and not _kwargs:
            return _args[0]
        return _decorator

from data_layer import llm_available
from mock_llm import mock_chat, mock_embed

NEBIUS_BASE_URL = "https://api.tokenfactory.nebius.com/v1"
NEBIUS_MODEL = "meta-llama/Llama-3.3-70B-Instruct"
NEBIUS_EMBEDDING_MODEL = "Qwen/Qwen3-Embedding-8B"

_client = None


def get_client():
    """Get or create the Nebius API client.

    Raises only when a live client is genuinely required. In offline/mock mode
    (no ``NEBIUS_API_KEY`` or ``MEDPSY_OFFLINE=1``) callers route through the
    synthetic tier instead of calling this.
    """
    global _client
    if _client is None:
        api_key = os.environ.get("NEBIUS_API_KEY")
        if not api_key:
            raise ValueError("NEBIUS_API_KEY environment variable must be set")
        if OpenAI is None:
            raise ImportError("openai package is required for live Nebius calls")
        _client = OpenAI(base_url=NEBIUS_BASE_URL, api_key=api_key)
    return _client


class NebiusAgent:
    """Base class for Nebius-powered agents with function calling.

    Three-tier behaviour: when a live LLM is available it calls Nebius; otherwise
    it transparently serves deterministic synthetic completions (mock tier) so
    the pipeline runs end-to-end with zero credentials.
    """

    def __init__(self, model: str = NEBIUS_MODEL, system_prompt: str = ""):
        self.model = model
        self.system_prompt = system_prompt
        # Defer creating the live client until we know we're online, so offline
        # runs never require NEBIUS_API_KEY or the openai package.
        self.offline = not llm_available()
        self.client = None if self.offline else get_client()

    @resilient(timeout=60.0, max_attempts=3)
    def chat(
        self,
        messages: list,
        tools: Optional[list] = None,
        tool_choice: Optional[str] = None,
        response_format: Optional[dict] = None,
        temperature: float = 0.1,
        max_tokens: int = 1000,
    ) -> dict:
        """Send a chat completion request to Nebius (or the synthetic mock tier)."""
        # Tier 3 (mock): no live LLM available — serve a deterministic synthetic
        # completion so the pipeline still runs offline.
        if self.offline or self.client is None:
            return mock_chat(
                self.system_prompt, messages, tools, tool_choice, response_format
            )

        full_messages = []
        if self.system_prompt:
            full_messages.append({"role": "system", "content": self.system_prompt})
        full_messages.extend(messages)

        kwargs = {
            "model": self.model,
            "messages": full_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            kwargs["tools"] = tools
        if tool_choice:
            kwargs["tool_choice"] = tool_choice
        if response_format:
            kwargs["response_format"] = response_format

        response = self.client.chat.completions.create(**kwargs)
        message = response.choices[0].message

        result = {"content": message.content, "role": message.role}
        if message.tool_calls:
            result["tool_calls"] = [
                {
                    "id": tc.id,
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    "type": tc.type,
                }
                for tc in message.tool_calls
            ]
        return result

    @resilient(timeout=30.0, max_attempts=3)
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed texts using Nebius embedding model (or synthetic mock tier)."""
        if self.offline or self.client is None:
            return mock_embed(texts)
        response = self.client.embeddings.create(
            model=NEBIUS_EMBEDDING_MODEL, input=texts
        )
        return [d.embedding for d in response.data]
