"""Cyberpunk 2020 records to Cards."""

from __future__ import annotations

from ...model import Card, Table
from . import cache, wiki

WEAPON_TYPES = {"P": "Pistol", "SMG": "SMG", "RIF": "Rifle", "SHT": "Shotgun",
                "HVY": "Heavy Weapon", "MEL": "Melee", "EX": "Exotic"}
CONCEAL = {"N": "None", "J": "Jacket", "L": "Long Coat", "P": "Pocket"}
AVAILABILITY = {"P": "Poor", "C": "Common", "R": "Rare", "E": "Excellent"}
RELIABILITY = {"ST": "Standard", "VR": "Very Reliable", "UR": "Unreliable"}
SURGERY = {"N": "None", "M": "Minor", "MA": "Major"}
LOCATIONS = {"torso": "Torso", "head": "Head", "rarm": "Right Arm", "larm": "Left Arm",
             "rleg": "Right Leg", "lleg": "Left Leg", "llarm": "Left Arm"}
MANOEUVRES = ("strike", "punch", "kick", "disarm", "sweep", "block", "dodge",
              "grapple", "throw", "hold", "choke", "escape", "ram")


# Some rows carry the unit in a numeric field; the unit alone is no value.
BARE_UNITS = frozenset(("kg", "m", "km", "mph", "eb"))


def _add(fields: list[tuple[str, str]], label: str, value: object) -> None:
    text = str(value).strip() if value is not None else ""
    if text and text not in ("0", "None") and text.lower() not in BARE_UNITS:
        fields.append((label, text))


def _cost(value: object) -> str:
    text = str(value).strip() if value is not None else ""
    if not text or text == "0":
        return ""
    return f"{text} eb"


def _signed(value: object) -> str:
    if isinstance(value, int):
        return f"{value:+d}"
    return str(value or "")


def _code(value: object, table: dict[str, str]) -> str:
    text = str(value or "").strip()
    return table.get(text.upper().rstrip("*"), text)


def _named(record: dict) -> str:
    return str(record.get("name") or "Untitled").strip()


def weapon(record: dict) -> Card:
    fields: list[tuple[str, str]] = []
    _add(fields, "Damage", record.get("damage"))
    _add(fields, "Ammo", record.get("ammo"))
    _add(fields, "Shots", record.get("shots"))
    _add(fields, "Rate of Fire", record.get("rof"))
    _add(fields, "Range", f"{record['range']} m" if record.get("range") else "")
    _add(fields, "Accuracy", _signed(record.get("wa")))
    _add(fields, "Concealability", _code(record.get("conc"), CONCEAL))
    _add(fields, "Availability", _code(record.get("avail"), AVAILABILITY))
    _add(fields, "Reliability", _code(record.get("rel"), RELIABILITY))
    _add(fields, "Cost", _cost(record.get("cost")))
    subtitle = WEAPON_TYPES.get(str(record.get("type") or "").strip().upper(), "Weapon")
    paragraphs = wiki.prose(cache.wikitext(_named(record)) or "")
    return Card(_named(record), subtitle, fields, [("", paragraphs)] if paragraphs else [])


def armor(record: dict) -> Card:
    fields: list[tuple[str, str]] = []
    _add(fields, "Stopping Power", record.get("baseSP"))
    _add(fields, "Encumbrance", record.get("ev"))
    kind = "Hard" if record.get("isHard") else "Soft"
    if record.get("isActive"):
        kind += ", active"
    if record.get("isSkinWeave"):
        kind += ", skinweave"
    _add(fields, "Armor", kind)
    _add(fields, "Cost", _cost(record.get("cost")))
    rows = [["Location", "SP"]]
    for key, value in (record.get("locations") or {}).items():
        if value:
            rows.append([LOCATIONS.get(key, key.title()), str(value)])
    sections = [("", [Table(rows, header=True)])] if len(rows) > 1 else []
    return Card(_named(record), "Armor", fields, sections)


def cyberware(record: dict) -> Card:
    fields: list[tuple[str, str]] = []
    _add(fields, "Cost", _cost(record.get("cost")))
    _add(fields, "Humanity Cost", record.get("hc"))
    _add(fields, "Surgery", _code(record.get("surgery"), SURGERY))
    notes = str(record.get("notes") or "").strip()
    return Card(_named(record), str(record.get("type") or "Cyberware").title(), fields,
                [("", [notes])] if notes else [])


