"""Foundry PF2 item JSON to Card, one builder per item type."""

from __future__ import annotations

import re

from ...model import Card, Table
from ..pf1 import html
from . import macros

SIZES = {"tiny": "Tiny", "sm": "Small", "med": "Medium", "lg": "Large",
         "huge": "Huge", "grg": "Gargantuan"}
ABILITIES = ("str", "dex", "con", "int", "wis", "cha")

_BLOCK = re.compile(r"<(p|ul|ol|table)\b[^>]*>(.*?)</\1>", re.S | re.I)
_ITEM = re.compile(r"<li\b[^>]*>(.*?)</li>", re.S | re.I)
_LEAD = re.compile(r"^(Heightened\s*\([^)]*\)|Special|Critical Success|Success|Failure|Critical Failure)\s*(.*)$", re.S)


def clean(markup: object) -> str:
    return macros.expand(html.text(str(markup or "")))


def parts(markup: object) -> list:
    out: list = []
    for tag, inner in _BLOCK.findall(str(markup or "")):
        tag = tag.lower()
        if tag == "table":
            grid = html.table(inner)
            if grid.rows:
                out.append(grid)
        elif tag in ("ul", "ol"):
            for item in _ITEM.findall(inner):
                line = clean(item)
                if line:
                    out.append(f"- {line}")
        else:
            line = clean(inner)
            if line:
                out.append(line)
    return out


def description(markup: object) -> tuple[list, list[tuple[str, list]]]:
    """Body paragraphs, plus one section per `<hr>` chunk (Heightened, success degrees)."""
    chunks = re.split(r"<hr\s*/?>", str(markup or ""))
    body = parts(chunks[0])
    sections: list[tuple[str, list]] = []
    for chunk in chunks[1:]:
        lines = parts(chunk)
        if not lines:
            continue
        first = lines[0]
        match = _LEAD.match(first) if isinstance(first, str) else None
        if match:
            rest = [match.group(2).strip()] + lines[1:] if match.group(2).strip() else lines[1:]
            sections.append((match.group(1).strip(), [part for part in rest if part]))
        else:
            sections.append(("", lines))
    return [part for part in body if part], sections


def _value(entry: object, key: str = "value") -> str:
    if isinstance(entry, dict):
        return str(entry.get(key, "") or "").strip()
    return str(entry or "").strip()


def _level(system: dict) -> int:
    try:
        return int(system.get("level", {}).get("value", 0))
    except (TypeError, ValueError, AttributeError):
        return 0


def _traits(system: dict) -> str:
    traits = system.get("traits") or {}
    values = [str(value).replace("-", " ").title() for value in traits.get("value", []) if value]
    rarity = str(traits.get("rarity", "")).strip()
    if rarity and rarity != "common":
        values.insert(0, rarity.title())
    return ", ".join(values)


def _actions(value: object) -> str:
    text = str(value or "").strip()
    if text in ("1", "2", "3"):
        return f"{text} action" + ("" if text == "1" else "s")
    return text


def _money(price: object) -> str:
    coins = price.get("value", {}) if isinstance(price, dict) else {}
    if isinstance(coins, dict):
        return ", ".join(f"{amount} {coin}" for coin, amount in coins.items() if amount)
    return str(coins)


def _bulk(bulk: object) -> str:
    value = bulk.get("value") if isinstance(bulk, dict) else bulk
    return "light" if value in ("L", "l") else str(value or "").replace(".0", "")


