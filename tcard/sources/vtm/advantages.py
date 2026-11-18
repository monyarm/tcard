"""Merits and flaws, which share one wiki page of paired tables."""

from __future__ import annotations

import re

from ...model import Card
from ...names import normalize, split_path
from ..base import Kind
from . import cache, md, pack

INDEX = "Advantages_and_Flaws"


def group_id(heading: str) -> str:
    """`Substance Use` -> `substance_use`, `Archaic Flaws` -> `archaic_flaw`."""
    words = []
    for word in re.split(r"[^a-z0-9]+", heading.lower()):
        if not word:
            continue
        if word.endswith("ies") and len(word) > 4:
            word = word[:-3] + "y"
        elif word.endswith("ses") or word.endswith("xes") or word.endswith("ches"):
            word = word[:-2]
        elif word.endswith("s") and not word.endswith(("ss", "us", "is")):
            word = word[:-1]
        words.append(word)
    return "_".join(words)


def _rows(table, section: str) -> list[dict]:
    """Split a paired table into one entry per side."""
    header = [md.text(cell).lower() for cell in table.rows[0]]
    out: list[dict] = []
    for row in table.rows[1:]:
        if not any(row):
            continue
        for side in ("merits", "flaws"):
            if side not in header:
                continue
            start = header.index(side)
            name = row[start].strip() if start < len(row) else ""
            if not name:
                continue
            dots_at = start + 1 if start + 1 < len(header) and "dot" in header[start + 1] else None
            dots = row[dots_at] if dots_at is not None and dots_at < len(row) else ""
            text_at = (dots_at + 1) if dots_at is not None else start + 1
            text = row[text_at] if text_at < len(row) else ""
            out.append({
                "name": name,
                "group": group_id(section),
                "dots": dots,
                "text": text,
                "kind": "merit" if side == "merits" else "flaw",
            })
    return out


def records(refresh: bool = False) -> list[dict]:
    markdown = cache.page(INDEX, refresh)
    head, _, tail = markdown.partition("\n## Backgrounds and Flaws")
    out: list[dict] = []
    for section, table in md.tables(head):
        out.extend(_rows(table, section))
    # Backgrounds reuse the merit table shape, so the row named after its own
    # heading is the background itself. Merits listed beside it (Zeroed under
    # Mask) are still merits.
    for section, table in md.tables("## Backgrounds and Flaws" + tail):
        out.extend(record for record in _rows(table, section)
                   if normalize(record["name"]) != normalize(section))
    return out


def to_card(record: dict) -> Card:
    fields = [("Dots", md.dots(record["dots"]))] if md.rating(record["dots"]) else []
    # The wiki keeps only the opening clause of a merit, so the book's own text
    # comes from the pack when it has the entry.
    extra = pack.feature(record["name"]) or {}
    body = [line for line in extra.get("prose") or [] if line] or [record["text"]]
    subtitle = f"{record['kind'].title()} ({record['group'].replace('_', ' ').title()})"
    return Card(record["name"], subtitle, fields, [("", body)] if any(body) else [])


class AdvantageKind(Kind):
    """One kind per side: merits and flaws are separate lookups."""

    def __init__(self, side: str) -> None:
        self.id = side

    def records(self, refresh: bool = False) -> list[dict]:
        return [record for record in records(refresh) if record["kind"] == self.id]

    def card(self, record: dict) -> Card:
        return to_card(record)

    def display(self, record: dict) -> str:
        return f"{record['name']} ({record['group'].replace('_', ' ').title()})"

    def matches(self, records: list[dict], query: str) -> list[dict]:
        parts = split_path(query)
        if len(parts) == 1:
            # A group on its own lists that group, for `--all look`.
            pool = [r for r in records if r["group"] == parts[0]]
            if pool:
                return pool
        if len(parts) == 2:
            pool = [r for r in records if r["group"] == parts[0]]
            if pool:
                return super().matches(pool, parts[1])
        return super().matches(records, query)
