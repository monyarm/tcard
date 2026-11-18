import json
from pathlib import Path

from tcard.model import Table
from tcard.render.layout import layout
from tcard.render.text import render
from tcard.sources import registry
from tcard.sources.fivee import monster
from tcard.sources.fivee.tags import render_tags

FIXTURES = Path(__file__).parent / "fixtures"


def _records():
    return {record["name"] + " " + record["source"]: record for record in json.loads((FIXTURES / "bestiary.json").read_text())}


def test_goblin_stat_block():
    card = monster.to_card(_records()["Goblin MM"])
    assert card.title == "Goblin"
    assert card.subtitle == "Small, humanoid (goblinoid), neutral evil"
    fields = dict(card.fields)
    assert fields["AC"] == "15 (leather armor, shield)"
    assert fields["HP"] == "7 (2d6)"
    assert fields["Speed"] == "30 ft."
    assert fields["Senses"] == "darkvision 60 ft., passive Perception 9"
    assert fields["CR"] == "1/4"
    assert "Source" not in fields


def test_ability_tables_are_tables():
    card = monster.to_card(_records()["Goblin MM"])
    rows = [part for part in card.sections[0][1] if isinstance(part, Table)]
    assert len(rows) == 2
    assert rows[0].rows == [["STR", "DEX", "CON"], ["8 (-1)", "14 (+2)", "10 (+0)"]]
    assert rows[1].rows[0] == ["INT", "WIS", "CHA"]


def test_feature_text_resolves_tags():
    card = monster.to_card(_records()["Goblin MM"])
    headings = dict(card.sections)
    assert headings["Traits"][0].startswith("Nimble Escape. The goblin")
    action = headings["Actions"][0]
    assert "Melee Weapon Attack: +4 to hit" in action
    assert "5 (1d6 + 2) slashing damage" in action
    assert "{" not in "".join(action)


def test_dragon_sections_and_recharge():
    card = monster.to_card(_records()["Adult Black Dragon XMM"])
    fields = dict(card.fields)
    assert fields["AC"] == "19"
    assert fields["HP"] == "195 (17d12 + 85)"
    assert fields["Damage Immunities"] == "acid"
    headings = dict(card.sections)
    assert "Legendary Actions" in headings
    breath = next(part for part in headings["Actions"] if "Acid Breath" in part)
    assert breath.startswith("Acid Breath Recharge 5-6.")


def test_bestiary_renders_clean_at_32():
    for record in json.loads((FIXTURES / "bestiary.json").read_text()):
        output = render(layout(monster.to_card(record), 32))
        assert output.isascii()
        assert max(len(line) for line in output.splitlines()) <= 32
        assert "{" not in output and "@" not in output


def test_hp_and_scores_tolerate_odd_shapes():
    assert monster._hp({"hp": {"special": "See below"}}) == "See below"
    assert monster._hp({"hp": {"formula": "3d8"}}) == "3d8"
    assert monster._hp({"hp": 12}) == "12"
    assert monster._score({"value": 17}) == 17
    assert monster._score(9) == 9
    assert monster._score(None) is None


def test_render_tags_monster_tags():
    assert render_tags("{@atk mw,rw}") == "Melee or Ranged Weapon Attack:"
    assert render_tags("{@atkr m}") == "Melee Attack Roll:"
    assert render_tags("{@recharge 5}") == "Recharge 5-6"
    assert render_tags("{@recharge}") == "Recharge 6"
    assert render_tags("{@h}13 ({@damage 2d6 + 6})") == "Hit: 13 (2d6 + 6)"
    assert render_tags("{@actSave dex} {@dc 18}, each") == "Dexterity Saving Throw: DC 18, each"


def test_monster_kind_is_registered():
    assert "monster" in registry.kinds("dnd:5e")
    assert registry.kinds("dnd:5e")["monster"].id == "monster"
