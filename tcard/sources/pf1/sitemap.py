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

# Official class-feature families that deserve their own kind, like 5e's invocations.
FAMILY_KINDS = {
    "rogue-talents": "rogue_talent",
    "rage-powers": "rage_power",
    "magus-arcana": "magus_arcana",
    "ninja-tricks": "ninja_trick",
    "bardic-masterpieces": "bardic_masterpiece",
    "slayer-talents": "slayer_talent",
    "ki-powers": "ki_power",
    "wild-talents": "wild_talent",
    "arcane-schools": "arcane_school",
    "arcane-exploits": "arcanist_exploit",
    "weapon-training": "weapon_training",
}
_SINGULAR = {
    "talents": "talent", "tricks": "trick", "powers": "power", "discoveries": "discovery",
    "mysteries": "mystery", "curses": "curse", "hexes": "hex", "schools": "school",
    "exploits": "exploit", "spirits": "spirit", "domains": "domain", "bloodlines": "bloodline",
    "orders": "order", "masterpieces": "masterpiece", "techniques": "technique", "deeds": "deed",
}
# A bare "discovery" means nothing without the class that grants it.
GENERIC = frozenset(("discovery", "hex", "mystery", "curse", "bloodline", "order", "spirit", "domain", "school", "exploit"))


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


SUFFIXES = (
    "-archetypes", "-archetype", "-prestige-class", "-racial-trait", "-trait", "-traits",
    "-ex", "-su", "-sp", "-uc", "-um", "-oa",
)
# Index pages for a family carry the family word, or a publisher name.
PUBLISHER_HINTS = ("publishing", "press", "llc", "d20pfsrd", "games", "legendary", "paizo", "fan")
# Hex collections are official but not published under a "paizo-" set name.
OFFICIAL_SETS = frozenset(("hexes", "common-hexes", "major-hexes", "grand-hexes", "grand-hex"))


def _slug(url: str) -> str:
    return url.rstrip("/").rsplit("/", 1)[-1]


def _strip_suffix(slug: str) -> str:
    for suffix in SUFFIXES:
        if slug.endswith(suffix):
            return slug[: -len(suffix)]
    return slug


def name_for(url: str) -> str:
    return _strip_suffix(_slug(url)).replace("-", " ").title()


def _segments(url: str) -> list[str]:
    path = url.split("://", 1)[-1].split("/", 1)[-1]
    return [part for part in path.split("/") if part]


def _race_words() -> set[str]:
    words: set[str] = set()
    for url in urls():
        segs = _segments(url)
        if segs[:1] == ["races"] and len(segs) >= 3:
            words.update(segs[-1].split("-"))
    return words


def _trait_name(url: str, race_words: set[str], group: str = "") -> str:
    tokens = [token for token in _strip_suffix(_slug(url)).split("-") if token]
    # "arcane-dabbler-elf-racial-trait" -> "Arcane Dabbler"
    while tokens and (tokens[-1] in race_words or (group and tokens[-1] == group)):
        tokens.pop()
    return " ".join(tokens).title()


def _trait_group(segs: list[str]) -> str:
    group = segs[1] if len(segs) > 1 else ""
    for suffix in ("-traits", "-trait"):
        if group.endswith(suffix):
            group = group[: -len(suffix)]
    return "racial" if group == "race" else group


def family_kind(segs: list[str]) -> str | None:
    """Kind id for a class-feature page, or None when it is not one."""
    if not segs or segs[0] != "classes" or "archetypes" in segs:
        return None
    if len(segs) < 5:
        return None
    family = segs[3]
    slug = segs[-1]
    leaf = family.split("-")[-1]
    # Collection index pages end with the family words ("...-rogue-talents", "hexes").
    if slug == family or slug in OFFICIAL_SETS or slug.endswith(leaf) or slug.endswith(family):
        return None
    # Collection pages whose slug repeats the family name, e.g. magus-arcana-samurai-sheepdog.
    if slug.startswith(family + "-"):
        return None
    if any(hint in slug for hint in PUBLISHER_HINTS):
        return None
    if len(segs) > 5:
        # Official families group leaves under "paizo-<family>" or a plain hex set.
        collection = segs[-2]
        if not (collection.startswith("paizo-") or collection in OFFICIAL_SETS or collection == family):
            return None
    kind = FAMILY_KINDS.get(family)
    if kind:
        return kind
    singular = _SINGULAR.get(family.split("-")[-1])
    if not singular:
        return None
    if singular in GENERIC:
        return f"{segs[2]}_{singular}".replace("-", "_")
    return singular


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
    if kind == "monster":
        return head == "bestiary" and len(segs) >= 4 and segs[1] == "monster-listings"
    if kind == "archetype":
        if segs[0] != "classes" or "archetypes" not in segs:
            return False
        index = segs.index("archetypes")
        # Publisher-named sets are 3PP; official sets are "paizo-<class>-archetypes".
        tail = segs[index + 1:]
        return len(tail) == 2 and tail[0].startswith("paizo-")
    if kind == "prestige_class":
        return len(segs) in (4, 5) and segs[:2] == ["classes", "prestige-classes"] and segs[-1] not in BOOKS
    if kind in ("feat", "trait", "equipment", "magic_item", "race", "archetype", "prestige_class"):
        return False
    # Anything left is a class-feature family kind (rogue_talent, witch_hex, ...).
    return family_kind(segs) == kind


def records(kind: str, refresh: bool = False) -> list[dict]:
    out: list[dict] = []
    race_words: set[str] | None = None
    for url in urls(refresh):
        segs = _segments(url)
        if not _match(kind, segs):
            continue
        name = name_for(url)
        record = {"name": name, "url": url}
        if kind == "trait":
            group = _trait_group(segs)
            # Campaign traits nest under an adventure-path name, so len 3 is the book, not a trait.
            if group == "campaign" and len(segs) < 4:
                continue
            if race_words is None:
                race_words = _race_words()
            record["name"] = _trait_name(url, race_words, group)
            record["group"] = group
        elif segs[0] == "classes":
            family = family_kind(segs)
            if family:
                record["family_kind"] = family
                record["class"] = segs[2].replace("-", " ")
                record["family"] = segs[3].replace("-", " ")
        out.append(record)
    return out
