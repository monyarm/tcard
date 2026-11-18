"""Cyberpunk Wiki wikitext to description paragraphs."""

from __future__ import annotations

import difflib
import html
import re

REF = re.compile(r"<ref[^>]*>.*?</ref>|<ref[^>]*/>", re.S | re.I)
FILE = re.compile(r"\[\[(?:File|Image|Category):[^\]]*\]\]", re.I)
LINK = re.compile(r"\[\[([^\]|]+)\|([^\]]+)\]\]|\[\[([^\]]+)\]\]")
EXTERNAL = re.compile(r"\[https?://\S+\s+([^\]]+)\]")
HEADING = re.compile(r"^\s*=+.*?=+\s*$")
STOP = re.compile(r"(?i)^\s*=+\s*(gallery|references|external links|navigation|see also)")
_TIDY = re.compile(r"[^\w\s]", re.U)
# Templates that carry real text: the game edition (`{{CP|2077}}`) and a
# rarity's number (`{{R|TI|2}}`). Dropping them leaves holes like "in ."
_VALUED = (
    (re.compile(r"\{\{\s*CP\s*\|\s*(\d{4})\s*\}\}", re.I), r"\1"),
    (re.compile(r"\{\{\s*R\s*\|\s*[^|}]*\s*\|\s*(\d+)\s*\}\}", re.I), r"\1"),
)


def _shape(name: str) -> str:
    """Names compare without case, punctuation or trademark marks."""
    return " ".join(_TIDY.sub(" ", name).lower().split())


def _ratio(name: str, title: str) -> float:
    """How likely a search hit is this item, 0 to 1."""
    wanted, found = set(_shape(name).split()), set(_shape(title).split())
    if wanted == found:
        return 1.0
    shared = len(wanted & found)
    # Wiki titles add or drop one word (`Techtronica Black-Zap Glove`,
    # `Tsunami Arms Airhammer Air Pistol`); a hit with more words than that in
    # either direction (`IEC Phase 4 Infrared Laser Sight` for `Laser Sight`) is
    # a different item.
    if shared >= 2 and max(len(wanted - found), len(found - wanted)) <= 1:
        return 0.92
    return difflib.SequenceMatcher(None, " ".join(sorted(wanted)), " ".join(sorted(found))).ratio()


def closest(name: str, titles: list[str], cutoff: float = 0.88) -> str | None:
    """The search hit that really is this item: `Militech UAW` -> `Militech UAW Speargun`.

    The wiki pads titles with trademark signs, quotes and manufacturer names, so
    an exact title is rare. A hit that only shares a word (`Stun` for `Militech
    Stun Knuks`) stays out.
    """
    best, score = None, 0.0
    for title in titles:
        ratio = _ratio(name, title)
        if ratio > score:
            best, score = title, ratio
    return best if best and score >= cutoff else None


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
    for pattern, replacement in _VALUED:
        text = pattern.sub(replacement, text)
    text = _drop_templates(text)
    text = _drop_tables(text)
    text = FILE.sub("", text)
    text = LINK.sub(lambda m: m.group(2) or m.group(3), text)
    text = EXTERNAL.sub(r"\1", text)
    text = text.replace("'''", "").replace("''", "")
    text = re.sub(r"<[^>]+>", "", text)
    # The wiki leaves `&nbsp;` and friends in prose, and a raw nbsp breaks the
    # 32-column wrap.
    text = html.unescape(text).replace("\xa0", " ")

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
