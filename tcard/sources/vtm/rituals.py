"""Blood Sorcery rituals and Oblivion ceremonies: one table row each."""

from __future__ import annotations

import re

from ...model import Card
from ...names import normalize, split_path
from ..base import Kind
from . import cache, md

PAGES = {"Blood Sorcery": "Blood_Sorcery_Rituals", "Oblivion": "Oblivion_Ceremonies"}
KEY_FIELDS = ("Cost", "Origin", "Pre-requisite", "Ritual Roll")


def _rows(markdown: str, discipline: str) -> list[dict]:
    out: list[dict] = []
    for section, table in md.tables(markdown):
        match = re.fullmatch(r"Level (\d)", section)
        if not match:
            continue
        level = int(match.group(1))
        columns = [md.text(cell) for cell in table.rows[0]]
        for row in table.rows[1:]:
            if not any(row):
                continue
            values = dict(zip(columns, row))
            name = values.get("Name", "").strip()
            if not name:
                continue
            out.append({
                "name": name,
                "discipline": discipline,
                "level": level,
                "fields": {key: values.get(key, "") for key in KEY_FIELDS},
                "text": values.get("Effect", ""),
                "notes": values.get("Additional Notes", ""),
            })
    return out


def records(refresh: bool = False) -> list[dict]:
    out: list[dict] = []
    for discipline, page in PAGES.items():
        out.extend(_rows(cache.page(page, refresh), discipline))
    return out


def to_card(record: dict) -> Card:
    fields = [("Level", str(record["level"]))]
    fields += [(key, value) for key, value in record["fields"].items() if value and value.lower() != "none"]
    body = [text for text in (record["text"], record["notes"]) if text]
    return Card(record["name"], f"{record['discipline']} Ritual", fields, [("", body)] if body else [])


class RitualKind(Kind):
    def __init__(self) -> None:
        self.id = "ritual"

    def records(self, refresh: bool = False) -> list[dict]:
        return records(refresh)

    def card(self, record: dict) -> Card:
        return to_card(record)

    def display(self, record: dict) -> str:
        return f"{record['name']} ({record['discipline']})"

    def matches(self, records: list[dict], query: str) -> list[dict]:
        parts = split_path(query)
        if len(parts) > 1:
            *prefix, wanted = parts
            keys = {normalize(part) for part in prefix}
            pool = [r for r in records if normalize(r["discipline"]) in keys]
            if pool:
                return super().matches(pool, wanted)
        return super().matches(records, query)
