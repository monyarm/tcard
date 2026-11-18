"""5e.tools content kinds."""

from __future__ import annotations

from ...model import Card
from ..base import Kind
from . import index, spell

SYSTEM_ID = "dnd:5e"
ALIASES = ("5e",)


class SpellKind(Kind):
    id = "spell"

    def records(self, refresh: bool = False) -> list[dict]:
        return index.spell_records(refresh)

    def card(self, record: dict) -> Card:
        return spell.to_card(record)


KINDS = {"spell": SpellKind()}
