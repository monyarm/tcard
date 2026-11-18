import json
import pathlib
import unittest.mock as mock

from tcard.sources.fivee import klass

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


def _load(rel: str, refresh: bool = False):
    return json.loads((FIXTURES / rel).read_text())


def _records():
    with mock.patch.object(klass.cache, "load_json", _load):
        return klass.records()


def _kind():
    with mock.patch.object(klass.cache, "load_json", _load):
        return klass.ClassAbilityKind()


def test_records_merge_base_and_subclass():
    names = {record["name"] for record in _records()}
    assert {"Second Wind", "Action Surge", "Assassinate", "Improved Critical"} <= names


def test_card_fields():
    records = _records()
    record = next(r for r in records if r["name"] == "Second Wind" and r["source"] == "PHB")
    card = klass.to_card(record)
    assert card.subtitle == "Fighter"
    assert dict(card.fields)["Level"] == "1"


def test_subclass_card_subtitle():
    records = _records()
    record = next(r for r in records if r["name"] == "Assassinate")
    card = klass.to_card(record)
    assert card.subtitle == "Rogue (Assassin)"
    assert dict(card.fields)["Level"] == "3"


def test_match_class_and_feature():
    kind = _kind()
    hits = kind.matches(_records(), "fighter:second_wind")
    assert hits and all(hit["name"] == "Second Wind" for hit in hits)


def test_match_class_subclass_feature():
    kind = _kind()
    hits = kind.matches(_records(), "rogue:assassin:assassinate")
    assert hits and all(hit["name"] == "Assassinate" for hit in hits)


def test_match_subclass_then_feature():
    kind = _kind()
    assert kind.matches(_records(), "assassin:assassinate")


def test_match_bare_feature():
    kind = _kind()
    assert kind.matches(_records(), "assassinate")


def test_wrong_class_does_not_match():
    kind = _kind()
    assert kind.matches(_records(), "wizard:second_wind") == []
