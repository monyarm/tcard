"""Inline 5e.tools tags ({@damage 8d6}) to plain text."""

from __future__ import annotations

import re

TAG = re.compile(r"\{@(\w+) ([^{}]*)\}")
LEFTOVER = re.compile(r"\{@\w+[^{}]*")

_DISPLAY_SECOND = {"quickref", "link"}
# Published text wants the per-slot increase and the human name, not the lookup key.
_DISPLAY_THIRD = {"scaledamage", "scaledice", "variantrule"}


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
    if tag in _DISPLAY_SECOND and len(parts) > 1 and parts[1]:
        return parts[1]
    if tag in _DISPLAY_THIRD and len(parts) > 2 and parts[2]:
        return parts[2]
    return first


def render_tags(text: str) -> str:
    """Resolve innermost tags first so nested tags work; unknown tags keep field 1."""
    for _ in range(10):
        replaced = TAG.sub(lambda match: _replace(match.group(1), match.group(2)), text)
        if replaced == text:
            break
        text = replaced
    return LEFTOVER.sub("", text)
