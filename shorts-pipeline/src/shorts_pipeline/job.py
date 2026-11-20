"""A job is one video. It lives in its own directory and records every stage.

The manifest makes a job resumable: a crash during rendering restarts at
rendering, not at script writing (which costs money and changes the output).
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, Field

from .models import STAGE_ORDER, PublishResult, Script, Stage, VisualAsset, VoiceTrack

_SLUG = re.compile(r"[^a-z0-9]+")


def slugify(text: str, limit: int = 40) -> str:
    slug = _SLUG.sub("-", text.lower()).strip("-")
    return slug[:limit].rstrip("-") or "untitled"


class Manifest(BaseModel):
    job_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed: list[Stage] = Field(default_factory=list)
    script: Script | None = None
    voice: VoiceTrack | None = None
    visuals: list[VisualAsset] = Field(default_factory=list)
    final_video: Path | None = None
    thumbnail: Path | None = None
    publish_results: list[PublishResult] = Field(default_factory=list)
    error: str | None = None

    def next_stage(self) -> Stage | None:
        for stage in STAGE_ORDER:
            if stage not in self.completed:
                return stage
        return None

    @property
    def is_published(self) -> bool:
        return Stage.PUBLISH in self.completed and any(r.ok for r in self.publish_results)


class Job:
    MANIFEST = "manifest.json"

    def __init__(self, directory: Path, manifest: Manifest) -> None:
        self.dir = directory
        self.manifest = manifest

    @classmethod
    def create(cls, jobs_root: Path, job_id: str | None = None) -> Job:
        job_id = job_id or datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        directory = jobs_root / job_id
        if directory.exists():
            raise FileExistsError(f"job {job_id} already exists at {directory}")
        directory.mkdir(parents=True)
        job = cls(directory, Manifest(job_id=job_id))
        job.save()
        return job

    @classmethod
    def load(cls, directory: Path) -> Job:
        path = directory / cls.MANIFEST
        if not path.exists():
            raise FileNotFoundError(f"no manifest at {path}")
        manifest = Manifest.model_validate_json(path.read_text(encoding="utf-8"))
        return cls(directory, manifest)

    @classmethod
    def list_all(cls, jobs_root: Path) -> list[Job]:
        if not jobs_root.exists():
            return []
        jobs: list[Job] = []
        for child in sorted(jobs_root.iterdir()):
            if (child / cls.MANIFEST).exists():
                jobs.append(cls.load(child))
        return jobs

    def save(self) -> None:
        tmp = self.dir / (self.MANIFEST + ".tmp")
        tmp.write_text(self.manifest.model_dump_json(indent=2), encoding="utf-8")
        tmp.replace(self.dir / self.MANIFEST)  # atomic on POSIX

    def mark_done(self, stage: Stage) -> None:
        if stage not in self.manifest.completed:
            self.manifest.completed.append(stage)
        self.manifest.error = None
        self.save()

    def fail(self, message: str) -> None:
        self.manifest.error = message
        self.save()

    def path(self, name: str) -> Path:
        return self.dir / name

    def write_json(self, name: str, payload: object) -> Path:
        target = self.path(name)
        target.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        return target
