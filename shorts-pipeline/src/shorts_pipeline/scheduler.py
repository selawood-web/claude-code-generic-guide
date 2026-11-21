"""Cadence: one published video every N days, measured from the last successful publish."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from .config import ScheduleConfig
from .job import Job


def last_publish_time(jobs_root: Path) -> datetime | None:
    latest: datetime | None = None
    for job in Job.list_all(jobs_root):
        for result in job.manifest.publish_results:
            if result.ok and (latest is None or result.published_at > latest):
                latest = result.published_at
    return latest


def next_due(last: datetime | None, cfg: ScheduleConfig, now: datetime) -> datetime:
    """When the next video is due. Pure, unit-tested.

    No history: due now. Otherwise N days after the last publish, snapped to the
    preferred hour of that day (never earlier than the raw N-day mark's date).
    """
    if last is None:
        return now
    raw = last + timedelta(days=cfg.every_days)
    due = raw.replace(hour=cfg.hour_utc, minute=0, second=0, microsecond=0)
    if due < raw - timedelta(hours=12):
        due += timedelta(days=1)
    return due


def is_due(jobs_root: Path, cfg: ScheduleConfig, now: datetime | None = None) -> bool:
    now = now or datetime.now(UTC)
    return next_due(last_publish_time(jobs_root), cfg, now) <= now


def unfinished_jobs(jobs_root: Path) -> list[Job]:
    """Jobs that stopped before publishing: resume these before starting a new one."""
    return [j for j in Job.list_all(jobs_root) if j.manifest.next_stage() is not None]
