"""A whole 5e subclass as one card: every feature, grouped by level."""

from __future__ import annotations

from ...model import Card
from ...names import normalize, split_path
from ..base import Kind
from . import cache
from .fields import sections


def records(refresh: bool = False) -> list[dict]:
    """One record per (class, subclass, source) holding all its features."""
    index = cache.load_json("class/index.json", refresh)
    groups: dict[tuple[str, str, str], dict] = {}
    for filename in dict.fromkeys(index.values()):
        data = cache.load_json(f"class/{filename}", refresh)
        for feature in data.get("subclassFeature") or []:
            class_name = str(feature.get("className") or "")
            short = str(feature.get("subclassShortName") or "")
            source = str(feature.get("source") or "")
            if not class_name or not short:
                continue
            key = (class_name, short, source)
            group = groups.get(key)
            if group is None:
                group = groups[key] = {
                    "name": short,
                    "className": class_name,
                    "source": source,
                    "features": [],
                }
            group["features"].append(feature)
    out = list(groups.values())
    for group in out:
        # Older files repeat a feature per reprint; keep one card line each.
        seen: set[tuple[object, object]] = set()
        unique = []
        for feature in group["features"]:
            key = (feature.get("level"), feature.get("name"))
            if key in seen:
                continue
            seen.add(key)
            unique.append(feature)
        group["features"] = unique
        group["features"].sort(key=lambda item: (item.get("level") or 0, item.get("name") or ""))
    out.sort(key=lambda item: (item["name"], item["className"], item["source"]))
    return out


def to_card(record: dict) -> Card:
    heading = f"{record['className']} Subclass"
    intro: list = []
    sections_out: list[tuple[str, list]] = []
    for feature in record["features"]:
        parts = [part for _, paragraphs in sections(feature.get("entries")) for part in paragraphs]
        # The subclass's own feature only carries its description; no level heading.
        if normalize(str(feature.get("name") or "")) == normalize(record["name"]):
            intro.extend(parts)
            continue
        level = feature.get("level")
        title = str(feature.get("name") or "Feature")
        name = f"Level {level}: {title}" if level is not None else title
        sections_out.append((name, parts))
    if intro:
        sections_out.insert(0, ("", intro))
    return Card(str(record["name"]), heading, [], sections_out)


def _matches_class(record: dict, token: str) -> bool:
    return normalize(record["className"]) == token


class SubclassKind(Kind):
    id = "subclass"

    def records(self, refresh: bool = False) -> list[dict]:
        return records(refresh)

    def card(self, record: dict) -> Card:
        return to_card(record)

    def matches(self, records: list[dict], query: str) -> list[dict]:
        parts = split_path(query)
        if not parts:
            return []
        name, prefixes = parts[-1], parts[:-1]
        pool = records
        for prefix in prefixes:
            pool = [record for record in pool if _matches_class(record, prefix)]
        exact = [record for record in pool if normalize(record["name"]) == name]
        if exact:
            return exact
        return [record for record in pool if normalize(record["name"]).startswith(name)]