def spell(item: dict) -> Card:
    system = item["system"]
    level = _level(system)
    fields: list[tuple[str, str]] = []
    traditions = system.get("traits", {}).get("traditions", [])
    if traditions:
        fields.append(("Traditions", ", ".join(word.title() for word in traditions)))
    fields.append(("Cast", _actions(_value(system.get("time")))))
    for key, label in (("range", "Range"), ("target", "Targets"), ("requirements", "Requires"),
                       ("cost", "Cost")):
        value = _value(system.get(key))
        if value:
            fields.append((label, value))
    area = system.get("area") or {}
    if _value(area):
        fields.append(("Area", f"{_value(area)}-foot {area.get('type', '')}".replace("  ", " ")))
    defense = system.get("defense") or {}
    save = defense.get("save") or {}
    if save:
        stat = str(save.get("statistic", "")).replace("-", " ").title()
        fields.append(("Defense", f"Basic {stat} save" if save.get("basic") else f"{stat} save"))
    duration = system.get("duration") or {}
    if duration.get("sustained"):
        fields.append(("Duration", "Sustained"))
    elif _value(duration):
        fields.append(("Duration", _value(duration)))
    traits = _traits(system)
    if traits:
        fields.append(("Traits", traits))
    body, sections = description(system.get("description", {}).get("value"))
    subtitle = "Cantrip" if level == 0 else f"Spell {level}"
    return Card(item["name"], subtitle, fields, [("", body)] + sections)


def feat(item: dict) -> Card:
    system = item["system"]
    level = _level(system)
    category = str(system.get("category", "")).replace("-", " ").title()
    fields: list[tuple[str, str]] = []
    prerequisites = [clean(value.get("value", "")) if isinstance(value, dict) else clean(value)
                     for value in _value(system.get("prerequisites"), "value") or []]
    prerequisites = [value for value in prerequisites if value]
    if prerequisites:
        fields.append(("Prerequisites", ", ".join(prerequisites)))
    action = _actions(_value(system.get("actionType")))
    if action:
        fields.append(("Action", action))
    frequency = system.get("frequency") or {}
    if frequency.get("max"):
        fields.append(("Frequency", f"{frequency['max']} per {frequency.get('per', '')}".strip()))
    for key, label in (("trigger", "Trigger"), ("requirements", "Requires")):
        value = _value(system.get(key))
        if value:
            fields.append((label, value))
    traits = _traits(system)
    if traits:
        fields.append(("Traits", traits))
    body, sections = description(system.get("description", {}).get("value"))
    subtitle = f"{category} Feat {level}" if category else f"Feat {level}"
    return Card(item["name"], subtitle, fields, [("", body)] + sections)


def equipment(item: dict) -> Card:
    system = item["system"]
    kind = str(item.get("type", "equipment")).title()
    fields: list[tuple[str, str]] = []
    level = _level(system)
    if level:
        fields.append(("Level", str(level)))
    price = _money(system.get("price"))
    if price:
        fields.append(("Price", price))
    bulk = _bulk(system.get("bulk"))
    if bulk:
        fields.append(("Bulk", bulk))
    damage = system.get("damage") or {}
    if damage.get("die"):
        fields.append(("Damage", f"{damage.get('dice', 1)}{damage['die']} "
                                 f"{damage.get('damageType', '')}".strip()))
    armor = system.get("armor") or {}
    if system.get("acBonus") or armor.get("acBonus"):
        bonus = system.get("acBonus") or armor.get("acBonus")
        fields.append(("AC", f"+{bonus}"))
        for key, label in (("dexCap", "Dex Cap"), ("checkPenalty", "Check Penalty"),
                           ("speedPenalty", "Speed Penalty"), ("strength", "Strength")):
            value = system.get(key) if system.get(key) is not None else armor.get(key)
            if value not in (None, "", 0):
                fields.append((label, str(value)))
    category = str(system.get("category", "")).replace("-", " ").title()
    if category:
        fields.append(("Category", category))
    usage = _value(system.get("usage")).replace("-", " ")
    if usage:
        fields.append(("Usage", usage))
    traits = _traits(system)
    if traits:
        fields.append(("Traits", traits))
    body, sections = description(system.get("description", {}).get("value"))
    return Card(item["name"], kind, fields, [("", body)] + sections)


