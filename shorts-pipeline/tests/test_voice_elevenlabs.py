import base64
from pathlib import Path

import httpx
import pytest

from shorts_pipeline.config import VoiceConfig
from shorts_pipeline.providers.base import ProviderError
from shorts_pipeline.providers.voice_elevenlabs import ElevenLabsVoice, words_from_characters
from shorts_pipeline.render import ffmpeg


def test_words_from_characters_groups_on_whitespace() -> None:
    chars = list("hi yo")
    starts = [0.0, 0.1, 0.2, 0.3, 0.4]
    ends = [0.1, 0.2, 0.3, 0.4, 0.5]
    words = words_from_characters(chars, starts, ends)
    assert [(w.word, w.start, w.end) for w in words] == [("hi", 0.0, 0.2), ("yo", 0.3, 0.5)]


def test_words_from_characters_handles_leading_and_double_spaces() -> None:
    chars = list("  a  b ")
    n = len(chars)
    words = words_from_characters(chars, [i * 1.0 for i in range(n)], [i + 1.0 for i in range(n)])
    assert [w.word for w in words] == ["a", "b"]


def test_words_from_characters_empty() -> None:
    assert words_from_characters([], [], []) == []


def test_words_from_characters_rejects_mismatched_lengths() -> None:
    with pytest.raises(ValueError):
        words_from_characters(["a"], [0.0], [])


def _transport(handler):  # type: ignore[no-untyped-def]
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_synthesize_writes_audio_and_words(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/with-timestamps")
        assert request.headers["xi-api-key"] == "k"
        return httpx.Response(
            200,
            json={
                "audio_base64": base64.b64encode(b"MP3").decode(),
                "alignment": {
                    "characters": list("go on"),
                    "character_start_times_seconds": [0, 0.1, 0.2, 0.3, 0.4],
                    "character_end_times_seconds": [0.1, 0.2, 0.3, 0.4, 0.5],
                },
            },
        )

    monkeypatch.setattr(ffmpeg, "duration", lambda p: 0.5)
    voice = ElevenLabsVoice(VoiceConfig(), "k", http=_transport(handler))
    voice._http.headers["xi-api-key"] = "k"
    track = voice.synthesize("go on", tmp_path)
    assert track.audio_path.read_bytes() == b"MP3"
    assert [w.word for w in track.words] == ["go", "on"]
    assert track.duration == 0.5


def test_synthesize_surfaces_http_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("shorts_pipeline.providers._http.time.sleep", lambda s: None)
    voice = ElevenLabsVoice(
        VoiceConfig(), "k", http=_transport(lambda r: httpx.Response(401, text="bad key"))
    )
    with pytest.raises(ProviderError, match="401"):
        voice.synthesize("x", tmp_path)
