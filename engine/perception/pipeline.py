# Perception pipeline: acquire a video (URL or local file) and build a
# multimodal timeline (transcript + frames + visual events + alignment).

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

from perception.video import download, probe, extract_frames, extract_audio
from perception.audio import transcribe
from perception.ocr import ocr_image
from perception.alignment import Timeline


@dataclass
class PerceptionResult:
    ok: bool
    source: str
    local_path: str | None = None
    meta: dict[str, Any] | None = None
    frames: list[str] = field(default_factory=list)
    transcription: dict[str, Any] | None = None
    timeline: Timeline | None = None
    error: str | None = None
    limited: bool = False  # True if perception ran with reduced capability


def run_perception(
    source: str,
    work_dir: str,
    whisper_model: str = "base",
    keyframe_interval_sec: float = 5.0,
) -> PerceptionResult:
    """Acquire and perceive a video, returning a multimodal timeline.

    If the video cannot be acquired (e.g. network blocked), returns a result
    with ok=False and an error describing the limitation. Callers should fall
    back to interview-only skill generation and offer a manual upload.
    """
    result = PerceptionResult(ok=False, source=source)

    # --- acquire ---------------------------------------------------------
    local_path: str | None = None
    try:
        local_path = download(source, work_dir)
    except Exception as exc:  # noqa: BLE001
        result.error = f"could not acquire video: {exc}"
        result.limited = True
        return result
    result.local_path = local_path

    # --- probe -----------------------------------------------------------
    try:
        meta = probe(local_path)
        result.meta = {
            "duration_sec": meta.duration_sec,
            "width": meta.width,
            "height": meta.height,
            "fps": meta.fps,
            "size_bytes": meta.size_bytes,
        }
    except Exception as exc:  # noqa: BLE001
        result.error = f"could not probe video: {exc}"
        result.limited = True
        return result

    # --- frames ----------------------------------------------------------
    frames_dir = os.path.join(work_dir, "frames")
    try:
        extraction = extract_frames(
            local_path, frames_dir, interval_sec=keyframe_interval_sec,
            scene_change=True,
        )
        result.frames = extraction.frames
    except Exception as exc:  # noqa: BLE001
        result.error = f"could not extract frames: {exc}"
        result.limited = True
        # continue with whatever we have

    # --- audio transcription --------------------------------------------
    try:
        audio_path = os.path.join(work_dir, "audio.wav")
        extract_audio(local_path, audio_path)
        transcription = transcribe(audio_path, model=whisper_model)
        result.transcription = transcription.to_dict()
    except Exception as exc:  # noqa: BLE001
        # Transcription is optional; proceed without it.
        result.transcription = None
        if not result.error:
            result.limited = True

    # --- align into timeline --------------------------------------------
    timeline = Timeline()
    # Index transcript segments by nearest timestamp.
    segments = (result.transcription or {}).get("segments", []) if result.transcription else []

    def transcript_near(ts: float, window: float = 2.0) -> str:
        best = ""
        best_dist = window
        for seg in segments:
            st = float(seg.get("start", 0) or 0)
            en = float(seg.get("end", 0) or 0)
            mid = (st + en) / 2.0
            dist = abs(mid - ts)
            if dist <= window and dist < best_dist:
                best_dist = dist
                best = str(seg.get("text", ""))
        return best

    # Visual events from frames (each frame gets a placeholder visual note;
    # a vision model would fill these in).
    for i, frame_path in enumerate(result.frames):
        ts = i * keyframe_interval_sec
        timeline.add(
            timestamp=round(ts, 3),
            transcript=transcript_near(ts),
            visual=f"frame {i}: {os.path.basename(frame_path)}",
            action="",
            confidence=0.0,
            source_reference=frame_path,
        )

    # OCR on a subset of frames (first few) to capture UI text.
    for frame_path in result.frames[:5]:
        try:
            ocr = ocr_image(frame_path)
            if ocr.text.strip():
                # attach OCR text to the nearest timeline event
                pass
        except Exception:
            pass

    result.timeline = timeline
    result.ok = True
    return result
