"""5e.tools class and subclass features to Cards."""

from __future__ import annotations

from ...model import Card
from ...names import normalize, split_path
from ..base import Kind
from . import cache
from .fields import sections
from .index import _dedupe


def records(refresh: bool = False) -> list[dict]:
    index = cache.load_json("class/index.json", refresh)
    out: list[dict] = []
    for filename in dict.fromkeys(index.values()):
        data = cache.load_json(f"class/{filename}", refresh)
        out.extend(data.get("classFeature") or [])
        out.extend(data.get("subclassFeature") or [])
    return _dedupe(out)


def _class(record: dict) -> str:
    return normalize(str(record.get("className") or ""))


def _subclass(record: dict) -> str:
    return normalize(str(record.get("subclassShortName") or ""))


def to_card(record: dict) -> Card:
    class_name = str(record.get("className") or "")
    subclass = record.get("subclassShortName")
    subtitle = f"{class_name} ({subclass})" if subclass else class_name
    fields: list[tuple[str, str]] = []
    if record.get("level") is not None:
        fields.append(("Level", str(record["level"])))
    return Card(str(record.get("name", "Untitled")), subtitle, fields, sections(record.get("entries")))


class ClassAbilityKind(Kind):
    id = "class_ability"

    def records(self, refresh: bool = False) -> list[dict]:
        return records(refresh)

    def card(self, record: dict) -> Card:
        return to_card(record)

    def matches(self, records: list[dict], query: str) -> list[dict]:
        parts = split_path(query)
        if not parts:
            return []
        feature, prefixes = parts[-1], parts[:-1]
        pool = records
        if len(prefixes) == 2:
            class_name, subclass = prefixes
            pool = [record for record in pool if _class(record) == class_name and _subclass(record) == subclass]
        elif len(prefixes) == 1:
            prefix = prefixes[0]
            if prefix in {_class(record) for record in records}:
                pool = [record for record in pool if _class(record) == prefix]
            else:
                pool = [record for record in pool if _subclass(record) == prefix]
        exact = [record for record in pool if normalize(str(record.get("name", ""))) == feature]
        if exact:
            return exact
        return [record for record in pool if normalize(str(record.get("name", ""))).startswith(feature)]
