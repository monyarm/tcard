"""5e.tools variant rule record to Card."""

from __future__ import annotations

from ...model import Card
from . import cache, fields

# ruleType codes: core, optional, variant, and variant-optional.
SUBTITLES = {"C": "Rule", "O": "Optional Rule", "V": "Variant Rule", "VO": "Variant Rule"}


def records(refresh: bool = False) -> list[dict]:
    return cache.load_json("variantrules.json", refresh).get("variantrule", [])


def to_card(record: dict) -> Card:
    subtitle = SUBTITLES.get(str(record.get("ruleType") or ""), "Rule")
    return Card(record["name"], subtitle, [], fields.sections(record.get("entries")))
