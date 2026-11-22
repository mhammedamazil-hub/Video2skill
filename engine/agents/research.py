# Research Agent: acquires knowledge and tags every finding with evidence type.

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Finding:
    """A single piece of knowledge with traceable evidence.

    evidence_type is one of:
      - demonstrated: observed in the video
      - documented: from official docs / manuals
      - inference: AI-derived, not directly evidenced
    """

    claim: str
    evidence_type: str  # demonstrated | documented | inference
    timestamp: float | None = None
    source_reference: str = ""
    confidence: float = 0.0


@dataclass
class ResearchOutput:
    ok: bool = True
    findings: list[Finding] = field(default_factory=list)
    missing_knowledge: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class ResearchAgent:
    name = "research"

    def run(self, source: str, timeline_events: list[dict[str, Any]]) -> ResearchOutput:
        output = ResearchOutput()

        # Every timeline event that has a transcript or visual description is a
        # demonstrated fact. Everything else is an inference pending verification.
        for event in timeline_events:
            ts = event.get("timestamp")
            transcript = event.get("transcript", "")
            visual = event.get("visual", "")
            action = event.get("action", "")
            ref = event.get("source_reference", "")

            if transcript or visual or action:
                claim_parts = [p for p in [transcript, visual, action] if p]
                output.findings.append(
                    Finding(
                        claim=" | ".join(claim_parts),
                        evidence_type="demonstrated",
                        timestamp=ts,
                        source_reference=ref,
                        confidence=float(event.get("confidence", 0.0) or 0.0),
                    )
                )
            else:
                output.missing_knowledge.append(f"unsubstantiated event at t={ts}")

        return output
