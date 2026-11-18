"""5e.tools content kinds."""

from __future__ import annotations

from ...model import Card
from ..base import Kind
from . import (
    actions,
    backgrounds,
    conditions,
    feats,
    index,
    items,
    klass,
    monster,
    optional,
    rules,
    simple,
    species,
    spell,
    subclass,
)

SYSTEM_ID = "dnd:5e"
ALIASES = ("5e",)


class SpellKind(Kind):
    id = "spell"

    def records(self, refresh: bool = False) -> list[dict]:
        return index.spell_records(refresh)

    def card(self, record: dict) -> Card:
        return spell.to_card(record)


KINDS = {
    "spell": SpellKind(),
    "item": items.ItemKind(),
    "background": simple.SimpleKind("background", backgrounds.records, backgrounds.to_card),
    "class_ability": klass.ClassAbilityKind(),
    "subclass": subclass.SubclassKind(),
    "monster": simple.SimpleKind("monster", monster.records, monster.to_card),
    "species": species.SpeciesKind(),
    "variant_rule": simple.SimpleKind("variant_rule", rules.records, rules.to_card),
    **{kind_id: optional.OptionalKind(kind_id, codes) for kind_id, codes in optional.KINDS.items()},
    "feat": simple.SimpleKind("feat", feats.records, feats.to_card),
    "condition": simple.SimpleKind("condition", conditions.records, conditions.to_card),
    "action": simple.SimpleKind("action", actions.records, actions.to_card),
}
