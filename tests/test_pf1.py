from pathlib import Path

from tcard.render.layout import layout
from tcard.render.text import render
from tcard.sources import registry
from tcard.sources.pf1 import KINDS, cache, html, spell

FIXTURES = Path(__file__).parent / "fixtures"


def test_letter_page_links():
    records = cache.parse_letter((FIXTURES / "pf1-letter-f.html").read_text())
    names = [record["name"] for record in records]
    assert set(names) == {"Fireball", "Fabricate", "Fable Tapestry"}
    assert all(record["url"].startswith("https://www.d20pfsrd.com/magic/all-spells/f/") for record in records)


def test_fireball_card():
    card = spell.parse((FIXTURES / "pf1-fireball.html").read_text())
    assert card.title == "Fireball"
    assert card.subtitle == "Evocation [fire]"
    fields = dict(card.fields)
    assert fields["Casting Time"] == "1 standard action"
    assert fields["Components"] == "Sample text for layout."
    assert fields["Range"].startswith("long (400 ft.")
    assert fields["Saving Throw"] == "Reflex half"
    assert fields["Spell Resistance"] == "yes"
    assert fields["Level"] == "bloodrager 3, magus 3, sorcerer/wizard 3"
    headings = [heading for heading, _ in card.sections]
    assert headings == [""]
    assert card.sections[0][1]
    assert not any("Augmented (6th)" in part for part in card.sections[0][1])


def test_archetype_headings_become_sections():
    markup = (
        "<article><h1>Acrobat</h1>"
        "<p>Intro prose.</p>"
        "<h4><b>Expert Acrobat (Ex)</b></h4>"
        "<p>At 1st level this ability replaces trapfinding.</p>"
        "<h4><b>Second Chance (Ex)</b></h4>"
        "<p>At 3rd level you may reroll.</p>"
        "</article>"
    )
    card = spell.parse(markup)
    headings = [heading for heading, _ in card.sections]
    assert headings == ["", "Expert Acrobat (Ex)", "Second Chance (Ex)"]
    assert card.sections[2][1] == ["At 3rd level you may reroll."]


def test_fireball_renders_clean_at_32():
    card = spell.parse((FIXTURES / "pf1-fireball.html").read_text())
    output = render(layout(card, 32))
    assert output.isascii()
    assert max(len(line) for line in output.splitlines()) <= 32
    assert "<" not in output and "&#" not in output and "\x00" not in output
    assert output.startswith("FIREBALL        EVOCATION [FIRE]\n")


def test_labelled_splits_on_br_and_semicolon():
    pairs = html.labelled("<b>Range</b> long<br /><b>Saving Throw</b> Reflex half; <b>Spell Resistance</b> yes")
    assert pairs == [("Range", "long"), ("Saving Throw", "Reflex half"), ("Spell Resistance", "yes")]


def test_kind_matches_underscored_query():
    kind = KINDS["spell"]
    records = [{"name": "Fable Tapestry", "url": "u"}, {"name": "Fireball", "url": "v"}]
    assert kind.matches(records, "fable_tapestry") == records[:1]
    assert kind.matches(records, "fire") == records[1:]


def test_registry_knows_pf1_and_alias():
    assert "pf:1e" in registry.systems()
    assert registry.resolve("pf1") == "pf:1e"
    assert "spell" in registry.kinds("pf:1e")
    kinds = registry.kinds("pf:1e")
    assert {"monster", "deity", "racial_trait"} <= set(kinds)


def test_candidate_line_without_source():
    from tcard.cli import _candidate_lines

    line = _candidate_lines([("spell", {"name": "Fireball", "url": "u"})], {"spell": KINDS["spell"]})[0]
    assert line == "  Fireball (spell)"
