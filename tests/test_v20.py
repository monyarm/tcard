"""V20 cards: disciplines, clans, bloodlines, rituals, paths, merits, flaws."""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest import mock

from tcard.render.layout import layout
from tcard.render.text import render
from tcard.sources import registry
from tcard.sources.v20 import advantages, cache, disciplines, kindred, paths, rituals, wiki

FIXTURES = Path(__file__).parent / "fixtures" / "v20"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text()


def _page(mapping: dict[str, str]):
    def load(title: str, refresh: bool = False) -> str | None:
        return mapping.get(title)
    return load


def _category(mapping: dict[str, list[str]]):
    def load(name: str, refresh: bool = False) -> list[str]:
        return mapping.get(name, [])
    return load


def test_discipline_card_lists_powers_with_effects() -> None:
    with mock.patch.object(cache, "wikitext", _page({"Auspex (VTM)": _read("auspex.txt")})), \
         mock.patch.object(cache, "category", _category({"Discipline (VTM)": ["Auspex (VTM)"]})):
        records = disciplines.records()
        card = disciplines.to_card(records[0])
    assert card.title == "Auspex"
    assert card.subtitle == "Discipline"
    assert card.sections[0][0].startswith("Level 1 ")
    assert card.sections[0][1][0] == "- Heightened Senses: Sample prose for testing."
    assert card.sections[1][0].startswith("Level 3 ")


def test_discipline_power_by_path() -> None:
    kind = disciplines.DisciplineKind()
    with mock.patch.object(cache, "wikitext", _page({"Auspex (VTM)": _read("auspex.txt")})), \
         mock.patch.object(cache, "category", _category({"Discipline (VTM)": ["Auspex (VTM)"]})):
        records = kind.records()
        found = kind.matches(records, "auspex:the_spirits_touch")
    assert [record["name"] for record in found] == ["The Spirit's Touch"]
    card = kind.card(found[0])
    assert card.subtitle == "Auspex " + "\u25cf" * 3 + "\u25cb" * 2
    assert card.sections[0][1] == ["Sample prose for testing."]


def test_clan_card_and_parts() -> None:
    kind = kindred.KindredKind("clan", "Clans (VTM)", "Clan", set())
    with mock.patch.object(cache, "wikitext", _page({"Brujah": _read("brujah.txt")})), \
         mock.patch.object(cache, "category", _category({"Clans (VTM)": ["Brujah"]})):
        records = kind.records()
        card = kind.card(records[0])
        bane = kind.matches(records, "brujah:bane")[0]
        banes = kind.matches(records, "brujah:banes")[0]
        compulsion = kind.matches(records, "brujah:compulsion")[0]
        bane_card = kind.card(bane)
        banes_card = kind.card(banes)
        compulsion_card = kind.card(compulsion)
    assert card.title == "Brujah"
    assert card.subtitle == "Clan"
    assert dict(card.fields)["Disciplines"] == "Celerity, Potence, Presence"
    assert dict(card.fields)["Nicknames"] == "Agitators, Rebels"
    headings = [heading for heading, _ in card.sections]
    assert headings == ["Overview", "Banes", "Compulsion"]
    assert bane_card.title == "Violent Temper"
    assert bane_card.subtitle == "Brujah Bane"
    assert len(banes_card.sections) == 2
    assert banes_card.sections[1][0] == "Violence"
    assert compulsion_card.title == "Rebellion"


def test_clan_lore_part_prints_the_whole_page() -> None:
    kind = kindred.KindredKind("clan", "Clans (VTM)", "Clan", set())
    with mock.patch.object(cache, "wikitext", _page({"Brujah": _read("brujah.txt")})), \
         mock.patch.object(cache, "category", _category({"Clans (VTM)": ["Brujah"]})):
        records = kind.records()
        lore = kind.card(kind.matches(records, "brujah:lore")[0])
        history = kind.matches(records, "brujah:history")
    assert lore.subtitle == "Lore"
    assert [heading for heading, _ in lore.sections] == ["Overview", "Banes", "Compulsion"]
    assert lore.sections[0][1] == ["Sample prose for testing."]
    assert lore.sections[1][1] == [
        "- Violent Temper: Sample prose for testing.",
        "- Variant — Violence: Sample prose for testing.",
    ]
    assert history[0]["part"] == ("lore",)


def test_clan_without_overview_opens_with_its_history() -> None:
    markup = ("==History==\nThe clan is old.\n\n===Dark Ages===\nThe clan woke in the dark.\n\n"
              "==Members==\n* Someone\n\n==References==\n<ref>book</ref>\n")
    card = kindred.build(markup, "Clan", "Cappadocian")
    assert card.sections[0] == ("Overview", ["The clan is old."])
    assert [heading for heading, _ in kindred.lore(markup)] == ["History", "Dark Ages"]


def test_bloodline_uses_the_same_shape() -> None:
    kind = kindred.KindredKind("bloodline", "Bloodlines (VTM)", "Bloodline", set())
    with mock.patch.object(cache, "wikitext", _page({"Brujah": _read("brujah.txt")})), \
         mock.patch.object(cache, "category", _category({"Bloodlines (VTM)": ["Brujah"]})):
        card = kind.card(kind.records()[0])
    assert card.subtitle == "Bloodline"
    assert dict(card.fields)["Faction"].startswith("Camarilla")


