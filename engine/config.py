"""Engine configuration loaded from the Video2Skill config directory."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ProviderConfig:
    id: str
    name: str
    type: str
    api_key_env: str
    base_url: str | None
    default_model: str
    enabled: bool


@dataclass
class EngineConfig:
    config_dir: str
    library_path: str
    providers: list[ProviderConfig] = field(default_factory=list)
    default_provider: str | None = None
    sandbox_enabled: bool = True
    sandbox_driver: str = "none"
    sandbox_timeout_ms: int = 300000
    sandbox_max_memory_mb: int = 2048
    sandbox_network: bool = False
    whisper_model: str = "base"
    keyframe_interval_sec: int = 5
    adaptive_sampling: bool = True


def _config_dir() -> str:
    return os.environ.get("VIDEO2SKILL_CONFIG_DIR", os.path.join(os.path.expanduser("~"), ".video2skill"))


def _read_json(path: str, default):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        return default
    except json.JSONDecodeError:
        return default


def engine_config() -> EngineConfig:
    config_dir = _config_dir()
    config_path = os.path.join(config_dir, "config.json")
    raw = _read_json(config_path, {})

    providers = []
    for p in raw.get("providers", []):
        providers.append(
            ProviderConfig(
                id=p.get("id", ""),
                name=p.get("name", ""),
                type=p.get("type", ""),
                api_key_env=p.get("apiKeyEnv", ""),
                base_url=p.get("baseUrl"),
                default_model=p.get("defaultModel", ""),
                enabled=bool(p.get("enabled", False)),
            )
        )

    library_path = raw.get("library", {}).get("path") or os.path.join(config_dir, "library")

    return EngineConfig(
        config_dir=config_dir,
        library_path=library_path,
        providers=providers,
        default_provider=raw.get("defaultProvider"),
        sandbox_enabled=bool(raw.get("sandbox", {}).get("enabled", True)),
        sandbox_driver=raw.get("sandbox", {}).get("driver", "none"),
        sandbox_timeout_ms=int(raw.get("sandbox", {}).get("timeoutMs", 300000)),
        sandbox_max_memory_mb=int(raw.get("sandbox", {}).get("maxMemoryMb", 2048)),
        sandbox_network=bool(raw.get("sandbox", {}).get("network", False)),
        whisper_model=raw.get("perception", {}).get("whisperModel", "base"),
        keyframe_interval_sec=int(raw.get("perception", {}).get("keyframeIntervalSec", 5)),
        adaptive_sampling=bool(raw.get("perception", {}).get("adaptiveSampling", True)),
    )
