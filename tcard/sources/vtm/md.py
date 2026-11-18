"""Markdown from the proxy: clean prose, read tables, render dot ratings."""

from __future__ import annotations

import re

from ...model import Table

HEAD = re.compile(r"^(#{2,4})\s*(.+?)\s*$")
IMAGE_LINK = re.compile(r"\[!\[[^\]]*\]\([^)]*\)\]\([^)]*\)")
IMAGE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
CITE = re.compile(r"\[\[\d+\]\]\([^)]*\)|\[\[\d+\]\]")
LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
ITALIC = re.compile(r"(?<!\w)_([^_]+)_(?!\w)")
LABEL = re.compile(r"^\*\*([^*]+?):?\*\*\s*(.*)$")
RULE = re.compile(r"^\s*(?:\*\s*){3}$")

FILLED = "\u25cf"
HOLLOW = "\u25cb"


def text(markdown: str) -> str:
    """Inline markdown to plain text."""
    markdown = IMAGE_LINK.sub("", markdown)
    markdown = IMAGE.sub("", markdown)
    markdown = CITE.sub("", markdown)
    markdown = LINK.sub(r"\1", markdown)
    markdown = markdown.replace("**", "").replace("__", "")
    markdown = ITALIC.sub(r"\1", markdown)
    # The wiki marks errata inline; it is not part of the rules text.
    markdown = re.sub(r"\s*Errata\b", "", markdown)
    markdown = re.sub(r"\s+", " ", markdown)
    return markdown.strip(" \t*_")


def heading(line: str) -> tuple[int, str] | None:
    match = HEAD.match(line)
    if not match:
        return None
    return len(match.group(1)), text(match.group(2))


def label(line: str) -> tuple[str, str] | None:
    """`**Type:**Mental` -> ("Type", "Mental")."""
    match = LABEL.match(line.strip())
    if not match:
        return None
    name = text(match.group(1)).rstrip(":")
    if not name or " " in name and len(name) > 20:
        return None
    return name, text(match.group(2))


def _cells(line: str) -> list[str]:
    inner = line.strip().strip("|")
    return [text(cell) for cell in inner.split("|")]


def _is_rule(line: str) -> bool:
    body = line.replace("|", "").replace("-", "").replace(":", "").replace(" ", "")
    return line.startswith("|") and body == ""


def tables(markdown: str) -> list[tuple[str, Table]]:
    """Every table in the page, with the heading it sits under."""
    out: list[tuple[str, Table]] = []
    section = ""
    lines = markdown.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        found = heading(line)
        if found:
            level, title = found
            if level <= 3:
                section = title
            index += 1
            continue
        if line.startswith("|") and index + 1 < len(lines) and _is_rule(lines[index + 1]):
            header = _cells(line)
            index += 2
            rows: list[list[str]] = []
            while index < len(lines) and lines[index].startswith("|"):
                if not _is_rule(lines[index]):
                    rows.append(_cells(lines[index]))
                index += 1
            if any(header):
                out.append((section, Table([header] + rows, header=True)))
            continue
        index += 1
    return out


def blocks(markdown: str) -> list[tuple[str, list[str]]]:
    """Split a page into (heading, body lines) at level 2 and 3 headings."""
    out: list[tuple[str, list[str]]] = []
    current = ("", [])
    for line in markdown.splitlines():
        found = heading(line)
        if found and found[0] <= 3:
            if current[1]:
                out.append(current)
            current = (found[1], [])
            continue
        current[1].append(line)
    if current[1]:
        out.append(current)
    return out


def paragraphs(lines: list[str]) -> list[str]:
    """Prose paragraphs of a block, tables and rules dropped."""
    out: list[str] = []
    buffer: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or RULE.match(stripped):
            if buffer:
                out.append(text(" ".join(buffer)))
                buffer = []
            continue
        if stripped.startswith(("|", "!")) or (stripped.startswith("*") and not RULE.match(stripped)):
            continue
        buffer.append(stripped)
    if buffer:
        out.append(text(" ".join(buffer)))
    return [part for part in out if part]


def bullets(lines: list[str]) -> list[str]:
    """List items of a block, as `Name - text` style plain lines."""
    out = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("*") and not RULE.match(stripped):
            item = text(stripped.lstrip("*").strip())
            if item:
                out.append(f"- {item}")
    return out


def dots(markdown: str) -> str:
    """`••`, `•• or ••••`, `(•)` -> filled/hollow circles, five per rating."""
    value = text(markdown).strip("()")
    value = value.replace("\u2022", FILLED)
    parts = [part.strip() for part in re.split(r"\s+or\s+|\s+-\s+", value) if part.strip()]
    rendered = []
    for part in parts:
        filled = part.count(FILLED)
        if not filled:
            return value
        rendered.append(FILLED * filled + HOLLOW * (5 - filled))
    return " OR ".join(rendered)


def rating(markdown: str) -> int:
    """Dot value of a merit cell, 0 when it is not a plain rating."""
    value = text(markdown)
    return value.count("\u2022") or value.count(FILLED)
