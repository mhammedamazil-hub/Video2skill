# Skill Architect: builds the portable skill package (SKILL.md + manifest).

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SkillPackage:
    skill_id: str
    name: str
    description: str
    version: str = "0.1.0"
    skill_md: str = ""
    manifest: dict[str, Any] = field(default_factory=dict)


class SkillArchitect:
    name = "architect"

    def build(
        self,
        sas: dict[str, Any],
        procedure,
        research_findings,
        provider_id: str,
        model: str,
    ) -> SkillPackage:
        goal = sas.get("goal", "Untitled capability")
        domain = sas.get("domain", "")
        software = sas.get("software", "")
        source = sas.get("source", "")

        skill_id = "skill-" + self._slug(goal)
        name = self._slug(goal)
        description = f"Learn {goal} from {source} via Video2Skill."

        skill_md = self._render_skill_md(name, description, sas, procedure, research_findings, source)

        manifest = {
            "id": skill_id,
            "name": name,
            "description": description,
            "version": "0.1.0",
            "status": "draft",
            "source": source,
            "provider": provider_id,
            "model": model,
            "capability": sas,
            "procedure": self._procedure_to_dict(procedure),
            "findings_count": len(research_findings) if research_findings else 0,
        }

        return SkillPackage(
            skill_id=skill_id,
            name=name,
            description=description,
            skill_md=skill_md,
            manifest=manifest,
        )

    def _slug(self, text: str) -> str:
        slug = "".join(c if c.isalnum() else "-" for c in text.lower()).strip("-")
        return slug or "skill"

    def _procedure_to_dict(self, procedure) -> dict[str, Any]:
        return {
            "preconditions": procedure.preconditions,
            "required_tools": procedure.required_tools,
            "initial_state": procedure.initial_state,
            "actions": [
                {
                    "step": a.step,
                    "timestamp": a.timestamp,
                    "action": a.action,
                    "parameters": a.parameters,
                    "precondition": a.precondition,
                    "expected_state": a.expected_state,
                    "decision_point": a.decision_point,
                    "common_mistake": a.common_mistake,
                    "error_recovery": a.error_recovery,
                    "evidence": a.evidence,
                }
                for a in procedure.actions
            ],
            "final_result": procedure.final_result,
            "error_recovery": procedure.error_recovery,
        }

    def _render_skill_md(
        self,
        name: str,
        description: str,
        sas: dict[str, Any],
        procedure,
        research_findings,
        source: str,
    ) -> str:
        lines = []
        lines.append("---")
        lines.append(f"name: {name}")
        lines.append(f"description: {description}")
        lines.append("allowed-tools: Read")
        lines.append("metadata:")
        lines.append(f"  source: {source}")
        lines.append(f"  generated_by: video2skill")
        lines.append(f"  domain: {sas.get('domain', '')}")
        lines.append(f"  software: {sas.get('software', '')}")
        lines.append(f"  software_version: {sas.get('software_version', '')}")
        lines.append("---")
        lines.append("")
        lines.append(f"# {name}")
        lines.append("")
        lines.append(description)
        lines.append("")
        lines.append("## Source")
        lines.append(f"- Video/source: {source}")
        lines.append(f"- Goal: {sas.get('goal', '')}")
        lines.append(f"- Domain: {sas.get('domain', '')}")
        lines.append(f"- Software: {sas.get('software', '')} ({sas.get('software_version', '')})")
        lines.append(f"- Operating system: {sas.get('operating_system', '')}")
        lines.append("")
        lines.append("## Preconditions")
        for p in procedure.preconditions or ["None specified"]:
            lines.append(f"- {p}")
        lines.append("")
        lines.append("## Required tools")
        for t in procedure.required_tools or ["None specified"]:
            lines.append(f"- {t}")
        lines.append("")
        lines.append("## Procedure")
        lines.append("")
        for a in procedure.actions or []:
            lines.append(f"### Step {a.step} (t={a.timestamp}s)")
            lines.append(f"- Action: {a.action}")
            if a.precondition:
                lines.append(f"- Precondition: {a.precondition}")
            if a.expected_state:
                lines.append(f"- Expected state: {a.expected_state}")
            if a.common_mistake:
                lines.append(f"- Common mistake: {a.common_mistake}")
            if a.error_recovery:
                lines.append(f"- Error recovery: {a.error_recovery}")
            for e in a.evidence or []:
                lines.append(f"  - Evidence: t={e.get('timestamp')}s type={e.get('type')} conf={e.get('confidence')}")
            lines.append("")
        lines.append("## Final result")
        lines.append(procedure.final_result or "Task completed.")
        lines.append("")
        lines.append("## Error recovery")
        for r in procedure.error_recovery or ["No specific recovery steps recorded."]:
            lines.append(f"- {r}")
        lines.append("")
        lines.append("## Verification")
        lines.append("- Run `video2skill test <skill-name>` to examine this skill.")
        lines.append("- Verification is execution, not vibes: steps are run in a sandbox.")
        lines.append("")
        lines.append("## Evidence")
        lines.append("Every step cites its source timestamp and frame evidence from the video.")
        lines.append("")
        return "\n".join(lines)
