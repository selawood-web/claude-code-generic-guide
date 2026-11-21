"""Tiny HTTP server: health check, run listing, and public media for Instagram.

Standard library only. Runs alongside the scheduler loop in `shorts serve`.
GET /health            -> {"ok": true, "jobs": n, "last_publish": iso, "next_due": iso}
GET /runs              -> manifests summary
GET /media/<job>/final.mp4 or thumbnail.jpg -> the rendered file (read-only, no listing)
"""

from __future__ import annotations

import json
import re
import threading
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .config import Config
from .job import Job
from .scheduler import last_publish_time, next_due

_MEDIA = re.compile(r"^/media/([A-Za-z0-9_-]+)/(final\.mp4|thumbnail\.jpg)$")


def make_handler(config: Config) -> type[BaseHTTPRequestHandler]:
    jobs_root = config.data_dir / "jobs"

    class Handler(BaseHTTPRequestHandler):
        server_version = "shorts-pipeline"

        def log_message(self, format: str, *args: object) -> None:  # noqa: A002
            return  # quiet; the pipeline logs what matters

        def _json(self, status: int, payload: object) -> None:
            body = json.dumps(payload, default=str).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802 - http.server API
            if self.path == "/health":
                now = datetime.now(UTC)
                last = last_publish_time(jobs_root)
                self._json(
                    200,
                    {
                        "ok": True,
                        "jobs": len(Job.list_all(jobs_root)),
                        "last_publish": last,
                        "next_due": next_due(last, config.schedule, now),
                        "now": now,
                    },
                )
                return
            if self.path == "/runs":
                self._json(
                    200,
                    [
                        {
                            "job_id": j.manifest.job_id,
                            "completed": list(j.manifest.completed),
                            "error": j.manifest.error,
                            "title": j.manifest.script.title if j.manifest.script else None,
                            "results": [r.model_dump() for r in j.manifest.publish_results],
                        }
                        for j in Job.list_all(jobs_root)
                    ],
                )
                return
            match = _MEDIA.match(self.path)
            if match:
                target = (jobs_root / match.group(1) / match.group(2)).resolve()
                if target.is_file() and jobs_root.resolve() in target.parents:
                    data = target.read_bytes()
                    self.send_response(200)
                    self.send_header(
                        "Content-Type", "video/mp4" if target.suffix == ".mp4" else "image/jpeg"
                    )
                    self.send_header("Content-Length", str(len(data)))
                    self.send_header("Accept-Ranges", "none")
                    self.end_headers()
                    self.wfile.write(data)
                    return
            self._json(404, {"error": "not found"})

    return Handler


def serve(config: Config, host: str, port: int) -> ThreadingHTTPServer:
    """Start the server in a daemon thread and return it (call .shutdown() to stop)."""
    httpd = ThreadingHTTPServer((host, port), make_handler(config))
    threading.Thread(target=httpd.serve_forever, daemon=True, name="http").start()
    return httpd


def media_root(config: Config) -> Path:
    return config.data_dir / "jobs"
