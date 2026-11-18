"""Pathfinder 2e: cards from the foundryvtt/pf2e compendium packs."""

from __future__ import annotations

from ...model import Card
from ..base import Kind
from . import cache, cards

SYSTEM_ID = "pf:2e"
ALIASES = ("pf2",)

# Core bestiaries plus every adventure path bestiary, added on first monster lookup.
BESTIARY = (
    "pathfinder-monster-core",
    "pathfinder-monster-core-2",
    "pathfinder-npc-core",
    "pathfinder-bestiary",
    "pathfinder-bestiary-2",
    "pathfinder-bestiary-3",
    "npc-gallery",
    "*-bestiary",
)


class PackKind(Kind):
    """One compendium pack (or a family of packs) as a card kind."""

    def __init__(self, kind_id: str, packs: tuple[str, ...]) -> None:
        self.id = kind_id
        self.packs = packs

    def records(self, refresh: bool = False) -> list[dict]:
        out: list[dict] = []
        for path in cache.files(self.packs, refresh):
            item = cache.load(path)
            if item.get("name"):
                out.append({"name": str(item["name"]), "path": path})
        return out

    def card(self, record: dict) -> Card:
        return cards.to_card(cache.load(record["path"]))


KINDS: dict[str, Kind] = {
    "spell": PackKind("spell", ("spells",)),
    "feat": PackKind("feat", ("feats",)),
    "equipment": PackKind("equipment", ("equipment",)),
    "ancestry": PackKind("ancestry", ("ancestries",)),
    "heritage": PackKind("heritage", ("heritages",)),
    "background": PackKind("background", ("backgrounds",)),
    "class": PackKind("class", ("classes",)),
    "class_feature": PackKind("class_feature", ("class-features",)),
    "deity": PackKind("deity", ("deities",)),
    "monster": PackKind("monster", BESTIARY),
    "condition": PackKind("condition", ("conditions",)),
    "action": PackKind("action", ("actions",)),
    "hazard": PackKind("hazard", ("hazards",)),
}
