"""Whole-subclass cards: every feature of a subclass, grouped by level."""

import json
import pathlib
import unittest.mock as mock

from tcard.names import split_path
from tcard.sources.fivee import subclass

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


def _load(rel: str, refresh: bool = False):
    return json.loads((FIXTURES / rel).read_text())


def _records():
    with mock.patch.object(subclass.cache, "load_json", _load):
        return subclass.records()


def test_one_record_per_subclass():
    records = _records()
    names = {(record["className"], record["name"]) for record in records}
    assert ("Rogue", "Assassin") in names
    assert ("Fighter", "Champion") in names


def test_card_groups_features_by_level():
    record = next(r for r in _records() if r["name"] == "Assassin")
    card = subclass.to_card(record)
    assert card.title == "Assassin"
    assert card.subtitle == "Rogue Subclass"
    headings = [heading for heading, _ in card.sections]
    assert any(heading.startswith("Level 3: Assassinate") for heading in headings)


def test_matches_by_class_prefix():
    records = _records()
    kind = subclass.SubclassKind()
    found = kind.matches(records, "assassin")
    assert {r["name"] for r in found} == {"Assassin"}
    assert {r["source"] for r in found} == {"PHB", "XPHB"}
    assert {r["name"] for r in kind.matches(records, "rogue:assassin")} == {"Assassin"}
    assert kind.matches(records, "wizard:assassin") == []


def test_split_path_keeps_class_and_name():
    assert split_path("rogue:assassin") == ["rogue", "assassin"]
