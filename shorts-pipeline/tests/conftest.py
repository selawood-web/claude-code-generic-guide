from __future__ import annotations

from pathlib import Path

import pytest

from shorts_pipeline.models import Scene, Script, VoiceTrack, WordTiming


@pytest.fixture
def script() -> Script:
    return Script(
        topic="t",
        hook="One two three.",
        scenes=[
            Scene(narration="Four five six.", visual_prompt="a"),
            Scene(narration="Seven eight nine ten.", visual_prompt="b"),
        ],
        title="Title",
        description="Desc",
        hashtags=["#a", "b"],
    )


def make_voice(words: list[str], per_word: float, audio: Path) -> VoiceTrack:
    timings = [
        WordTiming(word=w, start=i * per_word, end=(i + 1) * per_word - 0.05)
        for i, w in enumerate(words)
    ]
    return VoiceTrack(audio_path=audio, duration=len(words) * per_word, words=timings)


@pytest.fixture
def voice(script: Script, tmp_path: Path) -> VoiceTrack:
    audio = tmp_path / "voice.m4a"
    audio.write_bytes(b"")
    return make_voice(script.full_narration.split(), 0.4, audio)
