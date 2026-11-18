"""Kind: one content type. Adding a kind means one object in a system package."""

from __future__ import annotations

from ..model import Card
from ..names import normalize


class Kind:
    id = ""

    def records(self, refresh: bool = False) -> list[dict]:
        raise NotImplementedError

    def card(self, record: dict) -> Card:
        raise NotImplementedError

    def key(self, record: dict) -> str:
        return normalize(str(record.get("name", "")))

    def display(self, record: dict) -> str:
        return str(record.get("name", "?"))

    def matches(self, records: list[dict], query: str) -> list[dict]:
        wanted = normalize(query)
        exact = [record for record in records if self.key(record) == wanted]
        if exact:
            return exact
        return [record for record in records if self.key(record).startswith(wanted)]
