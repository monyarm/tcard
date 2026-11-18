"""V20 disciplines: the power list, plus one card per power."""

from __future__ import annotations

from ...model import Card
from ...names import normalize, split_path
from ..base import Kind
from . import cache, wiki

CATEGORY = "Discipline (VTM)"
SKIP = {"Amalgam (VTM)", "Discipline (VTM)", "Blood Magic (VTM)"}


def name_of(title: str) -> str:
    return title.replace(" (VTM)", "").strip()


def _discipline(title: str, refresh: bool = False) -> dict:
    markdown = cache.wikitext(title, refresh) or ""
    powers = wiki.dot_bullets(wiki.block(markdown, "Official Abilities", "Powers"))
    levels: dict[int, list[dict]] = {}
    for level, name, effect in powers:
        levels.setdefault(level or 1, []).append({"name": name, "text": effect})
    return {
        "name": name_of(title),
        "title": title,
        "levels": levels,
        "summary": (wiki.paragraphs(wiki.block(markdown, "Overview")) or [""])[0],
    }


def records(refresh: bool = False) -> list[dict]:
    out: list[dict] = []
    for title in cache.category(CATEGORY, refresh):
        if title in SKIP:
            continue
        entry = _discipline(title, refresh)
        out.append(entry)
        for level, powers in entry["levels"].items():
            for power in powers:
                out.append({
                    "name": power["name"],
                    "discipline": entry["name"],
                    "level": level,
                    "text": power["text"],
                })
    return out


def _discipline_card(record: dict) -> Card:
    sections = []
    for level in sorted(record["levels"]):
        bullets = []
        for power in record["levels"][level]:
            bullets.append(f"- {power['name']}: {power['text']}" if power["text"] else f"- {power['name']}")
        sections.append((f"Level {level} {wiki.dot_bar(level)}", bullets))
    return Card(record["name"], "Discipline", [], sections)


def _power_card(record: dict) -> Card:
    body = [record["text"]] if record.get("text") else []
    return Card(record["name"], f"{record['discipline']} {wiki.dot_bar(record['level'])}", [], [("", body)])


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
        if "discipline" in record:
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
