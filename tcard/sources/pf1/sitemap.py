"""d20pfsrd sitemap index, cached once, filtered per content kind."""

from __future__ import annotations

import json
import re
from pathlib import Path

from ...errors import TcardError
from . import cache

BASE = "https://www.d20pfsrd.com"
_CACHE_NAME = "urls.json"
_LOC = re.compile(r"<loc>\s*([^<\s]+)\s*</loc>")
# Community (3PP) and staging paths, plus the site's own debris.
SKIP = tuple(part.lower() for part in ("/extras/", "/work-area/", "/s-class-characters/", "3rd-party", "__trashed"))
# Landing pages that list magic items rather than describe one.
MAGIC_GROUPS = frozenset(
    ("artifacts", "major-artifacts", "minor-artifacts", "rings", "rods", "staves", "wands",
     "wondrous-items", "cursed-items", "intelligent-items", "specific-cursed-items", "armor", "weapons")
)
# Book-code segments that introduce a group of prestige classes.
BOOKS = frozenset(("apg", "acg", "arg", "uc", "um", "ui", "oa", "iswg", "core-rulebook", "inner-sea-combat"))


def _wanted(url: str) -> bool:
    lowered = url.lower()
    return "/wp-sitemap-posts-page-" in lowered or lowered.endswith("sitemap.xml")


def urls(refresh: bool = False) -> list[str]:
    path = cache.cache_dir() / _CACHE_NAME
    if not refresh and path.exists():
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            path.unlink(missing_ok=True)

    children = [url for url in _LOC.findall(cache.fetch(f"{BASE}/sitemap.xml")) if "/wp-sitemap-posts-page-" in url]
    if not children:
        raise TcardError("d20pfsrd sitemap listed no page sitemaps", 3)
    found: list[str] = []
    for child in children:
        found.extend(_LOC.findall(cache.fetch(child)))
    found = [url for url in found if not any(part in url.lower() for part in SKIP)]
    found.sort()

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(found))
    tmp.replace(path)
    return found


def name_for(url: str) -> str:
    slug = url.rstrip("/").rsplit("/", 1)[-1]
    for suffix in ("-archetypes", "-archetype", "-prestige-class", "-ex", "-uc", "-um", "-oa"):
        if slug.endswith(suffix):
            slug = slug[: -len(suffix)]
            break
    return slug.replace("-", " ").title()


def _segments(url: str) -> list[str]:
    path = url.split("://", 1)[-1].split("/", 1)[-1]
    return [part for part in path.split("/") if part]


def _match(kind: str, segs: list[str]) -> bool:
    if not segs:
        return False
    head, last = segs[0], segs[-1]
    if kind == "feat":
        return head == "feats" and len(segs) >= 3
    if kind == "trait":
        return head == "traits" and len(segs) >= 3
    if kind == "equipment":
        return head == "equipment" and len(segs) >= 3
    if kind == "magic_item":
        return head == "magic-items" and len(segs) >= 3 and last not in MAGIC_GROUPS
    if kind == "race":
        return head == "races" and len(segs) >= 3
    if kind == "archetype":
        if segs[0] != "classes" or "archetypes" not in segs:
            return False
        index = segs.index("archetypes")
        return len(segs) == index + 2
    if kind == "prestige_class":
        return len(segs) in (4, 5) and segs[:2] == ["classes", "prestige-classes"] and segs[-1] not in BOOKS
    if kind == "class_ability":
        if segs[0] != "classes" or "archetypes" in segs:
            return False
        if len(segs) == 5:
            return segs[-1] != segs[-2] and not segs[-1].startswith("paizo-")
        # Official families group their pages under "paizo-<family>".
        return len(segs) == 6 and segs[-2].startswith("paizo-")
    return False


def records(kind: str, refresh: bool = False) -> list[dict]:
    out: list[dict] = []
    for url in urls(refresh):
        segs = _segments(url)
        if not _match(kind, segs):
            continue
        record = {"name": name_for(url), "url": url}
        if kind == "class_ability":
            record["class"] = segs[2].replace("-", " ")
            record["family"] = segs[3].replace("-", " ")
        out.append(record)
    return out
