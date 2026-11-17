from tcard.model import Card, Line, LineKind


def test_card_defaults():
    card = Card("Fireball")
    assert card.fields == []
    assert card.sections == []


def test_line_is_immutable():
    line = Line(LineKind.BODY, "x")
    try:
        line.text = "y"
    except AttributeError:
        return
    raise AssertionError("Line must be frozen")


def test_kinds_compare_as_strings():
    assert LineKind.TITLE == "title"
