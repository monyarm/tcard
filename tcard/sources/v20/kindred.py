"""V20 clans and bloodlines: one card each, or a single bane or compulsion."""

from __future__ import annotations

import re

from ...model import Card
from ...names import normalize, split_path
from ..base import Kind
from . import cache, wiki

PARTS = {"bane": ("bane",), "banes": ("bane", "bane_2"), "bane_1": ("bane",),
         "banes_1": ("bane",), "bane_2": ("bane_2",), "banes_2": ("bane_2",),
         "compulsion": ("compulsion",)}
_NUMBERED = re.compile(r"^(?:bane|banes)[ _]?(\d)$")


def _joined(value: str) -> str:
    """Infobox bullet lists read as one comma-separated field."""
    items = wiki.list_items(value.splitlines())
    return ", ".join(items) if items else wiki.text(value)


def _fields(markdown: str) -> list[tuple[str, str]]:
    box = wiki.infobox(markdown)
    fields = []
    if box.get("disciplines"):
        fields.append(("Disciplines", _joined(box["disciplines"])))
    if box.get("nicknames"):
        fields.append(("Nicknames", _joined(box["nicknames"])))
    if box.get("faction"):
        fields.append(("Faction", _joined(box["faction"])))
    return fields


def _banes(markdown: str) -> list[tuple[str, str]]:
    out = []
    for item in wiki.list_items(wiki.block(markdown, "Weaknesses")):
        name, _, text = item.partition(": ")
        name = re.sub(r"(?i)^variant\s*[-—]\s*", "", name.strip())
        out.append((name, text.strip() or item))
    return out


def _compulsion(markdown: str) -> tuple[str, str] | None:
    prose = wiki.paragraphs(wiki.block(markdown, "Compulsion"))
    if not prose:
        return None
    name, _, text = prose[0].partition(": ")
    return (name.strip(), text.strip() or prose[0])


def build(markdown: str, subtitle: str, title: str = "") -> Card:
    fields = _fields(markdown)
    summary = wiki.paragraphs(wiki.block(markdown, "Overview"))
    sections = []
    if summary:
        sections.append(("Overview", summary[:1]))
    banes = _banes(markdown)
    if banes:
        sections.append(("Banes", [f"{name}: {text}" for name, text in banes]))
    compulsion = _compulsion(markdown)
    if compulsion:
        sections.append(("Compulsion", [f"{compulsion[0]}: {compulsion[1]}"]))
    return Card(title or "Untitled", subtitle, fields, sections)


def build_part(markdown: str, subtitle: str, wanted: tuple[str, ...]) -> Card:
    banes = dict(_banes(markdown))
    if wanted[0] == "compulsion":
        compulsion = _compulsion(markdown)
        if not compulsion:
            return Card(subtitle, "", [], [])
        return Card(compulsion[0], f"{subtitle} Compulsion", [], [("", [compulsion[1]])])
    if len(wanted) == 1:
        key = "bane" if wanted[0] == "bane" else "bane_2"
        picked = _pick(banes, key)
        if picked:
            return Card(picked[0], f"{subtitle} Bane", [], [("", [picked[1]])])
        return Card(subtitle, "Bane", [], [])
    sections = [(name, [text]) for name, text in _banes(markdown)]
    return Card(subtitle, "Banes", [], sections)


def _pick(banes: dict[str, str], key: str) -> tuple[str, str] | None:
    items = list(banes.items())
    if key == "bane":
        return items[0] if items else None
    return items[1] if len(items) > 1 else None


def _part_name(query: str) -> tuple[str, ...] | None:
    key = normalize(query)
    if key in PARTS:
        return PARTS[key]
    match = _NUMBERED.match(key)
    if not match:
        return None
    return ("bane_2",) if match.group(1) == "2" else ("bane",)


class KindredKind(Kind):
    """Clan or bloodline: same page shape, different category."""

    def __init__(self, kind_id: str, category: str, subtitle: str, skip: set[str]) -> None:
        self.id = kind_id
        self._category = category
        self._subtitle = subtitle
        self._skip = skip

    def records(self, refresh: bool = False) -> list[dict]:
        out = []
        for title in cache.category(self._category, refresh):
            if title in self._skip:
                continue
            out.append({"name": title.replace(" (VTM)", ""), "title": title})
        return out

    def card(self, record: dict) -> Card:
        markdown = cache.wikitext(record["title"]) or ""
        part = record.get("part")
        if part:
            return build_part(markdown, record["name"], part)
        return build(markdown, self._subtitle, record["name"])

    def matches(self, records: list[dict], query: str) -> list[dict]:
        parts = split_path(query)
        if len(parts) == 2:
            pool = [r for r in records if normalize(r["name"]) == parts[0]]
            if pool and _part_name(parts[1]):
                return [pool[0] | {"part": _part_name(parts[1])}]
        return super().matches(records, query)
