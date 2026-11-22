#!/usr/bin/env python3
"""Video2Skill experiment runner for GitHub Actions CI.

Orchestrates the full baseline-vs-skilled learning experiment:

1. Download the tutorial video using yt-dlp
2. Run multimodal perception (frames, audio, transcription, OCR, timeline)
3. Generate a portable SKILL.md from the video evidence
4. Run BASELINE examination: fresh learner WITHOUT the skill
5. Run SKILLED examination: fresh learner WITH the skill
6. Objectively compare results
7. Improve and repeat if the skilled learner fails
8. Store all reports and evidence as workflow artifacts

Usage:
    python scripts/run_experiment.py <VIDEO_URL>

Environment variables:
    V2S_GOAL, V2S_DOMAIN, V2S_SOFTWARE, ...  - Skill specification fields
    V2S_SPEC_JSON                            - JSON file with full specification
    ANTHROPIC_API_KEY / OPENAI_API_KEY / ... - AI provider keys (optional)
    V2S_PROVIDER                             - Provider id to use for examination
    V2S_MODEL                                - Model id to use
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ENGINE_ROOT = Path(__file__).resolve().parents[1] / "engine"
if str(ENGINE_ROOT) not in sys.path:
    sys.path.insert(0, str(ENGINE_ROOT))

from bootstrap import (  # noqa: E402
    _default_provider_id as _bp_default_provider,
)
from config import engine_config  # noqa: E402
from evolution.engine import evolve_skill  # noqa: E402
from evaluation.runner import run_examination as _run_examination_internal  # noqa: E402
from library.store import SkillLibrary  # noqa: E402
from perception.pipeline import run_perception  # noqa: E402


def run_cmd(cmd: list[str], cwd: str | None = None, timeout: int = 600) -> subprocess.CompletedProcess:
    """Run a command, streaming output, returning the completed process."""
    print(f"[run] {' '.join(cmd)}", flush=True)
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, timeout=timeout)


def ensure_ffmpeg() -> str:
    """Locate ffmpeg, installing via apt if available on the runner."""
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        return ffmpeg

    # GitHub-hosted runners have sudo + apt.
    try:
        subprocess.run(["sudo", "apt-get", "update", "-qq"], check=False, timeout=120)
        subprocess.run(["sudo", "apt-get", "install", "-y", "-qq", "ffmpeg"], check=False, timeout=300)
    except Exception:
        pass

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        return ffmpeg

    raise RuntimeError("ffmpeg is required but not available. Install ffmpeg on the runner.")


def ensure_yt_dlp() -> str:
    """Locate yt-dlp, installing via pip if needed."""
    yt = shutil.which("yt-dlp")
    if yt:
        return yt

    subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "yt-dlp"], check=False, timeout=180)
    yt = shutil.which("yt-dlp")
    if yt:
        return yt

    # Try python -m yt_dlp
    return "yt-dlp"


def download_video(url: str, work_dir: str) -> str:
    """Download the tutorial video using yt-dlp. Returns local path."""
    out_dir = Path(work_dir) / "download"
    out_dir.mkdir(parents=True, exist_ok=True)

    yt = ensure_yt_dlp()
    out_template = str(out_dir / "%(id)s.%(ext)s")

    cmd = [yt, "--no-playlist", "-o", out_template, url]
    if isinstance(yt, str) and yt == "yt-dlp":
        cmd = [sys.executable, "-m", "yt_dlp", "--no-playlist", "-o", out_template, url]

    result = run_cmd(cmd, timeout=600)
    if result.returncode != 0:
        raise RuntimeError(f"yt-dlp failed:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}")

    # Find the downloaded file.
    for f in out_dir.iterdir():
        if f.is_file() and f.suffix.lower() in (".mp4", ".mkv", ".webm", ".mov", ".avi", ".flv"):
            return str(f)

    raise RuntimeError("yt-dlp completed but no video file was found.")


def probe_video(path: str) -> dict:
    """Get video metadata using ffprobe."""
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return {"error": "ffprobe not available"}

    cmd = [
        ffprobe, "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate,duration",
        "-show_entries", "format=duration,size",
        "-of", "json",
        path,
    ]
    result = run_cmd(cmd, timeout=60)
    if result.returncode != 0:
        return {"error": f"ffprobe failed: {result.stderr}"}

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"error": "could not parse ffprobe output"}


def run_examination_internal(skill_name: str, library: SkillLibrary, cfg) -> dict:
    """Run examination and return the report dict."""
    return _run_examination_internal(skill_name, library, cfg)


def run_baseline_examination(
    task_spec: dict,
    library: SkillLibrary,
    cfg,
) -> dict:
    """Run examination WITHOUT the skill (baseline).

    We temporarily blank the SKILL.md so learners have no skill guidance.
    """
    skill_name = task_spec.get("skill_name", "")
    skill_dir = library._skill_dir(skill_name)
    skill_md_path = skill_dir / "SKILL.md"

    # Save original skill md.
    original_skill_md = None
    if skill_md_path.exists():
        original_skill_md = skill_md_path.read_text(encoding="utf-8")
        # Blank the skill md - learners get no skill guidance.
        skill_md_path.write_text(
            "---\nname: baseline\n"
            "description: Baseline examination without skill guidance.\n"
            "allowed-tools: Read\n---\n\n# Baseline\n\nNo skill provided. "
            "Attempt the task using only general knowledge.\n",
            encoding="utf-8",
        )

    try:
        report = run_examination_internal(skill_name, library, cfg)
        report["condition"] = "baseline"
        return report
    finally:
        # Restore original skill md.
        if original_skill_md is not None:
            skill_md_path.write_text(original_skill_md, encoding="utf-8")


def _spec_from_env() -> dict[str, Any]:
    """Build a Skill Acquisition Specification from environment variables."""
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


def generate_skill_from_video(
    url: str,
    work_dir: str,
    cfg,
) -> tuple[dict, str]:
    """Download video, run perception, generate skill. Returns (discover_result, skill_id)."""
    # Download video.
    local_path = download_video(url, work_dir)
    print(f"[experiment] Video downloaded: {local_path}", flush=True)

    # Probe metadata.
    meta = probe_video(local_path)
    print(f"[experiment] Video metadata: {json.dumps(meta, indent=2)}", flush=True)

    # First, run discovery to get SAS + readiness.
    from agents.discovery import run_discovery_noninteractive  # noqa: E402

    library = SkillLibrary(cfg.library_path)
    source = local_path  # Use local path as source for CI

    spec_overrides = _spec_from_env()
    spec_overrides["source"] = source

    discover_result = run_discovery_noninteractive(source, library, cfg, spec_overrides=spec_overrides)
    print(f"[experiment] Discovery: {json.dumps(discover_result.get('readiness', {}), indent=2)}", flush=True)

    if not discover_result.get("readiness", {}).get("gate_met"):
        raise RuntimeError(
            f"Readiness gate not met: score={discover_result.get('readiness', {}).get('score')}, "
            f"gaps={discover_result.get('readiness', {}).get('gaps')}"
        )

    # Run perception on the local video.
    perception_work = Path(work_dir) / "perception"
    perception_work.mkdir(parents=True, exist_ok=True)

    perception = run_perception(
        local_path,
        str(perception_work),
        whisper_model=cfg.whisper_model,
        keyframe_interval_sec=float(cfg.keyframe_interval_sec),
    )
    print(f"[experiment] Perception: ok={perception.ok}, frames={len(perception.frames)}, "
          f"transcription={bool(perception.transcription)}", flush=True)

    # Generate skill package.
    from agents.architect import SkillArchitect  # noqa: E402
    from agents.research import ResearchAgent  # noqa: E402
    from agents.teacher import TeacherAgent  # noqa: E402
    from library.store import SkillManifest  # noqa: E402

    sas = discover_result["specification"]
    provider_id = _bp_default_provider(cfg) or "none"
    model = "claude-3-5-sonnet-20241022"
    for p in cfg.providers:
        if p.id == provider_id:
            model = p.default_model
            break

    research = ResearchAgent()
    timeline_events = []
    if perception.ok and perception.timeline:
        timeline_events = perception.timeline.to_dict().get("events", [])
    research_output = research.run(sas, timeline_events)

    teacher = TeacherAgent()
    teacher_output = teacher.run(research_output.findings, timeline_events)

    architect = SkillArchitect()
    package = architect.build(sas, teacher_output.procedure, research_output.findings, provider_id, model)

    # Persist evidence.
    skill_dir = library._skill_dir(package.skill_id)
    evidence_dir = skill_dir / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)

    if perception.frames:
        for i, frame in enumerate(perception.frames):
            try:
                shutil.copy2(frame, evidence_dir / f"frame_{i:04d}.jpg")
            except (OSError, shutil.Error):
                pass
    if perception.meta:
        (evidence_dir / "video.json").write_text(
            json.dumps(perception.meta, indent=2), encoding="utf-8"
        )
    if perception.transcription:
        (evidence_dir / "transcript.json").write_text(
            json.dumps(perception.transcription, indent=2), encoding="utf-8"
        )

    # Save video metadata separately.
    (evidence_dir / "video_probe.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    library.write_skill_md(package.skill_id, package.skill_md)

    manifest = SkillManifest(
        id=package.skill_id,
        name=package.name,
        description=package.description,
        source=source,
        capability=sas,
        providers=[provider_id] if provider_id != "none" else [],
        models=[model],
        status="draft",
    )
    library.save(manifest)

    print(f"[experiment] Skill generated: {package.skill_id} ({package.name})", flush=True)
    print(f"[experiment] Procedure steps: {len(teacher_output.procedure.actions)}", flush=True)

    discover_result["skill"] = {
        "id": package.skill_id,
        "name": package.name,
        "skill_md": package.skill_md,
        "procedure_steps": len(teacher_output.procedure.actions),
        "evidence_events": len(timeline_events),
        "perception_ok": perception.ok,
        "perception_limited": perception.limited,
        "perception_error": perception.error,
        "video_meta": meta,
        "local_video_path": local_path,
    }

    return discover_result, package.skill_id


def write_report(path: str, data: dict) -> None:
    """Write a JSON report file."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")


