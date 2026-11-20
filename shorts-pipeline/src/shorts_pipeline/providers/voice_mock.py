"""Offline voice: a quiet tone track with evenly spaced word timings.

Produces a real audio file so the renderer and the publishers see the same
shapes they would see in production.
"""

from __future__ import annotations

from pathlib import Path

from ..models import VoiceTrack, WordTiming
from ..render import ffmpeg

WORDS_PER_SECOND = 2.6


class MockVoice:
    def synthesize(self, text: str, out_dir: Path) -> VoiceTrack:
        tokens = text.split()
        if not tokens:
            raise ValueError("cannot synthesize empty text")
        per_word = 1.0 / WORDS_PER_SECOND
        total = round(len(tokens) * per_word + 0.6, 2)
        audio_path = out_dir / "voice.m4a"
        ffmpeg.run(
            [
                "-f",
                "lavfi",
                "-i",
                f"sine=frequency=220:sample_rate=44100:duration={total}",
                "-af",
                "volume=0.05",
                "-c:a",
                "aac",
                "-b:a",
                "96k",
                str(audio_path),
            ]
        )
        words = [
            WordTiming(
                word=w, start=round(i * per_word, 3), end=round((i + 1) * per_word - 0.05, 3)
            )
            for i, w in enumerate(tokens)
        ]
        return VoiceTrack(audio_path=audio_path, duration=ffmpeg.duration(audio_path), words=words)
