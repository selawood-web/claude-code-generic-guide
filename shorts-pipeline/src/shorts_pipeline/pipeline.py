"""Runs a job stage by stage, persisting after each one so a crash resumes, not restarts."""

from __future__ import annotations

import logging
from pathlib import Path

from .config import Config, Secrets
from .job import Job
from .models import Stage
from .providers import build_publishers, build_script_writer, build_visuals, build_voice
from .providers.base import ProviderError
from .render.compose import compose

log = logging.getLogger(__name__)


class PipelineError(RuntimeError):
    pass


def recent_topics(jobs_root: Path, limit: int) -> list[str]:
    topics = [j.manifest.script.topic for j in Job.list_all(jobs_root) if j.manifest.script]
    return topics[-limit:] if limit else []


class Pipeline:
    def __init__(self, config: Config, secrets: Secrets) -> None:
        self.config = config
        self.secrets = secrets
        self.jobs_root = config.data_dir / "jobs"
        self.jobs_root.mkdir(parents=True, exist_ok=True)

    def run_new(self, job_id: str | None = None) -> Job:
        job = Job.create(self.jobs_root, job_id)
        return self.resume(job)

    def resume(self, job: Job) -> Job:
        """Execute every remaining stage. Stops at the first failure, leaving the manifest
        pointing at the stage to retry."""
        while (stage := job.manifest.next_stage()) is not None:
            log.info("job %s: stage %s", job.manifest.job_id, stage)
            try:
                self._run_stage(job, stage)
            except (ProviderError, PipelineError, OSError, ValueError) as exc:
                job.fail(f"{stage}: {exc}")
                raise PipelineError(f"job {job.manifest.job_id} failed at {stage}: {exc}") from exc
            job.mark_done(stage)
        return job

    def _run_stage(self, job: Job, stage: Stage) -> None:
        m = job.manifest
        if stage is Stage.SCRIPT:
            writer = build_script_writer(self.config, self.secrets)
            m.script = writer.write(
                recent_topics=recent_topics(self.jobs_root, self.config.script.avoid_recent)
            )
            job.write_json("script.json", m.script.model_dump())
        elif stage is Stage.VOICE:
            if m.script is None:
                raise PipelineError("voice stage needs a script")
            m.voice = build_voice(self.config, self.secrets).synthesize(
                m.script.full_narration, job.dir
            )
        elif stage is Stage.VISUALS:
            if m.script is None:
                raise PipelineError("visuals stage needs a script")
            visuals_dir = job.path("visuals")
            visuals_dir.mkdir(exist_ok=True)
            m.visuals = build_visuals(self.config, self.secrets).generate(m.script, visuals_dir)
        elif stage is Stage.RENDER:
            if m.script is None or m.voice is None or not m.visuals:
                raise PipelineError("render stage needs script, voice and visuals")
            m.final_video, m.thumbnail = compose(
                m.script, m.voice, m.visuals, self.config.render, job.dir
            )
        elif stage is Stage.PUBLISH:
            if m.script is None or m.final_video is None:
                raise PipelineError("publish stage needs a rendered video")
            results = [
                p.publish(m.final_video, m.thumbnail, m.script, m.job_id)
                for p in build_publishers(self.config, self.secrets)
            ]
            m.publish_results = results
            for r in results:
                log.log(
                    logging.INFO if r.ok else logging.ERROR,
                    "publish %s: %s",
                    r.platform,
                    r.url or r.remote_id or r.error,
                )
            failed = [r for r in results if not r.ok]
            if (
                not results
                or (failed and self.config.publish.require_all)
                or len(failed) == len(results)
            ):
                raise PipelineError(
                    "; ".join(r.error or str(r.platform) for r in failed) or "no publishers"
                )
