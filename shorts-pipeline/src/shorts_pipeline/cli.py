"""Command line: `shorts run | resume | status | doctor | serve`."""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from . import __version__
from .config import Config, MissingSecretError, Secrets
from .job import Job
from .pipeline import Pipeline, PipelineError
from .render import ffmpeg
from .scheduler import is_due, last_publish_time, next_due, unfinished_jobs
from .server import serve

log = logging.getLogger("shorts")


def _load(args: argparse.Namespace) -> tuple[Config, Secrets]:
    if args.mock:
        return Config.mock(Path(args.data_dir or "data")), Secrets()
    config = Config.load(Path(args.config))
    if args.data_dir:
        config.data_dir = Path(args.data_dir)
    return config, Secrets()


def cmd_run(args: argparse.Namespace) -> int:
    config, secrets = _load(args)
    pipeline = Pipeline(config, secrets)
    try:
        job = pipeline.run_new(args.job_id)
    except (PipelineError, MissingSecretError) as exc:
        log.error("%s", exc)
        return 1
    print(job.manifest.final_video)
    for r in job.manifest.publish_results:
        print(f"{r.platform}: {'ok' if r.ok else 'FAILED'} {r.url or r.remote_id or r.error}")
    return 0


def cmd_resume(args: argparse.Namespace) -> int:
    config, secrets = _load(args)
    pipeline = Pipeline(config, secrets)
    job = Job.load(pipeline.jobs_root / args.job_id)
    try:
        pipeline.resume(job)
    except (PipelineError, MissingSecretError) as exc:
        log.error("%s", exc)
        return 1
    print(job.manifest.final_video)
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    config, _ = _load(args)
    jobs_root = config.data_dir / "jobs"
    now = datetime.now(UTC)
    last = last_publish_time(jobs_root)
    print(f"jobs: {len(Job.list_all(jobs_root))}")
    print(f"last publish: {last.isoformat() if last else 'never'}")
    print(f"next due: {next_due(last, config.schedule, now).isoformat()}")
    for job in Job.list_all(jobs_root)[-10:]:
        m = job.manifest
        state = m.error or (f"next: {m.next_stage()}" if m.next_stage() else "published")
        print(f"  {m.job_id}  {state}")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    """Check binaries, config and the keys every configured provider needs."""
    config, secrets = _load(args)
    ok = True
    try:
        ffmpeg.ensure_available()
        print("ffmpeg: ok")
    except ffmpeg.FfmpegError as exc:
        print(f"ffmpeg: {exc}")
        ok = False
    needs: dict[str, list[str]] = {
        "script.claude": ["anthropic_api_key"],
        "voice.elevenlabs": ["elevenlabs_api_key"],
        "visuals.fal": ["fal_key"],
        "visuals.pexels": ["pexels_api_key"],
        "publish.youtube": ["youtube_client_id", "youtube_client_secret", "youtube_refresh_token"],
        "publish.instagram": [
            "instagram_user_id",
            "instagram_access_token",
            "shorts_public_base_url",
        ],
        "publish.tiktok": ["tiktok_access_token"],
    }
    active = {
        f"script.{config.script.provider}",
        f"voice.{config.voice.provider}",
        f"visuals.{config.visuals.provider}",
        *(f"publish.{p}" for p in config.publish.providers),
    }
    for provider, keys in needs.items():
        if provider not in active:
            continue
        missing = [k.upper() for k in keys if not getattr(secrets, k)]
        print(f"{provider}: {'ok' if not missing else 'missing ' + ', '.join(missing)}")
        ok = ok and not missing
    print(
        f"cadence: every {config.schedule.every_days} days at {config.schedule.hour_utc:02d}:00 UTC"
    )
    return 0 if ok else 1


def cmd_serve(args: argparse.Namespace) -> int:
    """Health/media server plus the scheduler loop. This is the deployed entry point."""
    config, secrets = _load(args)
    pipeline = Pipeline(config, secrets)
    port = int(os.environ.get("PORT", args.port))
    httpd = serve(config, "0.0.0.0", port)  # noqa: S104 - container service must bind all interfaces
    log.info(
        "serving on :%d, checking cadence every %ds", port, config.schedule.check_interval_seconds
    )
    try:
        while True:
            try:
                pending = unfinished_jobs(pipeline.jobs_root)
                if pending:
                    log.info("resuming unfinished job %s", pending[0].manifest.job_id)
                    pipeline.resume(pending[0])
                elif is_due(pipeline.jobs_root, config.schedule):
                    log.info("video due; starting a new job")
                    pipeline.run_new()
            except (PipelineError, MissingSecretError) as exc:
                log.error("run failed: %s", exc)
            if args.once:
                return 0
            time.sleep(config.schedule.check_interval_seconds)
    except KeyboardInterrupt:
        return 0
    finally:
        httpd.shutdown()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="shorts", description="Automated short-form video pipeline"
    )
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--config", default="config.yaml", help="YAML config path")
    parser.add_argument("--data-dir", default=None, help="Where jobs are stored (default: data/)")
    parser.add_argument("--mock", action="store_true", help="All providers offline; still renders")
    parser.add_argument("-v", "--verbose", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Produce and publish one video now")
    run.add_argument("--job-id", default=None)
    run.set_defaults(func=cmd_run)

    resume = sub.add_parser("resume", help="Continue a job from its last completed stage")
    resume.add_argument("job_id")
    resume.set_defaults(func=cmd_resume)

    sub.add_parser("status", help="Show jobs and the next due time").set_defaults(func=cmd_status)
    sub.add_parser("doctor", help="Check binaries and required keys").set_defaults(func=cmd_doctor)

    srv = sub.add_parser("serve", help="Run the health server and the every-N-days scheduler")
    srv.add_argument("--port", type=int, default=8080)
    srv.add_argument("--once", action="store_true", help="One scheduler tick, then exit")
    srv.set_defaults(func=cmd_serve)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )
    result: int = args.func(args)
    return result


if __name__ == "__main__":
    sys.exit(main())
