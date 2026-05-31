"""
Nebius Token Factory client wrapper for MedPsy Clinical Trial Matching Agent.
Uses the Nebius OpenAI-compatible API.
"""

import os
import json
from typing import Optional
from openai import OpenAI

NEBIUS_BASE_URL = "https://api.tokenfactory.nebius.com/v1"
NEBIUS_MODEL = "meta-llama/Llama-3.3-70B-Instruct"
NEBIUS_EMBEDDING_MODEL = "Qwen/Qwen3-Embedding-8B"

_client: Optional[OpenAI] = None


def get_client() -> OpenAI:
    """Get or create the Nebius API client."""
    global _client
    if _client is None:
        api_key = os.environ.get("NEBIUS_API_KEY")
        if not api_key:
            raise ValueError("NEBIUS_API_KEY environment variable must be set")
        _client = OpenAI(base_url=NEBIUS_BASE_URL, api_key=api_key)
    return _client


class NebiusAgent:
    """Base class for Nebius-powered agents with function calling."""

    def __init__(self, model: str = NEBIUS_MODEL, system_prompt: str = ""):
        self.model = model
        self.system_prompt = system_prompt
        self.client = get_client()

    def chat(
        self,
        messages: list,
        tools: Optional[list] = None,
        tool_choice: Optional[str] = None,
        response_format: Optional[dict] = None,
        temperature: float = 0.1,
        max_tokens: int = 1000,
    ) -> dict:
        """Send a chat completion request to Nebius."""
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

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed texts using Nebius embedding model."""
        response = self.client.embeddings.create(
            model=NEBIUS_EMBEDDING_MODEL, input=texts
        )
        return [d.embedding for d in response.data]
