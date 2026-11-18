"""datafortress2020: humanity cost, surgery and effect prose for CP2020 ware.

Two pages: `bio.htm` (bioware tables) and `ultrachrome/Cyberware.html`, the
illustrated catalogue of every cybernetic item printed for the game.
"""

from __future__ import annotations

import html
import re

from ...names import normalize
from . import cache

BIO = "https://www.datafortress2020.com/bio.htm"
PAGE = "https://www.datafortress2020.com/ultrachrome/Cyberware.html"
_ROW = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S | re.I)
_CELL = re.compile(r"<t[dh][^>]*>(.*?)</t[dh]>", re.S | re.I)
_PARA = re.compile(r"<p\b[^>]*>(.*?)</p>", re.S | re.I)
_TAG = re.compile(r"<[^>]+>")
_REF = re.compile(r"^[A-Za-z]{2,5}\d{0,2}$")
_NUM = re.compile(r"^[\d.+\-/()%d]+[A-Za-z%]{0,2}$")
SURGERY = {"N": "None", "M": "Minor", "MA": "Major", "CR": "Critical"}
_INDEX: dict[str, dict] | None = None


def _clean(cell: str) -> str:
    text = html.unescape(_TAG.sub("", cell)).replace("\xa0", " ")
    # The catalogue escapes ampersands as `\&`.
    text = text.replace("\\&", "&")
    return re.sub(r"\s+", " ", text).strip()


def parse(markup: str) -> list[dict]:
    """Bioware items as {name, cost, hc, surgery, effect} from the row pairs."""
    out: list[dict] = []
    pending: dict | None = None
    for row in _ROW.findall(markup):
        cells = [_clean(cell) for cell in _CELL.findall(row)]
        if len(cells) == 4 and cells[0] != "Type":
            pending = {"name": cells[0], "cost": cells[1], "hc": cells[2],
                       "surgery": cells[3], "effect": ""}
            out.append(pending)
        elif len(cells) == 1 and pending is not None:
            if cells[0].lower() == "effect":
                continue
            if not pending["effect"]:
                pending["effect"] = cells[0]
    return [item for item in out if item["name"]]


def parse_stats(markup: str) -> list[dict]:
    """Cyberware items from the catalogue's name/stats paragraph pairs.

    A stats paragraph ends with `cost HC book`, e.g.
    `CR +2 to Death Saves for Torso wounds 1300 1d6+4 Chr1`.
    """
    out: list[dict] = []
    previous = ""
    previous_is_stats = False
    section = "Cyberware"

    def is_stats(text: str) -> bool:
        tokens = text.split()
        return (len(tokens) >= 4 and bool(_REF.match(tokens[-1]))
                and bool(_NUM.match(tokens[-2])) and bool(_NUM.match(tokens[-3])))

    for paragraph in (_clean(part) for part in _PARA.findall(markup)):
        if not paragraph:
            continue
        if paragraph.isupper() and len(paragraph) < 48:
            section = paragraph
            previous = ""
            previous_is_stats = False
            continue
        tokens = paragraph.split()
        if is_stats(paragraph):
            body = tokens[:-3]
            code = body[0].rstrip(".")
            surgery = SURGERY.get(code, "")
            if surgery:
                body = body[1:]
            # A stats line directly after another one means the item never had a
            # name paragraph, so the "name" would be the previous item's stats.
            if previous and not previous_is_stats:
                out.append({
                    "name": previous,
                    "cost": tokens[-3],
                    "hc": tokens[-2],
                    "surgery": surgery,
                    "effect": " ".join(body).strip(" -"),
                    "type": section,
                })
            previous_is_stats = True
        else:
            previous_is_stats = False
        previous = paragraph
    return [item for item in out if item["name"]]


def records(refresh: bool = False) -> list[dict]:
    global _INDEX
    if refresh or _INDEX is None:
        items = parse(cache.raw(BIO, refresh)) + parse_stats(cache.raw(PAGE, refresh))
        _INDEX = {}
        for item in items:
            if not item["name"]:
                continue
            key = normalize(item["name"])
            existing = _INDEX.get(key)
            if existing is None:
                _INDEX[key] = dict(item)
                continue
            # Both pages overlap; keep whichever field each one actually fills.
            for field in ("cost", "hc", "surgery", "effect"):
                if not existing.get(field):
                    existing[field] = item.get(field)
    return list(_INDEX.values())


def lookup(name: str) -> dict | None:
    """Exact name first, then the shortest containing name."""
    records()
    assert _INDEX is not None
    key = normalize(name)
    if key in _INDEX:
        return _INDEX[key]
    hits = [item for other, item in _INDEX.items() if key and (key in other or other in key)]
    return min(hits, key=lambda item: len(item["name"]), default=None)
