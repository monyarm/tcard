"""Field formatting shared by the 5e content kinds."""

from __future__ import annotations

from .entries import flatten
from .tags import render_tags


def source_field(record: dict) -> tuple[str, str] | None:
    source = record.get("source")
    if not source:
        return None
    page = record.get("page")
    return ("Source", f"{source} p.{page}" if page else source)


def sections(nodes: object) -> list[tuple[str, list[str]]]:
    return [(heading, [render_tags(text) for text in paragraphs]) for heading, paragraphs in flatten(nodes)]


def _clean(text: object) -> str:
    return str(text).split("#", 1)[0].split("|", 1)[0]


def _as_list(value: object) -> list:
    if isinstance(value, list):
        return value
    return [value]


def _describe(value: object) -> str:
    if isinstance(value, dict):
        if value.get("entry"):
            return _clean(value["entry"])
        if "choose" in value:
            return ""
        name = value.get("name") or value.get("displayName")
        level = value.get("level")
        if name and level:
            return f"{name} {level}"
        if name:
            return _clean(name)
        return ", ".join(_describe(item) for item in value.values())
    if isinstance(value, list):
        return ", ".join(part for part in (_describe(item) for item in value) if part)
    return _clean(value)


def _prereq_item(key: str, value: object) -> str:
    if key == "other":
        return _describe(value)
    if key == "level":
        if isinstance(value, dict) and value.get("class"):
            return f"{_describe(value['class'])} level {_describe(value.get('level'))}"
        return f"level {_describe(value)}"
    if key == "ability":
        return ", ".join(f"{str(k).upper()} {v}" for item in _as_list(value) if isinstance(item, dict) for k, v in item.items())
    if key in ("class", "feat", "feature", "race", "background", "deity", "item", "spell", "proficiency"):
        return f"{key} {_describe(value)}"
    return _describe(value)


def format_prereq(value: object) -> str:
    parts: list[str] = []
    for entry in _as_list(value):
        if isinstance(entry, str):
            parts.append(_clean(entry))
        elif isinstance(entry, dict):
            for key, item in entry.items():
                text = _prereq_item(str(key), item)
                if text:
                    parts.append(text)
    return ", ".join(part for part in parts if part)
