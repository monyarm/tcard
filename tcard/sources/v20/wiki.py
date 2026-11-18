"""Wikitext helpers for the White Wolf wiki."""

from __future__ import annotations

import re

from ...model import Table

HEAD = re.compile(r"^(={2,5})\s*(.+?)\s*\1\s*$")
REF = re.compile(r"<ref[^>]*/>|<ref[^>]*>.*?</ref>", re.S | re.I)
COMMENT = re.compile(r"<!--.*?-->", re.S)
HTML = re.compile(r"<[^>]+>")
FILE = re.compile(r"\[\[(?:File|Image|Category):[^\]]*\]\]", re.I)
LINK = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]*))?\]\]")
OUTER = re.compile(r"\[https?://\S+\s+([^\]]*)\]")
DOT = re.compile(r"\{\{\s*dot\s*\|\s*(\d)\s*\}\}", re.I)
POWER = re.compile(r"^\*\*+\s*'''(.+?)'''\s*:?\s*(.*)$")
INFOBOXES = ("organization", "path", "bloodline", "clan")


def _balanced(text: str, start: int, opening: str, closing: str) -> int:
    """Index just past the matching close, or -1."""
    depth = 0
    index = start
    while index < len(text):
        if text.startswith(opening, index):
            depth += 1
            index += len(opening)
            continue
        if text.startswith(closing, index):
            depth -= 1
            index += len(closing)
            if depth == 0:
                return index
            continue
        index += 1
    return -1


def templates(markdown: str) -> list[tuple[int, int, str]]:
    """(start, end, name) for every top-level {{template}}."""
    out = []
    index = 0
    while True:
        start = markdown.find("{{", index)
        if start < 0:
            return out
        end = _balanced(markdown, start, "{{", "}}")
        if end < 0:
            return out
        inner = markdown[start + 2 : end - 2]
        out.append((start, end, inner.split("|", 1)[0].strip().lower()))
        index = end


def drop_templates(markdown: str) -> str:
    out = []
    index = 0
    for start, end, _ in templates(markdown):
        out.append(markdown[index:start])
        index = end
    out.append(markdown[index:])
    return "".join(out)


def drop_tables(markdown: str) -> str:
    out = []
    depth = 0
    for line in markdown.splitlines():
        if line.strip().startswith("{|"):
            depth += 1
            continue
        if line.strip().startswith("|}"):
            depth = max(0, depth - 1)
            continue
        if not depth:
            out.append(line)
    return "\n".join(out)


def text(markdown: str) -> str:
    """Inline wikitext to plain text."""
    markdown = COMMENT.sub("", markdown)
    markdown = REF.sub("", markdown)
    markdown = DOT.sub(lambda m: dot_bar(int(m.group(1))) + " ", markdown)
    markdown = FILE.sub("", markdown)
    markdown = LINK.sub(lambda m: m.group(2) if m.group(2) else m.group(1), markdown)
    markdown = OUTER.sub(r"\1", markdown)
    markdown = markdown.replace("'''", "").replace("''", "")
    markdown = drop_templates(markdown)
    markdown = HTML.sub(" ", markdown)
    markdown = re.sub(r"\s+", " ", markdown)
    return markdown.strip(" \t|*:,")


def dot_bar(count: int) -> str:
    count = max(0, min(5, count))
    return "\u25cf" * count + "\u25cb" * (5 - count)


def sections(markdown: str) -> list[tuple[int, str, list[str]]]:
    """Split a page at == headings; body lines keep their wikitext."""
    out: list[tuple[int, str, list[str]]] = []
    level, title, body = 0, "", []
    for line in markdown.splitlines():
        match = HEAD.match(line)
        if match:
            out.append((level, title, body))
            level, title, body = len(match.group(1)), text(match.group(2)), []
            continue
        body.append(line)
    out.append((level, title, body))
    return out[1:] if len(out) > 1 else out


def find(markdown: str, *titles: str) -> list[str]:
    """Body of the first section whose title matches, case-insensitively."""
    wanted = {title.lower() for title in titles}
    for _, title, body in sections(markdown):
        if title.lower() in wanted:
            return body
    return []


def block(markdown: str, *titles: str) -> list[str]:
    """Lines of a section including its subsections."""
    wanted = {title.lower() for title in titles}
    lines = markdown.splitlines()
    out: list[str] = []
    depth = 0
    for line in lines:
        match = HEAD.match(line)
        if match:
            level = len(match.group(1))
            title = text(match.group(2))
            if depth and level <= depth:
                break
            if not depth and title.lower() in wanted:
                depth = level
            continue
        if depth:
            out.append(line)
    return out


