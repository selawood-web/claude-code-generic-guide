from pathlib import Path

import pytest

from shorts_pipeline.models import Scene, Script, VoiceTrack, WordTiming
from shorts_pipeline.render.compose import MIN_SCENE, segment_bounds


def test_segment_bounds_follow_word_timings(script: Script, voice: VoiceTrack) -> None:
    bounds = segment_bounds(script, voice)
    assert len(bounds) == 3
    assert bounds[0][0] == 0.0
    assert bounds[0][1] == pytest.approx(voice.words[3].start)
    assert bounds[1][1] == pytest.approx(voice.words[6].start)
    assert bounds[2][1] == pytest.approx(voice.duration)
    for (_, prev_end), (start, _) in zip(bounds, bounds[1:], strict=False):
        assert start == prev_end


def test_segment_bounds_fall_back_when_word_counts_differ(script: Script, tmp_path: Path) -> None:
    words = [WordTiming(word="x", start=0, end=1), WordTiming(word="y", start=1, end=2)]
    voice = VoiceTrack(audio_path=tmp_path / "v", duration=12.0, words=words)
    bounds = segment_bounds(script, voice)
    assert bounds[0][0] == 0.0 and bounds[-1][1] == 12.0
    assert all(end > start for start, end in bounds)


def test_segment_bounds_enforce_minimum_scene_length(tmp_path: Path) -> None:
    script = Script(
        topic="t",
        hook="a",
        title="x",
        description="d",
        scenes=[Scene(narration="b", visual_prompt="v"), Scene(narration="c", visual_prompt="v")],
    )
    words = [WordTiming(word=w, start=i * 0.1, end=i * 0.1 + 0.05) for i, w in enumerate("abc")]
    voice = VoiceTrack(audio_path=tmp_path / "v", duration=0.3, words=words)
    for start, end in segment_bounds(script, voice):
        assert end - start >= MIN_SCENE


def test_segment_bounds_with_no_words_uses_length_split(script: Script, tmp_path: Path) -> None:
    voice = VoiceTrack(audio_path=tmp_path / "v", duration=9.0, words=[])
    bounds = segment_bounds(script, voice)
    assert bounds[-1][1] == 9.0 and len(bounds) == 3
