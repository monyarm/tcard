"""Read-only config: ~/.config/tcard/config.toml, defaults when absent."""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path


class ConfigError(Exception):
    pass


@dataclass
class Config:
    systems: list[str] = field(default_factory=lambda: ["dnd:5e"])
    kinds: list[str] = field(default_factory=list)
    prefer: list[str] = field(default_factory=lambda: ["XPHB", "PHB"])
    cols: int = 32


def config_path() -> Path:
    root = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(root) / "tcard" / "config.toml"


def _string_list(raw: dict, key: str, default: list[str], allow_empty: bool = False) -> list[str]:
    if key not in raw:
        return default
    value = raw[key]
    if not isinstance(value, list) or not all(isinstance(v, str) and v for v in value):
        raise ConfigError(f"{key} must be a list of non-empty strings")
    if not value and not allow_empty:
        raise ConfigError(f"{key} must be a non-empty list of strings")
    return value


def load(path: Path | None = None) -> Config:
    path = path or config_path()
    config = Config()
    if not path.exists():
        return config
    try:
        raw = tomllib.loads(path.read_text())
    except (tomllib.TOMLDecodeError, OSError) as exc:
        raise ConfigError(f"cannot read {path}: {exc}") from exc
    config.systems = _string_list(raw, "systems", config.systems)
    config.kinds = _string_list(raw, "kinds", config.kinds, allow_empty=True)
    config.prefer = _string_list(raw, "prefer", config.prefer)
    if "cols" in raw:
        cols = raw["cols"]
        if not isinstance(cols, int) or isinstance(cols, bool) or not 8 <= cols <= 200:
            raise ConfigError("cols must be an integer between 8 and 200")
        config.cols = cols
    return config
