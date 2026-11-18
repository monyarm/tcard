"""Predator types: one section each, prose plus the dots and skills they grant."""

from __future__ import annotations

from ...model import Card
from ..base import Kind
from . import cache, md

INDEX = "Predator_type"


def records(refresh: bool = False) -> list[dict]:
    markdown = cache.page(INDEX, refresh)
    out: list[dict] = []
    for name, lines in md.blocks(markdown):
        if not name or name.lower().startswith(("references", "gallery")):
            continue
        prose = md.paragraphs(lines)
        if not prose:
            continue
        out.append({"name": name, "body": prose, "bullets": md.bullets(lines)})
    return out


def to_card(record: dict) -> Card:
    body = list(record["body"]) + list(record["bullets"])
    return Card(record["name"], "Predator Type", [], [("", body)])


class PredatorKind(Kind):
    def __init__(self) -> None:
        self.id = "predator_type"

    def records(self, refresh: bool = False) -> list[dict]:
        return records(refresh)

    def card(self, record: dict) -> Card:
        return to_card(record)
