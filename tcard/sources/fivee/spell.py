"""5e.tools spell record to Card."""

from __future__ import annotations

from ...model import Card
from .entries import flatten
from .tags import render_tags

SCHOOLS = {
    "A": "Abjuration",
    "C": "Conjuration",
    "D": "Divination",
    "E": "Enchantment",
    "V": "Evocation",
    "I": "Illusion",
    "N": "Necromancy",
    "T": "Transmutation",
}

_UNITS = {"bonus": "bonus action"}


def school_name(code: str) -> str:
    return SCHOOLS.get(code, code or "Unknown")


def _plural(amount: int, unit: str) -> str:
    return unit if amount == 1 else unit + "s"


def format_time(value: list) -> str:
    parts = []
    for item in value or []:
        number = item.get("number", 1)
        unit = item.get("unit", "action")
        if unit in _UNITS:
            parts.append(f"{number} {_UNITS[unit]}")
        else:
            parts.append(f"{number} {_plural(number, unit)}")
    text = " or ".join(parts) if parts else "Special"
    condition = value[0].get("condition") if value else None
    if condition:
        text += f", {condition}"
    return text


def format_range(value: dict) -> str:
    distance = value.get("distance") or {}
    amount = distance.get("amount")
    kind = distance.get("type", "")
    shape = value.get("type", "point")
    if amount and kind in ("feet", "miles"):
        if shape not in ("point", "self"):
            return f"Self ({amount}-foot {shape})"
        return f"{amount} {kind}"
    return {
        "touch": "Touch",
        "self": "Self",
        "sight": "Sight",
        "unlimited": "Unlimited",
    }.get(kind, "Special")


def format_duration(value: list) -> str:
    parts = []
    for item in value or []:
        kind = item.get("type")
        if kind == "instant":
            parts.append("Instantaneous")
        elif kind == "permanent":
            parts.append("Permanent")
        elif kind == "timed":
            timed = item.get("duration") or {}
            amount = timed.get("amount", 1)
            unit = timed.get("type", "minute")
            text = f"up to {amount} {_plural(amount, unit)}"
            if item.get("concentration"):
                text = "Concentration, " + text
            else:
                text = text[0].upper() + text[1:]
            parts.append(text)
        else:
            parts.append("Special")
    return " or ".join(parts) if parts else "Special"


def format_components(value: dict) -> str:
    parts = [letter.upper() for letter in ("v", "s") if value.get(letter)]
    material = value.get("m")
    if isinstance(material, dict):
        material = material.get("text", "")
    if material:
        parts.append(f"M ({material})")
    elif value.get("m") is not None:
        parts.append("M")
    return ", ".join(parts)


def _sections(nodes: object) -> list[tuple[str, list[str]]]:
    return [(heading, [render_tags(p) for p in paragraphs]) for heading, paragraphs in flatten(nodes)]


def to_card(record: dict) -> Card:
    level = record.get("level", 0)
    school = school_name(record.get("school", ""))
    subtitle = f"{school} Cantrip" if level == 0 else f"Level {level} {school}"
    fields = [
        ("Casting Time", format_time(record.get("time", []))),
        ("Range", format_range(record.get("range") or {})),
        ("Components", format_components(record.get("components") or {})),
        ("Duration", format_duration(record.get("duration", []))),
    ]
    source = record.get("source")
    if source:
        page = record.get("page")
        fields.append(("Source", f"{source} p.{page}" if page else source))
    fields = [(label, render_tags(value)) for label, value in fields]
    sections = _sections(record.get("entries", []))
    sections += _sections(record.get("entriesHigherLevel", []))
    return Card(record.get("name", "Untitled"), subtitle, fields, sections)
