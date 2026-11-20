"""Image generation on fal.ai via the synchronous queue-less endpoint.

POST https://fal.run/{model} with {"prompt", "image_size"} returns {"images": [{"url"}]}.
Defaults to FLUX schnell (fast, cheap, portrait-capable). Any fal image model with the
same request shape works by changing `visuals.fal_model` in config.
"""

from __future__ import annotations

from functools import partial
from pathlib import Path

import httpx

from ..config import VisualsConfig
from ..models import Script, VisualAsset
from ._http import client, retry
from .base import ProviderError


class FalVisuals:
    def __init__(
        self, config: VisualsConfig, api_key: str, http: httpx.Client | None = None
    ) -> None:
        self._config = config
        self._http = http or client(headers={"Authorization": f"Key {api_key}"})

    def _image_url(self, prompt: str) -> str:
        body = {
            "prompt": f"{prompt}, {self._config.style_suffix}",
            "image_size": {"width": 1080, "height": 1920},
            "num_images": 1,
            "enable_safety_checker": True,
        }

        def call() -> httpx.Response:
            resp = self._http.post(f"https://fal.run/{self._config.fal_model}", json=body)
            resp.raise_for_status()
            return resp

        try:
            data = retry(call).json()
        except httpx.HTTPStatusError as exc:
            raise ProviderError(
                f"fal.ai returned {exc.response.status_code}: {exc.response.text[:300]}"
            ) from exc
        images = data.get("images") or []
        if not images or "url" not in images[0]:
            raise ProviderError(f"fal.ai returned no image for prompt: {prompt[:60]}")
        return str(images[0]["url"])

    def generate(self, script: Script, out_dir: Path) -> list[VisualAsset]:
        assets: list[VisualAsset] = []
        prompts = [script.hook, *(s.visual_prompt for s in script.scenes)]
        # scene 0 (the hook) reuses the first scene's visual to avoid a text-like prompt
        prompts[0] = script.scenes[0].visual_prompt
        for index, prompt in enumerate(prompts):
            url = self._image_url(prompt)
            target = out_dir / f"scene_{index:02d}.png"
            resp = retry(partial(self._http.get, url))
            resp.raise_for_status()
            target.write_bytes(resp.content)
            assets.append(VisualAsset(scene_index=index, path=target, kind="image"))
        return assets
