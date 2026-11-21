"""Data contracts shared by every stage.

Every provider speaks these types and nothing else, so swapping a tool
(ElevenLabs for another voice, fal.ai for Pexels) never touches the pipeline.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

WIDTH = 1080
HEIGHT = 1920


class Scene(BaseModel):
    """One beat of the video: a few seconds of narration with one visual."""

    narration: str = Field(min_length=1, description="Spoken text for this scene")
    visual_prompt: str = Field(min_length=1, description="What the viewer sees; image/video prompt")
    caption_hint: str | None = Field(default=None, description="Optional on-screen keyword")


class Script(BaseModel):
    """Output of the script stage: everything the later stages need to know."""

    topic: str
    hook: str = Field(description="First line, must stop the scroll in under 2 seconds")
    scenes: list[Scene] = Field(min_length=2, max_length=12)
    title: str = Field(max_length=100)
    description: str = Field(max_length=2000)
    hashtags: list[str] = Field(default_factory=list, max_length=15)
    music_mood: str = Field(default="calm", description="Keyword for background music choice")

    @field_validator("hashtags")
    @classmethod
    def _normalise_hashtags(cls, tags: list[str]) -> list[str]:
        out: list[str] = []
        for tag in tags:
            clean = tag.strip().lstrip("#").replace(" ", "")
            if clean:
                out.append("#" + clean)
        return out

    @property
    def full_narration(self) -> str:
        return " ".join([self.hook, *(s.narration for s in self.scenes)])


class WordTiming(BaseModel):
    """A spoken word and when it is heard, in seconds from the start of the voice track."""

    word: str
    start: float = Field(ge=0)
    end: float = Field(ge=0)

    @field_validator("end")
    @classmethod
    def _end_after_start(cls, end: float, info: object) -> float:
        # pydantic passes ValidationInfo; keep typing loose to stay strict-mypy clean
        data = getattr(info, "data", {})
        start = data.get("start", 0.0)
        if end < start:
            raise ValueError(f"word ends ({end}) before it starts ({start})")
        return end


class VoiceTrack(BaseModel):
    audio_path: Path
    duration: float = Field(gt=0)
    words: list[WordTiming]


class VisualAsset(BaseModel):
    """One rendered visual per scene. Either a still image or a video clip."""

    scene_index: int = Field(ge=0)
    path: Path
    kind: str = Field(pattern="^(image|video)$")


class Platform(StrEnum):
    YOUTUBE = "youtube"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"


class PublishResult(BaseModel):
    platform: Platform
    ok: bool
    remote_id: str | None = None
    url: str | None = None
    error: str | None = None
    published_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Stage(StrEnum):
    SCRIPT = "script"
    VOICE = "voice"
    VISUALS = "visuals"
    RENDER = "render"
    PUBLISH = "publish"


STAGE_ORDER: tuple[Stage, ...] = (
    Stage.SCRIPT,
    Stage.VOICE,
    Stage.VISUALS,
    Stage.RENDER,
    Stage.PUBLISH,
)
