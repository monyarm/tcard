"""d20pfsrd spell page to Card."""

from __future__ import annotations

from ...model import Card
from .page import parse  # re-exported for tests and callers
from . import page

__all__ = ["parse", "to_card"]


def to_card(record: dict, refresh: bool = False) -> Card:
    return page.to_card(record, refresh, spell=True)
