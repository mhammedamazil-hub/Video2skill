# Local model inference server adapter (e.g. Ollama, llama.cpp, TGI).

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from providers.base import ModelResponse, Provider


class LocalProvider(Provider):
    provider_id = "local"

    def available(self) -> bool:
        return bool(os.environ.get("LOCAL_MODEL_BASE_URL"))

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
                "Local provider is not configured. Set LOCAL_MODEL_BASE_URL in your environment."
            )
        model = model or os.environ.get("LOCAL_MODEL", "llama3.1")
        base_url = os.environ["LOCAL_MODEL_BASE_URL"].rstrip("/")

        # Try OpenAI-compatible chat endpoint first.
        try:
            return self._openai_chat(base_url, model, messages, temperature, max_tokens)
        except (urllib.error.URLError, RuntimeError):
            pass
        # Fall back to Ollama /api/generate style.
        return self._ollama_generate(base_url, model, messages, temperature)

    def _openai_chat(
        self,
        base_url: str,
        model: str,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> ModelResponse:
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
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise RuntimeError(
                f"Local model API error ({exc.code}): {exc.read().decode('utf-8', 'ignore')}"
            ) from exc

        text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return ModelResponse(text=text, model=model, provider="local", raw=data)

    def _ollama_generate(
        self,
        base_url: str,
        model: str,
        messages: list[dict[str, str]],
        temperature: float,
    ) -> ModelResponse:
        prompt = "\n".join(f"{m.get('role', 'user')}: {m.get('content', '')}" for m in messages)
        body = {"model": model, "prompt": prompt, "stream": False, "temperature": temperature}
        url = base_url.rstrip("/") + "/api/generate"
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise RuntimeError(
                f"Local model API error ({exc.code}): {exc.read().decode('utf-8', 'ignore')}"
            ) from exc

        text = data.get("response", "")
        return ModelResponse(text=text, model=model, provider="local", raw=data)
