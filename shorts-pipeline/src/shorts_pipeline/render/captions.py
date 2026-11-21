"""Word-highlight captions as an ASS subtitle file.

Captions are shown in small groups (up to three words); the word being spoken is
coloured. One Dialogue event per word, so timing comes straight from the voice track.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from ..models import HEIGHT, WIDTH, WordTiming

MAX_GROUP = 3
MAX_GROUP_CHARS = 18


def ass_time(seconds: float) -> str:
    seconds = max(0.0, seconds)
    hours = int(seconds // 3600)
    minutes = int(seconds % 3600 // 60)
    secs = seconds % 60
    return f"{hours}:{minutes:02d}:{secs:05.2f}"


def _escape(text: str) -> str:
    return text.replace("{", "(").replace("}", ")").replace("\n", " ")


def group_words(words: Iterable[WordTiming]) -> list[list[WordTiming]]:
    """Split the word stream into display groups. Pure, unit-tested."""
    groups: list[list[WordTiming]] = []
    current: list[WordTiming] = []
    length = 0
    for word in words:
        if current and (len(current) >= MAX_GROUP or length + len(word.word) + 1 > MAX_GROUP_CHARS):
            groups.append(current)
            current, length = [], 0
        current.append(word)
        length += len(word.word) + 1
        # a sentence end closes the group so the next sentence starts on a fresh line
        if word.word[-1:] in ".!?":
            groups.append(current)
            current, length = [], 0
    if current:
        groups.append(current)
    return groups


def build_ass(
    words: list[WordTiming],
    *,
    font: str = "DejaVu Sans",
    font_size: int = 72,
    highlight: str = "&H0000D7FF",
) -> str:
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {WIDTH}
PlayResY: {HEIGHT}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Word,{font},{font_size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,1,0,1,6,2,2,60,60,560,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines: list[str] = []
    for group in group_words(words):
        for i, current in enumerate(group):
            parts: list[str] = []
            for j, w in enumerate(group):
                text = _escape(w.word.upper())
                parts.append(f"{{\\c{highlight}&}}{text}{{\\c&H00FFFFFF&}}" if j == i else text)
            # hold the last word of a group until the next group starts, avoiding flicker
            end = current.end if i < len(group) - 1 else max(current.end, current.start + 0.25)
            lines.append(
                f"Dialogue: 0,{ass_time(current.start)},{ass_time(end)},Word,,0,0,0,,"
                + " ".join(parts)
            )
    return header + "\n".join(lines) + "\n"


def write_ass(words: list[WordTiming], target: Path, **style: object) -> Path:
    target.write_text(build_ass(words, **style), encoding="utf-8")  # type: ignore[arg-type]
    return target
