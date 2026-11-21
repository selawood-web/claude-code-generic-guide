from datetime import UTC, datetime, timedelta
from pathlib import Path

from shorts_pipeline.config import ScheduleConfig
from shorts_pipeline.job import Job
from shorts_pipeline.models import STAGE_ORDER, Platform, PublishResult
from shorts_pipeline.scheduler import is_due, last_publish_time, next_due, unfinished_jobs

CFG = ScheduleConfig(every_days=3, hour_utc=14)
NOW = datetime(2026, 1, 10, 9, 0, tzinfo=UTC)


def test_next_due_with_no_history_is_now() -> None:
    assert next_due(None, CFG, NOW) == NOW


def test_next_due_is_n_days_later_at_preferred_hour() -> None:
    last = datetime(2026, 1, 1, 14, 5, tzinfo=UTC)
    assert next_due(last, CFG, NOW) == datetime(2026, 1, 4, 14, 0, tzinfo=UTC)


def test_next_due_snaps_back_within_twelve_hours() -> None:
    last = datetime(2026, 1, 1, 23, 50, tzinfo=UTC)
    # raw mark is Jan 4 23:50; 14:00 the same day is under 12h earlier, so keep that day
    assert next_due(last, CFG, NOW) == datetime(2026, 1, 4, 14, 0, tzinfo=UTC)


def test_next_due_rolls_forward_when_preferred_hour_is_far_behind() -> None:
    last = datetime(2026, 1, 1, 23, 50, tzinfo=UTC)
    cfg = ScheduleConfig(every_days=3, hour_utc=2)
    # raw mark is Jan 4 23:50; 02:00 that day is ~22h earlier, so publish Jan 5 02:00
    assert next_due(last, cfg, NOW) == datetime(2026, 1, 5, 2, 0, tzinfo=UTC)


def test_next_due_every_one_day() -> None:
    last = datetime(2026, 1, 1, 14, 0, tzinfo=UTC)
    assert next_due(last, ScheduleConfig(every_days=1, hour_utc=14), NOW) == last + timedelta(
        days=1
    )


def _published_job(root: Path, job_id: str, when: datetime, ok: bool = True) -> Job:
    job = Job.create(root, job_id)
    for stage in STAGE_ORDER:
        job.mark_done(stage)
    job.manifest.publish_results.append(
        PublishResult(platform=Platform.YOUTUBE, ok=ok, published_at=when)
    )
    job.save()
    return job


def test_last_publish_time_ignores_failures(tmp_path: Path) -> None:
    assert last_publish_time(tmp_path) is None
    _published_job(tmp_path, "a", NOW - timedelta(days=5))
    _published_job(tmp_path, "b", NOW - timedelta(days=1), ok=False)
    assert last_publish_time(tmp_path) == NOW - timedelta(days=5)


def test_is_due(tmp_path: Path) -> None:
    assert is_due(tmp_path, CFG, NOW)
    _published_job(tmp_path, "a", NOW - timedelta(days=1))
    assert not is_due(tmp_path, CFG, NOW)
    assert is_due(tmp_path, CFG, NOW + timedelta(days=3))


def test_unfinished_jobs(tmp_path: Path) -> None:
    _published_job(tmp_path, "done", NOW)
    Job.create(tmp_path, "half").mark_done(STAGE_ORDER[0])
    assert [j.manifest.job_id for j in unfinished_jobs(tmp_path)] == ["half"]