def ancestry(item: dict) -> Card:
    system = item["system"]
    fields: list[tuple[str, str]] = []
    for key, label in (("hp", "HP"), ("speed", "Speed")):
        value = system.get(key)
        if value:
            fields.append((label, str(value)))
    size = SIZES.get(str(system.get("size", "")), "")
    vision = str(system.get("vision", "")).replace("-", " ").title()
    boosts = _ability_list(system.get("boosts"))
    flaws = _ability_list(system.get("flaws"))
    languages = [_value(entry) for entry in
                 (system.get("languages") or {}).get("value", [])]
    for label, value in (("Size", size), ("Vision", vision), ("Boosts", ", ".join(boosts)),
                         ("Flaws", ", ".join(flaws)), ("Languages", ", ".join(languages))):
        if value:
            fields.append((label, value))
    traits = _traits(system)
    if traits:
        fields.append(("Traits", traits))
    body, sections = description(system.get("description", {}).get("value"))
    return Card(item["name"], "Ancestry", fields, [("", body)] + sections)


def heritage(item: dict) -> Card:
    system = item["system"]
    fields: list[tuple[str, str]] = []
    ancestry = system.get("ancestry") or {}
    name = ancestry.get("name") if isinstance(ancestry, dict) else ""
    if name:
        fields.append(("Ancestry", str(name)))
    traits = _traits(system)
    if traits:
        fields.append(("Traits", traits))
    body, sections = description(system.get("description", {}).get("value"))
    return Card(item["name"], "Heritage", fields, [("", body)] + sections)


def background(item: dict) -> Card:
    system = item["system"]
    fields: list[tuple[str, str]] = []
    boosts = _ability_list(system.get("boosts"))
    if boosts:
        fields.append(("Boosts", ", ".join(boosts)))
    trained = system.get("trainedSkills") or {}
    skills = [_value(entry).replace("-", " ").title() for entry in trained.get("value", [])]
    if skills:
        fields.append(("Trained Skill", ", ".join(skills)))
    lore = [_value(entry) for entry in trained.get("lore", [])]
    if lore:
        fields.append(("Trained Lore", ", ".join(lore)))
    body, sections = description(system.get("description", {}).get("value"))
    return Card(item["name"], "Background", fields, [("", body)] + sections)


def klass(item: dict) -> Card:
    system = item["system"]
    fields: list[tuple[str, str]] = []
    hp = system.get("hp")
    if hp:
        fields.append(("HP", str(hp)))
    key = [value.upper() for value in _flatten(system.get("keyAbility"))]
    if key:
        fields.append(("Key Ability", ", ".join(key)))
    perception = _value(system.get("perception"))
    if perception:
        fields.append(("Perception", perception.title()))
    for key_name in ("fortitude", "reflex", "will"):
        rank = _value((system.get("savingThrows") or {}).get(key_name))
        if rank:
            fields.append((key_name.title(), rank.title()))
    body, sections = description(system.get("description", {}).get("value"))
    return Card(item["name"], "Class", fields, [("", body)] + sections)


def deity(item: dict) -> Card:
    system = item["system"]
    fields: list[tuple[str, str]] = []
    domains = system.get("domains") or {}
    primary = ", ".join(word.title() for word in domains.get("primary", []))
    alternate = ", ".join(word.title() for word in domains.get("alternate", []))
    font = ", ".join(word.title() for word in system.get("font", []))
    skill = ", ".join(word.replace("-", " ").title() for word in system.get("skill", []))
    weapon = system.get("weapon")
    weapon_name = weapon.get("name", "") if isinstance(weapon, dict) else str(weapon or "")
    sanctification = system.get("sanctification") or {}
    holy = ", ".join(word.title() for word in sanctification.get("what", []))
    modal = str(sanctification.get("modal", ""))
    spells = system.get("spells") or {}
    spell_lines = []
    for level in sorted(spells, key=lambda key: int(key) if str(key).isdigit() else 99):
        names = [macros.render("UUID", entry) for entry in spells[level]]
        if names:
            spell_lines.append(f"{level}: {', '.join(names)}")
    for label, value in (("Domains", primary), ("Alternate Domains", alternate),
                         ("Divine Font", font), ("Skill", skill), ("Weapon", weapon_name),
                         ("Sanctification", f"{modal.title()} {holy}".strip())):
        if value:
            fields.append((label, value))
    body, sections = description(system.get("description", {}).get("value"))
    if spell_lines:
        sections = sections + [("Cleric Spells", spell_lines)]
    return Card(item["name"], "Deity", fields, [("", body)] + sections)


