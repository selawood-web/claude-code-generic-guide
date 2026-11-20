"""Stock video from Pexels (free API). Search per scene, pick the best portrait HD file."""

from __future__ import annotations

from functools import partial
from pathlib import Path

import httpx

from ..config import VisualsConfig
from ..models import Script, VisualAsset
from ._http import client, retry
from .base import ProviderError


def pick_portrait_file(video: dict[str, object]) -> str | None:
    """Choose the smallest portrait file at least 1080 wide (true HD). Pure, unit-tested."""
    files = video.get("video_files")
    if not isinstance(files, list):
        return None
    candidates: list[tuple[int, str]] = []
    for f in files:
        if not isinstance(f, dict):
            continue
        w, h, link = f.get("width"), f.get("height"), f.get("link")
        if (
            isinstance(w, int)
            and isinstance(h, int)
            and isinstance(link, str)
            and h > w
            and w >= 1080
        ):
            candidates.append((h, link))
    if not candidates:
        return None
    return min(candidates)[1]


class PexelsVisuals:
    def __init__(
        self, config: VisualsConfig, api_key: str, http: httpx.Client | None = None
    ) -> None:
        self._config = config
        self._http = http or client(headers={"Authorization": api_key})

    def generate(self, script: Script, out_dir: Path) -> list[VisualAsset]:
        assets: list[VisualAsset] = []
        prompts = [script.scenes[0].visual_prompt, *(s.visual_prompt for s in script.scenes)]
        seen: set[str] = set()
        for index, prompt in enumerate(prompts):
            query = " ".join(prompt.split()[:5])
            resp = retry(
                partial(
                    self._http.get,
                    "https://api.pexels.com/videos/search",
                    params={
                        "query": query,
                        "orientation": "portrait",
                        "size": "medium",
                        "per_page": 8,
                    },
                )
            )
            if resp.status_code != 200:
                raise ProviderError(f"Pexels returned {resp.status_code}: {resp.text[:200]}")
            link: str | None = None
            for video in resp.json().get("videos", []):
                candidate = pick_portrait_file(video)
                if candidate and candidate not in seen:
                    link = candidate
                    break
            if link is None:
                raise ProviderError(f"Pexels had no portrait HD clip for '{query}'")
            seen.add(link)
            target = out_dir / f"scene_{index:02d}.mp4"
            with self._http.stream("GET", link) as stream, target.open("wb") as fh:
                for chunk in stream.iter_bytes():
                    fh.write(chunk)
            assets.append(VisualAsset(scene_index=index, path=target, kind="video"))
        return assets
