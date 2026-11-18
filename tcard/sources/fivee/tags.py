"""Inline 5e.tools tags ({@damage 8d6}) to plain text."""

from __future__ import annotations

import re

TAG = re.compile(r"\{@(\w+) ([^{}]*)\}")
LEFTOVER = re.compile(r"\{@\w+[^{}]*")
NOARG_TAG = re.compile(r"\{@(\w+)\}")

_DISPLAY_SECOND = {"quickref", "link"}
# Published text wants the per-slot increase and the human name, not the lookup key.
_DISPLAY_THIRD = {"scaledamage", "scaledice", "variantrule"}
# {recharge} without an argument means the action recharges on a 6.
_NOARG = {
    "recharge": "Recharge 6",
    "h": "Hit: ",
    "actSaveFail": "Failure:",
    "actSaveSuccess": "Success:",
    "actSaveSuccessOrFail": "Success or Failure:",
    "actTrigger": "Trigger:",
    "actResponse": "Response:",
}
ABILITY = {
    "str": "Strength",
    "dex": "Dexterity",
    "con": "Constitution",
    "int": "Intelligence",
    "wis": "Wisdom",
    "cha": "Charisma",
}
_ATTACK = {
    "mw": "Melee Weapon Attack",
    "rw": "Ranged Weapon Attack",
    "ms": "Melee Spell Attack",
    "rs": "Ranged Spell Attack",
    "m": "Melee Attack",
    "r": "Ranged Attack",
}
_COMBINED = {
    ("mw", "rw"): "Melee or Ranged Weapon Attack",
    ("ms", "rs"): "Melee or Ranged Spell Attack",
    ("m", "r"): "Melee or Ranged Attack",
}


def _attack(codes: str, roll: bool = False) -> str:
    key = tuple(sorted(code.strip() for code in codes.split(",") if code.strip()))
    if key in _COMBINED:
        text = _COMBINED[key]
    else:
        words: list[str] = []
        for code in key:
            word = _ATTACK.get(code)
            if word and word not in words:
                words.append(word)
        if not words:
            return ""
        text = " or ".join(words)
    return text + (" Roll:" if roll else ":")


def _replace(tag: str, body: str) -> str:
    parts = body.split("|")
    first = parts[0]
    if tag == "note":
        return f"({first})"
    if tag == "book":
        page = parts[2] if len(parts) > 2 and parts[2] else ""
        return f"{first}, p.{page}" if page else first
    if tag == "hit":
        return first if first.startswith(("+", "-")) else f"+{first}"
    if tag == "dc":
        return f"DC {first}"
    if tag == "chance":
        return f"{first}%"
    if tag == "atk" or tag == "atkr":
        return _attack(first, roll=tag == "atkr")
    if tag == "recharge":
        return "Recharge 6" if first == "6" else f"Recharge {first}-6"
    if tag == "actSave":
        return f"{ABILITY.get(first.lower(), first.title())} Saving Throw:"
    if tag in _DISPLAY_SECOND and len(parts) > 1 and parts[1]:
        return parts[1]
    if tag in _DISPLAY_THIRD and len(parts) > 2 and parts[2]:
        return parts[2]
    return first


def render_tags(text: str) -> str:
    """Resolve innermost tags first so nested tags work; unknown tags keep field 1."""
    text = NOARG_TAG.sub(lambda match: _NOARG.get(match.group(1), ""), text)
    for _ in range(10):
        replaced = TAG.sub(lambda match: _replace(match.group(1), match.group(2)), text)
        if replaced == text:
            break
        text = replaced
    return LEFTOVER.sub("", text)
