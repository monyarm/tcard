"""V20 rituals: seven tradition list pages, two different layouts."""

from __future__ import annotations

import re

from ...model import Card
from ...names import normalize, split_path
from ..base import Kind
from . import cache, wiki

LISTS = {
    "Thaumaturgy": "List of Thaumaturgy Rituals",
    "Necromancy": "List of Necromancy Rituals",
    "Akhu": "List of Akhu Rituals",
    "Anarch": "List of Anarch Rituals",
    "Dur-An-Ki": "List of Dur-An-Ki Rituals",
    "Koldunic": "List of Koldunic Rituals",
    "Sadhana": "List of Sadhana Rituals",
}
LEVEL = re.compile(r"(?i)\b(?:rank|level)\s*(\d)")
FIELDS = ("Ingredients", "Process", "Effect", "Developer")


def _level(heading: str) -> int:
    match = LEVEL.search(heading)
    return int(match.group(1)) if match else 0


def _table_rituals(heading: str, table, tradition: str) -> list[dict]:
    columns = [wiki.text(cell) for cell in table.rows[0]]
    if "Name" not in columns:
        return []
    out = []
    for row in table.rows[1:]:
        if not any(row):
            continue
        values = dict(zip(columns, row))
        name = values.get("Name", "")
        if not name:
            continue
        out.append({
            "name": name,
            "tradition": tradition,
            "level": _level(heading),
            "fields": {key: values.get(key, "") for key in FIELDS},
        })
    return out


def _bullet_rituals(markdown: str, tradition: str) -> list[dict]:
    out = []
    for level, name, effect in wiki.dot_bullets(markdown):
        out.append({
            "name": name,
            "tradition": tradition,
            "level": level,
            "fields": {"Effect": effect},
        })
    return out


def records(refresh: bool = False) -> list[dict]:
    out: list[dict] = []
    for tradition, page in LISTS.items():
        markdown = cache.wikitext(page, refresh) or ""
        rows = []
        for heading, table in wiki.tables(markdown):
            rows.extend(_table_rituals(heading, table, tradition))
        if not rows:
            rows = _bullet_rituals(markdown, tradition)
        out.extend(row for row in rows if row["name"])
    return out


def to_card(record: dict) -> Card:
    fields = []
    if record["level"]:
        fields.append(("Level", str(record["level"])))
    for key in ("Ingredients", "Process", "Developer"):
        value = record["fields"].get(key, "")
        if value:
            fields.append((key, value))
    effect = record["fields"].get("Effect", "")
    return Card(record["name"], f"{record['tradition']} Ritual", fields,
                [("", [effect])] if effect else [])


class RitualKind(Kind):
    def __init__(self) -> None:
        self.id = "ritual"

    def records(self, refresh: bool = False) -> list[dict]:
        return records(refresh)

    def card(self, record: dict) -> Card:
        return to_card(record)

    def display(self, record: dict) -> str:
        return f"{record['name']} ({record['tradition']})"

    def matches(self, records: list[dict], query: str) -> list[dict]:
        parts = split_path(query)
        if len(parts) > 1:
            *prefix, wanted = parts
            keys = {normalize(part) for part in prefix}
            pool = [r for r in records if normalize(r["tradition"]) in keys]
            if pool:
                return super().matches(pool, wanted)
        return super().matches(records, query)
