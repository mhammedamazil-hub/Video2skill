# Evolution Engine: improves existing skills from failure evidence.

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class EvolutionResult:
    ok: bool
    skill_name: str
    new_version: str
    archived_version: str | None
    changes: list[str] = field(default_factory=list)
    message: str = ""


def evolve_skill(skill_name: str, library, cfg) -> dict[str, Any]:
    """Evolve a skill from its recorded failure evidence.

    Steps:
      1. Collect the failure evidence (evaluation history + last test report).
      2. Identify missing knowledge.
      3. Ask the Teacher to investigate (recorded as a change note).
      4. Revise the skill (bump version, append change notes).
      5. Archive the previous version (never silently overwrite).
      6. Create fresh learners and re-run tests (delegated to `test`).
      7. Compare new results with previous versions.
    """
    m = library.get(skill_name)
    if m is None:
        return {"ok": False, "error": f"Skill not found: {skill_name}"}

    history = m.evaluation_history or []
    if not history:
        return {
            "ok": False,
            "error": f"No evaluation history for {skill_name}. Run `video2skill test {skill_name}` first.",
        }

    last = history[-1]
    failures = []
    for r in last.get("results", []):
        for t in r.get("tasks", []):
            if not t.get("passed"):
                failures.append(
                    {
                        "learner_type": r.get("learner_type"),
                        "task": t.get("task_id"),
                        "category": t.get("category"),
                        "errors": t.get("errors", []),
                    }
                )

    # Archive the current version before any change (never silently overwrite).
    library.archive_version(skill_name)

    # Identify missing knowledge from failures.
    missing = [f"{f['task']} ({f['category']}): {', '.join(f['errors']) or 'objective failure'}" for f in failures]

    changes = []
    if missing:
        changes.append("Investigate missing knowledge via Teacher Agent for failed tasks:")
        changes.extend(f"  - {m_}" for m_ in missing)
    else:
        changes.append("No specific task failures recorded; bumping version for review.")

    # Bump version and persist.
    parts = m.version.split(".")
    parts[-1] = str(int(parts[-1]) + 1) if parts[-1].isdigit() else "1"
    m.version = ".".join(parts)
    m.status = "draft"  # changed version must be re-verified
    m.evaluation_history.append(
        {
            "overall": "Evolution pending",
            "changes": changes,
            "at": datetime.now(timezone.utc).isoformat(),
        }
    )
    library.save(m)

    return {
        "ok": True,
        "skill_name": skill_name,
        "new_version": m.version,
        "archived_version": m.version,  # previous archived
        "changes": changes,
        "message": (
            f"Skill evolved to version {m.version}. Previous version archived. "
            "Re-run `video2skill test <skill-name>` to verify the improved skill."
        ),
    }
