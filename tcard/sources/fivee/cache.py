"""Generic 5e.tools JSON cache: fetch a file once, keep it next to the spells."""

from __future__ import annotations

import json
from pathlib import Path

from ...errors import TcardError
from .index import _get, _store, cache_dir

ROOT = "https://5e.tools/data"


def load_json(rel: str, refresh: bool = False) -> object:
    path: Path = cache_dir() / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    if refresh or not path.exists():
        _store(path, _get(f"{ROOT}/{rel}"))
    try:
        return json.loads(path.read_bytes())
    except json.JSONDecodeError as exc:
        path.unlink(missing_ok=True)
        raise TcardError(f"corrupt cache {path}: {exc}", 3) from exc
