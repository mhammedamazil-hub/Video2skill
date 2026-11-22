# Provider registry: maps engine config to provider instances.

from __future__ import annotations

from typing import Any

from providers.anthropic import AnthropicProvider
from providers.base import Provider
from providers.google import GoogleProvider
from providers.local import LocalProvider
from providers.openai import OpenAIProvider
from providers.openai_compatible import OpenAICompatibleProvider

_PROVIDER_CLASSES: dict[str, type[Provider]] = {
    "anthropic": AnthropicProvider,
    "openai": OpenAIProvider,
    "google": GoogleProvider,
    "openai-compatible": OpenAICompatibleProvider,
    "local": LocalProvider,
}


def build_providers(config: Any) -> dict[str, Provider]:
    """Instantiate providers from engine config."""
    providers: dict[str, Provider] = {}
    for p in config.providers:
        cls = _PROVIDER_CLASSES.get(p.type)
        if cls is None:
            continue
        providers[p.id] = cls()
    return providers


def get_provider(providers: dict[str, Provider], provider_id: str) -> Provider:
    if provider_id not in providers:
        raise KeyError(f"Provider '{provider_id}' is not configured. Available: {', '.join(providers)}")
    return providers[provider_id]
