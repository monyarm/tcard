"""Plain ASCII backend: the one that works with tp today."""

from __future__ import annotations

from ..model import EMPHASIS, Line


def render(lines: list[Line]) -> str:
    parts = [line.text.upper() if line.kind in EMPHASIS else line.text for line in lines]
    return "\n".join(parts) + "\n"
