"""Archives of Nethys deity page to Card.

d20pfsrd has no deity pages (deities are Product Identity), so this kind reads
the Pathfinder 1e Archives of Nethys instead.
"""

from __future__ import annotations

import json
import re
import urllib.parse

from ...errors import TcardError
from ...model import Card
from . import cache, html

# html module shadows the stdlib one inside this package.
unescape = html.htmlmod.unescape

INDEX_URL = "https://aonprd.com/DeitiesByGroup.aspx"
PAGE_URL = "https://aonprd.com/DeityDisplay.aspx?ItemName={name}"
_LINK = re.compile(r'DeityDisplay\.aspx\?ItemName=([^"&]+)')
_HEADING = re.compile(r"<h([123])[^>]*>(.*?)</h\1>", re.S)
_TOKEN = re.compile(r"(<h[123][^>]*>.*?</h[123]>)", re.S)
_SKIP_FIELD = {"source", "pathfinder wiki"}
# "For followers of X" sections are cross-reference link lists, not rules.
_SKIP_SECTION = re.compile(
    r"(?i)^(for followers of|archetypes|feats|magic items|monsters|prestige classes|spells|traits)"
)


def records(refresh: bool = False) -> list[dict]:
    path = cache.cache_dir() / "deities.json"
    if refresh or not path.exists():
        markup = cache.fetch(INDEX_URL)
        names: list[str] = []
        for raw in _LINK.findall(markup):
            name = urllib.parse.unquote(unescape(raw)).strip()
            if name and name not in names:
                names.append(name)
        names.sort()
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(names, indent=0))
        tmp.replace(path)
    try:
        names = json.loads(path.read_text())
    except ValueError as exc:
        path.unlink(missing_ok=True)
        raise TcardError(f"corrupt deity index at {path}", 3) from exc
    return [{"name": name, "url": PAGE_URL.format(name=urllib.parse.quote(name))} for name in names]


def _chunks(token: str):
    """Split one run of markup into label/value pairs or prose."""
    for part in re.split(r"<br\s*/?>", token):
        if not part.strip():
            continue
        yield from html.labelled(part)


def parse(markup: str, name: str | None = None) -> Card:
    start = markup.find('id="main"')
    body = markup[start:] if start != -1 else markup

    title = name or "Untitled"
    subtitle = ""
    fields: list[tuple[str, str]] = []
    sections: list[tuple[str, list[str]]] = [("", [])]
    details = False
    skip = False
    seen_title = False

    for token in _TOKEN.split(body):
        match = _HEADING.fullmatch(token)
        if match:
            level, text = match.group(1), html.text(match.group(2)).strip()
            if not text:
                continue
            if level == "1":
                if not seen_title and 'class="title"' in token:
                    title = text
                    seen_title = True
                continue
            if level == "2" and not subtitle and not details:
                subtitle = text
                continue
            skip = bool(_SKIP_SECTION.match(text))
            if skip:
                continue
            if text.lower() == "details":
                details = True
                continue
            details = False
            sections.append((text, []))
            continue

        if skip:
            continue
        if not seen_title:
            continue
        for label, value in _chunks(token):
            if not value:
                continue
            if label is None:
                if details and not value.lower().startswith("nethys note"):
                    sections[-1][1].append(value)
                elif not details:
                    sections[-1][1].append(value)
                continue
            if label.lower() in _SKIP_FIELD:
                continue
            if details:
                fields.append((label, value))
            else:
                sections[-1][1].append(f"{label}: {value}")

    kept = [(heading, parts) for heading, parts in sections if parts]
    return Card(title, subtitle, fields, kept)


def to_card(record: dict, refresh: bool = False) -> Card:
    return parse(cache.page(record, refresh), record.get("name"))
