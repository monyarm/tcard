"""Glyphs the printer's font draws in exactly one cell.

Everything else is folded to ASCII before it reaches the pipe; these survive.
"""

from __future__ import annotations

BULLET = "\u2022 "  # list marker
DOT = "\u25cf"  # filled pip
HOLLOW = "\u25cb"  # empty pip
KEEP = frozenset("\u2022\u25cf\u25cb")


def dots(count: int, total: int = 5) -> str:
    """A pip bar: `count` filled, the rest hollow."""
    count = max(0, min(total, count))
    return DOT * count + HOLLOW * (total - count)
