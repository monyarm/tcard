"""5e.tools optional features: invocations, metamagic, maneuvers and friends."""

from __future__ import annotations

from ...model import Card
from ..base import Kind
from . import cache
from .fields import format_prereq, sections, source_field

LABELS = {
    "EI": "Eldritch Invocation",
    "MM": "Metamagic",
    "MV:B": "Maneuver",
    "FS:F": "Fighting Style",
    "FS:R": "Fighting Style",
    "FS:P": "Fighting Style",
    "FS:B": "Fighting Style",
    "PB": "Pact Boon",
    "AI": "Artificer Infusion",
    "RN": "Rune",
    "AS": "Arcane Shot",
    "ED": "Elemental Discipline",
    "RP": "Renown Boon",
}

KINDS = {
    "invocation": ("EI",),
    "metamagic": ("MM",),
    "maneuver": ("MV:B",),
    "fighting_style": ("FS:F", "FS:R", "FS:P", "FS:B"),
    "pact_boon": ("PB",),
    "infusion": ("AI",),
    "rune": ("RN",),
    "arcane_shot": ("AS",),
    "elemental_discipline": ("ED",),
    "renown_boon": ("RP",),
}


def records(refresh: bool = False) -> list[dict]:
    return cache.load_json("optionalfeatures.json", refresh).get("optionalfeature", [])


def to_card(record: dict) -> Card:
    types = record.get("featureType") or []
    subtitle = next((LABELS[code] for code in types if code in LABELS), "Optional Feature")
    fields: list[tuple[str, str]] = []
    prerequisite = format_prereq(record.get("prerequisite"))
    if prerequisite:
        fields.append(("Prerequisite", prerequisite))
    source = source_field(record)
    if source:
        fields.append(source)
    return Card(str(record.get("name", "Untitled")), subtitle, fields, sections(record.get("entries")))


class OptionalKind(Kind):
    def __init__(self, kind_id: str, codes: tuple[str, ...]) -> None:
        self.id = kind_id
        self.codes = set(codes)

    def records(self, refresh: bool = False) -> list[dict]:
        return [record for record in records(refresh) if self.codes & set(record.get("featureType") or [])]

    def card(self, record: dict) -> Card:
        return to_card(record)
