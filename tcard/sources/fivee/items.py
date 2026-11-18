"""5e.tools item records to Cards (magic items plus mundane gear)."""

from __future__ import annotations

from ...model import Card
from ..base import Kind
from . import cache
from .fields import sections, source_field
from .index import _dedupe

DAMAGE_TYPES = {"B": "bludgeoning", "P": "piercing", "S": "slashing"}

DEFENCE_FIELDS = {"ac": "Armor", "bonusAc": "AC"}


def records(refresh: bool = False) -> list[dict]:
    magic = cache.load_json("items.json", refresh).get("item", [])
    base = cache.load_json("items-base.json", refresh)
    return _dedupe(magic + base.get("baseitem", []) + base.get("item", []))


def tables(refresh: bool = False) -> tuple[dict[str, str], dict[str, str]]:
    base = cache.load_json("items-base.json", refresh)
    types: dict[str, str] = {}
    for entry in base.get("itemType", []):
        abbreviation, name = entry.get("abbreviation"), entry.get("name")
        if abbreviation and name:
            types.setdefault(abbreviation, name)
    properties: dict[str, str] = {}
    for entry in base.get("itemProperty", []):
        abbreviation = entry.get("abbreviation")
        name = entry.get("name") or next(
            (node.get("name") for node in entry.get("entries") or [] if isinstance(node, dict) and node.get("name")),
            None,
        )
        if abbreviation and name:
            properties.setdefault(abbreviation, name)
    return types, properties


def type_name(code: object, types: dict[str, str]) -> str:
    if not code:
        return "Wondrous Item"
    abbreviation = str(code).split("|", 1)[0]
    return types.get(abbreviation, "Wondrous Item")


def attunement(record: dict) -> str:
    value = record.get("reqAttune")
    if value is True:
        return "Required"
    if isinstance(value, str) and value:
        return f"Required ({value})"
    return ""


def weapon_line(record: dict, properties: dict[str, str]) -> tuple[str, str] | None:
    damage = record.get("dmg1")
    if not damage:
        return None
    text = f"{damage} {DAMAGE_TYPES.get(record.get('dmgType', ''), 'damage')}"
    if record.get("dmg2"):
        text += f", versatile ({record['dmg2']})"
    for abbreviation in record.get("property") or []:
        if abbreviation == "V" and record.get("dmg2"):
            continue
        name = properties.get(abbreviation)
        if name:
            text += f", {name.lower()}"
    return ("Damage", text)


def armour_line(record: dict) -> tuple[str, str] | None:
    for key, label in DEFENCE_FIELDS.items():
        value = record.get(key)
        if not value:
            continue
        text = f"AC {value}" if key == "ac" else f"AC {value}"
        if record.get("strength"):
            text += f", Str {record['strength']}"
        if record.get("stealth") is True:
            text += ", stealth disadvantage"
        return (label, text)
    return None


def _quantity(label: str, value: object, suffix: str) -> tuple[str, str] | None:
    if not isinstance(value, (int, float)) or not value:
        return None
    return (label, f"{value:g} {suffix}")


def to_card(record: dict) -> Card:
    types, properties = tables()
    rarity = str(record.get("rarity") or "").title()
    if rarity in ("None", "Unknown", "Unknown (Magic)"):
        rarity = ""
    kind = "Wondrous Item" if record.get("wondrous") else type_name(record.get("type"), types)
    subtitle = " ".join(part for part in (rarity, kind) if part)

    fields: list[tuple[str, str]] = []
    if attunement(record):
        fields.append(("Attunement", attunement(record)))
    combat = weapon_line(record, properties) or armour_line(record)
    if combat:
        fields.append(combat)
    for label, value, suffix in (
        ("Weight", record.get("weight"), "lb"),
        ("Value", record.get("value") and record["value"] / 100, "gp"),
    ):
        field = _quantity(label, value, suffix)
        if field:
            fields.append(field)
    source = source_field(record)
    if source:
        fields.append(source)

    nodes = list(record.get("entries") or []) + list(record.get("additionalEntries") or [])
    return Card(str(record.get("name", "Untitled")), subtitle, fields, sections(nodes))


class ItemKind(Kind):
    id = "item"

    def records(self, refresh: bool = False) -> list[dict]:
        return records(refresh)

    def card(self, record: dict) -> Card:
        return to_card(record)
