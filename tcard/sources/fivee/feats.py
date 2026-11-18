"""5e.tools feats to Cards."""

from __future__ import annotations

from ...model import Card
from . import cache
from .fields import format_prereq, sections, source_field

CATEGORIES = {"O": "Origin Feat", "G": "General Feat", "FS": "Fighting Style Feat", "EB": "Epic Boon Feat"}


def records(refresh: bool = False) -> list[dict]:
    return cache.load_json("feats.json", refresh).get("feat", [])


def to_card(record: dict) -> Card:
    category = str(record.get("category") or "")
    subtitle = CATEGORIES.get(category, category.title())
    fields: list[tuple[str, str]] = []
    prerequisite = format_prereq(record.get("prerequisite"))
    if prerequisite:
        fields.append(("Prerequisite", prerequisite))
    source = source_field(record)
    if source:
        fields.append(source)
    return Card(str(record.get("name", "Untitled")), subtitle, fields, sections(record.get("entries")))
