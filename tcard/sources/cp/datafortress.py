"""datafortress2020 bio.htm: humanity cost, surgery and effect prose."""

from __future__ import annotations

import html
import re

from ...names import normalize
from . import cache

PAGE = "https://www.datafortress2020.com/bio.htm"
_ROW = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S | re.I)
_CELL = re.compile(r"<t[dh][^>]*>(.*?)</t[dh]>", re.S | re.I)
_TAG = re.compile(r"<[^>]+>")
_INDEX: dict[str, dict] | None = None


def _clean(cell: str) -> str:
    text = html.unescape(_TAG.sub("", cell))
    return re.sub(r"\s+", " ", text).strip()


def parse(markup: str) -> list[dict]:
    """Items as {name, cost, hc, surgery, effect} from the row pairs."""
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


def records(refresh: bool = False) -> list[dict]:
    global _INDEX
    if refresh or _INDEX is None:
        _INDEX = {normalize(item["name"]): item for item in parse(cache.raw(PAGE, refresh))}
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
