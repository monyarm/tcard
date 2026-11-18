import json
import pathlib

import unittest.mock as mock

from tcard.render.layout import layout
from tcard.render.text import render
from tcard.sources import registry
from tcard.sources.pf2 import cards, cache, macros

FIXTURES = pathlib.Path(__file__).parent / "fixtures" / "pf2"

FILES = {
    "spell": "spell-fireball.json",
    "feat": "feat-toughness.json",
    "equipment": "equipment-longsword.json",
    "ancestry": "ancestry-dwarf.json",
    "deity": "deity-sarenrae.json",
    "monster": "npc-goblin-warrior.json",
    "condition": "condition-prone.json",
}


def _load(name: str):
    return json.loads((FIXTURES / name).read_text())


def _item(kind: str) -> dict:
    return _load(FILES[kind])


def _card(kind: str):
    return cards.to_card(_item(kind))


def _text(card) -> str:
    return render(layout(card, 32))


def test_fireball_spell_card():
    card = _card("spell")
    fields = dict(card.fields)
    assert card.title == "Fireball"
    assert card.subtitle == "Spell 3"
    assert fields["Traditions"] == "Arcane, Primal"
    assert fields["Cast"] == "2 actions"
    assert fields["Range"] == "500 feet"
    assert fields["Area"] == "20-foot burst"
    assert fields["Defense"] == "Basic Reflex save"
    headings = [heading for heading, _ in card.sections]
    assert any("Heightened" in heading for heading in headings)


def test_toughness_feat_card():
    card = _card("feat")
    fields = dict(card.fields)
    assert card.title == "Toughness"
    assert card.subtitle == "General Feat 1"
    assert fields["Traits"] == "General"
    assert "Source" not in fields
    assert card.sections and card.sections[0][1]


def test_longsword_equipment_card():
    card = _card("equipment")
    fields = dict(card.fields)
    assert card.title == "Longsword"
    assert fields["Price"] == "1 gp"
    assert fields["Damage"] == "1d8 slashing"
    assert fields["Bulk"] == "1"


def test_dwarf_ancestry_card():
    card = _card("ancestry")
    fields = dict(card.fields)
    assert card.subtitle == "Ancestry"
    assert fields["HP"] == "10"
    assert fields["Speed"] == "20"
    assert fields["Boosts"] == "CON, WIS, free"
    assert fields["Flaws"] == "CHA"


def test_sarenrae_deity_card():
    card = _card("deity")
    fields = dict(card.fields)
    assert card.title == "Sarenrae"
    assert card.subtitle == "Deity"
    assert fields["Domains"] == "Fire, Healing, Sun, Truth"
    assert fields["Divine Font"] == "Heal"


def test_goblin_monster_stat_block():
    card = _card("monster")
    fields = dict(card.fields)
    assert card.subtitle == "Creature 0"
    assert fields["AC"] == "16"
    assert fields["HP"] == "6"
    assert fields["Skills"].startswith("Acrobatics +5")
    assert fields["Traits"] == "Small, Goblin, Humanoid"
    table = card.sections[0][1][0]
    assert table.header is True
    assert table.rows[0][:3] == ["STR", "DEX", "CON"]


def test_prone_condition_card():
    card = _card("condition")
    assert card.title == "Prone"
    assert card.subtitle == "Condition"
    assert card.sections and "Off Guard" in card.sections[0][1][0]


def test_uuid_macro_uses_its_label():
    assert macros.expand("You are @UUID[Compendium.pf2e.conditionitems.Item.Off-Guard]{off-guard}.") == (
        "You are off-guard."
    )


def test_bare_uuid_macro_uses_the_last_segment():
    assert macros.expand("@UUID[Compendium.pf2e.spells-srd.Item.Fireball]") == "Fireball"


def test_damage_and_check_macros():
    assert macros.expand("@Damage[2d6[fire]]") == "2d6 fire"
    assert "DC 20" in macros.expand("@Check[type:reflex|dc:20]")


def test_check_macro_names_the_bare_statistic_token():
    assert macros.expand("@Check[thievery|dc:20]") == "DC 20 Thievery"
    assert macros.expand("@Check[deception|dc:28|name:Confound the Haunt]") == "DC 28 Deception"
    assert macros.expand("@Check[flat|dc:11]") == "DC 11 Flat Check"
    assert macros.expand("@Check[will]") == "Will"


def test_template_macro_reads_distance():
    assert macros.expand("@Template[type:burst|distance:20]") == "20-foot burst"


def test_fixture_cards_render_clean_at_32_columns():
    for kind in FILES:
        text = _text(_card(kind))
        assert max(len(line) for line in text.splitlines()) <= 32, kind
        assert "<" not in text and ">" not in text, kind
        assert "@" not in text, kind
        assert "{" not in text and "}" not in text, kind


def test_registry_exposes_pf2():
    assert "pf:2e" in registry.systems()
    assert registry.resolve("pf2") == "pf:2e"
    kinds = registry.kinds("pf:2e")
    assert "spell" in kinds and "monster" in kinds
    assert len(kinds) == 13


def test_pack_kind_records_read_every_json_file():
    paths = [FIXTURES / name for name in FILES.values()]
    with mock.patch.object(cache, "files", lambda packs, refresh=False: paths):
        records = registry.kinds("pf:2e")["spell"].records()
    assert len(records) == len(paths)
    assert all(isinstance(record["path"], pathlib.Path) for record in records)


def test_pack_kind_card_loads_the_record_path():
    record = {"name": "Fireball", "path": FIXTURES / FILES["spell"]}
    with mock.patch.object(cache, "load", lambda path: json.loads(pathlib.Path(path).read_text())):
        card = registry.kinds("pf:2e")["spell"].card(record)
    assert card.title == "Fireball"


def test_hazard_card_reads_the_details_block():
    item = {"name": "Confounding Betrayal", "system": {
        "details": {"isComplex": True, "level": {"value": 8},
                    "description": "<p>Allies appear.</p>",
                    "disable": "<p>@Check[deception|dc:28] twice.</p>",
                    "reset": "<p>Resets at dawn.</p>"},
        "attributes": {"ac": {"value": 10}, "hp": {"max": 0}, "hardness": 0,
                       "stealth": {"value": 21, "details": "<p>(expert)</p>"}},
        "saves": {"fortitude": {"value": 0}, "reflex": {"value": 0}, "will": {"value": 0}},
        "traits": {"value": ["haunt"], "rarity": "common"}}}
    card = cards.hazard(item)
    fields = dict(card.fields)
    assert card.subtitle == "Hazard 8"
    assert fields["Complexity"] == "Complex"
    assert fields["Stealth"] == "21 (expert)"
    assert fields["AC"] == "10"
    assert "HP" not in fields and "Saves" not in fields
    body = card.sections[0][1]
    assert body[0] == "Allies appear."
    assert body[1] == "Disable: DC 28 Deception twice."
    assert body[2] == "Reset: Resets at dawn."
