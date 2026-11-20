import json
from pathlib import Path

import httpx
import pytest

from shorts_pipeline.models import Platform, Script
from shorts_pipeline.providers.publish_instagram import InstagramPublisher
from shorts_pipeline.providers.publish_mock import MockPublisher
from shorts_pipeline.providers.publish_tiktok import (
    CHUNK,
    SINGLE_CHUNK_MAX,
    TikTokPublisher,
    chunk_plan,
)
from shorts_pipeline.providers.publish_youtube import YouTubePublisher
from shorts_pipeline.providers.visuals_pexels import pick_portrait_file


@pytest.fixture
def video(tmp_path: Path) -> Path:
    path = tmp_path / "final.mp4"
    path.write_bytes(b"\x00" * 1024)
    return path


def _client(handler):  # type: ignore[no-untyped-def]
    return httpx.Client(transport=httpx.MockTransport(handler))


# --- pure helpers -------------------------------------------------------------


def test_chunk_plan_single_chunk_up_to_64mb() -> None:
    assert chunk_plan(1) == [(0, 0)]
    assert chunk_plan(SINGLE_CHUNK_MAX) == [(0, SINGLE_CHUNK_MAX - 1)]


def test_chunk_plan_splits_large_files_and_absorbs_remainder() -> None:
    size = SINGLE_CHUNK_MAX + CHUNK + 7
    plan = chunk_plan(size)
    assert plan[0] == (0, CHUNK - 1)
    assert plan[-1][1] == size - 1
    assert plan[-1][1] - plan[-1][0] + 1 >= CHUNK  # last chunk is never tiny
    assert all(b[0] == a[1] + 1 for a, b in zip(plan, plan[1:], strict=False))


def test_chunk_plan_rejects_empty() -> None:
    with pytest.raises(ValueError):
        chunk_plan(0)


def test_pick_portrait_file_prefers_smallest_hd_portrait() -> None:
    video = {
        "video_files": [
            {"width": 1920, "height": 1080, "link": "landscape"},
            {"width": 720, "height": 1280, "link": "small"},
            {"width": 1080, "height": 1920, "link": "hd"},
            {"width": 2160, "height": 3840, "link": "4k"},
            {"width": "x", "height": 1920, "link": "bad"},
        ]
    }
    assert pick_portrait_file(video) == "hd"
    assert pick_portrait_file({"video_files": []}) is None
    assert pick_portrait_file({}) is None


# --- mock ---------------------------------------------------------------------


def test_mock_publisher_records_call(video: Path, script: Script) -> None:
    pub = MockPublisher()
    result = pub.publish(video, None, script, "j")
    assert result.ok and pub.calls[0]["job_id"] == "j"


def test_mock_publisher_rejects_empty_video(tmp_path: Path, script: Script) -> None:
    empty = tmp_path / "e.mp4"
    empty.write_bytes(b"")
    assert not MockPublisher().publish(empty, None, script, "j").ok


# --- youtube ------------------------------------------------------------------


def test_youtube_happy_path(video: Path, script: Script) -> None:
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(f"{request.method} {request.url.host}{request.url.path}")
        if request.url.host == "oauth2.googleapis.com":
            return httpx.Response(200, json={"access_token": "tok"})
        if request.method == "POST":
            assert request.headers["X-Upload-Content-Length"] == "1024"
            assert request.headers["Authorization"] == "Bearer tok"
            return httpx.Response(200, headers={"Location": "https://upload.example/session"})
        assert request.content == b"\x00" * 1024
        return httpx.Response(200, json={"id": "vid123"})

    pub = YouTubePublisher(
        client_id="c", client_secret="s", refresh_token="r", http=_client(handler)
    )
    result = pub.publish(video, None, script, "j")
    assert result.ok and result.url == "https://youtube.com/shorts/vid123"
    assert seen == [
        "POST oauth2.googleapis.com/token",
        "POST www.googleapis.com/upload/youtube/v3/videos",
        "PUT upload.example/session",
    ]


def test_youtube_reports_auth_failure(video: Path, script: Script) -> None:
    pub = YouTubePublisher(
        client_id="c",
        client_secret="s",
        refresh_token="bad",
        http=_client(lambda r: httpx.Response(400, text="invalid_grant")),
    )
    result = pub.publish(video, None, script, "j")
    assert not result.ok and "400" in (result.error or "")


def test_youtube_missing_session_url(video: Path, script: Script) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "oauth2.googleapis.com":
            return httpx.Response(200, json={"access_token": "tok"})
        return httpx.Response(200)

    pub = YouTubePublisher(
        client_id="c", client_secret="s", refresh_token="r", http=_client(handler)
    )
    assert "session" in (pub.publish(video, None, script, "j").error or "")


