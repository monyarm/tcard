"""Minimal HTML to text blocks, enough for d20pfsrd stat pages."""

from __future__ import annotations

import html as htmlmod
import re

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


def labelled(fragment: str) -> list[tuple[str | None, str]]:
    """Split a stat paragraph into (label, value) pairs, or (None, prose).

    d20pfsrd marks labels with <b>/<strong>, separates entries with <br />
    and separates some labels with "; ". Bold runs become markers before tags
    are stripped so the label boundary survives.
    """
    bolded = re.sub(r"<(b|strong)>(.*?)</\1>", lambda m: _MARK + text(m.group(2)) + _MARK, fragment, flags=re.S)
    out: list[tuple[str | None, str]] = []
    for line in re.split(r"<br\s*/?>", bolded):
        for part in re.split(r";\s*(?=" + _MARK + ")", line):
            flat = text(part)
            match = re.match(_MARK + r"([^" + _MARK + r"]+)" + _MARK + r"\s*(.*)", flat)
            if match:
                out.append((match.group(1), match.group(2)))
            elif flat:
                out.append((None, flat))
    return out
