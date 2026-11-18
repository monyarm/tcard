"""VTM disciplines: the overview card plus one card per power."""

from __future__ import annotations

import re

from ...model import Card
from ...names import normalize, split_path
from ... import glyphs
from ..base import Kind
from . import cache, md

INDEX = "Disciplines"
LINK = re.compile(r'\*\*\[([^\]]+)\]\((https://vtm\.paradoxwikis\.com/[^)\s"]+)')
HEADER_FIELDS = ("Type", "Masquerade threat", "Resonance")
POWER_FIELDS = ("Cost", "Prerequisite", "Amalgam", "Duration", "Dice pool", "Opposing pool")
# The rules text of a power, kept out of the field list because it is prose.
POWER_TEXT = ("Effect", "Additional Notes")
PLACEHOLDERS = frozenset(("", "-", "\u2014", "n/a", "none"))
EMPTY_VALUES = ("", "none", "n/a", "no")


def _section(markdown: str, title: str) -> list[str]:
    for name, lines in md.blocks(markdown):
        if name.lower() == title.lower():
            return lines
    return []


def _flavour(markdown: str) -> str:
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("_**") and stripped.endswith("**_"):
            return md.text(stripped)
    return ""


def _header(markdown: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in md.blocks(markdown)[0][1] if md.blocks(markdown) else []:
        pair = md.label(line)
        if pair and pair[0] in HEADER_FIELDS:
            out[pair[0]] = pair[1]
    return out


def _powers(markdown: str) -> list[dict]:
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
                "level": level,
                "fields": {key: values.get(key, "") for key in POWER_FIELDS},
                "text": [values[key] for key in POWER_TEXT
                         if values.get(key, "").strip().lower() not in PLACEHOLDERS],
            })
    return out


def _index(refresh: bool = False) -> list[dict]:
    """Discipline name and page URL from the index table."""
    markdown = cache.page(INDEX, refresh)
    out: list[dict] = []
    seen: set[str] = set()
    for line in markdown.splitlines():
        if not line.startswith("|"):
            continue
        for name, url in LINK.findall(line):
            if name in seen:
                continue
            seen.add(name)
            out.append({"name": name, "url": url})
    return out


def records(refresh: bool = False) -> list[dict]:
    """Every discipline and every power, so both can be looked up by name."""
    out: list[dict] = []
    for entry in _index(refresh):
        markdown = cache.page(entry["url"].rstrip("/").rsplit("/", 1)[-1], refresh)
        out.append({
            "name": entry["name"],
            "url": entry["url"],
            "discipline": entry["name"],
            "header": _header(markdown),
            "flavour": _flavour(markdown),
            "levels": _series(_powers(markdown)),
        })
        for power in _powers(markdown):
            out.append({
                "name": power["name"],
                "url": entry["url"],
                "discipline": entry["name"],
                "level": power["level"],
                "fields": power["fields"],
                "text": power["text"],
            })
    return out


def _series(powers: list[dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for power in powers:
        out.setdefault(str(power["level"]), []).append(power)
    return out


def _discipline_card(record: dict) -> Card:
    fields = [(key, record["header"][key]) for key in HEADER_FIELDS if record["header"].get(key)]
    sections = []
    for level in sorted(record["levels"], key=int):
        bullets = []
        for power in record["levels"][level]:
            effect = (power.get("text") or [""])[0]
            bullets.append(f"- {power['name']}: {effect}" if effect else f"- {power['name']}")
        sections.append((f"Level {level}", bullets))
    return Card(record["name"], record.get("flavour", ""), fields, sections)


def _power_card(record: dict) -> Card:
    fields = []
    for key in POWER_FIELDS:
        value = record["fields"].get(key, "")
        if value and value.lower() not in EMPTY_VALUES:
            fields.append((key, value))
    body = [paragraph for paragraph in record.get("text", []) if paragraph]
    # Powers are level-gated 1-5, so the level reads as pips, like V20.
    subtitle = f"{record['discipline']} {glyphs.DOT * int(record['level'])}"
    return Card(record["name"], subtitle, fields, [("", body)] if body else [])


def to_card(record: dict) -> Card:
    if "levels" in record:
        return _discipline_card(record)
    return _power_card(record)


class DisciplineKind(Kind):
    def __init__(self) -> None:
        self.id = "discipline"

    def records(self, refresh: bool = False) -> list[dict]:
        return records(refresh)

    def card(self, record: dict) -> Card:
        return to_card(record)

    def display(self, record: dict) -> str:
        if "discipline" in record and "levels" not in record:
            return f"{record['name']} ({record['discipline']})"
        return record["name"]

    def matches(self, records: list[dict], query: str) -> list[dict]:
        parts = split_path(query)
        if len(parts) > 1:
            *prefix, wanted = parts
            keys = {normalize(part) for part in prefix}
            pool = [r for r in records if normalize(r.get("discipline", "")) in keys]
            if pool:
                return super().matches(pool, wanted)
        return super().matches(records, query)
