"""YouTube Shorts via the Data API v3 resumable upload.

A Short is just a vertical video under 3 minutes; "#Shorts" in the description
helps classification. Cost: videos.insert = 1600 quota units of the default 10,000/day,
so one upload every few days is far inside the free quota.
"""

from __future__ import annotations

import time
from pathlib import Path

import httpx

from ..models import Platform, PublishResult, Script
from ._http import client, retry

TOKEN_URL = "https://oauth2.googleapis.com/token"  # noqa: S105 - endpoint, not a secret
UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"


class YouTubePublisher:
    name = "youtube"

    def __init__(
        self,
        *,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        privacy: str = "public",
        http: httpx.Client | None = None,
    ) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._refresh_token = refresh_token
        self._privacy = privacy
        self._http = http or client()

    def _access_token(self) -> str:
        resp = self._http.post(
            TOKEN_URL,
            data={
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "refresh_token": self._refresh_token,
                "grant_type": "refresh_token",
            },
        )
        resp.raise_for_status()
        return str(resp.json()["access_token"])

    def publish(
        self, video: Path, thumbnail: Path | None, script: Script, job_id: str
    ) -> PublishResult:
        try:
            token = self._access_token()
            size = video.stat().st_size
            metadata = {
                "snippet": {
                    "title": script.title[:100],
                    "description": f"{script.description}\n\n{' '.join(script.hashtags)} #Shorts"[
                        :5000
                    ],
                    "tags": [t.lstrip("#") for t in script.hashtags][:30],
                    "categoryId": "27",  # Education
                },
                "status": {"privacyStatus": self._privacy, "selfDeclaredMadeForKids": False},
            }
            headers = {
                "Authorization": f"Bearer {token}",
                "X-Upload-Content-Type": "video/mp4",
                "X-Upload-Content-Length": str(size),
            }
            init = self._http.post(
                UPLOAD_URL,
                params={"uploadType": "resumable", "part": "snippet,status"},
                json=metadata,
                headers=headers,
            )
            init.raise_for_status()
            session_url = init.headers.get("Location")
            if not session_url:
                return PublishResult(
                    platform=Platform.YOUTUBE, ok=False, error="no upload session URL"
                )

            def upload() -> httpx.Response:
                with video.open("rb") as fh:
                    resp = self._http.put(
                        session_url,
                        content=fh.read(),
                        headers={"Authorization": f"Bearer {token}", "Content-Type": "video/mp4"},
                    )
                resp.raise_for_status()
                return resp

            video_id = str(retry(upload).json()["id"])
            time.sleep(0)  # placeholder for future processing poll; Shorts need none to be public
            return PublishResult(
                platform=Platform.YOUTUBE,
                ok=True,
                remote_id=video_id,
                url=f"https://youtube.com/shorts/{video_id}",
            )
        except httpx.HTTPStatusError as exc:
            return PublishResult(
                platform=Platform.YOUTUBE,
                ok=False,
                error=f"YouTube {exc.response.status_code}: {exc.response.text[:300]}",
            )
        except (httpx.TransportError, KeyError, OSError) as exc:
            return PublishResult(platform=Platform.YOUTUBE, ok=False, error=f"YouTube: {exc}")
