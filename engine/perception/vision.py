# Visual action understanding: vision model interface.

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class VisualEvent:
    timestamp: float
    frame_path: str
    description: str
    action: str
    ui_state: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0


@dataclass
class VisionAnalysis:
    events: list[VisualEvent] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "events": [
                {
                    "timestamp": e.timestamp,
                    "frame_path": e.frame_path,
                    "description": e.description,
                    "action": e.action,
                    "ui_state": e.ui_state,
                    "confidence": e.confidence,
                }
                for e in self.events
            ]
        }


class VisionModel:
    """Interface to a vision-capable foundation model.

    The concrete provider adapter is responsible for calling the model.
    This class holds the vision analysis contract only.
    """

    def analyze_frame(self, frame_path: str, prompt: str) -> VisualEvent:
        raise NotImplementedError
