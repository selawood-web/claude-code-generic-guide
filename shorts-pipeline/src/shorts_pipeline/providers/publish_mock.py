"""Publisher that records what would have been posted. Used in dry runs and tests."""

from __future__ import annotations

from pathlib import Path

from ..models import Platform, PublishResult, Script


class MockPublisher:
    name = "mock"

    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def publish(
        self, video: Path, thumbnail: Path | None, script: Script, job_id: str
    ) -> PublishResult:
        if not video.exists() or video.stat().st_size == 0:
            return PublishResult(
                platform=Platform.YOUTUBE, ok=False, error="video missing or empty"
            )
        self.calls.append({"video": video, "title": script.title, "job_id": job_id})
        return PublishResult(
            platform=Platform.YOUTUBE, ok=True, remote_id=f"mock-{job_id}", url=f"mock://{job_id}"
        )
