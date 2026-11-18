"""V20 paths of enlightenment."""

from __future__ import annotations

from ...model import Card
from ..base import Kind
from . import cache, wiki

CATEGORY = "Paths"
SKIP = {"Path (DAV)"}
FIELDS = ("nickname", "faction", "bearing", "virtues", "plural")


def records(refresh: bool = False) -> list[dict]:
    return [{"name": title, "title": title}
            for title in cache.category(CATEGORY, refresh) if title not in SKIP]


def to_card(record: dict) -> Card:
    markdown = cache.wikitext(record["title"]) or ""
    box = wiki.infobox(markdown)
    fields = [(key.title(), wiki.text(value)) for key, value in
              ((key, box.get(key, "")) for key in FIELDS) if value]
    sections = []
    for title in ("Overview", "Ethics", "Description"):
        prose = wiki.paragraphs(wiki.block(markdown, title))
        if prose:
            sections.append((title, prose))
    if not sections:
        body = wiki.paragraphs(markdown)
        if body:
            sections.append(("", body))
    return Card(record["name"], "Path", fields, sections)


class PathKind(Kind):
    def __init__(self) -> None:
        self.id = "path"

    def records(self, refresh: bool = False) -> list[dict]:
        return records(refresh)

    def card(self, record: dict) -> Card:
        return to_card(record)
