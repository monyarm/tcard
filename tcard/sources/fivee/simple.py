"""A Kind built from a loader and a card builder."""

from __future__ import annotations

from ...model import Card
from ..base import Kind


class SimpleKind(Kind):
    def __init__(self, kind_id: str, loader, builder) -> None:
        self.id = kind_id
        self._loader = loader
        self._builder = builder

    def records(self, refresh: bool = False) -> list[dict]:
        return self._loader(refresh)

    def card(self, record: dict) -> Card:
        return self._builder(record)
