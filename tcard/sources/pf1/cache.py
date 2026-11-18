"""d20pfsrd fetch and cache: letter pages build the name index, pages fetch on demand."""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from ...errors import TcardError
from . import html

BASE = "https://www.d20pfsrd.com"
LETTERS = "abcdefghijklmnopqrstuvwxyz"
# nginx answers 410 to non-browser agents.
AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"

_LINK = re.compile(r'href="([^"]*/magic/all-spells/([a-z])/[^"/]+/)"[^>]*>([^<]+)<')


def cache_dir() -> Path:
    root = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return Path(root) / "tcard" / "pf1"


def fetch(url: str) -> str:
    request = Request(url, headers={"User-Agent": AGENT})
    try:
        with urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8", "replace")
    except HTTPError as exc:
        # d20pfsrd serves valid sitemap bodies with a 404 status.
        body = exc.read()
        if body:
            return body.decode("utf-8", "replace")
        raise TcardError(f"cannot fetch {url}: {exc}", 3) from exc
    except OSError as exc:
        raise TcardError(f"cannot fetch {url}: {exc}", 3) from exc


def parse_letter(markup: str) -> list[dict]:
    """(name, url) pairs from one letter listing page."""
    seen: set[str] = set()
    out: list[dict] = []
    for url, _, name in _LINK.findall(markup):
        name = html.text(name)
        if not name or url in seen:
            continue
        seen.add(url)
        out.append({"name": name, "url": url})
    return out


def index(refresh: bool = False) -> list[dict]:
    directory = cache_dir()
    path = directory / "index.json"
    if not refresh and path.exists():
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            path.unlink(missing_ok=True)
    records: list[dict] = []
    for letter in LETTERS:
        records.extend(parse_letter(fetch(f"{BASE}/magic/all-spells/{letter}/")))
        time.sleep(0.2)
    directory.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(records))
    tmp.replace(path)
    return records


def page(record: dict, refresh: bool = False) -> str:
    # Slug-keyed pages collide across kinds (feats/power-attack vs traits/power-attack).
    digest = hashlib.sha1(record["url"].encode()).hexdigest()[:12]
    path = cache_dir() / "pages" / f"{digest}.html"
    if refresh or not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(fetch(record["url"]))
        tmp.replace(path)
    return path.read_text()
