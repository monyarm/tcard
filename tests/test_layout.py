import pathlib

from tcard.model import Card, LineKind
from tcard.render.layout import layout
from tcard.render.text import render

CARD = Card(
    "Fireball",
    "Level 3 Evocation",
    [
        ("Casting Time", "1 action"),
        ("Range", "150 feet"),
        ("Components", "V, S, M (a ball of bat guano and sulfur)"),
        ("Duration", "Instantaneous"),
        ("Source", "XPHB p.274"),
    ],
    [("", ["A bright streak flashes from you."])],
)

GOLDEN = pathlib.Path(__file__).parent / "golden" / "fireball-32.txt"


def test_layout_first_lines():
    lines = layout(CARD, 32)
    assert lines[0].kind is LineKind.TITLE and lines[0].text == "Fireball"
    assert lines[1].kind is LineKind.RULE and lines[1].text == "=" * 32
    assert lines[2].text == "Level 3 Evocation"


def test_layout_wraps_field_with_indent():
    texts = [line.text for line in layout(CARD, 32)]
    assert "Components: V, S, M (a ball of" in texts
    assert "  bat guano and sulfur)" in texts


def test_layout_rejects_narrow_width():
    try:
        layout(CARD, 8)
    except ValueError as exc:
        assert "8" in str(exc)
        return
    raise AssertionError("narrow width must raise")


def test_layout_never_exceeds_width():
    for cols in (20, 24, 32, 38, 54):
        for line in layout(CARD, cols):
            assert len(line.text) <= cols, (cols, line)


def test_layout_brief_omits_body():
    kinds = {line.kind for line in layout(CARD, 32, brief=True)}
    assert LineKind.BODY not in kinds
    assert LineKind.RULE in kinds


def test_layout_long_title_wraps():
    card = Card("Mordenkainen's Magnificent Mansion")
    lines = layout(card, 20)
    assert all(len(line.text) <= 20 for line in lines)
    assert len([line for line in lines if line.kind is LineKind.TITLE]) == 2


def test_render_uppercases_headings_only():
    out = render(layout(CARD, 32))
    assert out.startswith("FIREBALL\n")
    assert "Casting Time: 1 action" in out
    assert out.endswith("\n")


def test_render_is_ascii():
    assert render(layout(CARD, 32)).isascii()


def test_golden_fireball():
    assert render(layout(CARD, 32)) == GOLDEN.read_text()
