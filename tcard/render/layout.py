"""Card to width-checked Lines. Single layout pass, shared by every backend."""

from __future__ import annotations

import unicodedata

from ..model import Card, Line, LineKind

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
    "\u2022": "*",
    "\u00b7": "*",
    "\u25cf": "*",
    "\u00d7": "x",
    "\u00f7": "/",
    "\u00b0": " degrees",
    "\u00b1": "+/-",
    "\u00a0": " ",
    "\u2044": "/",
}


def fold(text: str) -> str:
    """Transliterate typography, then drop anything still non-ASCII."""
    text = text.translate(str.maketrans(_FOLD))
    text = unicodedata.normalize("NFKD", text)
    return text.encode("ascii", "ignore").decode("ascii")


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
        raise ValueError(f"{cols} columns too narrow for field {label!r}")
    out: list[Line] = []
    prefix = head
    limit = room
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
    return out or [Line(LineKind.FIELD, head.rstrip())]


def layout(card: Card, cols: int = 32, brief: bool = False) -> list[Line]:
    """Build the line list. Raises ValueError instead of truncating."""
    if cols < 4:
        raise ValueError(f"cols must be at least 4, got {cols}")

    out: list[Line] = []
    out += [Line(LineKind.TITLE, part) for part in wrap(card.title, cols)]
    out.append(Line(LineKind.RULE, "=" * cols))
    if card.subtitle:
        out += [Line(LineKind.SUBTITLE, part) for part in wrap(card.subtitle, cols)]
    out.append(Line(LineKind.RULE, "-" * cols))
    for label, value in card.fields:
        out += _field(label, value, cols)

    sections: list[tuple[str, list[str]]] = []
    if not brief:
        for heading, paragraphs in card.sections:
            body = [p for p in paragraphs if p.strip()]
            if body:
                sections.append((heading, body))

    # Only separate fields from something; a trailing rule on a brief card is noise.
    if card.fields and sections:
        out.append(Line(LineKind.RULE, "-" * cols))

    for heading, body in sections:
        if heading:
            if out:
                out.append(Line(LineKind.RULE, "-" * cols))
            out += [Line(LineKind.SECTION, part) for part in wrap(heading, cols)]
        for paragraph in body:
            if out and out[-1].kind is LineKind.BODY:
                out.append(Line(LineKind.BLANK))
            out += [Line(LineKind.BODY, part) for part in wrap(paragraph, cols)]

    for line in out:
        if len(line.text) > cols:
            raise ValueError(f"line exceeds {cols} columns: {line.text!r}")
        if not line.text.isascii():
            raise ValueError(f"non-ascii line: {line.text!r}")
    return out