def compare_results(baseline: dict, skilled: dict) -> dict:
    """Objectively compare baseline vs skilled examination results."""
    def extract_scores(report: dict) -> dict:
        results = report.get("results", [])
        passed = 0
        failed = 0
        skipped = 0
        total = 0
        for r in results:
            if r.get("skipped"):
                skipped += 1
                continue
            total += 1
            if r.get("overall") in ("Strongly verified", "Basic verified"):
                passed += 1
            else:
                failed += 1
        return {"passed": passed, "failed": failed, "skipped": skipped, "total": total}

    b = extract_scores(baseline)
    s = extract_scores(skilled)

    baseline_rate = (b["passed"] / b["total"]) if b["total"] > 0 else 0.0
    skilled_rate = (s["passed"] / s["total"]) if s["total"] > 0 else 0.0

    improvement = skilled_rate - baseline_rate

    # Determine improvement significance.
    if skilled_rate == 1.0 and baseline_rate < 1.0:
        significance = "significant"
    elif improvement > 0.25:
        significance = "moderate"
    elif improvement > 0:
        significance = "marginal"
    elif improvement == 0:
        significance = "none"
    else:
        significance = "negative"

    return {
        "baseline": b,
        "skilled": s,
        "baseline_pass_rate": baseline_rate,
        "skilled_pass_rate": skilled_rate,
        "improvement": improvement,
        "improvement_significance": significance,
        "baseline_overall": baseline.get("overall", "unknown"),
        "skilled_overall": skilled.get("overall", "unknown"),
    }


