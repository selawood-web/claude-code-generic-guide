"""Instagram Reels via the Graph API container flow.

1. POST /{ig-user-id}/media  media_type=REELS video_url=<public URL> caption=...
2. poll GET /{container-id}?fields=status_code until FINISHED
3. POST /{ig-user-id}/media_publish creation_id=<container-id>

Instagram downloads the file itself, so the video must be reachable at a public URL:
this service exposes rendered videos under /media/<job_id>/final.mp4 (see server.py).
Limits: 100 API posts per rolling 24h; a Business or Creator account is required.
"""

from __future__ import annotations

import time
from pathlib import Path

import httpx

from ..models import Platform, PublishResult, Script
from ._http import client

GRAPH = "https://graph.facebook.com"


class InstagramPublisher:
    name = "instagram"

    def __init__(
        self,
        *,
        user_id: str,
        access_token: str,
        public_base_url: str,
        api_version: str = "v25.0",
        http: httpx.Client | None = None,
        poll_seconds: float = 5.0,
        max_wait_seconds: float = 600.0,
    ) -> None:
        self._user_id = user_id
        self._token = access_token
        self._base = public_base_url.rstrip("/")
        self._api = f"{GRAPH}/{api_version}"
        self._http = http or client()
        self._poll = poll_seconds
        self._max_wait = max_wait_seconds

    def video_url(self, job_id: str) -> str:
        return f"{self._base}/media/{job_id}/final.mp4"

    def publish(
        self, video: Path, thumbnail: Path | None, script: Script, job_id: str
    ) -> PublishResult:
        caption = f"{script.title}\n\n{script.description}\n\n{' '.join(script.hashtags)}"[:2200]
        try:
            created = self._http.post(
                f"{self._api}/{self._user_id}/media",
                data={
                    "media_type": "REELS",
                    "video_url": self.video_url(job_id),
                    "caption": caption,
                    "share_to_feed": "true",
                    "access_token": self._token,
                },
            )
            created.raise_for_status()
            container = str(created.json()["id"])

            deadline = time.monotonic() + self._max_wait
            status = "IN_PROGRESS"
            while status in ("IN_PROGRESS", "PUBLISHED") and time.monotonic() < deadline:
                poll = self._http.get(
                    f"{self._api}/{container}",
                    params={"fields": "status_code,status", "access_token": self._token},
                )
                poll.raise_for_status()
                status = str(poll.json().get("status_code", "IN_PROGRESS"))
                if status == "FINISHED":
                    break
                if status in ("ERROR", "EXPIRED"):
                    return PublishResult(
                        platform=Platform.INSTAGRAM,
                        ok=False,
                        error=f"container {status}: {poll.json().get('status')}",
                    )
                time.sleep(self._poll)
            if status != "FINISHED":
                return PublishResult(
                    platform=Platform.INSTAGRAM,
                    ok=False,
                    error="container never finished processing",
                )

            published = self._http.post(
                f"{self._api}/{self._user_id}/media_publish",
                data={"creation_id": container, "access_token": self._token},
            )
            published.raise_for_status()
            media_id = str(published.json()["id"])
            permalink = self._http.get(
                f"{self._api}/{media_id}",
                params={"fields": "permalink", "access_token": self._token},
            )
            url = permalink.json().get("permalink") if permalink.status_code == 200 else None
            return PublishResult(platform=Platform.INSTAGRAM, ok=True, remote_id=media_id, url=url)
        except httpx.HTTPStatusError as exc:
            return PublishResult(
                platform=Platform.INSTAGRAM,
                ok=False,
                error=f"Instagram {exc.response.status_code}: {exc.response.text[:300]}",
            )
        except (httpx.TransportError, KeyError) as exc:
            return PublishResult(platform=Platform.INSTAGRAM, ok=False, error=f"Instagram: {exc}")
