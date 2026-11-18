"""VTM Wiki and White Wolf wiki fetch, cached on disk."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from ...errors import TcardError

BASE = "https://vtm.paradoxwikis.com"
# The wiki answers every request with a JS bot-gate shell. r.jina.ai renders it.
PROXY = "https://r.jina.ai/"
WIKI = "https://whitewolf.fandom.com"
# Both hosts reject a non-browser agent (403).
AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124 Safari/537.36"
)


def cache_dir() -> Path:
    root = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return Path(root) / "tcard" / "vtm-v5"


def fetch(url: str) -> str:
    return fetch_bytes(url).decode("utf-8", "replace")


def fetch_bytes(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": AGENT})
    try:
        with urlopen(request, timeout=120) as response:
            return response.read()
    except HTTPError as exc:
        raise TcardError(f"cannot fetch {url}: {exc}", 3) from exc
    except OSError as exc:
        raise TcardError(f"cannot fetch {url}: {exc}", 3) from exc


def get(url: str, refresh: bool = False) -> str:
    """Fetch any URL once and keep the body under the cache directory."""
    path = _cached(url, "txt", refresh, fetch)
    return path.read_text()


def get_bytes(url: str, refresh: bool = False) -> bytes:
    """Same cache, for binary bodies such as a Foundry pack."""
    return _cached(url, "bin", refresh, fetch_bytes).read_bytes()


def _cached(url: str, suffix: str, refresh: bool, fetch_body):
    digest = hashlib.sha1(url.encode()).hexdigest()[:12]
    path = cache_dir() / "pages" / f"{digest}.{suffix}"
    if refresh or not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_bytes(fetch_body(url))
        tmp.replace(path)
    return path


def page(name: str, refresh: bool = False) -> str:
    """One VTM Wiki page, rendered to markdown by the proxy."""
    from urllib.parse import quote

    slug = quote(name.replace(" ", "_"), safe="()_-'!,")
    return get(f"{PROXY}{BASE}/{slug}", refresh)


def wikitext(name: str, refresh: bool = False) -> str:
    """One White Wolf wiki page as MediaWiki wikitext."""
    url = f"{WIKI}/api.php?action=parse&page={name}&prop=wikitext&format=json"
    body = get(url, refresh)
    try:
        return json.loads(body)["parse"]["wikitext"]["*"]
    except (json.JSONDecodeError, KeyError) as exc:
        raise TcardError(f"cannot read wiki page {name}: {exc}", 3) from exc
