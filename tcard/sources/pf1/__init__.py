"""Pathfinder 1e: one parser, many sitemap-filtered kinds."""

from __future__ import annotations

from ...names import normalize, split_path
from ..base import Kind
from . import cache, page, sitemap

SYSTEM_ID = "pf:1e"
ALIASES = ("pf1",)


class PageKind(Kind):
    def __init__(self, kind_id: str) -> None:
        self.id = kind_id

    def records(self, refresh: bool = False) -> list[dict]:
        return sitemap.records(self.id, refresh)

    def card(self, record: dict):
        return page.to_card(record, spell=self.id == "spell")


class SpellKind(PageKind):
    def records(self, refresh: bool = False) -> list[dict]:
        return cache.index(refresh)

    def card(self, record: dict):
        return page.to_card(record, spell=True)


class FamilyKind(PageKind):
    """A class-feature family; accepts `class:feature` and `class:family:feature`."""

    def matches(self, records: list[dict], query: str) -> list[dict]:
        parts = split_path(query)
        if len(parts) >= 2:
            keys = {normalize(part) for part in parts[:-1]}
            pool = [
                record
                for record in records
                if keys & {normalize(str(record.get("class", ""))), normalize(str(record.get("family", "")))}
            ]
            if pool:
                return super().matches(pool, parts[-1])
        return super().matches(records, query)


class TraitKind(PageKind):
    """Accepts `group:name`, e.g. trait:magic:spell_focus or trait:racial:arcane_dabbler."""

    def matches(self, records: list[dict], query: str) -> list[dict]:
        parts = split_path(query)
        if len(parts) >= 2:
            group = normalize(parts[0])
            pool = [record for record in records if normalize(str(record.get("group", ""))) == group]
            if pool:
                return super().matches(pool, " ".join(parts[1:]))
        return super().matches(records, query)


# Family kinds observed on d20pfsrd; each one is its own kind so talents are not lumped together.
FAMILIES = (
    "alchemist_discovery",
    "arcane_school",
    "arcanist_exploit",
    "bardic_masterpiece",
    "bloodrager_bloodline",
    "cavalier_order",
    "cleric_domain",
    "magus_arcana",
    "ninja_trick",
    "oracle_curse",
    "oracle_mystery",
    "rage_power",
    "rogue_talent",
    "samurai_order",
    "shaman_spirit",
    "slayer_talent",
    "sorcerer_bloodline",
    "talent",
    "witch_hex",
    "wizard_discovery",
)

KINDS: dict[str, Kind] = {
    "spell": SpellKind("spell"),
    "feat": PageKind("feat"),
    "trait": TraitKind("trait"),
    "equipment": PageKind("equipment"),
    "magic_item": PageKind("magic_item"),
    "race": PageKind("race"),
    "archetype": PageKind("archetype"),
    "prestige_class": PageKind("prestige_class"),
}
KINDS.update({kind_id: FamilyKind(kind_id) for kind_id in FAMILIES})
