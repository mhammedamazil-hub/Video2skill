# Base model provider adapter.

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ModelResponse:
    text: str
    model: str
    provider: str
    raw: dict[str, Any]


class Provider:
    """Base adapter for a foundation model provider.

    Substances implement `complete(messages, **kwargs) -> ModelResponse`.
    Never hardcodes API keys: keys are read from environment variables.
    """

    provider_id: str = "base"

    def complete(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> ModelResponse:
        raise NotImplementedError

    def available(self) -> bool:
        """Whether this provider is configured and reachable."""
        return False