def test_ritual_table_format() -> None:
    with mock.patch.object(cache, "wikitext", _page({"List of Thaumaturgy Rituals": _read("rituals-thaumaturgy.txt")})), \
         mock.patch.object(rituals, "LISTS", {"Thaumaturgy": "List of Thaumaturgy Rituals"}):
        records = rituals.records()
    assert [record["name"] for record in records] == [
        "Bind the Accusing Tongue", "Blood Contract", "Principal Focus of Vitae Infusion"]
    assert records[0]["level"] == 1
    assert records[2]["level"] == 2
    card = rituals.to_card(records[0])
    assert card.subtitle == "Thaumaturgy Ritual"
    assert dict(card.fields)["Ingredients"] == "A lock of hair and a black silk cord"
    assert card.sections[0][1] == ["Sample cell."]


def test_ritual_table_keeps_pipes_inside_links() -> None:
    markup = ("{| class=\"wikitable\"\n! Name\n! Ingredients\n! Effect\n! Developer\n|-\n"
              "|'''Heart of Stone'''\n| A stone floor, a candle\n"
              "| The heart becomes stone, costing the caster [[Humanity (VTM)|Humanity]].\n"
              "|[[Clan (VTM)|Clan]] [[Tremere (VTM)|Tremere]]\n|}\n")
    table = wiki.tables(markup)[0][1]
    assert table.rows[1] == ["Heart of Stone", "A stone floor, a candle",
                            "The heart becomes stone, costing the caster Humanity.",
                            "Clan Tremere"]


def test_ritual_bullet_format_and_path_lookup() -> None:
    kind = rituals.RitualKind()
    with mock.patch.object(cache, "wikitext", _page({"List of Necromancy Rituals": _read("rituals-necromancy.txt")})), \
         mock.patch.object(rituals, "LISTS", {"Necromancy": "List of Necromancy Rituals"}):
        records = kind.records()
        found = kind.matches(records, "necromancy:knowing_stone")
    assert len(records) == 3
    assert [record["level"] for record in records] == [1, 3, 3]
    assert [record["name"] for record in found] == ["Knowing Stone"]
    assert kind.card(found[0]).subtitle == "Necromancy Ritual"


def test_path_card() -> None:
    with mock.patch.object(cache, "wikitext", _page({"Path of Caine": _read("path.txt")})), \
         mock.patch.object(cache, "category", _category({"Paths": ["Path of Caine"]})):
        card = paths.to_card(paths.records()[0])
    assert card.title == "Path of Caine"
    assert card.subtitle == "Path"
    fields = dict(card.fields)
    assert fields["Nickname"] == "Noddists"
    assert fields["Bearing"] == "Faith"
    assert [heading for heading, _ in card.sections] == ["Overview"]


def test_merits_and_flaws() -> None:
    with mock.patch.object(cache, "wikitext", _page({"List of Merits and Flaws (Storyteller System)": _read("merits.txt")})):
        rows = advantages.records()
    merits = [row for row in rows if row["side"] == "merit"]
    flaws = [row for row in rows if row["side"] == "flaw"]
    assert [row["name"] for row in merits] == ["Ability Aptitude", "Ambidextrous", "Favors"]
    assert [row["name"] for row in flaws] == ["Addiction", "Blind"]
    assert [row["group"] for row in flaws] == ["one", "two"]
    card = advantages.to_card(flaws[1])
    assert card.subtitle == "Flaw (Two)"
    assert card.sections[0][1] == ["Sample prose for testing."]


def test_merit_group_address_and_bare_name() -> None:
    kind = advantages.AdvantageKind("flaw")
    with mock.patch.object(cache, "wikitext", _page({"List of Merits and Flaws (Storyteller System)": _read("merits.txt")})):
        records = kind.records()
        grouped = kind.matches(records, "two:blind")
        bare = kind.matches(records, "blind")
    assert [record["name"] for record in grouped] == ["Blind"]
    assert [record["name"] for record in bare] == ["Blind"]


def test_every_card_renders_at_32_columns() -> None:
    cards = []
    with mock.patch.object(cache, "wikitext", _page({
        "Auspex (VTM)": _read("auspex.txt"),
        "Brujah": _read("brujah.txt"),
        "Path of Caine": _read("path.txt"),
        "List of Thaumaturgy Rituals": _read("rituals-thaumaturgy.txt"),
        "List of Merits and Flaws (Storyteller System)": _read("merits.txt"),
    })), mock.patch.object(cache, "category", _category({
        "Discipline (VTM)": ["Auspex (VTM)"],
        "Clans (VTM)": ["Brujah"],
        "Paths": ["Path of Caine"],
    })), mock.patch.object(rituals, "LISTS", {"Thaumaturgy": "List of Thaumaturgy Rituals"}):
        for record in disciplines.records():
            cards.append(disciplines.to_card(record))
        cards.append(kindred.KindredKind("clan", "Clans (VTM)", "Clan", set()).card({"name": "Brujah", "title": "Brujah"}))
        cards.append(paths.to_card({"name": "Path of Caine", "title": "Path of Caine"}))
        cards.extend(rituals.to_card(record) for record in rituals.records())
        cards.extend(advantages.to_card(row) for row in advantages.records())
    assert cards
    for card in cards:
        output = render(layout(card, 32))
        for line in output.splitlines():
            assert len(line) <= 32, line
            assert "<" not in line and "{{" not in line and "[[" not in line, line


def test_registry_knows_v20() -> None:
    assert "vtm:v20" in registry.systems()
    assert registry.resolve("v20") == "vtm:v20"
    kinds = registry.kinds("vtm:v20")
    assert set(kinds) == {"discipline", "clan", "bloodline", "ritual", "path", "merit", "flaw"}


if __name__ == "__main__":
    unittest.main()
