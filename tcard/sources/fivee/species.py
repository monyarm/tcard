"""5e.tools race record to Card. The 2024 books call these species."""

from __future__ import annotations

from ...model import Card
from . import cache, fields, index

SIZES = {"T": "Tiny", "S": "Small", "M": "Medium", "L": "Large", "H": "Huge", "G": "Gargantuan"}
ABILITY = {"str": "Str", "dex": "Dex", "con": "Con", "int": "Int", "wis": "Wis", "cha": "Cha"}


def records(refresh: bool = False) -> list[dict]:
    return index._dedupe(cache.load_json("races.json", refresh).get("race", []))


def _types(record: dict) -> str:
    types = record.get("creatureTypes") or record.get("type") or []
    if isinstance(types, str):
        types = [types]
    return ", ".join(str(kind).capitalize() for kind in types)


def _size(record: dict) -> str:
    return " or ".join(SIZES.get(code, str(code)) for code in record.get("size", []))


def _speed(record: dict) -> str:
    speed = record.get("speed")
    if isinstance(speed, int):
        return f"{speed} ft."
    parts = [f"{value} ft." if key == "walk" else f"{key} {value} ft." for key, value in (speed or {}).items()]
    return ", ".join(parts)


def _resistances(record: dict) -> str:
    out = []
    for entry in record.get("resist") or []:
        if isinstance(entry, str):
            out.append(entry)
        elif isinstance(entry, dict) and entry.get("choose"):
            out.append("one of " + ", ".join(entry["choose"].get("from", [])))
    return ", ".join(out)


def _ability(record: dict) -> str:
    out = []
    for block in record.get("ability") or []:
        for key, value in block.items():
            if isinstance(value, int):
                out.append(f"{ABILITY.get(key, key)} {value:+d}")
    return ", ".join(out)


def to_card(record: dict) -> Card:
    fields_out: list[tuple[str, str]] = []
    for label, value in (
        ("Type", _types(record)),
        ("Size", _size(record)),
        ("Speed", _speed(record)),
        ("Darkvision", f"{record['darkvision']} ft." if record.get("darkvision") else ""),
        ("Resistances", _resistances(record)),
        ("Ability Scores", _ability(record)),
    ):
        if value:
            fields_out.append((label, value))
    return Card(record["name"], "Species", fields_out, fields.sections(record.get("entries")))
