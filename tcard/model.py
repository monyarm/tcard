"""Card model: source adapters emit a Card, renderers consume it."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class LineKind(StrEnum):
    TITLE = "title"
    SUBTITLE = "subtitle"
    FIELD = "field"
    SECTION = "section"
    BODY = "body"
    TABLE = "table"
    RULE = "rule"
    BLANK = "blank"


@dataclass
class Table:
    """Grid kept as rows so a backend can re-lay it out at its own width."""

    rows: list[list[str]] = field(default_factory=list)
    header: bool = True


@dataclass(frozen=True, slots=True)
class Line:
    kind: LineKind
    text: str = ""
    table: Table | None = None


EMPHASIS = {LineKind.TITLE, LineKind.SECTION}


@dataclass
class Card:
    title: str
    subtitle: str = ""
    fields: list[tuple[str, str]] = field(default_factory=list)
    sections: list[tuple[str, list[str | Table]]] = field(default_factory=list)
