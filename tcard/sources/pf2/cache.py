"""PF2 data: a blobless sparse checkout of the foundryvtt/pf2e packs."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from ...errors import TcardError

REPO = "https://github.com/foundryvtt/pf2e"
BRANCH = "v14-dev"
PACKS = "packs/pf2e"
MANIFEST = "packs.json"


def cache_dir() -> Path:
    root = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return Path(root) / "tcard" / "pf2"


def repo_dir() -> Path:
    return cache_dir() / "repo"


def _git(*args: str, cwd: Path | None = None) -> str:
    try:
        done = subprocess.run(
            ("git", *args), cwd=cwd, check=True, capture_output=True, text=True
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = getattr(exc, "stderr", None) or exc
        raise TcardError(f"git {args[0]} failed: {detail}", 3) from exc
    return done.stdout


def _checked() -> list[str]:
    path = cache_dir() / MANIFEST
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return []


def _remember(patterns: list[str]) -> None:
    cache_dir().mkdir(parents=True, exist_ok=True)
    path = cache_dir() / MANIFEST
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(sorted(patterns)))
    tmp.replace(path)


def ensure(packs: tuple[str, ...], refresh: bool = False) -> Path:
    """Clone the packs once, then add the requested directories to the checkout."""
    repo = repo_dir()
    known = _checked()
    if not (repo / ".git").exists():
        cache_dir().mkdir(parents=True, exist_ok=True)
        _git("clone", "--depth", "1", "--filter=blob:none", "--sparse",
             "--branch", BRANCH, REPO, str(repo))
        known = []
    elif refresh:
        _git("fetch", "--depth", "1", "origin", BRANCH, cwd=repo)
        _git("reset", "--hard", "FETCH_HEAD", cwd=repo)
    patterns = sorted(set(known) | {f"{PACKS}/{pack}/" for pack in packs})
    if patterns != known:
        # Cone mode cannot express the adventure bestiary wildcard.
        _git("sparse-checkout", "set", "--no-cone", *patterns, cwd=repo)
        _remember(patterns)
    return repo


def files(packs: tuple[str, ...], refresh: bool = False) -> list[Path]:
    """Every item JSON in the given pack directories, `_folders.json` excluded."""
    ensure(packs, refresh)
    out: list[Path] = []
    base = repo_dir() / PACKS
    for pack in packs:
        for directory in sorted(base.glob(pack)):
            if directory.is_dir():
                out.extend(sorted(path for path in directory.glob("**/*.json")
                                  if not path.name.startswith("_")))
    return out


def load(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise TcardError(f"cannot read {path}: {exc}", 3) from exc
