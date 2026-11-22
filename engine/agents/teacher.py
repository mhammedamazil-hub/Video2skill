# Teacher Agent: converts demonstrations into structured procedural knowledge.

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ActionStep:
    step: int
    timestamp: float
    action: str
    parameters: dict[str, Any] = field(default_factory=dict)
    precondition: str = ""
    expected_state: str = ""
    decision_point: bool = False
    alternatives: list[str] = field(default_factory=list)
    common_mistake: str = ""
    error_recovery: str = ""
    dependencies: list[str] = field(default_factory=list)
    evidence: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class Procedure:
    preconditions: list[str] = field(default_factory=list)
    required_tools: list[str] = field(default_factory=list)
    initial_state: str = ""
    actions: list[ActionStep] = field(default_factory=list)
    final_result: str = ""
    error_recovery: list[str] = field(default_factory=list)
    alternatives: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)


@dataclass
class TeacherOutput:
    ok: bool = True
    procedure: Procedure = field(default_factory=Procedure)
    why_notes: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class TeacherAgent:
    name = "teacher"

    def run(self, findings, timeline_events: list[dict[str, Any]]) -> TeacherOutput:
        output = TeacherOutput()
        procedure = Procedure()

        # Derive preconditions and tools from demonstrated facts.
        for f in findings:
            claim = f.claim.lower()
            if any(w in claim for w in ("install", "require", "need", "must have")):
                procedure.required_tools.append(f.claim)
            if any(w in claim for w in ("before", "first", "start", "open")):
                procedure.preconditions.append(f.claim)

        # Build action steps from timeline events that carry an action
        # (vision-model detections) OR from transcript + frame evidence.
        step = 0
        for event in timeline_events:
            action = event.get("action", "")
            transcript = event.get("transcript", "")
            visual = event.get("visual", "")
            ts = float(event.get("timestamp", 0) or 0)

            if not action and not transcript and not visual:
                continue

            # If no explicit action was detected (no vision model), synthesize
            # a step from the transcript/frame so the skill is usable, but mark
            # it as needing verification.
            if not action:
                action = transcript or f"Observe screen state at t={ts}s"
                action = f"[verify] {action}"

            step += 1
            procedure.actions.append(
                ActionStep(
                    step=step,
                    timestamp=ts,
                    action=action,
                    parameters={},
                    precondition=transcript,
                    expected_state=visual,
                    evidence=[
                        {
                            "timestamp": event.get("timestamp"),
                            "type": event.get("evidence_type", "demonstrated"),
                            "reference": event.get("source_reference", ""),
                            "confidence": event.get("confidence", 0.0),
                        }
                    ],
                )
            )

        procedure.initial_state = "Software launched and ready (per discovery spec)."
        procedure.final_result = "Tutorial outcome reproduced."

        output.procedure = procedure
        output.why_notes = [
            "Each action is tied to a timestamped video event with frame evidence where available.",
            "Steps prefixed with [verify] lack vision-model confirmation and should be reviewed.",
            "Steps without demonstrated evidence are flagged for verification.",
        ]
        return output
