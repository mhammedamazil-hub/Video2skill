# Discovery Agent.

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Answer:
    question_id: str
    text: str
    confidence: float = 1.0


@dataclass
class SkillAcquisitionSpecification:
    """Structured contract for what the skill must do."""

    source: str
    goal: str = ""
    domain: str = ""
    software: str = ""
    software_version: str = ""
    workflow: str = ""
    output_quality: str = ""
    reproduce_or_generalize: str = ""
    success_criteria: str = ""
    operate_software: bool | None = None
    sandbox_allowed: bool | None = None
    plugins: list[str] = field(default_factory=list)
    operating_system: str = ""
    out_of_scope: list[str] = field(default_factory=list)
    clarification_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "goal": self.goal,
            "domain": self.domain,
            "software": self.software,
            "software_version": self.software_version,
            "workflow": self.workflow,
            "output_quality": self.output_quality,
            "reproduce_or_generalize": self.reproduce_or_generalize,
            "success_criteria": self.success_criteria,
            "operate_software": self.operate_software,
            "sandbox_allowed": self.sandbox_allowed,
            "plugins": self.plugins,
            "operating_system": self.operating_system,
            "out_of_scope": self.out_of_scope,
            "clarification_notes": self.clarification_notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SkillAcquisitionSpecification":
        return cls(
            source=data.get("source", ""),
            goal=data.get("goal", ""),
            domain=data.get("domain", ""),
            software=data.get("software", ""),
            software_version=data.get("software_version", ""),
            workflow=data.get("workflow", ""),
            output_quality=data.get("output_quality", ""),
            reproduce_or_generalize=data.get("reproduce_or_generalize", "reproduce"),
            success_criteria=data.get("success_criteria", ""),
            operate_software=data.get("operate_software"),
            sandbox_allowed=data.get("sandbox_allowed"),
            plugins=data.get("plugins", []),
            operating_system=data.get("operating_system", ""),
            out_of_scope=data.get("out_of_scope", []),
            clarification_notes=data.get("clarification_notes", []),
        )


class DiscoveryAgent:
    name = "discovery"

    def __init__(self) -> None:
        self.answers: dict[str, Answer] = {}
        self.asked: set[str] = set()

    # ------------------------------------------------------------------ ask
    def ask(self, question_id: str, prompt: str) -> str:
        if question_id in self.asked:
            return self.answers[question_id].text
        print(f"\n[discovery] {prompt}")
        sys.stdout.flush()
        try:
            text = sys.stdin.readline()
        except (KeyboardInterrupt, EOFError):
            print("\n[discovery] interview aborted by user.")
            sys.exit(130)
        text = text.strip()
        self.asked.add(question_id)
        self.answers[question_id] = Answer(question_id=question_id, text=text)
        return text

    def confirm(self, question_id: str, prompt: str) -> bool:
        answer = self.ask(question_id, prompt + " (yes/no)")
        return answer.lower().startswith("y")

    # ------------------------------------------------------------------ readiness
    def readiness_score(self, sas: SkillAcquisitionSpecification) -> tuple[float, list[str]]:
        """Evidence-based readiness. Not an LLM self-declaration."""
        checks = [
            ("goal", bool(sas.goal.strip()), "skill goal is defined"),
            ("domain", bool(sas.domain.strip()), "domain / software area identified"),
            ("software", bool(sas.software.strip()), "target software named"),
            ("workflow", bool(sas.workflow.strip()), "actions / workflow described"),
            ("success_criteria", bool(sas.success_criteria.strip()), "success criteria defined"),
            ("operate_software", sas.operate_software is not None, "execution mode decided"),
            ("sandbox_allowed", sas.sandbox_allowed is not None, "sandbox policy decided"),
            ("operating_system", bool(sas.operating_system.strip()), "operating system known"),
        ]
        passed = sum(1 for _, ok, _ in checks if ok)
        score = round(100.0 * passed / len(checks), 1)
        gaps = [label for _, ok, label in checks if not ok]

        # Critical requirements must be satisfied regardless of aggregate score.
        critical = ["goal", "software", "workflow", "success_criteria"]
        critical_missing = [label for key, ok, label in checks if key in critical and not ok]
        return score, gaps + critical_missing

    # ------------------------------------------------------------------ interview
    def interview(self, source: str) -> SkillAcquisitionSpecification:
        sas = SkillAcquisitionSpecification(source=source)

        print("=" * 62)
        print("Video2Skill - Discovery Agent")
        print("=" * 62)
        print("I need to understand exactly what capability you want to learn.")
        print("Answer naturally. You can correct yourself at any time.")
        print("Type your answer and press Enter. (Ctrl-C to abort.)")

        sas.goal = self.ask("goal", "What exactly should the skill do? Describe the capability in one sentence.")

        sas.domain = self.ask("domain", "What domain or software area is this for (e.g. Blender, a browser, a CLI tool)?")

        sas.software = self.ask("software", "Which specific software or product is the skill for?")

        sas.software_version = self.ask("software_version", "Which version of that software are you targeting? (or 'any')")

        sas.workflow = self.ask(
            "workflow",
            "What actions or workflow should the skill cover? "
            "Should it reproduce the tutorial step-by-step, or generalize beyond it?",
        )

        # Context-aware follow-up: if generalizing, probe further.
        if any(w in sas.workflow.lower() for w in ("general", "beyond", "adapt")):
            sas.reproduce_or_generalize = self.ask(
                "generalize_scope",
                "You want to generalize beyond the tutorial. "
                "Which variations or edge cases should the skill handle?",
            )
        else:
            sas.reproduce_or_generalize = "reproduce"

        sas.output_quality = self.ask(
            "quality",
            "What output quality is expected (e.g. a rendered image, a script, a configured project)?",
        )

        sas.success_criteria = self.ask(
            "success",
            "What does success look like? How will we verify the skill worked?",
        )

        sas.operate_software = self.confirm(
            "operate",
            "Should the agent operate the actual software to perform the task?",
        )

        if sas.operate_software:
            sas.sandbox_allowed = self.confirm(
                "sandbox",
                "Is execution allowed in a sandbox (isolated, disposable environment)?",
            )
            if not sas.sandbox_allowed:
                print("[discovery] Note: real-application execution requires explicit user authorization.")

        sas.plugins = self._list_answer(
            "plugins",
            "Are additional plugins or extensions necessary? (comma-separated, or 'none')",
        )

        sas.operating_system = self.ask(
            "os",
            "What operating system are you using (Windows, Linux, macOS)?",
        )

        sas.out_of_scope = self._list_answer(
            "scope",
            "What is explicitly outside the requested scope? (or 'none')",
        )

        note = self.ask("notes", "Any clarifications, corrections, or changes to requirements? (or 'none')")
        if note and note.lower() not in ("none", ""):
            sas.clarification_notes.append(note)

        return sas

    def _list_answer(self, question_id: str, prompt: str) -> list[str]:
        text = self.ask(question_id, prompt)
        if not text or text.lower() == "none":
            return []
        return [t.strip() for t in text.split(",") if t.strip()]

    # ------------------------------------------------------------------ run
    def run(self, source: str, library, cfg) -> dict[str, Any]:
        sas = self.interview(source)
        score, gaps = self.readiness_score(sas)

        report: dict[str, Any] = {
            "ok": True,
            "agent": self.name,
            "specification": sas.to_dict(),
            "readiness": {
                "score": score,
                "threshold": 95.0,
                "gate_met": score >= 95.0,
                "gaps": gaps,
            },
        }

        if score >= 95.0:
            report["message"] = (
                f"Readiness {score}% >= 95% threshold. Permission granted to begin controlled learning."
            )
            library.save_sas(source, sas.to_dict())
        else:
            report["message"] = (
                f"Readiness {score}% < 95% threshold. Missing: {', '.join(gaps) or 'minor items'}. "
                "Answer the gaps above and re-run discovery before acquisition begins."
            )

        return report


