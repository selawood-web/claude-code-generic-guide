"""TikTok Direct Post via the Content Posting API (FILE_UPLOAD source).

1. POST /v2/post/publish/video/init/  -> publish_id + upload_url
2. PUT the bytes to upload_url in chunks with Content-Range
3. poll POST /v2/post/publish/status/fetch/ until PUBLISH_COMPLETE

Requirements that are not code: the app needs the `video.publish` scope, and until
TikTok audits the app every post is forced to private (SELF_ONLY). Keep
`publish.tiktok_privacy: SELF_ONLY` until the audit passes. About 15 posts/day/creator.
"""

from __future__ import annotations

import time
from pathlib import Path

import httpx

from ..models import Platform, PublishResult, Script
from ._http import client

API = "https://open.tiktokapis.com/v2/post/publish"
MIN_CHUNK = 5 * 1024 * 1024
SINGLE_CHUNK_MAX = 64 * 1024 * 1024
CHUNK = 10 * 1024 * 1024


def chunk_plan(size: int) -> list[tuple[int, int]]:
    """Byte ranges (start, end inclusive) that satisfy TikTok's chunk rules. Pure, unit-tested.

    Files up to 64 MB go as one chunk. Larger files use 10 MB chunks and the final
    chunk absorbs the remainder (TikTok allows the last chunk to be larger).
    """
    if size <= 0:
        raise ValueError("empty file")
    if size <= SINGLE_CHUNK_MAX:
        return [(0, size - 1)]
    count = size // CHUNK
    ranges = [(i * CHUNK, (i + 1) * CHUNK - 1) for i in range(count)]
    start, _ = ranges[-1]
    ranges[-1] = (start, size - 1)
    return ranges


class TikTokPublisher:
    name = "tiktok"

    def __init__(
        self,
        *,
        access_token: str,
        privacy: str = "SELF_ONLY",
        http: httpx.Client | None = None,
        poll_seconds: float = 5.0,
        max_wait_seconds: float = 600.0,
    ) -> None:
        self._http = http or client()
        self._headers = {"Authorization": f"Bearer {access_token}"}
        self._privacy = privacy
        self._poll = poll_seconds
        self._max_wait = max_wait_seconds

    def publish(
        self, video: Path, thumbnail: Path | None, script: Script, job_id: str
    ) -> PublishResult:
        size = video.stat().st_size
        plan = chunk_plan(size)
        chunk_size = plan[0][1] - plan[0][0] + 1
        title = f"{script.title} {' '.join(script.hashtags)}"[:2200]
        try:
            init = self._http.post(
                f"{API}/video/init/",
                headers={**self._headers, "Content-Type": "application/json; charset=UTF-8"},
                json={
                    "post_info": {
                        "title": title,
                        "privacy_level": self._privacy,
                        "disable_duet": False,
                        "disable_comment": False,
                        "disable_stitch": False,
                        "video_cover_timestamp_ms": 1000,
                    },
                    "source_info": {
                        "source": "FILE_UPLOAD",
                        "video_size": size,
                        "chunk_size": chunk_size,
                        "total_chunk_count": len(plan),
                    },
                },
            )
            init.raise_for_status()
            data = init.json().get("data") or {}
            publish_id, upload_url = data.get("publish_id"), data.get("upload_url")
            if not publish_id or not upload_url:
                return PublishResult(
                    platform=Platform.TIKTOK, ok=False, error=f"init failed: {init.text[:300]}"
                )

            with video.open("rb") as fh:
                for start, end in plan:
                    fh.seek(start)
                    chunk = fh.read(end - start + 1)
                    put = self._http.put(
                        upload_url,
                        content=chunk,
                        headers={
                            "Content-Type": "video/mp4",
                            "Content-Length": str(len(chunk)),
                            "Content-Range": f"bytes {start}-{end}/{size}",
                        },
                    )
                    put.raise_for_status()

            deadline = time.monotonic() + self._max_wait
            while time.monotonic() < deadline:
                status = self._http.post(
                    f"{API}/status/fetch/",
                    headers={**self._headers, "Content-Type": "application/json; charset=UTF-8"},
                    json={"publish_id": publish_id},
                )
                status.raise_for_status()
                body = status.json().get("data") or {}
                state = body.get("status")
                if state == "PUBLISH_COMPLETE":
                    ids = body.get("publicaly_available_post_id") or []
                    return PublishResult(
                        platform=Platform.TIKTOK,
                        ok=True,
                        remote_id=str(ids[0]) if ids else publish_id,
                        url=None,
                    )
                if state == "FAILED":
                    return PublishResult(
                        platform=Platform.TIKTOK,
                        ok=False,
                        error=f"TikTok: {body.get('fail_reason')}",
                    )
                time.sleep(self._poll)
            return PublishResult(
                platform=Platform.TIKTOK, ok=False, error="TikTok: processing timed out"
            )
        except httpx.HTTPStatusError as exc:
            return PublishResult(
                platform=Platform.TIKTOK,
                ok=False,
                error=f"TikTok {exc.response.status_code}: {exc.response.text[:300]}",
            )
        except (httpx.TransportError, OSError) as exc:
            return PublishResult(platform=Platform.TIKTOK, ok=False, error=f"TikTok: {exc}")
