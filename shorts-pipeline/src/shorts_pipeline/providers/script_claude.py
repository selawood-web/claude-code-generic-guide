"""Script stage on Claude: one structured-output call returns a validated `Script`."""

from __future__ import annotations

import anthropic

from ..config import ScriptConfig
from ..models import Script
from .base import ProviderError

SYSTEM_PROMPT = """You write scripts for faceless vertical short videos (TikTok, YouTube Shorts,
Instagram Reels). You are precise about pacing: a viewer decides in two seconds.

Rules:
- The hook is one sentence that creates a curiosity gap or a bold claim. No greetings.
- Each scene is 1-2 spoken sentences (roughly 4-8 seconds aloud) and one concrete visual
  the viewer can see. Visual prompts describe a picture, never text or UI.
- Narration is spoken language: contractions, short sentences, no lists, no emojis.
- Total narration must fit the target duration at ~2.6 words per second.
- End with a payoff or a question that invites a comment, never "like and subscribe".
- Facts must be true and non-controversial. If unsure, choose a different topic.
- Title: under 60 characters, specific. Description: 1-3 sentences. Hashtags: 5-8, relevant."""


class ClaudeScriptWriter:
    def __init__(self, config: ScriptConfig, api_key: str) -> None:
        self._config = config
        self._client = anthropic.Anthropic(api_key=api_key)

    def write(self, *, recent_topics: list[str]) -> Script:
        cfg = self._config
        words = int(cfg.target_seconds * 2.6)
        queued = [t for t in cfg.topics if t not in recent_topics]
        topic_line = (
            f"Topic to cover: {queued[0]}"
            if queued
            else f"Pick one fresh topic within the niche: {cfg.niche}"
        )
        avoid = ", ".join(recent_topics[-cfg.avoid_recent :]) or "none yet"
        prompt = (
            f"{topic_line}\n"
            f"Audience: {cfg.audience}\nLanguage: {cfg.language}\n"
            f"Target length: {cfg.target_seconds} seconds, about {words} spoken words total.\n"
            f"Topics already covered (do not repeat): {avoid}\n"
            "Return the script."
        )
        try:
            response = self._client.beta.messages.parse(
                model=cfg.model,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
                output_format=Script,
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
            )
        except anthropic.AuthenticationError as exc:
            raise ProviderError("Anthropic rejected the API key") from exc
        except anthropic.RateLimitError as exc:
            raise ProviderError("Anthropic rate limit hit; try again later") from exc
        if response.stop_reason == "refusal":
            raise ProviderError("Claude declined to write this script (policy refusal)")
        script = response.parsed_output
        if script is None:
            raise ProviderError("Claude returned no parsable script")
        return script
