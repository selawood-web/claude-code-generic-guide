import pytest
from pydantic import ValidationError

from shorts_pipeline.models import Scene, Script, WordTiming


def _script(**kw: object) -> Script:
    base: dict[str, object] = dict(
        topic="t",
        hook="h",
        title="x",
        description="d",
        scenes=[Scene(narration="a", visual_prompt="v"), Scene(narration="b", visual_prompt="w")],
    )
    base.update(kw)
    return Script.model_validate(base)


def test_hashtags_are_normalised() -> None:
    s = _script(hashtags=["#Cats", "dogs", " # fish tank ", ""])
    assert s.hashtags == ["#Cats", "#dogs", "#fishtank"]


def test_full_narration_joins_hook_and_scenes() -> None:
    assert _script().full_narration == "h a b"


def test_script_needs_at_least_two_scenes() -> None:
    with pytest.raises(ValidationError):
        _script(scenes=[Scene(narration="a", visual_prompt="v")])


def test_script_rejects_too_many_scenes() -> None:
    with pytest.raises(ValidationError):
        _script(scenes=[Scene(narration="a", visual_prompt="v")] * 13)


def test_scene_rejects_empty_narration() -> None:
    with pytest.raises(ValidationError):
        Scene(narration="", visual_prompt="v")


def test_word_timing_rejects_end_before_start() -> None:
    with pytest.raises(ValidationError):
        WordTiming(word="x", start=2.0, end=1.0)


def test_word_timing_zero_length_is_allowed() -> None:
    assert WordTiming(word="x", start=1.0, end=1.0).end == 1.0


def test_word_timing_rejects_wrong_type() -> None:
    with pytest.raises(ValidationError):
        WordTiming(word="x", start="soon", end=1.0)  # type: ignore[arg-type]
