"""Provider adapters. `build_*` functions are the only place a config name meets a class."""

from __future__ import annotations

from ..config import Config, Secrets
from .base import Publisher, ScriptWriter, VisualGenerator, Voice


def build_script_writer(config: Config, secrets: Secrets) -> ScriptWriter:
    if config.script.provider == "mock":
        from .script_mock import MockScriptWriter

        return MockScriptWriter(config.script)
    from .script_claude import ClaudeScriptWriter

    return ClaudeScriptWriter(config.script, secrets.require("anthropic_api_key"))


def build_voice(config: Config, secrets: Secrets) -> Voice:
    if config.voice.provider == "mock":
        from .voice_mock import MockVoice

        return MockVoice()
    from .voice_elevenlabs import ElevenLabsVoice

    return ElevenLabsVoice(config.voice, secrets.require("elevenlabs_api_key"))


def build_visuals(config: Config, secrets: Secrets) -> VisualGenerator:
    if config.visuals.provider == "mock":
        from .visuals_mock import MockVisuals

        return MockVisuals()
    if config.visuals.provider == "pexels":
        from .visuals_pexels import PexelsVisuals

        return PexelsVisuals(config.visuals, secrets.require("pexels_api_key"))
    from .visuals_fal import FalVisuals

    return FalVisuals(config.visuals, secrets.require("fal_key"))


def build_publishers(config: Config, secrets: Secrets) -> list[Publisher]:
    publishers: list[Publisher] = []
    for name in config.publish.providers:
        if name == "mock":
            from .publish_mock import MockPublisher

            publishers.append(MockPublisher())
        elif name == "youtube":
            from .publish_youtube import YouTubePublisher

            publishers.append(
                YouTubePublisher(
                    client_id=secrets.require("youtube_client_id"),
                    client_secret=secrets.require("youtube_client_secret"),
                    refresh_token=secrets.require("youtube_refresh_token"),
                    privacy=config.publish.youtube_privacy,
                )
            )
        elif name == "instagram":
            from .publish_instagram import InstagramPublisher

            publishers.append(
                InstagramPublisher(
                    user_id=secrets.require("instagram_user_id"),
                    access_token=secrets.require("instagram_access_token"),
                    public_base_url=secrets.require("shorts_public_base_url"),
                )
            )
        elif name == "tiktok":
            from .publish_tiktok import TikTokPublisher

            publishers.append(
                TikTokPublisher(
                    access_token=secrets.require("tiktok_access_token"),
                    privacy=config.publish.tiktok_privacy,
                )
            )
    return publishers