# --- instagram ----------------------------------------------------------------


def test_instagram_happy_path(video: Path, script: Script) -> None:
    polls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/42/media"):
            body = request.read().decode()
            assert (
                "media_type=REELS" in body
                and "video_url=https%3A%2F%2Fx.test%2Fmedia%2Fj%2Ffinal.mp4" in body
            )
            return httpx.Response(200, json={"id": "c1"})
        if path.endswith("/c1"):
            polls["n"] += 1
            return httpx.Response(
                200, json={"status_code": "IN_PROGRESS" if polls["n"] < 2 else "FINISHED"}
            )
        if path.endswith("/media_publish"):
            return httpx.Response(200, json={"id": "m9"})
        if path.endswith("/m9"):
            return httpx.Response(200, json={"permalink": "https://instagram.com/reel/m9"})
        return httpx.Response(404)

    pub = InstagramPublisher(
        user_id="42",
        access_token="t",
        public_base_url="https://x.test/",
        http=_client(handler),
        poll_seconds=0,
    )
    result = pub.publish(video, None, script, "j")
    assert result.ok and result.remote_id == "m9" and result.url == "https://instagram.com/reel/m9"
    assert polls["n"] == 2


def test_instagram_container_error(video: Path, script: Script) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/media"):
            return httpx.Response(200, json={"id": "c1"})
        return httpx.Response(200, json={"status_code": "ERROR", "status": "bad codec"})

    pub = InstagramPublisher(
        user_id="42",
        access_token="t",
        public_base_url="https://x.test",
        http=_client(handler),
        poll_seconds=0,
    )
    result = pub.publish(video, None, script, "j")
    assert not result.ok and "bad codec" in (result.error or "")


def test_instagram_http_error(video: Path, script: Script) -> None:
    pub = InstagramPublisher(
        user_id="42",
        access_token="t",
        public_base_url="https://x.test",
        http=_client(lambda r: httpx.Response(403, text="no permission")),
    )
    assert "403" in (pub.publish(video, None, script, "j").error or "")


# --- tiktok -------------------------------------------------------------------


def test_tiktok_happy_path(video: Path, script: Script) -> None:
    polls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/video/init/"):
            payload = json.loads(request.read())
            assert payload["source_info"]["source"] == "FILE_UPLOAD"
            assert payload["source_info"]["total_chunk_count"] == 1
            assert payload["post_info"]["privacy_level"] == "SELF_ONLY"
            return httpx.Response(
                200, json={"data": {"publish_id": "p1", "upload_url": "https://up.test/x"}}
            )
        if request.method == "PUT":
            assert request.headers["Content-Range"] == "bytes 0-1023/1024"
            return httpx.Response(201)
        if path.endswith("/status/fetch/"):
            polls["n"] += 1
            state = "PROCESSING_UPLOAD" if polls["n"] < 2 else "PUBLISH_COMPLETE"
            return httpx.Response(
                200, json={"data": {"status": state, "publicaly_available_post_id": [777]}}
            )
        return httpx.Response(404)

    pub = TikTokPublisher(access_token="t", http=_client(handler), poll_seconds=0)
    result = pub.publish(video, None, script, "j")
    assert result.ok and result.remote_id == "777" and result.platform is Platform.TIKTOK


def test_tiktok_failed_status(video: Path, script: Script) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/video/init/"):
            return httpx.Response(
                200, json={"data": {"publish_id": "p1", "upload_url": "https://up.test/x"}}
            )
        if request.method == "PUT":
            return httpx.Response(201)
        return httpx.Response(200, json={"data": {"status": "FAILED", "fail_reason": "spam_risk"}})

    result = TikTokPublisher(access_token="t", http=_client(handler), poll_seconds=0).publish(
        video, None, script, "j"
    )
    assert not result.ok and "spam_risk" in (result.error or "")


def test_tiktok_init_without_upload_url(video: Path, script: Script) -> None:
    pub = TikTokPublisher(
        access_token="t",
        http=_client(lambda r: httpx.Response(200, json={"data": {}})),
        poll_seconds=0,
    )
    assert "init failed" in (pub.publish(video, None, script, "j").error or "")


def test_tiktok_http_error(video: Path, script: Script) -> None:
    pub = TikTokPublisher(access_token="t", http=_client(lambda r: httpx.Response(401, text="x")))
    assert "401" in (pub.publish(video, None, script, "j").error or "")
