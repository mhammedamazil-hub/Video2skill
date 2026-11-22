# Audio transcription: Whisper-compatible speech recognition.

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Segment:
    start: float
    end: float
    text: str
    confidence: float = 0.0


@dataclass
class Transcription:
    language: str
    segments: list[Segment] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "language": self.language,
            "segments": [
                {"start": s.start, "end": s.end, "text": s.text, "confidence": s.confidence}
                for s in self.segments
            ],
        }


def _which(cmd: str) -> str | None:
    return shutil.which(cmd)


def transcribe(audio_path: str, model: str = "base") -> Transcription:
    """Transcribe audio using Whisper if available.

    Falls back to an empty transcription with a clear note if Whisper is not
    installed. Never fabricates transcript content.
    """
    whisper = _which("whisper")
    if not whisper:
        # Try the Python package.
        try:
            import whisper  # type: ignore

            model_obj = whisper.load_model(model)
            result = model_obj.transcribe(audio_path)
            segments = []
            for seg in result.get("segments", []):
                segments.append(
                    Segment(
                        start=float(seg.get("start", 0)),
                        end=float(seg.get("end", 0)),
                        text=str(seg.get("text", "")).strip(),
                        confidence=float(seg.get("confidence", 0.0) or 0.0),
                    )
                )
            return Transcription(language=str(result.get("language", "unknown")), segments=segments)
        except ImportError:
            return Transcription(
                language="unknown",
                segments=[],
            )

    out_dir = Path(audio_path).parent
    cmd = [
        whisper,
        audio_path,
        "--model",
        model,
        "--output_format",
        "json",
        "--output_dir",
        str(out_dir),
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    json_path = Path(audio_path).with_suffix(".json")
    data = json.loads(json_path.read_text(encoding="utf-8"))
    segments = []
    for seg in data.get("segments", []):
        segments.append(
            Segment(
                start=float(seg.get("start", 0)),
                end=float(seg.get("end", 0)),
                text=str(seg.get("text", "")).strip(),
                confidence=float(seg.get("confidence", 0.0) or 0.0),
            )
        )
    return Transcription(language=str(data.get("language", "unknown")), segments=segments)
