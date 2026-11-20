import json
import urllib.request
from pathlib import Path

import pytest

from shorts_pipeline.cli import main
from shorts_pipeline.config import Config
from shorts_pipeline.job import Job
from shorts_pipeline.models import STAGE_ORDER
from shorts_pipeline.server import serve


@pytest.fixture
def base_url(tmp_path: Path):  # type: ignore[no-untyped-def]
    config = Config.mock(tmp_path / "data")
    jobs = config.data_dir / "jobs"
    job = Job.create(jobs, "j1")
    for stage in STAGE_ORDER:
        job.mark_done(stage)
    (job.dir / "final.mp4").write_bytes(b"MP4DATA")
    httpd = serve(config, "127.0.0.1", 0)
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()


def _get(url: str) -> tuple[int, bytes]:
    try:
        with urllib.request.urlopen(url) as resp:  # noqa: S310 - local test server
            return resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def test_health_and_runs(base_url: str) -> None:
    status, body = _get(f"{base_url}/health")
    payload = json.loads(body)
    assert status == 200 and payload["ok"] and payload["jobs"] == 1 and payload["next_due"]
    status, body = _get(f"{base_url}/runs")
    assert status == 200 and json.loads(body)[0]["job_id"] == "j1"


def test_media_served_and_guarded(base_url: str) -> None:
    assert _get(f"{base_url}/media/j1/final.mp4") == (200, b"MP4DATA")
    assert _get(f"{base_url}/media/j1/thumbnail.jpg")[0] == 404
    assert _get(f"{base_url}/media/../manifest.json")[0] == 404
    assert _get(f"{base_url}/media/j1/manifest.json")[0] == 404
    assert _get(f"{base_url}/nope")[0] == 404


def test_cli_doctor_and_status_in_mock_mode(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    data = str(tmp_path / "data")
    assert main(["--mock", "--data-dir", data, "doctor"]) == 0
    assert "ffmpeg: ok" in capsys.readouterr().out
    assert main(["--mock", "--data-dir", data, "status"]) == 0
    assert "last publish: never" in capsys.readouterr().out


def test_cli_doctor_reports_missing_keys(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    for var in ("ANTHROPIC_API_KEY", "ELEVENLABS_API_KEY", "FAL_KEY"):
        monkeypatch.delenv(var, raising=False)
    cfg = tmp_path / "config.yaml"
    cfg.write_text("publish:\n  providers: [youtube]\n")
    monkeypatch.chdir(tmp_path)  # no .env here
    assert main(["--config", str(cfg), "--data-dir", str(tmp_path / "d"), "doctor"]) == 1
    out = capsys.readouterr().out
    assert "ANTHROPIC_API_KEY" in out and "YOUTUBE_CLIENT_ID" in out


def test_cli_resume_unknown_job(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        main(["--mock", "--data-dir", str(tmp_path / "d"), "resume", "ghost"])


def test_config_load_rejects_non_mapping(tmp_path: Path) -> None:
    bad = tmp_path / "c.yaml"
    bad.write_text("- just\n- a list\n")
    with pytest.raises(ValueError):
        Config.load(bad)
    assert Config.load(tmp_path / "missing.yaml").schedule.every_days == 3
