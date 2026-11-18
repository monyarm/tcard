"""Minimal HTML to text blocks, enough for d20pfsrd stat pages."""

from __future__ import annotations

import html as htmlmod
import re

from ...model import Table

TAG = re.compile(r"<[^>]+>")
BLOCK = re.compile(r"</?(?:br|p|div|li|tr|td|h[1-6])\b[^>]*>", re.I)
SPACE = re.compile(r"\s+")


def text(fragment: str) -> str:
    """Tags stripped, block tags become spaces, entities decoded."""
    return SPACE.sub(" ", htmlmod.unescape(TAG.sub("", BLOCK.sub(" ", fragment)))).strip()


def paragraphs(markup: str) -> list[tuple[str, str]]:
    """Every <p> as (class attribute, inner html)."""
    found = re.findall(r"<p([^>]*)>(.*?)</p>", markup, re.S)
    classes = [re.search(r'class="([^"]*)"', attrs) for attrs, _ in found]
    return [(match.group(1) if match else "", inner) for match, (_, inner) in zip(classes, found)]


_MARK = "\x00"


def _labelled_chunk(fragment: str) -> list[tuple[str | None, str]]:
    """Split a stat paragraph at each bold label, or return it as prose.

    d20pfsrd separates entries with <br />, "; " or just spaces, so the bold
    run itself is the reliable boundary.
    """
    fragment = re.sub(r"<(b|strong)>\s*</\1>", "", fragment, flags=re.S)
    bolded = re.sub(r"<(b|strong)>(.*?)</\1>", lambda m: _MARK + text(m.group(2)) + _MARK, fragment, flags=re.S)
    chunks = text(bolded).split(_MARK)
    out: list[tuple[str | None, str]] = []
    prefix = chunks[0].strip(" ;")
    if prefix:
        out.append((None, prefix))
    for index in range(1, len(chunks) - 1, 2):
        label = chunks[index].strip().rstrip(":").strip()
        value = chunks[index + 1].strip().lstrip(": ").rstrip(" ,;").strip()
        if label:
            out.append((label, value))
    return out


def labelled(fragment: str) -> list[tuple[str | None, str]]:
    """Bold labels bound entries; <br> bounds them too on stat blocks."""
    out: list[tuple[str | None, str]] = []
    for chunk in re.split(r"<br\s*/?>", fragment):
        out.extend(_labelled_chunk(chunk))
    return out


BLOCK = re.compile(r"<(p|table)\b([^>]*)>(.*?)</\1>", re.S | re.I)
ROW = re.compile(r"<tr\b[^>]*>(.*?)</tr>", re.S | re.I)
CELL = re.compile(r"<(t[hd])\b[^>]*>(.*?)</t[hd]>", re.S | re.I)


def blocks(markup: str) -> list[tuple[str, str, str]]:
    """Paragraphs and tables in document order: (tag, class, inner html)."""
    out = []
    for tag, attrs, inner in BLOCK.findall(markup):
        css = re.search(r'class="([^"]*)"', attrs)
        out.append((tag.lower(), css.group(1) if css else "", inner))
    return out


def table(inner: str) -> Table:
    rows: list[list[str]] = []
    header = False
    for row_html in ROW.findall(inner):
        cells = CELL.findall(row_html)
        if any(tag.lower() == "th" for tag, _ in cells):
            header = True
        rows.append([text(cell) for _, cell in cells])
    return Table([row for row in rows if row], header=header)
