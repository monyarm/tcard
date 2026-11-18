"""5e.tools conditions to Cards."""

from __future__ import annotations

from ...model import Card
from . import cache
from .fields import sections, source_field


def records(refresh: bool = False) -> list[dict]:
    return cache.load_json("conditionsdiseases.json", refresh).get("condition", [])


def to_card(record: dict) -> Card:
    fields: list[tuple[str, str]] = []
    source = source_field(record)
    if source:
        fields.append(source)
    return Card(str(record.get("name", "Untitled")), "Condition", fields, sections(record.get("entries")))
