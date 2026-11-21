"""Full offline run: real ffmpeg, mock providers. Proves the stages fit together."""

from pathlib import Path

import pytest

from shorts_pipeline import pipeline as pipeline_module
from shorts_pipeline.config import Config, Secrets
from shorts_pipeline.job import Job
from shorts_pipeline.models import Platform, PublishResult, Stage
from shorts_pipeline.pipeline import Pipeline, PipelineError
from shorts_pipeline.render import ffmpeg


@pytest.fixture
def pipe(tmp_path: Path) -> Pipeline:
    return Pipeline(Config.mock(tmp_path / "data"), Secrets())


def test_mock_run_renders_a_vertical_video(pipe: Pipeline) -> None:
    job = pipe.run_new("e2e")
    final = job.manifest.final_video
    assert final is not None and final.exists()
    assert ffmpeg.video_size(final) == (1080, 1920)
    assert ffmpeg.has_audio(final)
    assert abs(ffmpeg.duration(final) - job.manifest.voice.duration) < 1.0  # type: ignore[union-attr]
    assert job.manifest.thumbnail is not None and job.manifest.thumbnail.stat().st_size > 0
    assert job.manifest.next_stage() is None and job.manifest.is_published
    assert (job.dir / "captions.ass").read_text().count("Dialogue:") == len(
        job.manifest.voice.words
    )  # type: ignore[union-attr]


class _FailOnce:
    name = "flaky"

    def __init__(self) -> None:
        self.calls = 0

    def publish(
        self, video: Path, thumbnail: Path | None, script: object, job_id: str
    ) -> PublishResult:
        self.calls += 1
        if self.calls == 1:
            return PublishResult(platform=Platform.YOUTUBE, ok=False, error="first try fails")
        return PublishResult(platform=Platform.YOUTUBE, ok=True, remote_id="ok")


def test_failed_publish_is_resumable_without_rerendering(
    pipe: Pipeline, monkeypatch: pytest.MonkeyPatch
) -> None:
    flaky = _FailOnce()
    monkeypatch.setattr(pipeline_module, "build_publishers", lambda c, s: [flaky])
    with pytest.raises(PipelineError, match="first try fails"):
        pipe.run_new("resume")
    job = Job.load(pipe.jobs_root / "resume")
    assert job.manifest.next_stage() is Stage.PUBLISH
    assert job.manifest.error is not None and job.manifest.error.startswith("publish:")
    rendered_at = job.manifest.final_video.stat().st_mtime  # type: ignore[union-attr]

    pipe.resume(job)
    assert job.manifest.is_published
    assert job.manifest.final_video.stat().st_mtime == rendered_at  # type: ignore[union-attr]
    assert flaky.calls == 2


def test_require_all_fails_on_partial_publish(
    pipe: Pipeline, monkeypatch: pytest.MonkeyPatch
) -> None:
    pipe.config.publish.require_all = True
    ok = _FailOnce()
    ok.calls = 1  # will succeed
    monkeypatch.setattr(pipeline_module, "build_publishers", lambda c, s: [_FailOnce(), ok])
    with pytest.raises(PipelineError):
        pipe.run_new("partial")


def test_recent_topics_feed_the_writer(pipe: Pipeline) -> None:
    pipe.run_new("a")
    second = pipe.run_new("b")
    assert second.manifest.script is not None
    assert "take 2" in second.manifest.script.topic


def test_missing_secret_is_named(tmp_path: Path) -> None:
    config = Config.mock(tmp_path / "data")
    config.script.provider = "claude"
    with pytest.raises(Exception, match="ANTHROPIC_API_KEY"):
        Pipeline(config, Secrets(_env_file=None)).run_new("nokey")  # type: ignore[call-arg]
