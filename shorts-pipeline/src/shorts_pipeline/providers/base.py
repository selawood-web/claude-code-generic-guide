"""The four seams of the pipeline. Implement one Protocol to plug in a new tool."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from ..models import PublishResult, Script, VisualAsset, VoiceTrack


class ScriptWriter(Protocol):
    def write(self, *, recent_topics: list[str]) -> Script: ...


class Voice(Protocol):
    def synthesize(self, text: str, out_dir: Path) -> VoiceTrack: ...


class VisualGenerator(Protocol):
    def generate(self, script: Script, out_dir: Path) -> list[VisualAsset]: ...


class Publisher(Protocol):
    name: str

    def publish(
        self, video: Path, thumbnail: Path | None, script: Script, job_id: str
    ) -> PublishResult: ...


class ProviderError(RuntimeError):
    """A provider failed in a way retrying will not fix without a human (bad key, quota, policy)."""
