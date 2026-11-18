"""Every fixture record must render at the default width without dropping out of ASCII."""

import json
import pathlib
import unittest.mock as mock

from tcard.render.layout import layout
from tcard.sources.fivee import cache, feats, items, klass, optional, spell

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


def _load(rel: str, refresh: bool = False):
    return json.loads((FIXTURES / rel).read_text())


def _cards():
    with mock.patch.object(cache, "load_json", _load):
        fireball = json.loads((FIXTURES / "fireball-xphb.json").read_text())
        cards = [spell.to_card(fireball)]
        cards += [items.to_card(record) for record in items.records()]
        cards += [klass.to_card(record) for record in klass.records()]
        cards += [optional.to_card(record) for record in optional.records()]
        cards += [feats.to_card(record) for record in feats.records()]
    return cards


def test_every_fixture_renders_ascii_at_32_columns():
    cards = _cards()
    assert len(cards) > 6
    for card in cards:
        lines = layout(card, 32)
        assert lines
        for line in lines:
            assert line.text.isascii(), line.text
            assert len(line.text) <= 32, line.text
