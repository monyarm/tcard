"""V20 merits and flaws from the Storyteller System list page."""

from __future__ import annotations

import re

from ...model import Card
from ...names import normalize, split_path
from ..base import Kind
from . import cache, wiki

PAGE = "List of Merits and Flaws (Storyteller System)"
SIDES = {"Merits": "merit", "Flaws": "flaw"}
ENTRY = re.compile(r"^'''(.+?)'''\s*(.*)$")


def _group(heading: str) -> str:
    return normalize(re.sub(r"<[^>]+>|'''", "", heading))


def records(refresh: bool = False) -> list[dict]:
    markdown = cache.wikitext(PAGE, refresh) or ""
    out: list[dict] = []
    side = ""
    group = ""
    for level, title, body in wiki.sections(markdown):
        if level == 2:
            side = SIDES.get(title, "")
            group = ""
            continue
        if not side:
            continue
        group = _group(title) if level == 3 else group
        for heading, table in wiki.tables("\n".join(body)):
            columns = [wiki.text(cell) for cell in table.rows[0]]
            if "Title" not in columns:
                continue
            for row in table.rows[1:]:
                values = dict(zip(columns, row))
                name = values.get("Title", "")
                if name:
                    out.append({"name": name, "side": side, "group": group,
                                "text": values.get("Description", "")})
        for line in body:
            raw = line.strip()
            match = ENTRY.match(raw)
            if not match:
                continue
            out.append({"name": wiki.text(match.group(1)), "side": side, "group": group,
                        "text": re.sub(r"^\([^)]*\)\s*", "", wiki.text(match.group(2)))})
    return [row for row in out if row["name"]]


def to_card(record: dict) -> Card:
    label = "Merit" if record["side"] == "merit" else "Flaw"
    subtitle = f"{label} ({record['group'].title()})" if record["group"] else label
    return Card(record["name"], subtitle, [], [("", [record["text"]])] if record["text"] else [])


class AdvantageKind(Kind):
    def __init__(self, side: str) -> None:
        self.id = side

    def records(self, refresh: bool = False) -> list[dict]:
        return [row for row in records(refresh) if row["side"] == self.id]

    def card(self, record: dict) -> Card:
        return to_card(record)

    def display(self, record: dict) -> str:
        return f"{record['name']} ({self.id.title()})"

    def matches(self, records: list[dict], query: str) -> list[dict]:
        parts = split_path(query)
        if len(parts) == 2:
            pool = [r for r in records if normalize(r["group"]) == parts[0]]
            if pool:
                return super().matches(pool, parts[1])
        return super().matches(records, query)
