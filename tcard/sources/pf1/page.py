"""d20pfsrd stat page to Card, shared by every page-based kind."""

from __future__ import annotations

import re

from ...model import Card, Table
from . import cache, html

TITLE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.S)
ARTICLE = re.compile(r"<article\b.*?</article>", re.S)
# Site furniture that sits inside the article body.
JUNK = re.compile(
    r"(?i)^(join our discord|support us|become a patron|follow us|pathfinder .*copyright"
    r"|open game license|compatibility with the pathfinder|authors?:)"
)
# d20pfsrd titles carry the feat/ability category in parentheses.
CATEGORY = re.compile(
    r"\s*\((?:Combat|General|Metamagic|Teamwork|Critical|Style|Achievement|Monster|Item Creation|"
    r"Grit|Panache|Performance|Racial|Story|Mythic|Local|Magic|EX|UC|UM|OA|APG|ACG|ARG)\)\s*$",
    re.I,
)


def parse(markup: str, name: str | None = None, spell: bool = False) -> Card:
    article = ARTICLE.search(markup)
    markup = article.group(0) if article else markup
    title = html.text(TITLE.search(markup).group(1)) if TITLE.search(markup) else (name or "Untitled")
    title = CATEGORY.sub("", title).strip() or title

    fields: list[tuple[str, str]] = []
    sections: list[tuple[str, list[str | Table]]] = [("", [])]
    mode = "stat"
    # Spell pages start on a School line; other pages begin with labels at once.
    started = not spell
    school = ""

    for tag, css, inner in html.blocks(markup):
        if tag == "table":
            grid = html.table(inner)
            if grid.rows:
                sections[-1][1].append(grid)
            continue

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
                if started and value and not JUNK.match(value):
                    sections[-1][1].append(value)
                continue
            if not value:
                continue
            if label == "School":
                school = value
                started = True
                continue
            if not started:
                continue
            if not spell and (len(value) > 90 or re.search(r"[.!?]\s+[A-Z]", value)):
                sections[-1][1].append(f"{label}: {value}")
                continue
            fields.append((label, value))

    subtitle = school[:1].upper() + school[1:] if school else ""
    sections = [(heading, paragraphs) for heading, paragraphs in sections if paragraphs]
    return Card(title, subtitle, fields, sections)


def to_card(record: dict, refresh: bool = False, spell: bool = False) -> Card:
    return parse(cache.page(record, refresh), record.get("name"), spell=spell)
