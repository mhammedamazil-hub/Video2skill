# Anthropic provider adapter.

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from providers.base import ModelResponse, Provider


class AnthropicProvider(Provider):
    provider_id = "anthropic"
    base_url = "https://api.anthropic.com/v1/messages"

    def available(self) -> bool:
        return bool(os.environ.get("ANTHROPIC_API_KEY"))

    def complete(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> ModelResponse:
        if not self.available():
            raise RuntimeError(
                "Anthropic provider is not configured. Set ANTHROPIC_API_KEY in your environment."
            )
        model = model or "claude-3-5-sonnet-20241022"
        api_key = os.environ["ANTHROPIC_API_KEY"]

        # Anthropic expects system and user messages split.
        system = ""
        user_messages = []
        for m in messages:
            if m.get("role") == "system":
                system = m.get("content", "")
            else:
                user_messages.append(m)

        body = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system,
            "messages": user_messages,
        }
        req = urllib.request.Request(
            self.base_url,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise RuntimeError(
                f"Anthropic API error ({exc.code}): {exc.read().decode('utf-8', 'ignore')}"
            ) from exc

        text = ""
        if data.get("content"):
            for block in data["content"]:
                if block.get("type") == "text":
                    text += block.get("text", "")
        return ModelResponse(text=text, model=model, provider="anthropic", raw=data)
