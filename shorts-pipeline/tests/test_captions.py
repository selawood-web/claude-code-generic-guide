from shorts_pipeline.models import WordTiming
from shorts_pipeline.render.captions import ass_time, build_ass, group_words


def _words(text: str) -> list[WordTiming]:
    return [
        WordTiming(word=w, start=i * 0.5, end=i * 0.5 + 0.4) for i, w in enumerate(text.split())
    ]


def test_ass_time_formats_hours_minutes_centiseconds() -> None:
    assert ass_time(0) == "0:00:00.00"
    assert ass_time(61.234) == "0:01:01.23"
    assert ass_time(3600) == "1:00:00.00"
    assert ass_time(-1) == "0:00:00.00"


def test_group_words_caps_at_three() -> None:
    groups = group_words(_words("a b c d e f g"))
    assert [len(g) for g in groups] == [3, 3, 1]


def test_group_words_breaks_on_sentence_end() -> None:
    groups = group_words(_words("one two. three four five"))
    assert [[w.word for w in g] for g in groups] == [["one", "two."], ["three", "four", "five"]]


def test_group_words_breaks_on_long_text() -> None:
    groups = group_words(_words("supercalifragilistic expialidocious"))
    assert len(groups) == 2


def test_group_words_empty() -> None:
    assert group_words([]) == []


def test_build_ass_highlights_each_word_once() -> None:
    ass = build_ass(_words("alpha beta"), highlight="&H0000D7FF")
    dialogues = [line for line in ass.splitlines() if line.startswith("Dialogue:")]
    assert len(dialogues) == 2
    assert "{\\c&H0000D7FF&}ALPHA" in dialogues[0] and "BETA" in dialogues[0]
    assert "{\\c&H0000D7FF&}BETA" in dialogues[1]
    assert "PlayResX: 1080" in ass and "PlayResY: 1920" in ass


def test_build_ass_escapes_braces() -> None:
    ass = build_ass([WordTiming(word="{x}", start=0, end=1)])
    assert "{\\c&H0000D7FF&}(X)" in ass