def _split_params(inner: str) -> list[str]:
    parts: list[str] = []
    depth = 0
    current: list[str] = []
    index = 0
    while index < len(inner):
        if inner.startswith("{{", index) or inner.startswith("[[", index):
            depth += 1
            current.append(inner[index : index + 2])
            index += 2
            continue
        if inner.startswith("}}", index) or inner.startswith("]]", index):
            depth -= 1
            current.append(inner[index : index + 2])
            index += 2
            continue
        if inner[index] == "|" and depth == 0:
            parts.append("".join(current))
            current = []
            index += 1
            continue
        current.append(inner[index])
        index += 1
    parts.append("".join(current))
    return parts


def infobox(markdown: str) -> dict[str, str]:
    """Parameters of the page's first Organization/Path/Clan infobox."""
    for start, end, name in templates(markdown):
        if name not in INFOBOXES:
            continue
        fields: dict[str, str] = {}
        for chunk in _split_params(markdown[start + 2 : end - 2])[1:]:
            if "=" not in chunk:
                continue
            key, value = chunk.split("=", 1)
            key = key.strip().lower()
            if key:
                fields[key] = value.strip()
        return fields
    return {}


def list_items(lines: list[str]) -> list[str]:
    out = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("*"):
            item = text(stripped.lstrip("*"))
            if item:
                out.append(item)
    return out


def paragraphs(lines: list[str]) -> list[str]:
    """Prose paragraphs from section body lines."""
    out: list[str] = []
    buffer: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith(("*", "|", "!", "{", "}", "=", "<", "[[File", "[[Image", "|}")):
            if buffer:
                out.append(text(" ".join(buffer)))
                buffer = []
            continue
        buffer.append(stripped)
    if buffer:
        out.append(text(" ".join(buffer)))
    return [part for part in out if part]


def _split_top(line: str, separator: str) -> list[str]:
    """Split on `separator`, ignoring pipes inside `[[links]]` and `{{templates}}`.

    A cell like `[[Humanity (VTM)|Humanity]]` owns a pipe of its own; splitting
    on it would shift every later column of the table.
    """
    parts: list[str] = []
    depth = start = index = 0
    while index < len(line):
        if line.startswith(("[[", "{{"), index):
            depth += 1
            index += 2
            continue
        if line.startswith(("]]", "}}"), index):
            depth = max(0, depth - 1)
            index += 2
            continue
        if depth == 0 and line.startswith(separator, index):
            parts.append(line[start:index])
            index += len(separator)
            start = index
            continue
        index += 1
    parts.append(line[start:])
    return parts


def _cell(raw: str) -> str:
    """A cell may carry attributes before its text: `style="x" | Value`."""
    return text(_split_top(raw, "|")[-1])


def tables(markdown: str) -> list[tuple[str, Table]]:
    """Every wikitable, paired with the nearest preceding heading."""
    out: list[tuple[str, Table]] = []
    heading = ""
    lines = markdown.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        match = HEAD.match(line)
        if match:
            heading = text(match.group(2))
            index += 1
            continue
        if not line.strip().startswith("{|"):
            index += 1
            continue
        index += 1
        rows: list[list[str]] = []
        header = False
        current: list[str] = []
        while index < len(lines) and not lines[index].strip().startswith("|}"):
            stripped = lines[index].strip()
            if stripped.startswith("|-"):
                if current:
                    rows.append(current)
                current = []
            elif stripped.startswith("!"):
                header = True
                current.extend(_cell(cell) for cell in _split_top(stripped[1:], "!!"))
            elif stripped.startswith("|"):
                current.extend(_cell(cell) for cell in _split_top(stripped[1:], "||"))
            elif current and stripped:
                current[-1] = f"{current[-1]} {text(stripped)}".strip()
            index += 1
        if current:
            rows.append(current)
        index += 1
        if rows:
            out.append((heading, Table(rows, header=header)))
    return out


def dot_bullets(lines: list[str]) -> list[tuple[int, str, str]]:
    """`* {{dot|N}}` level markers followed by `** '''Name''': text` entries."""
    if isinstance(lines, str):
        lines = lines.splitlines()
    out: list[tuple[int, str, str]] = []
    level = 0
    for line in lines:
        stripped = line.strip()
        dots = DOT.search(stripped)
        if dots and not stripped.startswith("**"):
            level = int(dots.group(1))
            continue
        match = POWER.match(stripped)
        if match:
            out.append((level, text(match.group(1)), text(match.group(2))))
    return out
