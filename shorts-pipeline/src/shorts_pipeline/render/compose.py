"""Turn a script, a voice track and per-scene visuals into one 1080x1920 MP4.

Pipeline: each scene -> silent intermediate clip (Ken Burns on stills, loop+crop on
video) -> concat -> mix voice (+ optional music) -> burn captions -> H.264 + AAC.
"""

from __future__ import annotations

from pathlib import Path

from ..config import RenderConfig
from ..models import HEIGHT, WIDTH, Script, VisualAsset, VoiceTrack
from . import ffmpeg
from .captions import write_ass

MIN_SCENE = 1.2


def segment_bounds(script: Script, voice: VoiceTrack) -> list[tuple[float, float]]:
    """Start/end seconds of the hook and each scene, derived from word timings.

    Word counts of the sent text and the returned alignment normally match. If a
    provider drops or merges tokens, fall back to splitting time by text length.
    """
    segments = [script.hook, *(s.narration for s in script.scenes)]
    counts = [len(seg.split()) for seg in segments]
    total_words = sum(counts)
    bounds: list[tuple[float, float]] = []
    if total_words == len(voice.words) and voice.words:
        cursor = 0
        for i, count in enumerate(counts):
            start = voice.words[cursor].start if i > 0 else 0.0
            cursor += count
            end = voice.duration if i == len(counts) - 1 else voice.words[cursor].start
            bounds.append((start, end))
    else:
        lengths = [max(1, len(seg)) for seg in segments]
        total = sum(lengths)
        t = 0.0
        for i, length in enumerate(lengths):
            end = voice.duration if i == len(lengths) - 1 else t + voice.duration * length / total
            bounds.append((t, end))
            t = end
    # guarantee a visible minimum per segment without exceeding the voice track
    fixed: list[tuple[float, float]] = []
    for start, end in bounds:
        fixed.append((start, max(end, start + MIN_SCENE)))
    return fixed


def _scene_clip(asset: VisualAsset, seconds: float, cfg: RenderConfig, target: Path) -> None:
    frames = max(1, round(seconds * cfg.fps))
    if asset.kind == "image":
        zoom = (
            f"zoompan=z='min(zoom+0.0006,1.12)':d={frames}"
            f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={WIDTH}x{HEIGHT}:fps={cfg.fps}"
        )
        big_w, big_h = WIDTH * 2, HEIGHT * 2  # oversample so the zoom never shows pixels
        fit = f"scale={big_w}:{big_h}:force_original_aspect_ratio=increase,crop={big_w}:{big_h}"
        vf = f"{fit},{zoom}"
        args = [
            "-loop",
            "1",
            "-framerate",
            str(cfg.fps),
            "-t",
            f"{seconds:.3f}",
            "-i",
            str(asset.path),
        ]
    else:
        vf = (
            f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
            f"crop={WIDTH}:{HEIGHT},fps={cfg.fps}"
        )
        args = ["-stream_loop", "-1", "-t", f"{seconds:.3f}", "-i", str(asset.path)]
    ffmpeg.run(
        [
            *args,
            "-vf",
            vf,
            "-an",
            "-t",
            f"{seconds:.3f}",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            str(target),
        ]
    )


def compose(
    script: Script,
    voice: VoiceTrack,
    visuals: list[VisualAsset],
    cfg: RenderConfig,
    work_dir: Path,
) -> tuple[Path, Path]:
    """Render final.mp4 and thumbnail.jpg into work_dir; return both paths."""
    ffmpeg.ensure_available()
    bounds = segment_bounds(script, voice)
    by_index = {a.scene_index: a for a in visuals}
    if len(bounds) != len(by_index):
        raise ValueError(f"{len(bounds)} narration segments but {len(by_index)} visuals")

    clips_dir = work_dir / "clips"
    clips_dir.mkdir(exist_ok=True)
    clip_paths: list[Path] = []
    for index, (start, end) in enumerate(bounds):
        clip = clips_dir / f"clip_{index:02d}.mp4"
        _scene_clip(by_index[index], end - start, cfg, clip)
        clip_paths.append(clip)

    concat_list = work_dir / "concat.txt"
    concat_list.write_text(
        "".join(f"file '{p.resolve().as_posix()}'\n" for p in clip_paths), encoding="utf-8"
    )
    silent = work_dir / "silent.mp4"
    ffmpeg.run(["-f", "concat", "-safe", "0", "-i", str(concat_list), "-c", "copy", str(silent)])

    ass_path = write_ass(
        voice.words,
        work_dir / "captions.ass",
        font=cfg.font,
        font_size=cfg.font_size,
        highlight=cfg.highlight_color,
    )

    inputs = ["-i", str(silent), "-i", str(voice.audio_path)]
    if cfg.music_path is not None and cfg.music_path.exists():
        inputs += ["-stream_loop", "-1", "-i", str(cfg.music_path)]
        audio = (
            f"[2:a]volume={cfg.music_gain_db}dB[m];"
            "[1:a][m]amix=inputs=2:duration=first:dropout_transition=2,"
            "loudnorm=I=-14:TP=-1.5:LRA=11[a]"
        )
    else:
        audio = "[1:a]loudnorm=I=-14:TP=-1.5:LRA=11[a]"
    escaped_ass = ass_path.resolve().as_posix().replace(":", "\\:").replace("'", "\\'")
    final = work_dir / "final.mp4"
    ffmpeg.run(
        [
            *inputs,
            "-filter_complex",
            f"[0:v]ass='{escaped_ass}'[v];{audio}",
            "-map",
            "[v]",
            "-map",
            "[a]",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            str(cfg.crf),
            "-pix_fmt",
            "yuv420p",
            "-r",
            str(cfg.fps),
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            "44100",
            "-movflags",
            "+faststart",
            "-shortest",
            str(final),
        ]
    )
    thumbnail = work_dir / "thumbnail.jpg"
    ffmpeg.run(["-ss", "1.0", "-i", str(final), "-frames:v", "1", "-q:v", "2", str(thumbnail)])
    return final, thumbnail
