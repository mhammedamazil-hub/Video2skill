# Multimodal timeline alignment: audio + video + visual events.

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TimelineEvent:
    timestamp: float
    transcript: str = ""
    visual: str = ""
    action: str = ""
    ui_state: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    source_reference: str = ""


@dataclass
class Timeline:
    events: list[TimelineEvent] = field(default_factory=list)

    def add(
        self,
        timestamp: float,
        transcript: str = "",
        visual: str = "",
        action: str = "",
        ui_state: dict[str, Any] | None = None,
        confidence: float = 0.0,
        source_reference: str = "",
    ) -> None:
        self.events.append(
            TimelineEvent(
                timestamp=timestamp,
                transcript=transcript,
                visual=visual,
                action=action,
                ui_state=ui_state or {},
                confidence=confidence,
                source_reference=source_reference,
            )
        )
        self.events.sort(key=lambda e: e.timestamp)

    def to_dict(self) -> dict[str, Any]:
        return {
            "events": [
                {
                    "timestamp": e.timestamp,
                    "transcript": e.transcript,
                    "visual": e.visual,
                    "action": e.action,
                    "ui_state": e.ui_state,
                    "confidence": e.confidence,
                    "source_reference": e.source_reference,
                }
                for e in self.events
            ]
        }
