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
    RULE = "rule"
    BLANK = "blank"


@dataclass(frozen=True, slots=True)
class Line:
    kind: LineKind
    text: str = ""


EMPHASIS = {LineKind.TITLE, LineKind.SECTION}


@dataclass
class Card:
    title: str
    subtitle: str = ""
    fields: list[tuple[str, str]] = field(default_factory=list)
    sections: list[tuple[str, list[str]]] = field(default_factory=list)
