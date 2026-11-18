"""Foundry inline macros in PF2 descriptions: @UUID, @Damage, @Check, @Template."""

from __future__ import annotations

import re

_MACRO = re.compile(r"@(\w+)\[")
_ABILITY = {
    "str": "Fortitude", "dex": "Reflex", "con": "Fortitude",
    "int": "Will", "wis": "Will", "cha": "Will",
    "reflex": "Reflex", "fortitude": "Fortitude", "will": "Will", "perception": "Perception",
}


def _closing(text: str, start: int) -> int:
    """Index of the bracket that closes the one at `start`."""
    depth = 0
    for index in range(start, len(text)):
        if text[index] == "[":
            depth += 1
        elif text[index] == "]":
            depth -= 1
            if depth == 0:
                return index
    return len(text)


def _damage(inner: str) -> str:
    out = []
    for part in inner.split(","):
        match = re.match(r"^([\ddh+\- ]+)\[([^\]]*)\]$", part.strip())
        if match:
            kinds = match.group(2).split(",")
            out.append(" ".join([match.group(1).strip(), kinds[-1]]))
        elif part.strip():
            out.append(part.strip())
    return ", ".join(out)


def _check(inner: str) -> str:
    options = dict(part.split(":", 1) for part in inner.split("|") if ":" in part)
    raw = options.get("type", "perception")
    statistic = _ABILITY.get(raw.lower(), raw.replace("-", " ").title())
    dc = options.get("dc", "")
    return f"DC {dc} {statistic}" if dc else statistic


def _template(inner: str) -> str:
    options = dict(part.split(":", 1) for part in inner.split("|") if ":" in part)
    shape = options.get("type", "").replace("-", " ")
    distance = options.get("distance", "")
    return f"{distance}-foot {shape}" if distance else shape


def render(kind: str, inner: str) -> str:
    if kind == "UUID":
        return inner.split(".")[-1].replace("-", " ").title()
    if kind == "Damage":
        return _damage(inner)
    if kind == "Check":
        return _check(inner)
    if kind == "Template":
        return _template(inner)
    if kind == "Localize":
        return inner.split(".")[-1].replace("-", " ").title()
    if kind == "Embed":
        return ""
    return inner


def expand(text: str) -> str:
    """Replace every macro with the words a reader needs."""
    out: list[str] = []
    index = 0
    while True:
        at = text.find("@", index)
        if at < 0:
            out.append(text[index:])
            break
        match = _MACRO.match(text, at)
        if not match:
            out.append(text[index:at + 1])
            index = at + 1
            continue
        open_bracket = match.end() - 1
        close = _closing(text, open_bracket)
        inner = text[open_bracket + 1:close]
        rest = close + 1
        label = ""
        if rest < len(text) and text[rest] == "{":
            end = text.find("}", rest)
            end = len(text) if end < 0 else end
            label = text[rest + 1:end]
            rest = end + 1
        out.append(text[index:at])
        out.append(label or render(match.group(1), inner))
        index = rest
    return "".join(out)
