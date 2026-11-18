"""Cyberpunk Wiki wikitext to description paragraphs."""

from __future__ import annotations

import re

REF = re.compile(r"<ref[^>]*>.*?</ref>|<ref[^>]*/>", re.S | re.I)
FILE = re.compile(r"\[\[(?:File|Image|Category):[^\]]*\]\]", re.I)
LINK = re.compile(r"\[\[([^\]|]+)\|([^\]]+)\]\]|\[\[([^\]]+)\]\]")
EXTERNAL = re.compile(r"\[https?://\S+\s+([^\]]+)\]")
HEADING = re.compile(r"^\s*=+.*?=+\s*$")
STOP = re.compile(r"(?i)^\s*=+\s*(gallery|references|external links|navigation|see also)")


def _drop_templates(text: str) -> str:
    out: list[str] = []
    depth = 0
    index = 0
    while index < len(text):
        pair = text[index : index + 2]
        if pair == "{{":
            depth += 1
            index += 2
            continue
        if pair == "}}" and depth:
            depth -= 1
            index += 2
            continue
        if not depth:
            out.append(text[index])
        index += 1
    return "".join(out)


def _drop_tables(text: str) -> str:
    out: list[str] = []
    inside = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("{|"):
            inside = True
            continue
        if inside:
            if stripped.startswith("|}"):
                inside = False
            continue
        out.append(line)
    return "\n".join(out)


def prose(markdown: str) -> list[str]:
    """Readable paragraphs from a weapon page's wikitext."""
    text = REF.sub("", markdown)
    text = _drop_templates(text)
    text = _drop_tables(text)
    text = FILE.sub("", text)
    text = LINK.sub(lambda m: m.group(2) or m.group(3), text)
    text = EXTERNAL.sub(r"\1", text)
    text = text.replace("'''", "").replace("''", "")
    text = re.sub(r"<[^>]+>", "", text)

    paragraphs: list[str] = []
    buffer: list[str] = []
    for line in text.splitlines():
        if STOP.match(line):
            break
        if HEADING.match(line):
            if buffer:
                paragraphs.append(" ".join(buffer))
                buffer = []
            continue
        stripped = line.strip()
        if not stripped:
            if buffer:
                paragraphs.append(" ".join(buffer))
                buffer = []
            continue
        if stripped.startswith(("|", "!", "{", "}")):
            continue
        buffer.append(stripped)
    if buffer:
        paragraphs.append(" ".join(buffer))
    cleaned = []
    for paragraph in paragraphs:
        paragraph = re.sub(r"\s+", " ", paragraph).strip()
        if paragraph and not paragraph.lower().startswith(("categories:", "[[category")):
            cleaned.append(paragraph)
    return cleaned
