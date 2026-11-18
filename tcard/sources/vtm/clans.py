"""VTM clans: the whole clan, or just its bane and compulsion."""

from __future__ import annotations

import re

from ...model import Card
from ...names import normalize, split_path
from ..base import Kind
from . import cache, md

INDEX = "Clans"
LINK = re.compile(r'\*\*\[([^\]]+)\]\((https://vtm\.paradoxwikis\.com/[^)\s"]+)')
SECTIONS = ("Bane", "Variant Bane", "Compulsion")
PARTS = {"bane": ("Bane",), "banes": ("Bane", "Variant Bane"),
         "banes_1": ("Bane",), "bane_1": ("Bane",), "banes_2": ("Variant Bane",),
         "bane_2": ("Variant Bane",), "compulsion": ("Compulsion",)}
_NUMBERED = re.compile(r"^(?:bane|banes)[ _]?(\d)$")


def _section(markdown: str, title: str) -> list[str]:
    for name, lines in md.blocks(markdown):
        if name.lower() == title.lower():
            return lines
    return []


def _named(lines: list[str]) -> tuple[str, str]:
    """`**Violent Temper** - A rage ...` -> ("Violent Temper", "A rage ...")."""
    body = " ".join(line.strip() for line in lines if line.strip() and not line.strip().startswith("|"))
    match = re.match(r"^\*\*(.+?)\*\*\s*[-:]?\s*(.*)$", body, re.S)
    if not match:
        return "", md.text(body)
    return md.text(match.group(1)), md.text(match.group(2))


def _disciplines(markdown: str) -> list[str]:
    out = []
    for line in _section(markdown, "Disciplines"):
        stripped = line.strip()
        if not stripped.startswith("*"):
            continue
        match = re.match(r"^\*\s+\*\*(.+?)\*\*", stripped)
        if match:
            out.append(md.text(match.group(1)))
    return out


def _index(refresh: bool = False) -> list[dict]:
    markdown = cache.page(INDEX, refresh)
    out: list[dict] = []
    seen: set[str] = set()
    for line in markdown.splitlines():
        for name, url in LINK.findall(line):
            if name in seen:
                continue
            seen.add(name)
            out.append({"name": name, "url": url})
    return out


def records(refresh: bool = False) -> list[dict]:
    return [{"name": entry["name"], "url": entry["url"], "clan": entry["name"]}
            for entry in _index(refresh)]


def _part_name(query: str) -> tuple[str, ...] | None:
    key = normalize(query)
    if key in PARTS:
        return PARTS[key]
    match = _NUMBERED.match(key)
    if not match:
        return None
    return ("Variant Bane",) if match.group(1) == "2" else ("Bane",)


def to_card(record: dict, part: tuple[str, ...] | None = None) -> Card:
    markdown = cache.page(record["name"])
    wanted = part or SECTIONS
    named = {title: _named(_section(markdown, title)) for title in wanted}

    if part:
        title = " and ".join(wanted)
        sections = []
        for name in wanted:
            label, text = named[name]
            if text:
                sections.append((name, [f"{label}: {text}" if label else text]))
        if len(sections) == 1 and named[wanted[0]][0]:
            # A single bane reads better as its own title than as one section.
            name, text = named[wanted[0]]
            return Card(name, f"{record['clan']} {title}", [], [("", [text])])
        return Card(record["clan"], title, [], sections)

    fields = [("Disciplines", ", ".join(_disciplines(markdown)))]
    sections = []
    for title in SECTIONS:
        name, text = named[title]
        if text:
            sections.append((title, [f"{name}: {text}" if name else text]))
    return Card(record["name"], "Clan", fields, sections)


class ClanKind(Kind):
    def __init__(self) -> None:
        self.id = "clan"

    def records(self, refresh: bool = False) -> list[dict]:
        return records(refresh)

    def card(self, record: dict) -> Card:
        return to_card(record, record.get("part"))

    def matches(self, records: list[dict], query: str) -> list[dict]:
        parts = split_path(query)
        if len(parts) == 2:
            clan = [r for r in records if normalize(r["name"]) == parts[0]]
            if clan and _part_name(parts[1]):
                return [clan[0] | {"part": _part_name(parts[1])}]
        return super().matches(records, query)
