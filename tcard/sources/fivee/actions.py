"""5e.tools actions to Cards."""

from __future__ import annotations

from ...model import Card
from . import cache
from .fields import sections, source_field
from .spell import format_time


def records(refresh: bool = False) -> list[dict]:
    return cache.load_json("actions.json", refresh).get("action", [])


def to_card(record: dict) -> Card:
    fields: list[tuple[str, str]] = []
    if record.get("time"):
        fields.append(("Time", format_time(record["time"])))
    source = source_field(record)
    if source:
        fields.append(source)
    return Card(str(record.get("name", "Untitled")), "Action", fields, sections(record.get("entries")))