def run_discovery(source: str, library, cfg) -> dict[str, Any]:
    agent = DiscoveryAgent()
    return agent.run(source, library, cfg)


def run_discovery_noninteractive(
    source: str,
    library,
    cfg,
    spec_overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Non-interactive discovery for CI/automation.

    Accepts a Skill Acquisition Specification via spec_overrides dict.
    Falls back to environment-specified spec JSON file (V2S_SPEC_JSON).
    """
    spec_data: dict[str, Any] = {}

    # 1. Explicit overrides take precedence.
    if spec_overrides:
        spec_data.update(spec_overrides)

    # 2. Load from env-specified JSON file if not already provided.
    spec_json_path = os.environ.get("V2S_SPEC_JSON")
    if spec_json_path and not spec_data:
        try:
            with open(spec_json_path, "r", encoding="utf-8") as fh:
                spec_data.update(json.load(fh))
        except (OSError, json.JSONDecodeError) as exc:
            return {
                "ok": False,
                "agent": "discovery",
                "error": f"could not read spec file {spec_json_path}: {exc}",
            }

    # 3. Ensure source is set.
    spec_data["source"] = source

    # 4. Build SAS.
    sas = SkillAcquisitionSpecification.from_dict(spec_data)

    # 5. Compute readiness.
    agent = DiscoveryAgent()
    score, gaps = agent.readiness_score(sas)

    report: dict[str, Any] = {
        "ok": True,
        "agent": "discovery",
        "specification": sas.to_dict(),
        "readiness": {
            "score": score,
            "threshold": 95.0,
            "gate_met": score >= 95.0,
            "gaps": gaps,
            "mode": "noninteractive",
        },
    }

    if score >= 95.0:
        report["message"] = (
            f"Readiness {score}% >= 95% threshold. Permission granted to begin controlled learning."
        )
        library.save_sas(source, sas.to_dict())
    else:
        report["message"] = (
            f"Readiness {score}% < 95% threshold. Missing: {', '.join(gaps) or 'minor items'}. "
            "Provide the missing specification fields before acquisition begins."
        )

    return report
