"""5e.tools spell data: fetch once, cache, key the cache by the index checksum.

The GitHub mirror is DMCA-blocked (HTTP 451), so 5e.tools itself is the source
and a fetched snapshot stands in for a pinned commit.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

from ...errors import TcardError

BASE = "https://5e.tools/data/spells"


def cache_dir() -> Path:
    root = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return Path(root) / "tcard" / "dnd-5e"


def _get(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "tcard/0.1 (+thermalstatblock)"})
    try:
        with urlopen(request, timeout=30) as response:
            return response.read()
    except OSError as exc:
        raise TcardError(f"cannot fetch {url}: {exc}", 3) from exc


def _store(path: Path, payload: bytes) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(payload)
    tmp.replace(path)


def _dedupe(records: list[dict]) -> list[dict]:
    seen: set[tuple[object, object]] = set()
    out: list[dict] = []
    for record in records:
        key = (record.get("name"), record.get("source"))
        if key in seen:
            continue
        seen.add(key)
        out.append(record)
    return out


def spell_records(refresh: bool = False) -> list[dict]:
    directory = cache_dir()
    directory.mkdir(parents=True, exist_ok=True)
    index_path = directory / "index.json"
    manifest_path = directory / "manifest.json"

    if refresh or not index_path.exists():
        _store(index_path, _get(f"{BASE}/index.json"))

    index_bytes = index_path.read_bytes()
    try:
        books = json.loads(index_bytes)
    except json.JSONDecodeError as exc:
        raise TcardError(f"corrupt cache {index_path}: {exc}", 3) from exc

    digest = hashlib.sha256(index_bytes).hexdigest()
    stamp: dict = {}
    if manifest_path.exists():
        try:
            stamp = json.loads(manifest_path.read_text())
        except json.JSONDecodeError:
            stamp = {}
    refetch_all = refresh or stamp.get("index_sha256") != digest

    records: list[dict] = []
    for name in dict.fromkeys(books.values()):
        path = directory / name
        if refetch_all or not path.exists():
            _store(path, _get(f"{BASE}/{name}"))
        try:
            payload = json.loads(path.read_bytes())
        except json.JSONDecodeError as exc:
            path.unlink(missing_ok=True)
            raise TcardError(f"corrupt cache {path}: {exc}", 3) from exc
        records.extend(payload.get("spell", []))

    if refetch_all:
        _store(manifest_path, json.dumps({"index_sha256": digest}).encode())
    return _dedupe(records)
