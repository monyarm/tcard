"""d20pfsrd spell page to Card."""

from __future__ import annotations

import re

from ...model import Card
from . import cache, html

TITLE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.S)
ARTICLE = re.compile(r"<article\b.*?</article>", re.S)
# Site furniture that sits inside the article body.
JUNK = re.compile(r"(?i)^(join our discord|support us|become a patron|follow us)")


def parse(markup: str, name: str | None = None) -> Card:
    article = ARTICLE.search(markup)
    markup = article.group(0) if article else markup
    title = html.text(TITLE.search(markup).group(1)) if TITLE.search(markup) else (name or "Untitled")

    fields: list[tuple[str, str]] = []
    sections: list[tuple[str, list[str]]] = [("", [])]
    mode = "stat"
    started = False
    school = ""

    for css, inner in html.paragraphs(markup):
        if "divider" in css:
            heading = html.text(inner).strip()
            upper = heading.upper()
            if upper in ("EFFECT", "CASTING"):
                mode = "stat"
            elif upper.startswith("DESCRIPTION"):
                mode = "body"
            else:
                mode = "body"
                sections.append((heading.title(), []))
            continue

        if mode == "body":
            prose = html.text(inner)
            if prose and not JUNK.match(prose):
                sections[-1][1].append(prose)
            continue

        for label, value in html.labelled(inner):
            if label is None:
                if started and value:
                    sections[-1][1].append(value)
                continue
            if label == "School":
                school = value
                started = True
                continue
            if not started:
                continue
            fields.append((label, value))

    subtitle = school[:1].upper() + school[1:] if school else ""
    sections = [(heading, paragraphs) for heading, paragraphs in sections if paragraphs]
    return Card(title, subtitle, fields, sections)


def to_card(record: dict, refresh: bool = False) -> Card:
    return parse(cache.page(record, refresh), record.get("name"))
