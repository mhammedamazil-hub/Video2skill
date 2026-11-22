# OpenAI-compatible provider adapter (any endpoint following the OpenAI chat schema).

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from providers.base import ModelResponse, Provider


class OpenAICompatibleProvider(Provider):
    provider_id = "openai-compatible"

    def available(self) -> bool:
        return bool(os.environ.get("OPENAI_COMPATIBLE_API_KEY")) and bool(
            os.environ.get("OPENAI_COMPATIBLE_BASE_URL")
        )

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
                "OpenAI-compatible provider is not configured. Set OPENAI_COMPATIBLE_API_KEY "
                "and OPENAI_COMPATIBLE_BASE_URL in your environment."
            )
        model = model or os.environ.get("OPENAI_COMPATIBLE_MODEL", "local-model")
        api_key = os.environ["OPENAI_COMPATIBLE_API_KEY"]
        base_url = os.environ["OPENAI_COMPATIBLE_BASE_URL"].rstrip("/")
        url = base_url + "/chat/completions"

        body = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        req = urllib.request.Request(
            url,
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
                f"OpenAI-compatible API error ({exc.code}): {exc.read().decode('utf-8', 'ignore')}"
            ) from exc

        text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return ModelResponse(text=text, model=model, provider="openai-compatible", raw=data)
