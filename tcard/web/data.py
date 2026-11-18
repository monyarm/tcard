"""Index over every kind: records, facets and filtering for the web UI.

Nothing here renders a card. The list view is the adapter's own record data,
trimmed to the fields a filter needs, so browsing a kind costs one `records()`
call and no network beyond what the adapter already caches.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from pathlib import PurePosixPath
from urllib.parse import urlsplit

from ..names import normalize
from ..sources import registry
from ..sources.cp.cards import (AVAILABILITY, CONCEAL, RELIABILITY, SURGERY,
                                WEAPON_TYPES)
from ..sources.fivee.spell import SCHOOLS

# Facets worth showing per system. Keys that the records do not carry are
# dropped, and any other scalar key with a small set of values is added on top.
FACETS = {
    "dnd:5e": ("source", "level", "school", "category", "type", "rarity", "className"),
    "pf:1e": ("section", "group"),
    "pf:2e": ("pack",),
    "vtm:v5": ("discipline", "group", "dots", "level"),
    "vtm:v20": ("tradition", "level", "group", "title"),
    "cp:2020": ("type", "category", "subcategory", "class", "surgery", "book"),
}

# Free text, identifiers and yes/no flags make poor dropdowns.
SKIP = {
    "name", "url", "path", "page", "source", "notes", "fields", "body", "text",
    "summary", "flavour", "description", "srd", "basicRules", "basicRules2024",
    "srd52", "hasFluff", "hasFluffImages", "isClassFeatureVariant", "reprintedAs",
    "alias", "otherSources", "group", "section", "pack", "book",
}

# Coded source values read badly in a dropdown, so the list shows the words the
# card prints; the filter value stays the raw code.
LABELS = {
    ("dnd:5e", None, "school"): SCHOOLS,
    ("cp:2020", "weapon", "type"): WEAPON_TYPES,
    ("cp:2020", "weapon", "conc"): CONCEAL,
    ("cp:2020", "weapon", "avail"): AVAILABILITY,
    ("cp:2020", "weapon", "rel"): RELIABILITY,
    ("cp:2020", "cyberware", "surgery"): SURGERY,
    ("dnd:5e", "spell", "level"): {"0": "Cantrip"},
}

MAX_VALUES = 40
LIMIT = 100
COLUMNS = 32


@dataclass
class Index:
    system: str
    kind: str
    rows: list[dict] = field(default_factory=list)
    facets: dict[str, list[dict]] = field(default_factory=dict)
    built: float = field(default_factory=time.monotonic)


_CACHE: dict[tuple[str, str], Index] = {}
_LOCK = threading.Lock()


def systems() -> list[dict]:
    return [{"id": system, "kinds": list(registry.kinds(system))}
            for system in registry.systems()]


def source(record: dict) -> str:
    """Book code; CP2020 writes {"book", "page"} where the others write a string."""
    value = record.get("source")
    if isinstance(value, dict):
        return str(value.get("book") or "")
    return str(value or "")


def _pf1_section(url: str, depth: int) -> str:
    path = urlsplit(str(url)).path.strip("/")
    parts = [part for part in path.split("/") if len(part) > 1]
    return "/".join(parts[:depth]) if parts else ""


def _pf2_pack(path: object) -> str:
    parts = PurePosixPath(str(path)).parts
    if "packs" in parts:
        rest = parts[parts.index("packs") + 2:]  # skip packs/<system>/
        if rest:
            return rest[0]
    return ""


def _value(record: dict, key: str, depth: int = 2) -> str:
    if key == "section":
        return _pf1_section(record.get("url", ""), depth)
    if key == "pack":
        return _pf2_pack(record.get("path", ""))
    if key == "book":
        return source(record)
    raw = record.get(key)
    if isinstance(raw, bool) or raw is None:
        return ""
    if isinstance(raw, (str, int, float)):
        return str(raw)
    return ""


def _scalar(record: dict, key: str) -> bool:
    raw = record.get(key)
    return not isinstance(raw, bool) and isinstance(raw, (str, int, float))


def _facet_keys(system: str, records: list[dict]) -> dict[str, int]:
    """Facet keys worth showing, mapped to the path depth they need."""
    keys: dict[str, int] = {}

    def values_of(key: str, depth: int) -> set[str]:
        found = {_value(record, key, depth) for record in records}
        found.discard("")
        return found

    for key in FACETS.get(system, ()):
        if key in keys:
            continue
        depth = 2
        found = values_of(key, depth)
        if key == "section":
            # d20pfsrd nests books and classes; widen until the list is usable.
            for depth in (2, 3, 4):
                found = values_of(key, depth)
                if len(found) <= MAX_VALUES:
                    break
        if 2 <= len(found) <= MAX_VALUES:
            keys[key] = depth
    if not records:
        return keys
    for key in records[0]:
        if key in keys or key in SKIP or not _scalar(records[0], key):
            continue
        found = values_of(key, 2)
        if 2 <= len(found) <= MAX_VALUES:
            keys[key] = 2
    return keys


def label(system: str, kind: str, key: str, value: str) -> str:
    table = LABELS.get((system, None, key)) or LABELS.get((system, kind, key))
    return table.get(value.strip().upper(), value) if table else value


def _sort_value(value: str) -> tuple:
    try:
        return (0, float(value), "")
    except ValueError:
        return (1, 0.0, value.casefold())


def build(system: str, kind: str, refresh: bool = False) -> Index:
    try:
        impl = registry.kinds(system)[kind]
    except KeyError:
        raise KeyError(kind) from None
    records = impl.records(refresh=refresh)
    depths = _facet_keys(system, records)
    keys = list(depths)
    rows: list[dict] = []
    counts: dict[str, dict[str, int]] = {key: {} for key in keys}
    for record in records:
        facets = {}
        for key in keys:
            value = _value(record, key, depths[key])
            if not value:
                continue
            facets[key] = value
            counts[key][value] = counts[key].get(value, 0) + 1
        shown = [source(record)] if source(record) else []
        shown += [label(system, kind, key, value) for key, value in facets.items()
                  if key not in ("source", "book")]
        rows.append({
            "name": str(record.get("name", "?")),
            "label": impl.display(record),
            "source": source(record),
            "facets": facets,
            "chips": " · ".join(shown[:4]),
        })
    rows.sort(key=lambda row: row["label"].casefold())
    index = Index(system=system, kind=kind, rows=rows)
    index.facets = {
        key: [{"value": value, "count": counts[key][value],
               "label": label(system, kind, key, value)}
              for value in sorted(counts[key], key=_sort_value)]
        for key in keys if counts[key]
    }
    return index


def index(system: str, kind: str, refresh: bool = False) -> Index:
    """Cached per kind; `refresh` re-reads the adapter's records."""
    cached = _CACHE.get((system, kind))
    if cached is not None and not refresh:
        return cached
    with _LOCK:
        cached = _CACHE.get((system, kind))
        if cached is not None and not refresh:
            return cached
        built = build(system, kind, refresh)
        _CACHE[(system, kind)] = built
        return built


def search(system: str, kind: str, query: str = "", filters: dict[str, list[str]] | None = None,
           offset: int = 0, limit: int = LIMIT, refresh: bool = False) -> dict:
    """Rows matching the name text and every facet, plus counts over the whole kind."""
    built = index(system, kind, refresh=refresh)
    wanted = normalize(query)
    chosen = {key: {value.casefold() for value in values if value}
              for key, values in (filters or {}).items()}

    def keep(row: dict) -> bool:
        if wanted and wanted not in normalize(row["name"]):
            return False
        return all(row["facets"].get(key, "").casefold() in values
                   for key, values in chosen.items() if values)

    matches = [row for row in built.rows if keep(row)]
    offset = max(0, offset)
    return {
        "system": system,
        "kind": kind,
        "total": len(matches),
        "count": len(built.rows),
        "offset": offset,
        "limit": limit,
        "rows": matches[offset:offset + limit],
        "facets": built.facets,
    }