def gear(record: dict) -> Card:
    fields: list[tuple[str, str]] = []
    _add(fields, "Cost", _cost(record.get("cost")))
    _add(fields, "Weight", record.get("wt"))
    notes = str(record.get("notes") or "").strip()
    return Card(_named(record), str(record.get("category") or "Gear").title(), fields,
                [("", [notes])] if notes else [])


def role(record: dict) -> Card:
    fields: list[tuple[str, str]] = []
    ability = record.get("specialability") or {}
    _add(fields, "Special Ability", ability.get("name"))
    _add(fields, "Ability Stat", ability.get("stat"))
    _add(fields, "IP Multiplier", ability.get("ipmod"))
    salary = record.get("salary") or []
    if salary:
        _add(fields, "Salary", ", ".join(f"{index + 1}: {value}" for index, value in enumerate(salary)))
    skills = [_joined(skill) for skill in record.get("skills") or []]
    _add(fields, "Skills", ", ".join(skill for skill in skills if skill))
    description = str(ability.get("description") or "").strip()
    return Card(_named(record), "Role", fields, [("", [description])] if description else [])


def _joined(value: object) -> str:
    if isinstance(value, list):
        return " or ".join(str(part) for part in value)
    return str(value or "")


def skill(record: dict) -> Card:
    fields: list[tuple[str, str]] = []
    _add(fields, "Stat", record.get("stat"))
    _add(fields, "IP Multiplier", record.get("ipmod"))
    subtitle = "Special Ability" if record.get("sa") else "Skill"
    description = str(record.get("description") or "").strip()
    return Card(_named(record), subtitle, fields, [("", [description])] if description else [])


def vehicle(record: dict) -> Card:
    fields: list[tuple[str, str]] = []
    _add(fields, "Top Speed", f"{record['topspeed']} mph" if record.get("topspeed") else "")
    _add(fields, "Acceleration", record.get("accelerate"))
    _add(fields, "Deceleration", record.get("decelerate"))
    _add(fields, "Crew", record.get("crew"))
    _add(fields, "Passengers", record.get("passengers"))
    _add(fields, "Cargo", record.get("cargo"))
    _add(fields, "Range", f"{record['range']} km" if record.get("range") else "")
    _add(fields, "Spaces", record.get("spaces"))
    _add(fields, "Maneuver", record.get("maneuver"))
    _add(fields, "SDP", record.get("sdp"))
    _add(fields, "SP", record.get("sp"))
    _add(fields, "Mass", record.get("mass"))
    _add(fields, "Options", record.get("options"))
    _add(fields, "Weapons", record.get("weapons"))
    _add(fields, "Cost", _cost(record.get("bookcost")))
    subtitle = str(record.get("type") or "Vehicle").title()
    return Card(_named(record), subtitle, fields)


def program(record: dict) -> Card:
    fields: list[tuple[str, str]] = []
    _add(fields, "Strength", record.get("str"))
    _add(fields, "Memory", record.get("mu"))
    _add(fields, "Cost", _cost(record.get("cost")))
    _add(fields, "Options", ", ".join(record.get("options") or []))
    description = str(record.get("description") or "").strip()
    subtitle = f"{str(record.get('class') or 'Program').title()} Program"
    return Card(_named(record), subtitle, fields, [("", [description])] if description else [])


def martial_art(record: dict) -> Card:
    fields: list[tuple[str, str]] = []
    _add(fields, "IP Multiplier", record.get("ipMod"))
    rows = [["Maneuver", "Bonus"]]
    for name in MANOEUVRES:
        value = record.get(name)
        if value is not None:
            rows.append([name.title(), _signed(value)])
    return Card(_named(record), "Martial Art", fields, [("", [Table(rows, header=True)])])


def weapon_option(record: dict) -> Card:
    fields: list[tuple[str, str]] = []
    _add(fields, "Applies To", record.get("type"))
    _add(fields, "Cost", _cost(record.get("cost")))
    notes = str(record.get("notes") or "").strip()
    return Card(_named(record), "Weapon Option", fields, [("", [notes])] if notes else [])


def corporation(record: dict) -> Card:
    fields: list[tuple[str, str]] = []
    _add(fields, "Industry", record.get("industry"))
    _add(fields, "Headquarters", record.get("hq"))
    _add(fields, "Appears In", ", ".join(record.get("version") or []))
    return Card(_named(record), "Corporation", fields)
