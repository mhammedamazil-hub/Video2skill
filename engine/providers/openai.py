# OpenAI provider adapter.

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from providers.base import ModelResponse, Provider


class OpenAIProvider(Provider):
    provider_id = "openai"
    base_url = "https://api.openai.com/v1/chat/completions"

    def available(self) -> bool:
        return bool(os.environ.get("OPENAI_API_KEY"))

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
                "OpenAI provider is not configured. Set OPENAI_API_KEY in your environment."
            )
        model = model or "gpt-4o"
        api_key = os.environ["OPENAI_API_KEY"]

        body = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        req = urllib.request.Request(
            self.base_url,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise RuntimeError(
                f"OpenAI API error ({exc.code}): {exc.read().decode('utf-8', 'ignore')}"
            ) from exc

        text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return ModelResponse(text=text, model=model, provider="openai", raw=data)
