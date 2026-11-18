import json
import pathlib
import unittest.mock as mock

from tcard.render.layout import layout
from tcard.render.text import render
from tcard.sources import registry
from tcard.sources.fivee import cache, rules, species

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


def _load(rel: str, refresh: bool = False):
    return json.loads((FIXTURES / rel).read_text())


def _with_data(call):
    with mock.patch.object(cache, "load_json", _load):
        return call()


def _record(records, name, source):
    return next(r for r in records if r["name"] == name and r["source"] == source)


def test_aasimar_fields():
    card = species.to_card(_record(_with_data(species.records), "Aasimar", "XPHB"))
    fields = dict(card.fields)
    assert card.subtitle == "Species"
    assert fields["Type"] == "Humanoid"
    assert fields["Size"] == "Small or Medium"
    assert fields["Speed"] == "30 ft."
    assert fields["Darkvision"] == "60 ft."
    assert fields["Resistances"] == "necrotic, radiant"
    assert card.sections


def test_2014_race_keeps_ability_scores():
    card = species.to_card(_record(_with_data(species.records), "Dragonborn", "PHB"))
    fields = dict(card.fields)
    assert fields["Ability Scores"] == "Str +2, Cha +1"
    assert fields["Resistances"].startswith("one of acid, cold, fire")
    assert "Type" not in fields
    assert "Darkvision" not in fields


def test_cover_is_a_core_rule():
    card = rules.to_card(_record(_with_data(rules.records), "Cover", "XPHB"))
    assert card.subtitle == "Rule"
    assert card.sections


def test_flanking_is_an_optional_rule():
    card = rules.to_card(_record(_with_data(rules.records), "Flanking", "DMG"))
    assert card.subtitle == "Optional Rule"


def test_cards_render_inside_32_columns():
    cards = [species.to_card(record) for record in _with_data(species.records)]
    cards.append(rules.to_card(_record(_with_data(rules.records), "Cover", "XPHB")))
    for card in cards:
        text = render(layout(card, 32))
        assert text.isascii(), card.title
        assert max(len(line) for line in text.splitlines()) <= 32, card.title


def test_registry_knows_both_kinds():
    kinds = registry.kinds("dnd:5e")
    assert "species" in kinds and "variant_rule" in kinds
