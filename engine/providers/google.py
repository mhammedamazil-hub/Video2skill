# Google Gemini provider adapter.

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from providers.base import ModelResponse, Provider


class GoogleProvider(Provider):
    provider_id = "google"
    base_url = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    def available(self) -> bool:
        return bool(os.environ.get("GEMINI_API_KEY"))

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
                "Google Gemini provider is not configured. Set GEMINI_API_KEY in your environment."
            )
        model = model or "gemini-1.5-pro"
        api_key = os.environ["GEMINI_API_KEY"]

        contents = []
        system = ""
        for m in messages:
            role = m.get("role", "user")
            if role == "system":
                system = m.get("content", "")
                continue
            gemini_role = "model" if role == "assistant" else "user"
            contents.append({"role": gemini_role, "parts": [{"text": m.get("content", "")}]})

        body = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        if system:
            body["systemInstruction"] = {"parts": [{"text": system}]}

        url = self.base_url.format(model=model) + "?key=" + api_key
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise RuntimeError(
                f"Google Gemini API error ({exc.code}): {exc.read().decode('utf-8', 'ignore')}"
            ) from exc

        text = ""
        for cand in data.get("candidates", []):
            parts = cand.get("content", {}).get("parts", [])
            for p in parts:
                text += p.get("text", "")
        return ModelResponse(text=text, model=model, provider="google", raw=data)
