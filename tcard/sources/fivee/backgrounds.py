"""5e.tools background record to Card."""

from __future__ import annotations

from ...model import Card
from .cache import load_json
from .fields import sections
from .index import _dedupe


def records(refresh: bool = False) -> list[dict]:
    payload = load_json("backgrounds.json", refresh)
    return _dedupe(payload.get("background", []))


def to_card(record: dict) -> Card:
    fields = []
    return Card(
        record.get("name", "Background"),
        "Background",
        fields,
        sections(record.get("entries", [])),
    )
