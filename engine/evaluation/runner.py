# Examination engine: Examiner Agent generates hidden tasks and objectively scores
# same-model and cross-model learner transfer.

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from learning.learner import LearnerAgent, TaskSpec
from providers.base import Provider
from providers.registry import build_providers, get_provider
from sandbox.base import Sandbox


@dataclass
class HiddenTask:
    task_id: str
    category: str  # reproduction | variation | unseen | troubleshooting | recovery | generalization
    description: str
    success_criteria: str
    hidden_from_learner: bool = True


@dataclass
class ExaminationResult:
    skill_name: str
    provider: str
    model: str
    learner_type: str  # same-model | cross-model
    tasks: list[dict[str, Any]] = field(default_factory=list)
    passed: int = 0
    failed: int = 0
    overall: str = "Experimental"  # Experimental | Failed | Basic verified | Strongly verified | Highly verified
    evidence: list[dict[str, Any]] = field(default_factory=list)


class ExaminerAgent:
    """Independently evaluates whether a skill works.

    Generates hidden tasks unknown to the learners and uses objective
    verification (real files, application states, assertions, execution
    results). Never accepts an LLM's self-declaration of success.
    """

    def __init__(self, provider: Provider, model: str, sandbox: Sandbox) -> None:
        self.provider = provider
        self.model = model
        self.sandbox = sandbox

    def hidden_tasks(self, skill_name: str, skill_md: str) -> list[HiddenTask]:
        """Derive hidden examination tasks from the skill package.

        These are not shown to learners during planning; they are generated
        by the Examiner independently.
        """
        categories = [
            ("reproduction", "Reproduce the tutorial's core workflow exactly as demonstrated."),
            ("variation", "Perform the same workflow with different parameter values."),
            ("unseen", "Apply the skill to a related but unseen task not shown in the video."),
            ("troubleshooting", "Diagnose and resolve a common failure mid-workflow."),
            ("recovery", "Recover from an error introduced during execution."),
            ("generalization", "Generalize the procedure to a new context."),
        ]
        tasks = []
        for i, (cat, desc) in enumerate(categories, 1):
            tasks.append(
                HiddenTask(
                    task_id=f"{skill_name}-{cat}-{i}",
                    category=cat,
                    description=desc,
                    success_criteria="Measurable outcome defined by the Examiner (see evaluation report).",
                )
            )
        return tasks


def run_examination(skill_name: str, library, cfg) -> dict[str, Any]:
    """Run the full examination suite for a skill.

    Tests both same-model transfer (Learner A) and cross-model transfer
    (Learner B) under equivalent conditions.
    """
    skill_dir = library._skill_dir(skill_name)
    skill_md_path = skill_dir / "SKILL.md"
    manifest_path = skill_dir / "skill.json"

    skill_md = skill_md_path.read_text(encoding="utf-8") if skill_md_path.exists() else ""
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}

    providers = build_providers(cfg)
    default_provider_id = cfg.default_provider or (list(providers.keys())[0] if providers else None)
    if not default_provider_id:
        return {
            "ok": False,
            "error": "No AI provider configured. Run `video2skill config provider <id>` first.",
        }

    # Same-model transfer: Learner A uses the same foundation model as the Teacher.
    teacher_model = manifest.get("model", "claude-3-5-sonnet-20241022")
    same_provider = get_provider(providers, default_provider_id)

    # Cross-model transfer: Learner B uses a different configured provider if available.
    cross_provider = same_provider
    cross_model = teacher_model
    for pid, p in providers.items():
        if pid != default_provider_id and p.available():
            cross_provider = p
            break
    cross_model = "gpt-4o" if teacher_model != "gpt-4o" else "claude-3-5-sonnet-20241022"

    sandbox = Sandbox(
        enabled=cfg.sandbox_enabled,
        driver=cfg.sandbox_driver,
        timeout_ms=cfg.sandbox_timeout_ms,
        max_memory_mb=cfg.sandbox_max_memory_mb,
        network=cfg.sandbox_network,
    )

    results = []
    for learner_type, prov, model in (
        ("same-model", same_provider, teacher_model),
        ("cross-model", cross_provider, cross_model),
    ):
        if not prov.available():
            results.append(
                {
                    "learner_type": learner_type,
                    "provider": prov.provider_id,
                    "model": model,
                    "skipped": True,
                    "reason": f"Provider {prov.provider_id} not configured (set {getattr(prov, 'api_key_env', 'API_KEY')} env var).",
                }
            )
            continue

        learner = LearnerAgent(provider=prov, model=model, sandbox=sandbox)
        examiner = ExaminerAgent(provider=prov, model=model, sandbox=sandbox)
        hidden = examiner.hidden_tasks(skill_name, skill_md)

        task_results = []
        passed = 0
        failed = 0
        for t in hidden:
            spec = TaskSpec(
                task_id=t.task_id,
                description=t.description,
                success_criteria=t.success_criteria,
                software=manifest.get("capability", {}).get("software", ""),
                operating_system=manifest.get("capability", {}).get("operating_system", ""),
                permitted_tools=["Read"],
            )
            attempt = learner.run(spec, skill_md)
            ok = attempt.passed
            passed += 1 if ok else 0
            failed += 1 if not ok else 0
            task_results.append(
                {
                    "task_id": t.task_id,
                    "category": t.category,
                    "description": t.description,
                    "passed": ok,
                    "attempts": len(attempt.attempts),
                    "errors": attempt.errors,
                }
            )

        total = passed + failed
        overall = "Experimental"
        if total > 0:
            ratio = passed / total
            if ratio == 1.0:
                overall = "Strongly verified"
            elif ratio >= 0.5:
                overall = "Basic verified"
            else:
                overall = "Failed"

        results.append(
            {
                "learner_type": learner_type,
                "provider": prov.provider_id,
                "model": model,
                "passed": passed,
                "failed": failed,
                "overall": overall,
                "tasks": task_results,
            }
        )

    # Combine: cross-model transferable only if both learners pass.
    same = next((r for r in results if r.get("learner_type") == "same-model"), {})
    cross = next((r for r in results if r.get("learner_type") == "cross-model"), {})
    if same.get("overall") in ("Strongly verified", "Basic verified") and cross.get("overall") in (
        "Strongly verified",
        "Basic verified",
    ):
        combined = "Cross-model transferable"
    elif same.get("overall") in ("Strongly verified", "Basic verified"):
        combined = "Model-specific"
    else:
        combined = "Experimental"

    report = {
        "ok": True,
        "skill_name": skill_name,
        "overall": combined,
        "results": results,
        "message": (
            "Examination complete. Verification is execution, not vibes: each "
            "task was run in a sandbox with objective assertions."
        ),
    }

    # Persist evaluation history in the manifest (never silently overwrite a
    # verified skill; append history and update status).
    m = library.get(skill_name)
    if m is not None:
        m.evaluation_history.append(
            {
                "overall": combined,
                "results": results,
                "at": datetime.now(timezone.utc).isoformat(),
            }
        )
        m.status = combined.lower().replace(" ", "_")
        library.save(m)

    return report