def draw_conclusion(comparison: dict) -> str:
    """Draw a conclusion from the comparison."""
    sig = comparison.get("improvement_significance", "none")
    imp = comparison.get("improvement", 0)

    if sig == "significant":
        return (
            "The skill produces a MEASURABLE IMPROVEMENT. The skilled learner "
            "achieved a perfect pass rate while the baseline did not. "
            "The generated skill transfers capability effectively."
        )
    if sig == "moderate":
        return (
            "The skill produces a MODERATE IMPROVEMENT. The skilled learner "
            "performed better than baseline. Consider skill refinement."
        )
    if sig == "marginal":
        return (
            "The skill produces a MARGINAL IMPROVEMENT. The skill may help "
            "but the effect is small. Skill needs improvement."
        )
    if sig == "none":
        return (
            "NO MEASURABLE IMPROVEMENT detected. Both baseline and skilled "
            "learners performed similarly. The skill may not transfer capability."
        )
    return (
        "NEGATIVE result. The skilled learner performed worse than baseline. "
        "The skill may contain incorrect instructions."
    )


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: run_experiment.py <VIDEO_URL>", file=sys.stderr)
        return 2

    video_url = sys.argv[1]

    # Validate required spec fields.
    required = ["V2S_GOAL", "V2S_DOMAIN", "V2S_SOFTWARE", "V2S_SUCCESS_CRITERIA"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        print(f"[experiment] ERROR: Missing required spec env vars: {missing}", file=sys.stderr)
        print(f"[experiment] Set V2S_GOAL, V2S_DOMAIN, V2S_SOFTWARE, V2S_SUCCESS_CRITERIA", file=sys.stderr)
        return 2

    cfg = engine_config()
    library = SkillLibrary(cfg.library_path)

    work_dir = tempfile.mkdtemp(prefix="v2s-experiment-")
    print(f"[experiment] Work directory: {work_dir}", flush=True)

    experiment: dict = {
        "video_url": video_url,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "environment": {
            "platform": sys.platform,
            "python": sys.version,
            "ffmpeg": shutil.which("ffmpeg") or "not found",
            "yt_dlp": shutil.which("yt-dlp") or "not found",
            "provider": _bp_default_provider(cfg) or "none",
            "model": cfg.providers[0].default_model if cfg.providers else "none",
        },
        "discovery": None,
        "baseline": None,
        "skilled": None,
        "comparison": None,
        "evolution": [],
        "conclusion": None,
    }

    try:
        # Step 1-3: Download, perceive, generate skill.
        print("[experiment] Phase 1: Acquiring video and generating skill...", flush=True)
        discover_result, skill_id = generate_skill_from_video(video_url, work_dir, cfg)
        experiment["discovery"] = discover_result

        # Step 4: Baseline examination (without skill).
        print("[experiment] Phase 2: Running baseline examination (no skill)...", flush=True)
        task_spec = {
            "skill_name": skill_id,
            "description": discover_result["specification"].get("goal", ""),
            "success_criteria": discover_result["specification"].get("success_criteria", ""),
            "software": discover_result["specification"].get("software", ""),
            "operating_system": discover_result["specification"].get("operating_system", ""),
        }
        baseline_report = run_baseline_examination(task_spec, library, cfg)
        experiment["baseline"] = baseline_report

        # Step 5: Skilled examination (with skill).
        print("[experiment] Phase 3: Running skilled examination (with skill)...", flush=True)
        skilled_report = run_examination_internal(skill_id, library, cfg)
        skilled_report["condition"] = "skilled"
        experiment["skilled"] = skilled_report

        # Step 6: Objective comparison.
        print("[experiment] Phase 4: Comparing results...", flush=True)
        comparison = compare_results(baseline_report, skilled_report)
        experiment["comparison"] = comparison

        # Step 7: Improve and repeat if skilled learner failed.
        evolution_reports = []
        if comparison.get("improvement_significance") in ("none", "negative", "marginal"):
            print("[experiment] Phase 5: Skilled learner needs improvement - evolving skill...", flush=True)
            for round_num in range(1, 3):  # Up to 2 evolution rounds
                print(f"[experiment] Evolution round {round_num}...", flush=True)
                evolve_result = evolve_skill(skill_id, library, cfg)
                evolution_reports.append({
                    "round": round_num,
                    "result": evolve_result,
                })
                if not evolve_result.get("ok"):
                    print(f"[experiment] Evolution failed: {evolve_result.get('error', 'unknown')}", flush=True)
                    break

                # Re-run skilled examination with evolved skill.
                evolved_report = run_examination_internal(skill_id, library, cfg)
                evolved_report["condition"] = f"skilled-evolved-round-{round_num}"
                evolution_reports[-1]["re_examination"] = evolved_report

                # Re-compare.
                new_comparison = compare_results(baseline_report, evolved_report)
                print(f"[experiment] Round {round_num}: baseline={comparison['baseline_overall']} "
                      f"skilled={evolved_report.get('overall', 'unknown')} "
                      f"improvement={new_comparison.get('improvement', 0):.2f}", flush=True)

                if new_comparison.get("improvement_significance") in ("significant", "moderate"):
                    comparison = new_comparison
                    experiment["skilled"] = evolved_report
                    break
                comparison = new_comparison

        experiment["evolution"] = evolution_reports

        # Step 8: Conclusion.
        experiment["conclusion"] = draw_conclusion(comparison)
        experiment["completed_at"] = datetime.now(timezone.utc).isoformat()

        # Write reports.
        reports_dir = Path(work_dir) / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)

        write_report(str(reports_dir / "experiment.json"), experiment)
        write_report(str(reports_dir / "baseline_results.json"), baseline_report)
        write_report(str(reports_dir / "skilled_results.json"), skilled_report)
        write_report(str(reports_dir / "comparison_report.json"), comparison)
        write_report(str(reports_dir / "conclusion.json"), {"conclusion": experiment["conclusion"]})
        if evolution_reports:
            write_report(str(reports_dir / "evolution.json"), {"evolution": evolution_reports})

        # Also write the skill package.
        skill_dir = library._skill_dir(skill_id)
        shutil.copytree(skill_dir, reports_dir / "skill_package", dirs_exist_ok=True)

        print(f"[experiment] Conclusion: {experiment['conclusion']}", flush=True)
        print(f"[experiment] Reports saved to: {reports_dir}", flush=True)

        # Print summary for CI log.
        print("\n" + "=" * 62, flush=True)
        print("VIDEO2SKILL EXPERIMENT RESULTS", flush=True)
        print("=" * 62, flush=True)
        print(f"Video: {video_url}", flush=True)
        print(f"Skill: {skill_id}", flush=True)
        print(f"Baseline: {baseline_report.get('overall', 'unknown')}", flush=True)
        print(f"Skilled: {skilled_report.get('overall', 'unknown')}", flush=True)
        print(f"Improvement: {comparison.get('improvement', 'unknown')}", flush=True)
        print(f"Conclusion: {experiment['conclusion']}", flush=True)
        print("=" * 62, flush=True)

        return 0

    except Exception as exc:  # noqa: BLE001
        experiment["error"] = str(exc)
        experiment["failed_at"] = datetime.now(timezone.utc).isoformat()
        print(f"[experiment] FAILED: {exc}", file=sys.stderr, flush=True)

        # Still write what we have.
        reports_dir = Path(work_dir) / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        write_report(str(reports_dir / "experiment.json"), experiment)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
