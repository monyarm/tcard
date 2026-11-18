"""5e.tools bestiary records to Cards."""

from __future__ import annotations

from ...model import Card, Table
from . import cache
from .fields import sections
from .index import _dedupe
from .tags import render_tags

SIZES = {
    "T": "Tiny",
    "S": "Small",
    "M": "Medium",
    "L": "Large",
    "H": "Huge",
    "G": "Gargantuan",
}
ALIGN = {"L": "lawful", "N": "neutral", "C": "chaotic", "G": "good", "E": "evil", "U": "unaligned", "A": "any"}
CR_FRACTIONS = {0.125: "1/8", 0.25: "1/4", 0.5: "1/2"}
ABILITIES = (("STR", "str"), ("DEX", "dex"), ("CON", "con"), ("INT", "int"), ("WIS", "wis"), ("CHA", "cha"))
GROUPS = (
    ("trait", "Traits"),
    ("action", "Actions"),
    ("bonus", "Bonus Actions"),
    ("reaction", "Reactions"),
    ("legendary", "Legendary Actions"),
    ("mythic", "Mythic Actions"),
    ("lairActions", "Lair Actions"),
    ("regionalEffects", "Regional Effects"),
)


def records(refresh: bool = False) -> list[dict]:
    index = cache.load_json("bestiary/index.json", refresh)
    out: list[dict] = []
    for filename in dict.fromkeys(index.values()):
        data = cache.load_json(f"bestiary/{filename}", refresh)
        out.extend(data.get("monster") or [])
    return _dedupe(out)


def _type(record: dict) -> str:
    kind = record.get("type")
    if isinstance(kind, dict):
        name = str(kind.get("type") or "")
        tags = kind.get("tags") or []
        return f"{name} ({', '.join(str(tag) for tag in tags)})" if tags else name
    return str(kind or "")


def _alignment(record: dict) -> str:
    words = []
    for code in record.get("alignment") or []:
        word = ALIGN.get(str(code))
        if word is None:
            words.append(str(code))
        elif word not in words:
            words.append(word)
    if not words:
        return ""
    if len(words) == 1:
        return words[0]
    return " ".join(words)


def subtitle(record: dict) -> str:
    size = " ".join(SIZES.get(code, code) for code in record.get("size") or [])
    parts = [part for part in (size, _type(record), _alignment(record)) if part]
    return ", ".join(parts)


def _ac(record: dict) -> str:
    first = (record.get("ac") or [{}])[0]
    if isinstance(first, int):
        return str(first)
    value = first.get("ac")
    source = first.get("from") or []
    return f"{value} ({', '.join(str(part) for part in source)})" if source else str(value)


def _speed(record: dict) -> str:
    speed = record.get("speed") or {}
    if isinstance(speed, str):
        return speed
    parts = []
    for key, value in speed.items():
        if isinstance(value, bool):
            continue
        parts.append(f"{key} {value} ft." if key != "walk" else f"{value} ft.")
    if record.get("hover"):
        parts.append("hover")
    return ", ".join(parts)


def _hp(record: dict) -> str:
    hp = record.get("hp") or {}
    if isinstance(hp, int):
        return str(hp)
    average = hp.get("average")
    formula = hp.get("formula")
    if average is not None and formula:
        return f"{average} ({formula})"
    if formula:
        return str(formula)
    return str(hp.get("special") or "")


def _cr(record: dict) -> str:
    value = record.get("cr")
    if isinstance(value, float) and value in CR_FRACTIONS:
        return CR_FRACTIONS[value]
    if isinstance(value, dict):
        return str(value.get("cr") or "")
    return str(value)


def _modifier(score: int) -> str:
    bonus = (score - 10) // 2
    return f"{bonus:+d}"


def _score(value: object) -> int | None:
    if isinstance(value, dict):
        value = value.get("value", value.get("score"))
    return value if isinstance(value, int) else None


def _ability_tables(record: dict) -> list[Table]:
    cells = []
    for label, key in ABILITIES:
        score = _score(record.get(key))
        cells.append((label, "-" if score is None else f"{score} ({_modifier(score)})"))
    tables = []
    for start in (0, 3):
        chunk = cells[start : start + 3]
        tables.append(Table([[label for label, _ in chunk], [value for _, value in chunk]], header=True))
    return tables


def _feature_parts(feature: dict) -> list[str]:
    parts = [part for _, paragraphs in sections(feature.get("entries")) for part in paragraphs]
    name = render_tags(str(feature.get("name") or "").strip())
    if not name:
        return parts
    if parts:
        parts[0] = f"{name}. {parts[0]}"
    else:
        parts = [f"{name}."]
    return parts


def to_card(record: dict) -> Card:
    fields: list[tuple[str, str]] = [("AC", _ac(record)), ("HP", _hp(record)), ("Speed", _speed(record))]
    if record.get("save"):
        fields.append(("Saves", ", ".join(f"{key.upper()} {value}" for key, value in record["save"].items())))
    if record.get("skill"):
        fields.append(("Skills", ", ".join(f"{key.title()} {value}" for key, value in record["skill"].items())))
    for label, key in (("Damage Immunities", "immune"), ("Damage Resistances", "resist"), ("Damage Vulnerabilities", "vulnerable"), ("Condition Immunities", "conditionImmune")):
        value = record.get(key)
        if value:
            fields.append((label, ", ".join(str(part) for part in value)))
    senses = list(record.get("senses") or [])
    if record.get("passive") is not None:
        senses.append(f"passive Perception {record['passive']}")
    if senses:
        fields.append(("Senses", ", ".join(str(part) for part in senses)))
    if record.get("languages"):
        fields.append(("Languages", ", ".join(str(part) for part in record["languages"])))
    if record.get("pb") is not None:
        fields.append(("Proficiency Bonus", f"+{record['pb']}"))
    fields.append(("CR", _cr(record)))

    sections_out: list[tuple[str, list]] = [("", _ability_tables(record))]
    legend = record.get("legendaryHeader")
    if legend:
        sections_out.append(("Legendary Actions", [part for _, paragraphs in sections(legend) for part in paragraphs]))
    for key, label in GROUPS:
        features = record.get(key)
        if not features:
            continue
        parts: list = []
        for feature in features:
            if isinstance(feature, dict):
                parts.extend(_feature_parts(feature))
            else:
                parts.extend(part for _, paragraphs in sections([feature]) for part in paragraphs)
        if parts:
            sections_out.append((label, parts))
    return Card(
        str(record.get("name") or "Untitled"),
        subtitle(record),
        [(label, render_tags(value)) for label, value in fields],
        sections_out,
    )
