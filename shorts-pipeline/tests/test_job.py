from pathlib import Path

import pytest

from shorts_pipeline.job import Job, slugify
from shorts_pipeline.models import STAGE_ORDER, Stage


def test_slugify() -> None:
    assert slugify("Hello, World! 2024") == "hello-world-2024"
    assert slugify("") == "untitled"
    assert len(slugify("a" * 100)) == 40


def test_create_and_load_roundtrip(tmp_path: Path) -> None:
    job = Job.create(tmp_path, "j1")
    job.mark_done(Stage.SCRIPT)
    loaded = Job.load(tmp_path / "j1")
    assert loaded.manifest.completed == [Stage.SCRIPT]
    assert loaded.manifest.next_stage() is Stage.VOICE
    assert not (tmp_path / "j1" / "manifest.json.tmp").exists()


def test_create_refuses_duplicate(tmp_path: Path) -> None:
    Job.create(tmp_path, "j1")
    with pytest.raises(FileExistsError):
        Job.create(tmp_path, "j1")


def test_load_missing_manifest(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        Job.load(tmp_path / "nope")


def test_next_stage_none_when_all_done(tmp_path: Path) -> None:
    job = Job.create(tmp_path, "j1")
    for stage in STAGE_ORDER:
        job.mark_done(stage)
    assert job.manifest.next_stage() is None
    assert not job.manifest.is_published  # no successful result recorded


def test_fail_records_error_and_mark_done_clears_it(tmp_path: Path) -> None:
    job = Job.create(tmp_path, "j1")
    job.fail("boom")
    assert Job.load(job.dir).manifest.error == "boom"
    job.mark_done(Stage.SCRIPT)
    assert Job.load(job.dir).manifest.error is None


def test_list_all_skips_dirs_without_manifest(tmp_path: Path) -> None:
    assert Job.list_all(tmp_path / "missing") == []
    (tmp_path / "junk").mkdir()
    Job.create(tmp_path, "b")
    Job.create(tmp_path, "a")
    assert [j.manifest.job_id for j in Job.list_all(tmp_path)] == ["a", "b"]