def condition(item: dict) -> Card:
    system = item["system"]
    fields: list[tuple[str, str]] = []
    duration = _value(system.get("duration"))
    if duration:
        fields.append(("Duration", duration))
    traits = _traits(system)
    if traits:
        fields.append(("Traits", traits))
    body, sections = description(system.get("description", {}).get("value"))
    return Card(item["name"], "Condition", fields, [("", body)] + sections)


def action(item: dict) -> Card:
    system = item["system"]
    fields: list[tuple[str, str]] = []
    actions = _actions(_value(system.get("actions")) or _value(system.get("actionType")))
    if actions:
        fields.append(("Action", actions))
    for key, label in (("trigger", "Trigger"), ("requirements", "Requires")):
        value = _value(system.get(key))
        if value:
            fields.append((label, value))
    traits = _traits(system)
    if traits:
        fields.append(("Traits", traits))
    body, sections = description(system.get("description", {}).get("value"))
    return Card(item["name"], "Action", fields, [("", body)] + sections)


def hazard(item: dict) -> Card:
    system = item["system"]
    details = system.get("details") or {}
    level = _level(details) or _level(system)
    attributes = system.get("attributes") or {}
    fields: list[tuple[str, str]] = []
    fields.append(("Complexity", "Complex" if details.get("isComplex") else "Simple"))
    stealth = attributes.get("stealth") or {}
    stealth_value = _value(stealth)
    if stealth_value and stealth_value != "0":
        detail = _value({"value": stealth.get("details")}).replace("<p>", "").replace("</p>", "")
        detail = f" {detail}" if detail else ""
        fields.append(("Stealth", f"{stealth_value}{detail}"))
    ac = (attributes.get("ac") or {}).get("value")
    if ac:
        fields.append(("AC", str(ac)))
    hp = (attributes.get("hp") or {}).get("max")
    if hp:
        fields.append(("HP", str(hp)))
    hardness = attributes.get("hardness")
    if hardness:
        fields.append(("Hardness", str(hardness)))
    saves = system.get("saves") or {}
    rolls = [_value(saves.get(name)) for name in ("fortitude", "reflex", "will")]
    rolls = [roll for roll in rolls if roll and roll != "0"]
    if rolls:
        fields.append(("Saves", " / ".join(rolls)))
    traits = _traits(system)
    if traits:
        fields.append(("Traits", traits))
    body, sections = description(details.get("description"))
    for key, label in (("trigger", "Trigger"), ("effect", "Effect"),
                       ("disable", "Disable"), ("routine", "Routine"),
                       ("reset", "Reset")):
        value = details.get(key)
        lines, _ = description(value)
        if lines:
            body.append(f"{label}: {lines[0]}")
            body.extend(lines[1:])
    return Card(item["name"], f"Hazard {level}", fields, [("", body)] + sections)


ALL_ABILITIES = frozenset(ABILITIES)


def _ability_list(entry: object) -> list[str]:
    """Boost buckets; a bucket listing all six abilities is a free boost."""
    out: list[str] = []
    for name, value in (entry or {}).items() if isinstance(entry, dict) else []:
        options = [str(option) for option in _flatten(value)]
        if len(set(options)) == len(ABILITIES) and set(options) == ALL_ABILITIES:
            out.append("free")
        else:
            out.extend(option.upper() for option in options)
    return out


