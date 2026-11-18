import json
import pathlib
import unittest.mock as mock

from tcard.sources.fivee import items

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


def _load(rel: str, refresh: bool = False):
    return json.loads((FIXTURES / rel).read_text())


def _cards():
    with mock.patch.object(items.cache, "load_json", _load):
        records = items.records()
        return records, {(record["name"], record["source"]): items.to_card(record) for record in records}


def test_records_merge_magic_and_mundane():
    records, _ = _cards()
    names = {record["name"] for record in records}
    assert {"Bag of Holding", "Longsword", "Plate Armor", "Ring of Protection"} <= names


def test_magic_item_card():
    _, cards = _cards()
    card = cards[("Bag of Holding", "DMG")]
    fields = dict(card.fields)
    assert card.subtitle == "Uncommon Wondrous Item"
    assert "Attunement" not in fields
    assert fields["Weight"] == "15 lb"
    assert "Source" not in fields


def test_ring_uses_item_type_table_and_bonus():
    _, cards = _cards()
    card = cards[("Ring of Protection", "DMG")]
    fields = dict(card.fields)
    assert card.subtitle == "Rare Ring"
    assert fields["Attunement"] == "Required"
    assert fields["AC"] in ("AC +1", "AC 1")


def test_weapon_damage_and_value_in_gold():
    _, cards = _cards()
    card = cards[("Longsword", "PHB")]
    fields = dict(card.fields)
    assert card.subtitle == "Melee Weapon"
    assert fields["Damage"] == "1d8 slashing, versatile (1d10)"
    assert fields["Weight"] == "3 lb"
    assert fields["Value"] == "15 gp"


def test_armour_line():
    _, cards = _cards()
    card = cards[("Plate Armor", "PHB")]
    fields = dict(card.fields)
    assert card.subtitle == "Heavy Armor"
    assert fields["Armor"] == "AC 18, Str 15, stealth disadvantage"
    assert fields["Value"] == "1500 gp"


def test_unknown_type_falls_back_to_wondrous():
    assert items.type_name("ZZ", {}) == "Wondrous Item"
    assert items.type_name(None, {}) == "Wondrous Item"
    assert items.type_name("RG|DMG", {"RG": "Ring"}) == "Ring"


def test_attunement_text():
    assert items.attunement({"reqAttune": "by a spellcaster"}) == "Required (by a spellcaster)"
    assert items.attunement({}) == ""
