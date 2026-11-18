"""White Wolf wiki (V20) API fetch, cached on disk."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from ...errors import TcardError

API = "https://whitewolf.fandom.com/api.php"
AGENT = "tcard/0.1 (+thermalstatblock)"


def cache_dir() -> Path:
    root = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return Path(root) / "tcard" / "vtm-v20"


def _fetch(url: str) -> str:
    request = Request(url, headers={"User-Agent": AGENT})
    try:
        with urlopen(request, timeout=60) as response:
            return response.read().decode("utf-8", "replace")
    except HTTPError as exc:
        raise TcardError(f"cannot fetch {url}: {exc}", 3) from exc
    except OSError as exc:
        raise TcardError(f"cannot fetch {url}: {exc}", 3) from exc


def get(url: str, refresh: bool = False) -> str:
    digest = hashlib.sha1(url.encode()).hexdigest()[:12]
    path = cache_dir() / "pages" / f"{digest}.json"
    if refresh or not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(_fetch(url))
        tmp.replace(path)
    return path.read_text()


def api(refresh: bool = False, **params: str) -> dict:
    params.setdefault("format", "json")
    url = f"{API}?{urlencode(params)}"
    try:
        return json.loads(get(url, refresh))
    except json.JSONDecodeError as exc:
        raise TcardError(f"cannot read wiki response: {exc}", 3) from exc


def category(name: str, refresh: bool = False) -> list[str]:
    body = api(refresh, action="query", list="categorymembers",
               cmtitle=f"Category:{name}", cmlimit="500")
    return [member["title"] for member in body.get("query", {}).get("categorymembers", [])]


def wikitext(title: str, refresh: bool = False) -> str | None:
    """Page wikitext, or None when the page does not exist."""
    body = api(refresh, action="parse", page=title, prop="wikitext", redirects="1")
    if "error" in body:
        return None
    try:
        return body["parse"]["wikitext"]["*"]
    except KeyError:
        return None
