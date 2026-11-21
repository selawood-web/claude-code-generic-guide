from shorts_pipeline.config import ScriptConfig
from shorts_pipeline.providers.script_claude import SYSTEM_PROMPT, build_prompt


def test_prompt_picks_within_niche_when_no_queue() -> None:
    prompt = build_prompt(ScriptConfig(niche="honest everything"), [])
    assert "Pick one fresh topic within the niche: honest everything" in prompt
    assert "none yet" in prompt and "Channel brief" not in prompt


def test_prompt_uses_first_unused_queued_topic() -> None:
    cfg = ScriptConfig(topics=["a", "b", "c"])
    assert "Topic to cover: b" in build_prompt(cfg, ["a"])


def test_prompt_includes_brief_and_recent_topics() -> None:
    cfg = ScriptConfig(brief="  Never name a real brand.  ", avoid_recent=2)
    prompt = build_prompt(cfg, ["x", "y", "z"])
    assert "Channel brief:\nNever name a real brand." in prompt
    assert "do not repeat): y, z" in prompt


def test_prompt_word_budget_scales_with_length() -> None:
    assert "about 130 spoken words" in build_prompt(ScriptConfig(target_seconds=50), [])


def test_prompt_avoid_recent_zero_lists_nothing() -> None:
    assert "none yet" in build_prompt(ScriptConfig(avoid_recent=0), ["x"])


def test_system_prompt_lets_brief_override_tone() -> None:
    assert "channel brief" in SYSTEM_PROMPT.lower()
