"""Card to width-checked Lines. Single layout pass, shared by every backend."""

from __future__ import annotations

import unicodedata

from ..model import Card, Line, LineKind, Table

# tp folds text to ASCII and drops what it cannot map. Do it here, once, so the
# pipe never sees a character the printer would smear.
_FOLD = {
    "\u2018": "'",
    "\u2019": "'",
    "\u201a": "'",
    "\u201b": "'",
    "\u201c": '"',
    "\u201d": '"',
    "\u201e": '"',
    "\u2013": "-",
    "\u2014": "-",
    "\u2015": "-",
    "\u2011": "-",
    "\u2212": "-",
    "\u2026": "...",
    "\u00b7": "*",
    "\u00d7": "x",
    "\u00f7": "/",
    "\u00b0": " degrees",
    "\u00b1": "+/-",
    "\u00a0": " ",
    "\u2044": "/",
}


# DejaVu Sans Mono draws these in exactly one cell, so they survive to the printer.
KEEP = frozenset("\u25cf\u25cb")


def fold(text: str) -> str:
    """Transliterate typography, then drop anything the printer cannot draw."""
    text = text.translate(str.maketrans(_FOLD))
    text = unicodedata.normalize("NFKD", text)
    return "".join(char for char in text if char in KEEP or ord(char) < 128)


def wrap(text: str, cols: int) -> list[str]:
    """Greedy word wrap; splits tokens longer than cols."""
    words = fold(text).expandtabs(4).split()
    if not words:
        return []
    lines: list[str] = []
    current = ""
    for word in words:
        while len(word) > cols:
            if current:
                lines.append(current)
                current = ""
            lines.append(word[:cols])
            word = word[cols:]
        if not word:
            continue
        candidate = f"{current} {word}" if current else word
        if len(candidate) <= cols:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _field(label: str, value: str, cols: int) -> list[Line]:
    head = f"{label}: "
    room = cols - len(head)
    if room < 4:
        # A label too long to share its line wraps above an indented value.
        label_lines = [Line(LineKind.FIELD, part) for part in wrap(f"{label}:", cols)]
        return label_lines + _field_value(value, "  ", cols - 2, cols)
    return _field_value(value, head, room, cols) or [Line(LineKind.FIELD, head.rstrip())]


def _field_value(value: str, prefix: str, limit: int, cols: int) -> list[Line]:
    out: list[Line] = []
    current = ""
    for word in fold(value).expandtabs(4).split():
        while len(word) > limit:
            if current:
                out.append(Line(LineKind.FIELD, prefix + current))
                current = ""
            out.append(Line(LineKind.FIELD, prefix + word[:limit]))
            word = word[limit:]
            prefix = "  "
            limit = cols - 2
        if not word:
            continue
        candidate = f"{current} {word}" if current else word
        if len(candidate) <= limit:
            current = candidate
        else:
            out.append(Line(LineKind.FIELD, prefix + current))
            prefix = "  "
            limit = cols - 2
            current = word
    if current:
        out.append(Line(LineKind.FIELD, prefix + current))
    return out


_BULLET = "- "


def _body(text: str, cols: int) -> list[str]:
    """Wrap a paragraph, keeping bullet and indented continuations aligned."""
    indent = text[: len(text) - len(text.lstrip(" "))]
    rest = text[len(indent) :]
    if rest.startswith(_BULLET):
        marker = indent + _BULLET
        room = cols - len(marker)
        if room < 4:
            return wrap(text, cols)
        parts = wrap(rest[len(_BULLET) :], room)
        return [marker + parts[0]] + [" " * len(marker) + part for part in parts[1:]] if parts else [marker.rstrip()]
    if indent:
        room = cols - len(indent)
        if room < 4:
            return wrap(text, cols)
        return [indent + part for part in wrap(rest, room)]
    return wrap(text, cols)


def _table_fallback(rows: list[list[str]], cols: int) -> list[str]:
    return [line for row in rows for line in wrap(", ".join(cell for cell in row if cell), cols)]


def _table_lines(table: Table, cols: int) -> list[str]:
    """Columns padded to a shared width, shrunk until the grid fits cols."""
    rows = [[fold(cell).strip() for cell in row] for row in table.rows]
    rows = [row for row in rows if any(row)]
    if not rows:
        return []
    width = max(len(row) for row in rows)
    rows = [row + [""] * (width - len(row)) for row in rows]
    widths = [max(1, max(len(row[i]) for row in rows)) for i in range(width)]
    gaps = width - 1
    if sum(widths) + gaps > cols:
        room = cols - gaps
        while sum(widths) > room:
            widest = max(range(width), key=lambda i: widths[i])
            if widths[widest] <= 3:
                return _table_fallback(rows, cols)
            widths[widest] -= 1
    out: list[str] = []
    for index, row in enumerate(rows):
        cells = [wrap(cell, widths[i]) or [""] for i, cell in enumerate(row)]
        for line_no in range(max(len(cell) for cell in cells)):
            parts = [cell[line_no] if line_no < len(cell) else "" for cell in cells]
            out.append(" ".join(part.ljust(widths[i]) for i, part in enumerate(parts)).rstrip())
        if index == 0 and table.header and len(rows) > 1:
            out.append("-" * min(cols, sum(widths) + gaps))
    return out


def layout(card: Card, cols: int = 32, brief: bool = False) -> list[Line]:
    """Build the line list. Raises ValueError instead of truncating."""
    if cols < 4:
        raise ValueError(f"cols must be at least 4, got {cols}")

    out: list[Line] = []
    out += [Line(LineKind.TITLE, part) for part in wrap(card.title, cols)]
    out.append(Line(LineKind.RULE, "=" * cols))
    if card.subtitle:
        out += [Line(LineKind.SUBTITLE, part) for part in wrap(card.subtitle, cols)]
    if card.subtitle:
        out.append(Line(LineKind.RULE, "-" * cols))
    for label, value in card.fields:
        out += _field(label, value, cols)

    sections: list[tuple[str, list[str | Table]]] = []
    if not brief:
        for heading, paragraphs in card.sections:
            body = [p for p in paragraphs if isinstance(p, Table) or p.strip()]
            if body:
                sections.append((heading, body))

    # Only separate fields from something; a trailing rule on a brief card is noise.
    if card.fields and sections:
        out.append(Line(LineKind.RULE, "-" * cols))

    for heading, body in sections:
        if heading:
            if out and out[-1].kind is not LineKind.RULE:
                out.append(Line(LineKind.RULE, "-" * cols))
            out += [Line(LineKind.SECTION, part) for part in wrap(heading, cols)]
        previous_bullet = False
        for paragraph in body:
            if isinstance(paragraph, Table):
                if out and out[-1].kind is LineKind.BODY:
                    out.append(Line(LineKind.BLANK))
                out += [Line(LineKind.TABLE, part, paragraph) for part in _table_lines(paragraph, cols)]
                continue
            # Consecutive bullets are one list, not separate blocks.
            bullets = paragraph.lstrip(" ").startswith(_BULLET) and previous_bullet
            if not bullets and out and out[-1].kind in (LineKind.BODY, LineKind.TABLE):
                out.append(Line(LineKind.BLANK))
            previous_bullet = paragraph.lstrip(" ").startswith(_BULLET)
            out += [Line(LineKind.BODY, part) for part in _body(paragraph, cols)]

    for line in out:
        if len(line.text) > cols:
            raise ValueError(f"line exceeds {cols} columns: {line.text!r}")
    return out
