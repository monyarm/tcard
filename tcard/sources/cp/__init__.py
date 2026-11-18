"""Cyberpunk 2020: stats and descriptions from Cybersmily's Datafort."""

from __future__ import annotations

from ...model import Card
from ...names import normalize
from ..base import Kind
from . import cache, cards, datafortress

SYSTEM_ID = "cp:2020"
ALIASES = ("cp2020", "cp")

# Equipment is one kind per shop category, like pf:1e class features per family.
GEAR = {
    "transport": "TRANSPORT",
    "security": "SECURITY",
    "electronics": "PERSONAL ELECTRONICS",
    "drugs": "DRUGS",
    "medical": "MEDICAL",
    "tools": "TOOLS",
    "entertainment": "ENTERTAINMENT",
    "media_equipment": "MEDIA EQUIPMENT",
    "space_gear": "SPACE GEAR",
    "surveillance": "SURVEILLANCE & B&E",
    "survival_gear": "SURVIVAL GEAR",
    "communication": "COMMUNICATION",
    "musical_equipment": "MUSICAL EQUIPMENT",
    "ocean_gear": "NUSCUBA AND OCEAN EQUIPMENT",
    "lifestyle": "LIFESTYLE",
    "demolition": "DEMOLITION",
    "remote_gear": "REMOTE/CYBERFORM EQUIPMENT",
    "furniture": "FURNITURE",
    "phone_upgrades": "PHONE UPGRADES",
    "military_gear": "MILITARY EQUIPMENT",
    "braindance": "BRAINDANCE",
    "wads": "WADS",
}


class JsonKind(Kind):
    def __init__(self, kind_id: str, loader, builder) -> None:
        self.id = kind_id
        self._loader = loader
        self._builder = builder

    def records(self, refresh: bool = False) -> list[dict]:
        return self._loader(refresh)

    def card(self, record: dict) -> Card:
        return self._builder(record)

    def matches(self, records: list[dict], query: str) -> list[dict]:
        found = super().matches(records, query)
        if found:
            return found
        # CP2020 names are full of hyphens; treat them as spaces on both sides.
        wanted = normalize(query).replace("-", " ")
        keys = [(record, normalize(str(record.get("name", ""))).replace("-", " "))
                for record in records]
        exact = [record for record, key in keys if key == wanted]
        if exact:
            return exact
        return [record for record, key in keys if key.startswith(wanted)]


def _list(relative: str):
    def load(refresh: bool = False) -> list[dict]:
        rows = cache.data(relative, refresh)
        if isinstance(rows, dict):
            # cp2020rolesext.json wraps its list: {"roles": [...]}
            rows = next((value for value in rows.values() if isinstance(value, list)), [])
        return [row for row in rows if isinstance(row, dict) and row.get("name")]
    return load


def _weapons(refresh: bool = False) -> list[dict]:
    rows = cache.data("wpns/cp2020weapons", refresh) + cache.data("data/moreguns", refresh)
    seen: set[str] = set()
    out: list[dict] = []
    for row in rows:
        key = str(row.get("name") or "").strip().casefold()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


def _shape(name: object) -> str:
    """Loose key, so "High Five, AKA The Palm Bomb" matches "High Five/The Palm Bomb"."""
    words = normalize(str(name or "")).replace("/", " ").replace(",", " ").split()
    return " ".join(word for word in words if word not in ("aka", "the", "a", "an", "and"))


def _cyberware(refresh: bool = False) -> list[dict]:
    """Cybersmily's list, plus the datafortress catalogue items it lacks."""
    rows = _list("data/cyberware")(refresh)
    seen = {_shape(row.get("name")) for row in rows}
    for item in datafortress.records(refresh):
        key = _shape(item["name"])
        if key and key not in seen:
            seen.add(key)
            rows.append({"name": item["name"], "type": item.get("type", ""),
                         "cost": item.get("cost"), "hc": item.get("hc"),
                         "surgery": item.get("surgery"), "notes": item.get("effect")})
    return rows


def _gear(category: str):
    def load(refresh: bool = False) -> list[dict]:
        return [row for row in cache.data("data/cp2020equipment", refresh)
                if str(row.get("category") or "").strip().upper() == category and row.get("name")]
    return load


KINDS: dict[str, Kind] = {
    "weapon": JsonKind("weapon", _weapons, cards.weapon),
    "armor": JsonKind("armor", _list("data/cp2020armor"), cards.armor),
    "cyberware": JsonKind("cyberware", _cyberware, cards.cyberware),
    "program": JsonKind("program", _list("apps/nrmap/cp2020programs"), cards.program),
    "vehicle": JsonKind("vehicle", _list("apps/maxmetal/cp2020-vehicles"), cards.vehicle),
    "martial_art": JsonKind("martial_art", _list("wpns/cp2020martialarts"), cards.martial_art),
    "weapon_option": JsonKind("weapon_option", _list("wpns/cp2020weaponoptions"), cards.weapon_option),
    "role": JsonKind("role", _list("apps/chargen/cp2020rolesext"), cards.role),
    "skill": JsonKind("skill", _list("apps/chargen/cp2020skills"), cards.skill),
    "corporation": JsonKind("corporation", _list("data/corporations"), cards.corporation),
}

for _kind, _category in GEAR.items():
    KINDS[_kind] = JsonKind(_kind, _gear(_category), cards.gear)
