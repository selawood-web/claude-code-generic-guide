"""Thin, typed wrapper around the ffmpeg and ffprobe binaries.

Every call is an argv list (never a shell string), and every failure surfaces
ffmpeg's own stderr so a bad filter graph is diagnosable from the log.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path


class FfmpegError(RuntimeError):
    pass


def ensure_available() -> None:
    for binary in ("ffmpeg", "ffprobe"):
        if shutil.which(binary) is None:
            raise FfmpegError(f"{binary} not found on PATH; install ffmpeg (>= 6) first")


def run(args: list[str], *, timeout: int = 900) -> None:
    """Run ffmpeg with the given arguments (without the leading 'ffmpeg')."""
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
    except subprocess.TimeoutExpired as exc:
        raise FfmpegError(f"ffmpeg timed out after {timeout}s: {' '.join(cmd)}") from exc
    if proc.returncode != 0:
        raise FfmpegError(f"ffmpeg failed ({proc.returncode}): {proc.stderr.strip()}")


def probe(path: Path) -> dict[str, object]:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise FfmpegError(f"ffprobe failed on {path}: {proc.stderr.strip()}")
    data: dict[str, object] = json.loads(proc.stdout)
    return data


def duration(path: Path) -> float:
    info = probe(path)
    fmt = info.get("format")
    if not isinstance(fmt, dict) or "duration" not in fmt:
        raise FfmpegError(f"no duration in ffprobe output for {path}")
    return float(fmt["duration"])


def video_size(path: Path) -> tuple[int, int]:
    info = probe(path)
    streams = info.get("streams")
    if isinstance(streams, list):
        for stream in streams:
            if isinstance(stream, dict) and stream.get("codec_type") == "video":
                return int(stream["width"]), int(stream["height"])
    raise FfmpegError(f"no video stream in {path}")


def has_audio(path: Path) -> bool:
    streams = probe(path).get("streams")
    return isinstance(streams, list) and any(
        isinstance(s, dict) and s.get("codec_type") == "audio" for s in streams
    )