def _flatten(entry: object) -> list[str]:
    """PF2 boost/flaw bags: {0: {value: [con]}, 2: {value: [all]}}."""
    out: list[str] = []
    if isinstance(entry, dict):
        for value in entry.values():
            out.extend(_flatten(value))
    elif isinstance(entry, list):
        for value in entry:
            out.extend(_flatten(value))
    elif entry:
        out.append(str(entry))
    return out


def _modifier(value: object) -> str:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return ""
    return f"{number:+d}"


def monster(item: dict) -> Card:
    system = item["system"]
    level = _level(system)
    attributes = system.get("attributes") or {}
    fields: list[tuple[str, str]] = []
    perception = system.get("perception") or {}
    senses = [str(value.get("type", "")).replace("-", " ") for value in perception.get("senses", [])]
    perception_line = _modifier(perception.get("mod"))
    if senses:
        perception_line = f"{perception_line}, {', '.join(senses)}" if perception_line else ", ".join(senses)
    fields.append(("Perception", perception_line))
    ac = (attributes.get("ac") or {}).get("value")
    if ac:
        fields.append(("AC", str(ac)))
    hp = attributes.get("hp") or {}
    if hp.get("max"):
        fields.append(("HP", str(hp["max"])))
    saves = system.get("saves") or {}
    save_line = ", ".join(
        f"{name.title()} {_modifier((saves.get(name) or {}).get('value'))}".strip()
        for name in ("fortitude", "reflex", "will") if (saves.get(name) or {}).get("value") is not None)
    if save_line:
        fields.append(("Saves", save_line))
    speed = attributes.get("speed") or {}
    if speed.get("value"):
        line = f"{speed['value']} feet"
        others = [f"{entry.get('type', '')} {entry.get('value', '')} feet"
                  for entry in speed.get("otherSpeeds", [])]
        if others:
            line = f"{line}, {', '.join(others)}"
        fields.append(("Speed", line))
    skills = system.get("skills") or {}
    if skills:
        fields.append(("Skills", ", ".join(
            f"{name.replace('-', ' ').title()} {_modifier((value or {}).get('base', (value or {}).get('mod')))}".strip()
            for name, value in skills.items())))
    for key, label in (("immunities", "Immunities"), ("weaknesses", "Weaknesses"),
                       ("resistances", "Resistances")):
        entries = attributes.get(key) or []
        text = ", ".join(
            f"{entry.get('type', '').title()} {entry.get('value', '')}".strip()
            for entry in entries if isinstance(entry, dict))
        if text:
            fields.append((label, text))
    traits = system.get("traits") or {}
    size = SIZES.get(str((traits.get("size") or {}).get("value", "")), "")
    kind = ", ".join(str(value).title() for value in traits.get("value", []))
    fields.append(("Traits", ", ".join(part for part in (size, kind) if part)))
    languages = (system.get("details") or {}).get("languages") or {}
    if languages.get("value"):
        fields.append(("Languages", ", ".join(str(word).title() for word in languages["value"])))
    abilities = system.get("abilities") or {}
    grid = Table([[name.upper() for name in ABILITIES],
                  [_modifier((abilities.get(name) or {}).get("mod")) or "+0" for name in ABILITIES]],
                 header=True)
    blurb = parts((system.get("details") or {}).get("publicNotes"))
    sections: list[tuple[str, list]] = [("", [grid] + blurb)]
    for entry in item.get("items", []):
        body = parts((entry.get("system") or {}).get("description", {}).get("value"))
        if body:
            sections.append((entry.get("name", ""), body))
    return Card(item["name"], f"Creature {level}", fields, sections)


BUILDERS = {
    "spell": spell,
    "feat": feat,
    "npc": monster,
    "ancestry": ancestry,
    "heritage": heritage,
    "background": background,
    "class": klass,
    "deity": deity,
    "condition": condition,
    "action": action,
    "hazard": hazard,
}


def to_card(item: dict) -> Card:
    builder = BUILDERS.get(str(item.get("type", "")), equipment)
    return builder(item)
