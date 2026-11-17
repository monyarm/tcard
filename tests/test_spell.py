import json
import pathlib

from tcard.render.layout import layout
from tcard.render.text import render
from tcard.sources.fivee.spell import (
    format_components,
    format_duration,
    format_range,
    format_time,
    school_name,
    to_card,
)

FIXTURES = pathlib.Path(__file__).parent / "fixtures"
FIREBALL = json.loads((FIXTURES / "fireball-xphb.json").read_text())
SHAPES = json.loads((FIXTURES / "spell-shapes.json").read_text())


def test_fireball_card():
    card = to_card(FIREBALL)
    assert card.title == "Fireball"
    assert card.subtitle == "Level 3 Evocation"
    fields = dict(card.fields)
    assert fields["Casting Time"] == "1 action"
    assert fields["Range"] == "150 feet"
    assert fields["Components"] == "V, S, M (a ball of bat guano and sulfur)"
    assert fields["Duration"] == "Instantaneous"
    assert fields["Source"] == "XPHB p.274"
    headings = [heading for heading, _ in card.sections]
    assert "Using a Higher-Level Spell Slot" in headings


def test_cantrip_subtitle():
    assert to_card(SHAPES[0]).subtitle == "Evocation Cantrip"


def test_sphere_range_is_self_centred():
    assert dict(to_card(SHAPES[1]).fields)["Range"] == "Self (60-foot sphere)"


def test_concentration_duration():
    assert dict(to_card(SHAPES[1]).fields)["Duration"] == "Concentration, up to 1 minute"


def test_reaction_condition():
    casting = dict(to_card(SHAPES[2]).fields)["Casting Time"]
    assert casting == "1 reaction, when you are hit by an attack"


def test_material_component_object():
    assert dict(to_card(SHAPES[3]).fields)["Components"] == "V, S, M (a diamond worth 50 gp)"


def test_fireball_renders_ascii_and_in_width():
    text = render(layout(to_card(FIREBALL), 32))
    assert text.isascii()
    assert all(len(line) <= 32 for line in text.splitlines())
    assert "@" not in text
    assert "8d6" in text


def test_fireball_renders_at_other_widths():
    card = to_card(FIREBALL)
    for cols in (20, 24, 38, 54):
        text = render(layout(card, cols))
        assert all(len(line) <= cols for line in text.splitlines()), cols


def test_format_time_plurals():
    assert format_time([{"number": 10, "unit": "minute"}]) == "10 minutes"
    assert format_time([{"number": 1, "unit": "bonus"}]) == "1 bonus action"


def test_format_range_variants():
    assert format_range({"type": "point", "distance": {"type": "touch"}}) == "Touch"
    assert format_range({"type": "point", "distance": {"type": "feet", "amount": 30}}) == "30 feet"
    assert format_range({"type": "cone", "distance": {"type": "feet", "amount": 15}}) == "Self (15-foot cone)"


def test_format_duration_variants():
    assert format_duration([{"type": "instant"}]) == "Instantaneous"
    assert format_duration([{"type": "permanent"}]) == "Permanent"
    assert format_duration([{"type": "timed", "duration": {"amount": 10, "type": "minute"}, "concentration": True}]) == (
        "Concentration, up to 10 minutes"
    )


def test_format_components_without_material():
    assert format_components({"v": True, "s": True}) == "V, S"


def test_school_unknown_code():
    assert school_name("Z") == "Z"


def test_duration_without_concentration_is_capitalised():
    assert dict(to_card(SHAPES[2]).fields)["Duration"] == "Up to 1 round"
