# Video ingestion: download (yt-dlp), probe and extract frames (FFmpeg).

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class VideoMeta:
    path: str
    duration_sec: float
    width: int
    height: int
    fps: float
    size_bytes: int


def _which(cmd: str) -> str | None:
    return shutil.which(cmd)


def require_tool(cmd: str, hint: str) -> str:
    path = _which(cmd)
    if not path:
        raise RuntimeError(f"{cmd} is required but not found on PATH. {hint}")
    return path


@dataclass
class ExtractionResult:
    video: VideoMeta
    frames: list[str] = field(default_factory=list)
    scene_changes: list[float] = field(default_factory=list)


def download(source: str, out_dir: str) -> str:
    """Download a video from a URL (YouTube etc.) or copy a local file.

    Returns the local file path.
    """
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    yt_dlp = _which("yt-dlp")
    is_url = source.startswith("http://") or source.startswith("https://")

    if is_url:
        if not yt_dlp:
            raise RuntimeError(
                "yt-dlp is required to download online videos but is not installed. "
                "Install it (e.g. `pip install yt-dlp`) or provide a local video file."
            )
        target = out_path / "source.%(ext)s"
        cmd = [
            yt_dlp,
            "-o",
            str(target),
            "--no-playlist",
            "--write-info-json",
            source,
        ]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        for f in out_path.iterdir():
            if f.name.startswith("source.") and f.suffix not in (".json",):
                return str(f)
        raise RuntimeError("yt-dlp download completed but no video file was found.")
    else:
        src = Path(source)
        if not src.exists():
            raise FileNotFoundError(f"Local video file not found: {source}")
        dst = out_path / ("source" + src.suffix)
        if src.resolve() != dst.resolve():
            shutil.copy2(src, dst)
        return str(dst)


def probe(path: str) -> VideoMeta:
    ffprobe = require_tool("ffprobe", "Install FFmpeg to inspect video metadata.")
    cmd = [
        ffprobe,
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height,r_frame_rate,duration",
        "-show_entries",
        "format=duration,size",
        "-of",
        "json",
        path,
    ]
    out = subprocess.run(cmd, check=True, capture_output=True, text=True).stdout
    data = json.loads(out)
    stream = data["streams"][0]
    fmt = data.get("format", {})
    duration = float(fmt.get("duration") or stream.get("duration") or 0)
    size = int(fmt.get("size") or 0)
    rate = stream.get("r_frame_rate", "0/1")
    num, den = rate.split("/")
    fps = float(num) / float(den) if float(den) != 0 else 0.0
    return VideoMeta(
        path=path,
        duration_sec=duration,
        width=int(stream.get("width", 0)),
        height=int(stream.get("height", 0)),
        fps=fps,
        size_bytes=size,
    )


def extract_frames(
    path: str,
    out_dir: str,
    interval_sec: float = 5.0,
    scene_change: bool = True,
) -> ExtractionResult:
    """Extract keyframes at a fixed interval, optionally augmented by scene detection.

    Adaptive sampling: scene changes add extra keyframes; we avoid extracting
    thousands of redundant frames by capping the total count.
    """
    ffmpeg = require_tool("ffmpeg", "Install FFmpeg to extract frames.")
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    meta = probe(path)
    duration = meta.duration_sec or 0.0

    timestamps: list[float] = []
    t = 0.0
    while t < duration:
        timestamps.append(round(t, 3))
        t += interval_sec

    if scene_change and duration > 0:
        sc_cmd = [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            path,
            "-vf",
            "select='gt(scene,0.3)',showinfo",
            "-f",
            "null",
            "-",
        ]
        res = subprocess.run(sc_cmd, capture_output=True, text=True)
        for line in res.stderr.splitlines():
            m = re.search(r"pts_time:([0-9.]+)", line)
            if m:
                sc_t = float(m.group(1))
                if all(abs(sc_t - existing) > 1.0 for existing in timestamps):
                    timestamps.append(round(sc_t, 3))
        timestamps.sort()

    max_frames = 120
    if len(timestamps) > max_frames:
        step = len(timestamps) / max_frames
        timestamps = [timestamps[int(i * step)] for i in range(max_frames)]

    frames: list[str] = []
    for i, t in enumerate(timestamps):
        frame_path = out / f"frame_{i:04d}_t{int(t)}.jpg"
        cmd = [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            str(t),
            "-i",
            path,
            "-frames:v",
            "1",
            "-q:v",
            "3",
            str(frame_path),
        ]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        if frame_path.exists():
            frames.append(str(frame_path))

    return ExtractionResult(video=meta, frames=frames)


def extract_audio(path: str, out_path: str) -> str:
    ffmpeg = require_tool("ffmpeg", "Install FFmpeg to extract audio.")
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        path,
        "-vn",
        "-acodec",
        "pcm_s16le",
        "-ar",
        "16000",
        "-ac",
        "1",
        str(out),
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    return str(out)
