"""Cybersmily's Datafort JSON and the Cyberpunk Wiki, cached on disk."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import ssl
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

from ...errors import TcardError

BASE = "https://cybersmily.net/json"
WIKI = "https://cyberpunk.fandom.com"
AGENT = "tcard/0.1 (+thermalstatblock)"


# datafortress2020 ships an expired certificate and will not be fixed.
LAX = ssl.create_default_context()
LAX.check_hostname = False
LAX.verify_mode = ssl.CERT_NONE


def cache_dir() -> Path:
    root = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return Path(root) / "tcard" / "cp-2020"


def _get(url: str, refresh: bool = False) -> bytes:
    digest = hashlib.sha1(url.encode()).hexdigest()[:12]
    path = cache_dir() / "files" / f"{digest}.bin"
    if refresh or not path.exists():
        request = Request(url, headers={"User-Agent": AGENT})
        try:
            with urlopen(request, timeout=60) as response:
                body = response.read()
        except HTTPError as exc:
            raise TcardError(f"cannot fetch {url}: {exc}", 3) from exc
        except OSError as exc:
            raise TcardError(f"cannot fetch {url}: {exc}", 3) from exc
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_bytes(body)
        tmp.replace(path)
    return path.read_bytes()


def raw(url: str, refresh: bool = False) -> str:
    """Fetch a page from a site with a broken certificate chain."""
    digest = hashlib.sha1(url.encode()).hexdigest()[:12]
    path = cache_dir() / "pages" / f"{digest}.txt"
    if refresh or not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        request = Request(url, headers={"User-Agent": AGENT})
        try:
            with urlopen(request, timeout=60, context=LAX) as response:
                body = response.read()
        except (HTTPError, OSError) as exc:
            raise TcardError(f"cannot fetch {url}: {exc}", 3) from exc
        path.write_bytes(body)
    return path.read_bytes().decode("cp1252", "replace")


def data(relative: str, refresh: bool = False) -> list[dict]:
    """One dataset, e.g. "wpns/cp2020weapons" -> /json/wpns/cp2020weapons.json."""
    body = _get(f"{BASE}/{relative}.json", refresh)
    try:
        # A few files start with a UTF-8 BOM, which json.loads rejects.
        return json.loads(body.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TcardError(f"cannot read {relative}: {exc}", 3) from exc


def wikitext(page: str, refresh: bool = False) -> str | None:
    """A Cyberpunk Wiki page as wikitext, or None when the page does not exist."""
    url = (
        f"{WIKI}/api.php?action=parse&format=json&redirects=1&prop=wikitext"
        f"&page={quote(page.replace(' ', '_'))}"
    )
    body = _get(url, refresh)
    try:
        parsed = json.loads(body.decode("utf-8", "replace"))
    except json.JSONDecodeError:
        return None
    if "error" in parsed or "parse" not in parsed:
        return None
    return parsed["parse"].get("wikitext", {}).get("*") or None
