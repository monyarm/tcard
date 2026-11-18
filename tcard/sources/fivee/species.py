"""5e.tools race record to Card. The 2024 books call these species."""

from __future__ import annotations

from ...model import Card
from ...names import normalize, split_path
from ..base import Kind
from . import cache, fields, index

SIZES = {"T": "Tiny", "S": "Small", "M": "Medium", "L": "Large", "H": "Huge", "G": "Gargantuan"}
ABILITY = {"str": "Str", "dex": "Dex", "con": "Con", "int": "Int", "wis": "Wis", "cha": "Cha"}


def records(refresh: bool = False) -> list[dict]:
    data = cache.load_json("races.json", refresh)
    races = data.get("race", [])
    base = {(race["name"], race["source"]): race for race in races}
    out = list(races)
    for sub in data.get("subrace", []):
        name, race = sub.get("name"), sub.get("raceName")
        if not name or not race:
            continue
        parent = base.get((race, sub.get("raceSource")))
        out.append({
            "name": f"{name} {race}",
            "source": sub.get("source", ""),
            "subrace": name,
            "race": race,
            "parent": parent,
            "record": sub,
        })
    return index._dedupe(out)


def _combined_ability(parent: dict, sub: dict) -> str:
    scores: dict[str, int] = {}
    for block in (parent.get("ability") or []) + (sub.get("ability") or []):
        for key, value in block.items():
            if isinstance(value, int):
                scores[key] = scores.get(key, 0) + value
    return ", ".join(f"{ABILITY.get(key, key)} {value:+d}" for key, value in scores.items())


def _combined_resistances(parent: dict, sub: dict) -> str:
    return _resistances({"resist": (parent.get("resist") or []) + (sub.get("resist") or [])})


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


def _subrace_card(record: dict) -> Card:
    parent = record.get("parent") or {}
    sub = record["record"]
    fields_out: list[tuple[str, str]] = []
    for label, value in (
        ("Type", _types(parent) or _types(sub)),
        ("Size", _size(sub) or _size(parent)),
        ("Speed", _speed(sub) or _speed(parent)),
        ("Darkvision", f"{(sub.get('darkvision') or parent.get('darkvision'))} ft."
         if (sub.get("darkvision") or parent.get("darkvision")) else ""),
        ("Resistances", _combined_resistances(parent, sub)),
        ("Ability Scores", _combined_ability(parent, sub)),
    ):
        if value:
            fields_out.append((label, value))
    sections = fields.sections(parent.get("entries")) + fields.sections(sub.get("entries"))
    return Card(record["name"], f"{record['race']} Subrace", fields_out, sections)


def to_card(record: dict) -> Card:
    if record.get("subrace"):
        return _subrace_card(record)
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


class SpeciesKind(Kind):
    def __init__(self) -> None:
        self.id = "species"

    def records(self, refresh: bool = False) -> list[dict]:
        return records(refresh)

    def card(self, record: dict) -> Card:
        return to_card(record)

    def matches(self, records: list[dict], query: str) -> list[dict]:
        parts = split_path(query)
        if len(parts) == 2:
            race, wanted = parts
            pool = [r for r in records
                    if r.get("subrace") and normalize(r.get("race", "")) == race]
            if pool:
                return super().matches(pool, wanted)
        return super().matches(records, query)
