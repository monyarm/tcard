from tcard.render.layout import fold, wrap


def test_fold_transliterates_typography():
    assert fold("Tasha\u2019s 5\u201310-foot \u00d7 3 \u2014 50%") == "Tasha's 5-10-foot x 3 - 50%"


def test_fold_drops_unmappable():
    assert fold("a\u2603b") == "ab"


def test_fold_output_is_ascii():
    out = fold("\u201cq\u201d \u00e9 \u00f1 \u2603")
    assert all(ord(c) < 128 for c in out)


def test_fold_keeps_the_glyphs_the_printer_can_draw():
    assert fold("\u2022 \u25cf\u25cb") == "\u2022 \u25cf\u25cb"


def test_wrap_respects_width():
    assert wrap("one two three four", 9) == ["one two", "three", "four"]


def test_wrap_hard_breaks_long_token():
    assert wrap("abcdefghij", 4) == ["abcd", "efgh", "ij"]


def test_wrap_empty():
    assert wrap("   ", 10) == []


def test_wrap_exact_fit():
    assert wrap("abcd ef", 7) == ["abcd ef"]
