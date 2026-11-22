"""Video2Skill Python engine entry point.

Called by the TypeScript CLI with subcommands:
  discover <source>      - discovery interview + readiness assessment (+ skill generation)
  discover-ni <source>   - non-interactive discovery (CI) using V2S_SPEC_JSON or env vars
  examine <skill-name>   - run learner examinations
  evolve <skill-name>    - evolve a skill from failure evidence
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ENGINE_ROOT = Path(__file__).resolve().parent
if str(ENGINE_ROOT) not in sys.path:
    sys.path.insert(0, str(ENGINE_ROOT))

from agents.discovery import run_discovery, run_discovery_noninteractive  # noqa: E402
from agents.architect import SkillArchitect  # noqa: E402
from agents.teacher import TeacherAgent  # noqa: E402
from agents.research import ResearchAgent  # noqa: E402
from library.store import SkillLibrary, SkillManifest  # noqa: E402
from perception.pipeline import run_perception  # noqa: E402
from evaluation.runner import run_examination  # noqa: E402
from evolution.engine import evolve_skill  # noqa: E402


def _default_provider_id(cfg) -> str | None:
    if cfg.default_provider:
        return cfg.default_provider
    for p in cfg.providers:
        if p.enabled:
            return p.id
    return None


def _generate_skill(sas, library, cfg, perception) -> dict[str, Any] | None:
    """Build a skill package from the SAS plus any perception evidence.

    Returns the skill dict, or None if generation was skipped.
    """
    from typing import Any

    provider_id = _default_provider_id(cfg) or "none"
    model = "claude-3-5-sonnet-20241022"
    for p in cfg.providers:
        if p.id == provider_id:
            model = p.default_model
            break

    # Research: tag every perception timeline event as demonstrated evidence.
    research = ResearchAgent()
    timeline_events = []
    if perception and perception.ok and perception.timeline:
        timeline_events = perception.timeline.to_dict().get("events", [])
    research_output = research.run(sas, timeline_events)

    # Teacher: convert demonstrated findings into procedural knowledge.
    teacher = TeacherAgent()
    teacher_output = teacher.run(research_output.findings, timeline_events)

    # Architect: build the portable skill package.
    architect = SkillArchitect()
    package = architect.build(sas, teacher_output.procedure, research_output.findings, provider_id, model)

    # Persist evidence frames into the skill directory.
    skill_dir = library._skill_dir(package.skill_id)
    evidence_dir = skill_dir / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    if perception and perception.frames:
        import shutil

        for i, frame in enumerate(perception.frames):
            try:
                shutil.copy2(frame, evidence_dir / f"frame_{i:04d}.jpg")
            except (OSError, shutil.Error):
                pass
    if perception and perception.meta:
        (evidence_dir / "video.json").write_text(
            json.dumps(perception.meta, indent=2), encoding="utf-8"
        )
    if perception and perception.transcription:
        (evidence_dir / "transcript.json").write_text(
            json.dumps(perception.transcription, indent=2), encoding="utf-8"
        )

    library.write_skill_md(package.skill_id, package.skill_md)

    manifest = SkillManifest(
        id=package.skill_id,
        name=package.name,
        description=package.description,
        source=sas.get("source", ""),
        capability=sas,
        providers=[provider_id] if provider_id != "none" else [],
        models=[model],
        status="draft",
    )
    library.save(manifest)

    return {
        "id": package.skill_id,
        "name": package.name,
        "skill_md": package.skill_md,
        "procedure_steps": len(teacher_output.procedure.actions),
        "evidence_events": len(timeline_events),
        "perception_ok": bool(perception and perception.ok),
        "perception_limited": bool(perception and perception.limited),
        "perception_error": perception.error if perception else None,
    }


def _spec_from_env() -> dict[str, Any]:
    """Build a Skill Acquisition Specification from environment variables.

    Used by non-interactive discovery in CI.
    """
    def env_bool(key: str, default: bool = False) -> bool | None:
        val = os.environ.get(key)
        if val is None:
            return default
        return val.lower() in ("1", "true", "yes", "y")

    return {
        "goal": os.environ.get("V2S_GOAL", ""),
        "domain": os.environ.get("V2S_DOMAIN", ""),
        "software": os.environ.get("V2S_SOFTWARE", ""),
        "software_version": os.environ.get("V2S_SOFTWARE_VERSION", ""),
        "workflow": os.environ.get("V2S_WORKFLOW", ""),
        "output_quality": os.environ.get("V2S_OUTPUT_QUALITY", ""),
        "reproduce_or_generalize": os.environ.get("V2S_REPRODUCE_OR_GENERALIZE", "reproduce"),
        "success_criteria": os.environ.get("V2S_SUCCESS_CRITERIA", ""),
        "operate_software": env_bool("V2S_OPERATE_SOFTWARE", True),
        "sandbox_allowed": env_bool("V2S_SANDBOX_ALLOWED", True),
        "plugins": [p.strip() for p in os.environ.get("V2S_PLUGINS", "").split(",") if p.strip()],
        "operating_system": os.environ.get("V2S_OPERATING_SYSTEM", ""),
        "out_of_scope": [p.strip() for p in os.environ.get("V2S_OUT_OF_SCOPE", "").split(",") if p.strip()],
        "clarification_notes": [],
    }


def cmd_discover(source: str) -> int:
    from config import engine_config

    cfg = engine_config()
    library = SkillLibrary(cfg.library_path)
    result = run_discovery(source, library, cfg)

    # When the readiness gate is met, generate a draft skill package.
    if result.get("readiness", {}).get("gate_met"):
        sas = result["specification"]

        # Try to acquire and perceive the video. Best-effort: if the source
        # cannot be fetched (network blocked, platform restriction), we still
        # generate a SAS-based draft and record the limitation.
        perception = None
        try:
            import tempfile

            work_dir = tempfile.mkdtemp(prefix="v2s-perception-")
            perception = run_perception(
                source,
                work_dir,
                whisper_model=cfg.whisper_model,
                keyframe_interval_sec=float(cfg.keyframe_interval_sec),
            )
        except Exception as exc:  # noqa: BLE001
            perception = type(
                "P",
                (),
                {
                    "ok": False,
                    "limited": True,
                    "error": str(exc),
                    "frames": [],
                    "meta": None,
                    "timeline": None,
                    "transcription": None,
                },
            )()

        skill = _generate_skill(sas, library, cfg, perception)

        result["skill"] = skill
        result["message"] += (
            f"\nDraft skill generated: {skill['id']} ({skill['name']}). "
            f"Procedure steps: {skill['procedure_steps']}; "
            f"evidence events: {skill['evidence_events']}. "
        )
        if skill["perception_ok"]:
            result["message"] += "Video perception evidence was captured. "
        else:
            result["message"] += (
                f"Video could not be perceived ({skill['perception_error'] or 'unavailable'}). "
                "Skill is interview-based; provide the video as a local file for evidence-backed steps. "
            )
        result["message"] += "Review it, then run `video2skill test <skill-name>` to examine learners."

    print(json.dumps(result, indent=2))
    return 0 if result.get("ok") else 1


def cmd_discover_ni(source: str) -> int:
    """Non-interactive discover for CI automation."""
    from config import engine_config

    cfg = engine_config()
    library = SkillLibrary(cfg.library_path)

    spec_overrides = _spec_from_env()
    result = run_discovery_noninteractive(source, library, cfg, spec_overrides=spec_overrides)

    if not result.get("ok"):
        print(json.dumps(result, indent=2))
        return 1

    # When the readiness gate is met, generate a draft skill package.
    if result.get("readiness", {}).get("gate_met"):
        sas = result["specification"]

        perception = None
        try:
            import tempfile

            work_dir = tempfile.mkdtemp(prefix="v2s-perception-")
            perception = run_perception(
                source,
                work_dir,
                whisper_model=cfg.whisper_model,
                keyframe_interval_sec=float(cfg.keyframe_interval_sec),
            )
        except Exception as exc:  # noqa: BLE001
            perception = type(
                "P",
                (),
                {
                    "ok": False,
                    "limited": True,
                    "error": str(exc),
                    "frames": [],
                    "meta": None,
                    "timeline": None,
                    "transcription": None,
                },
            )()

        skill = _generate_skill(sas, library, cfg, perception)

        result["skill"] = skill
        result["message"] += (
            f"\nDraft skill generated: {skill['id']} ({skill['name']}). "
            f"Procedure steps: {skill['procedure_steps']}; "
            f"evidence events: {skill['evidence_events']}. "
        )
        if skill["perception_ok"]:
            result["message"] += "Video perception evidence was captured. "
        else:
            result["message"] += (
                f"Video could not be perceived ({skill['perception_error'] or 'unavailable'}). "
                "Skill is interview-based; provide the video as a local file for evidence-backed steps. "
            )
        result["message"] += "Review it, then run `video2skill test <skill-name>` to examine learners."

    print(json.dumps(result, indent=2))
    return 0 if result.get("ok") else 1


def cmd_examine(skill_name: str) -> int:
    from config import engine_config

    cfg = engine_config()
    library = SkillLibrary(cfg.library_path)
    report = run_examination(skill_name, library, cfg)
    print(json.dumps(report, indent=2))
    return 0


def cmd_evolve(skill_name: str) -> int:
    from config import engine_config

    cfg = engine_config()
    library = SkillLibrary(cfg.library_path)
    result = evolve_skill(skill_name, library, cfg)
    print(json.dumps(result, indent=2))
    return 0 if result.get("ok") else 1


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print("Usage: bootstrap.py <discover|discover-ni|examine|evolve> <argument>", file=sys.stderr)
        return 2

    command, *rest = argv
    if command == "discover":
        if not rest:
            print("Usage: bootstrap.py discover <source>", file=sys.stderr)
            return 2
        return cmd_discover(rest[0])
    if command == "discover-ni":
        if not rest:
            print("Usage: bootstrap.py discover-ni <source>", file=sys.stderr)
            return 2
        return cmd_discover_ni(rest[0])
    if command == "examine":
        if not rest:
            print("Usage: bootstrap.py examine <skill-name>", file=sys.stderr)
            return 2
        return cmd_examine(rest[0])
    if command == "evolve":
        if not rest:
            print("Usage: bootstrap.py evolve <skill-name>", file=sys.stderr)
            return 2
        return cmd_evolve(rest[0])
    print(f"Unknown command: {command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
