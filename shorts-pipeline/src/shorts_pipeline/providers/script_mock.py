"""Deterministic script for tests and dry runs. No network."""

from __future__ import annotations

from ..config import ScriptConfig
from ..models import Scene, Script


class MockScriptWriter:
    def __init__(self, config: ScriptConfig) -> None:
        self._config = config

    def write(self, *, recent_topics: list[str]) -> Script:
        n = len(recent_topics) + 1
        topic = f"Why octopuses have three hearts (take {n})"
        return Script(
            topic=topic,
            hook="An octopus has three hearts, and two of them stop when it swims.",
            scenes=[
                Scene(
                    narration="Two hearts pump blood through the gills. The third feeds the body.",
                    visual_prompt="close-up of an octopus gliding over a coral reef",
                    caption_hint="3 hearts",
                ),
                Scene(
                    narration="When it swims, the body heart pauses. So it crawls instead.",
                    visual_prompt="octopus crawling along the seabed, sunlight rays from above",
                    caption_hint="pauses",
                ),
                Scene(
                    narration="Its blood is blue, because it uses copper, not iron, for oxygen.",
                    visual_prompt="abstract macro of deep blue liquid swirling",
                    caption_hint="blue blood",
                ),
                Scene(
                    narration="Which animal fact should we cover next?",
                    visual_prompt="dark ocean with a single glowing jellyfish",
                ),
            ],
            title="Octopuses have three hearts",
            description="Two pump to the gills, one to the body, and it stops when they swim.",
            hashtags=["octopus", "animalfacts", "science", "ocean", "didyouknow"],
            music_mood="mysterious",
        )
