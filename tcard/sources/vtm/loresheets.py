"""V5 loresheets: the White Wolf wiki has the full set, the Paradox wiki does not."""

from __future__ import annotations

import re

from ...errors import TcardError
from ...model import Card
from ...names import normalize, split_path
from ..base import Kind
from . import cache, md

INDEX = "Loresheet"
CATEGORY = "Category:Loresheets"
BULLET = re.compile(r"^\*\s*\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|([^\]]+))?\]\]")
DOT = re.compile(r"^\*+\s*\{\{Dot\|(\d)\}\}\s*(.*)$", re.I)
NAME = re.compile(r"^'''(?P<name>.+?):?'''\s*:?\s*(?P<text>.*)$")


def clean(wikitext: str) -> str:
    """Wikitext inline markup to plain text."""
    wikitext = re.sub(r"<ref[^>]*/>", "", wikitext)
    wikitext = re.sub(r"<ref.*?</ref>", "", wikitext, flags=re.S)
    wikitext = re.sub(r"\[\[[^\]|]*\|([^\]]+)\]\]", r"\1", wikitext)
    wikitext = re.sub(r"\[\[([^\]]+)\]\]", r"\1", wikitext)
    wikitext = re.sub(r"\[https?://\S+\s+([^\]]+)\]", r"\1", wikitext)
    wikitext = re.sub(r"\{\{[^{}]*\}\}", "", wikitext)
    wikitext = wikitext.replace("'''", "").replace("''", "")
    wikitext = re.sub(r"\s+", " ", wikitext)
    return wikitext.strip(" :")


def entries(wikitext: str) -> list[dict]:
    """The dot-rated bullets of one loresheet, in page order."""
    out: list[dict] = []
    current: dict | None = None
    for line in wikitext.splitlines():
        found = DOT.match(line)
        if found:
            body = found.group(2)
            name = ""
            match = NAME.match(body)
            if match:
                name = clean(match.group("name"))
                body = match.group("text")
            current = {"level": int(found.group(1)), "name": name, "lines": [body]}
            out.append(current)
            continue
        if current is None:
            continue
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(("*", "=", "{{", "|", "!", "<")):
            current = None
            continue
        current["lines"].append(stripped)
    result = []
    for item in out:
        text = clean(" ".join(item["lines"]))
        result.append({"level": item["level"], "name": item["name"], "text": text})
    return [item for item in result if item["text"]]


def index(refresh: bool = False) -> list[dict]:
    wikitext = cache.wikitext(INDEX, refresh)
    out: list[dict] = []
    seen: set[str] = set()
    for line in wikitext.splitlines():
        match = BULLET.match(line)
        if not match:
            continue
        page = match.group(1).strip()
        name = clean(match.group(2) or page)
        if not page or name in seen:
            continue
        seen.add(name)
        out.append({"name": name, "page": page})
    return out


def category(refresh: bool = False) -> list[dict]:
    """Loresheets the index misses but the category files."""
    import json

    url = (f"{cache.WIKI}/api.php?action=query&list=categorymembers"
           f"&cmtitle={CATEGORY}&cmlimit=500&format=json")
    body = cache.get(url, refresh)
    try:
        members = json.loads(body)["query"]["categorymembers"]
    except (json.JSONDecodeError, KeyError) as exc:
        raise cache.TcardError(f"cannot read {CATEGORY}: {exc}", 3) from exc
    return [{"name": clean(item["title"]), "page": item["title"]} for item in members]


def records(refresh: bool = False) -> list[dict]:
    out = index(refresh)
    seen = {item["name"] for item in out}
    for item in category(refresh):
        if item["name"] not in seen:
            out.append(item)
    return out


def _dots(level: int) -> str:
    return md.FILLED * level + md.HOLLOW * (5 - level)


def to_card(record: dict, part: str | None = None) -> Card:
    sheet = entries(cache.wikitext(record["page"]))
    if not sheet:
        raise TcardError(f"no loresheet text on {record['page']!r} ({record['name']})", 1)

    if part:
        chosen = _pick(sheet, part)
        if chosen is None:
            names = ", ".join(item["name"] or f"level {item['level']}" for item in sheet)
            raise TcardError(f"no loresheet entry {part!r} in {record['name']} ({names})", 1)
        title = chosen["name"] or f"Level {chosen['level']}"
        return Card(title, f"{record['name']} Loresheet", [("Dots", _dots(chosen["level"]))],
                    [("", [chosen["text"]])])

    sections = []
    for item in sheet:
        body = f"{item['name']}: {item['text']}" if item["name"] else item["text"]
        sections.append((f"Level {item['level']} {_dots(item['level'])}", [body]))
    return Card(record["name"], "Loresheet", [], sections)


def _pick(sheet: list[dict], part: str) -> dict | None:
    if part.isdigit():
        for item in sheet:
            if item["level"] == int(part):
                return item
        return None
    wanted = normalize(part)
    for item in sheet:
        if normalize(item["name"]) == wanted:
            return item
    for item in sheet:
        if normalize(item["name"]).startswith(wanted):
            return item
    return None


class LoresheetKind(Kind):
    def __init__(self) -> None:
        self.id = "loresheet"

    def records(self, refresh: bool = False) -> list[dict]:
        return records(refresh)

    def key(self, record: dict) -> str:
        key = normalize(record["name"])
        return key[4:] if key.startswith("the ") else key

    def display(self, record: dict) -> str:
        return record["name"]

    def card(self, record: dict) -> Card:
        return to_card(record, record.get("part"))

    def matches(self, records: list[dict], query: str) -> list[dict]:
        parts = split_path(query)
        if len(parts) == 2:
            sheet = [r for r in records if self.key(r) in (parts[0], f"the {parts[0]}")]
            if sheet:
                return [sheet[0] | {"part": parts[1]}]
        return super().matches(records, query)
