"""Configuration: a YAML file for choices, environment variables for secrets.

The YAML names *which* tool runs each stage; the keys that tool needs come from
the environment (or a `.env` file). A missing key fails at startup with the
variable name, never halfway through a render.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .models import Platform


class Secrets(BaseSettings):
    """Every secret the pipeline may need. All optional; providers check their own."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    anthropic_api_key: str | None = None
    elevenlabs_api_key: str | None = None
    fal_key: str | None = None
    pexels_api_key: str | None = None

    youtube_client_id: str | None = None
    youtube_client_secret: str | None = None
    youtube_refresh_token: str | None = None

    instagram_user_id: str | None = None
    instagram_access_token: str | None = None

    tiktok_access_token: str | None = None

    shorts_public_base_url: str | None = None

    def require(self, name: str) -> str:
        value = getattr(self, name)
        if not value:
            raise MissingSecretError(name.upper())
        return str(value)


class MissingSecretError(RuntimeError):
    def __init__(self, env_name: str) -> None:
        super().__init__(f"missing required environment variable {env_name}")
        self.env_name = env_name


class ScriptConfig(BaseModel):
    provider: Literal["claude", "mock"] = "claude"
    model: str = "claude-opus-5-5"
    niche: str = Field(default="surprising science facts", description="What the channel is about")
    brief: str = Field(
        default="",
        description="Channel rules in plain prose: format, tone, visual style, what to avoid. "
        "Goes into the prompt verbatim; empty means the generic educational default.",
    )
    audience: str = "curious adults scrolling on their phone"
    language: str = "English"
    target_seconds: int = Field(default=40, ge=15, le=90)
    topics: list[str] = Field(
        default_factory=list,
        description="Optional topic queue; when empty the model picks within the niche",
    )
    avoid_recent: int = Field(default=30, ge=0, description="Topics from the last N runs to avoid")


class VoiceConfig(BaseModel):
    provider: Literal["elevenlabs", "mock"] = "elevenlabs"
    voice_id: str = "21m00Tcm4TlvDq8ikWAM"
    model_id: str = "eleven_multilingual_v2"
    speed: float = Field(default=1.0, ge=0.7, le=1.2)


class VisualsConfig(BaseModel):
    provider: Literal["fal", "pexels", "mock"] = "fal"
    fal_model: str = "fal-ai/flux/schnell"
    style_suffix: str = (
        "cinematic, vertical 9:16 composition, dramatic lighting, high detail, no text"
    )
    motion: Literal["kenburns", "static"] = "kenburns"


class RenderConfig(BaseModel):
    fps: int = Field(default=30, ge=24, le=60)
    font: str = "DejaVu Sans"
    font_size: int = Field(default=72, ge=36, le=140)
    highlight_color: str = Field(
        default="&H0000D7FF", description="ASS colour as &HAABBGGRR; default is warm yellow"
    )
    music_path: Path | None = None
    music_gain_db: float = Field(default=-18.0, le=0)
    crf: int = Field(default=20, ge=14, le=30)


PublisherName = Literal["youtube", "instagram", "tiktok", "mock"]


def _default_publishers() -> list[PublisherName]:
    return ["mock"]


class PublishConfig(BaseModel):
    providers: list[PublisherName] = Field(default_factory=_default_publishers)
    youtube_privacy: Literal["public", "unlisted", "private"] = "public"
    tiktok_privacy: Literal[
        "PUBLIC_TO_EVERYONE", "MUTUAL_FOLLOW_FRIENDS", "FOLLOWER_OF_CREATOR", "SELF_ONLY"
    ] = "SELF_ONLY"
    require_all: bool = Field(
        default=False, description="If true, one failed platform fails the job"
    )


class ScheduleConfig(BaseModel):
    every_days: int = Field(default=3, ge=1)
    hour_utc: int = Field(default=14, ge=0, le=23, description="Preferred publish hour")
    check_interval_seconds: int = Field(default=900, ge=60)


class Config(BaseModel):
    data_dir: Path = Path("data")
    script: ScriptConfig = Field(default_factory=ScriptConfig)
    voice: VoiceConfig = Field(default_factory=VoiceConfig)
    visuals: VisualsConfig = Field(default_factory=VisualsConfig)
    render: RenderConfig = Field(default_factory=RenderConfig)
    publish: PublishConfig = Field(default_factory=PublishConfig)
    schedule: ScheduleConfig = Field(default_factory=ScheduleConfig)

    @classmethod
    def load(cls, path: Path | None) -> Config:
        if path is None or not path.exists():
            return cls()
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if not isinstance(raw, dict):
            raise ValueError(f"{path}: top level must be a mapping")
        return cls.model_validate(raw)

    @classmethod
    def mock(cls, data_dir: Path) -> Config:
        """Fully offline configuration: no network, no keys, still renders a real MP4."""
        return cls(
            data_dir=data_dir,
            script=ScriptConfig(provider="mock"),
            voice=VoiceConfig(provider="mock"),
            visuals=VisualsConfig(provider="mock"),
            publish=PublishConfig(providers=["mock"]),
        )

    def platforms(self) -> list[Platform]:
        return [Platform(p) for p in self.publish.providers if p != "mock"]
