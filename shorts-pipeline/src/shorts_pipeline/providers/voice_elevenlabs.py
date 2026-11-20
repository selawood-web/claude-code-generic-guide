"""ElevenLabs text-to-speech with character timestamps, folded into word timings.

Endpoint: POST https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/with-timestamps
Response: {"audio_base64": ..., "alignment": {"characters": [...],
           "character_start_times_seconds": [...], "character_end_times_seconds": [...]}}
"""

from __future__ import annotations

import base64
from pathlib import Path

import httpx

from ..config import VoiceConfig
from ..models import VoiceTrack, WordTiming
from ..render import ffmpeg
from ._http import client, retry
from .base import ProviderError

API = "https://api.elevenlabs.io/v1"


def words_from_characters(
    characters: list[str], starts: list[float], ends: list[float]
) -> list[WordTiming]:
    """Group character timings into words on whitespace. Pure, so it is unit-tested."""
    if not (len(characters) == len(starts) == len(ends)):
        raise ValueError("alignment arrays differ in length")
    words: list[WordTiming] = []
    buf: list[str] = []
    start = 0.0
    end = 0.0
    for ch, s, e in zip(characters, starts, ends, strict=True):
        if ch.isspace():
            if buf:
                words.append(WordTiming(word="".join(buf), start=start, end=end))
                buf = []
            continue
        if not buf:
            start = s
        buf.append(ch)
        end = e
    if buf:
        words.append(WordTiming(word="".join(buf), start=start, end=end))
    return words


class ElevenLabsVoice:
    def __init__(self, config: VoiceConfig, api_key: str, http: httpx.Client | None = None) -> None:
        self._config = config
        self._http = http or client(headers={"xi-api-key": api_key})

    def synthesize(self, text: str, out_dir: Path) -> VoiceTrack:
        cfg = self._config
        url = f"{API}/text-to-speech/{cfg.voice_id}/with-timestamps"
        body = {
            "text": text,
            "model_id": cfg.model_id,
            "output_format": "mp3_44100_128",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75, "speed": cfg.speed},
        }

        def call() -> httpx.Response:
            resp = self._http.post(url, json=body)
            resp.raise_for_status()
            return resp

        try:
            payload = retry(call).json()
        except httpx.HTTPStatusError as exc:
            raise ProviderError(
                f"ElevenLabs returned {exc.response.status_code}: {exc.response.text[:300]}"
            ) from exc

        audio_path = out_dir / "voice.mp3"
        audio_path.write_bytes(base64.b64decode(payload["audio_base64"]))
        alignment = payload.get("alignment") or payload.get("normalized_alignment")
        if not alignment:
            raise ProviderError("ElevenLabs response had no alignment data")
        words = words_from_characters(
            alignment["characters"],
            alignment["character_start_times_seconds"],
            alignment["character_end_times_seconds"],
        )
        return VoiceTrack(audio_path=audio_path, duration=ffmpeg.duration(audio_path), words=words)
