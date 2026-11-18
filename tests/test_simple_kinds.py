import json
import pathlib
import unittest.mock as mock

from tcard.sources.fivee import actions, backgrounds, cache, conditions, feats, optional

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


def _load(rel: str, refresh: bool = False):
    return json.loads((FIXTURES / rel).read_text())


def _with_data(call):
    with mock.patch.object(cache, "load_json", _load):
        return call()


def test_feat_card():
    records = _with_data(feats.records)
    record = next(r for r in records if r["name"] == "Lucky" and r["source"] == "XPHB")
    card = feats.to_card(record)
    assert card.subtitle == "Origin Feat"
    assert dict(card.fields)["Source"] == "XPHB p.201"
    assert card.sections and card.sections[0][1]


def test_condition_card():
    records = _with_data(conditions.records)
    record = next(r for r in records if r["name"] == "Prone")
    card = conditions.to_card(record)
    assert card.subtitle == "Condition"
    assert card.sections


def test_action_card_has_time():
    records = _with_data(actions.records)
    record = next(r for r in records if r["name"] == "Dash")
    card = actions.to_card(record)
    assert card.subtitle == "Action"
    assert dict(card.fields)["Time"] == "1 action"


def test_background_card():
    records = _with_data(backgrounds.records)
    record = next(r for r in records if r["name"] == "Acolyte" and r["source"] == "XPHB")
    card = backgrounds.to_card(record)
    assert card.subtitle == "Background"
    assert dict(card.fields)["Source"] == "XPHB p.178"
    assert card.sections and card.sections[0][1]


def test_background_picks_2014_record_too():
    records = _with_data(backgrounds.records)
    record = next(r for r in records if r["name"] == "Soldier")
    card = backgrounds.to_card(record)
    assert card.subtitle == "Background"
    assert dict(card.fields)["Source"].startswith("PHB")


def test_optional_labels_and_prerequisites():
    records = _with_data(optional.records)
    blast = next(r for r in records if r["name"] == "Agonizing Blast")
    card = optional.to_card(blast)
    assert card.subtitle == "Eldritch Invocation"
    assert "spell" in dict(card.fields).get("Prerequisite", "")


def test_optional_kinds_filter_by_feature_type():
    kind = optional.OptionalKind("fighting_style", optional.KINDS["fighting_style"])
    names = {record["name"] for record in _with_data(kind.records)}
    assert "Archery" in names
    assert "Trip Attack" not in names

    invocation = optional.OptionalKind("invocation", optional.KINDS["invocation"])
    names = {record["name"] for record in _with_data(invocation.records)}
    assert names == {"Agonizing Blast"}
