"""Pathfinder 1e via d20pfsrd: sitemap index, page on demand."""

from __future__ import annotations

from ..base import Kind
from ...names import normalize, split_path
from . import cache, page, sitemap

SYSTEM_ID = "pf:1e"
ALIASES = ("pf1",)


class PageKind(Kind):
    """Any d20pfsrd record: one sitemap URL, one cached page, one Card."""

    def __init__(self, kind_id: str) -> None:
        self.id = kind_id

    def records(self, refresh: bool = False) -> list[dict]:
        return sitemap.records(self.id, refresh)

    def card(self, record: dict):
        return page.to_card(record, spell=self.id == "spell")


class ClassAbilityKind(PageKind):
    """Class features accept `class:feature` and `class:family:feature`."""

    def matches(self, records: list[dict], query: str) -> list[dict]:
        parts = split_path(query)
        if len(parts) < 2:
            return super().matches(records, query)
        *prefix, wanted = parts
        keys = {normalize(part) for part in prefix}
        pool = [
            record
            for record in records
            if keys & {normalize(record.get("class", "")), normalize(record.get("family", ""))}
        ]
        if not pool:
            return []
        return super().matches(pool, wanted)


class SpellKind(PageKind):
    """Spells keep the letter-page index: it has real titles, not slugs."""

    def records(self, refresh: bool = False) -> list[dict]:
        return cache.index(refresh)

    def card(self, record: dict):
        return page.to_card(record, spell=True)


KINDS = {
    "spell": SpellKind("spell"),
    "class_ability": ClassAbilityKind("class_ability"),
    "archetype": PageKind("archetype"),
    "feat": PageKind("feat"),
    "trait": PageKind("trait"),
    "equipment": PageKind("equipment"),
    "magic_item": PageKind("magic_item"),
    "race": PageKind("race"),
    "prestige_class": PageKind("prestige_class"),
}
