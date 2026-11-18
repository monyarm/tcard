"""Pathfinder 1e via d20pfsrd."""

from __future__ import annotations

from ...model import Card
from ..base import Kind
from . import cache, spell

SYSTEM_ID = "pf:1e"
ALIASES = ("pf1",)


class SpellKind(Kind):
    id = "spell"

    def records(self, refresh: bool = False) -> list[dict]:
        return cache.index(refresh)

    def card(self, record: dict) -> Card:
        return spell.to_card(record)


KINDS = {"spell": SpellKind()}
