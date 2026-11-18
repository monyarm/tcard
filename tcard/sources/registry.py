"""Registered systems. Adding a system means adding one package and one line."""

from __future__ import annotations

from . import fivee

SYSTEMS = {fivee.SYSTEM_ID: fivee}
ALIASES = {alias: fivee.SYSTEM_ID for alias in fivee.ALIASES}


def systems() -> list[str]:
    return list(SYSTEMS)


def names() -> list[str]:
    return list(SYSTEMS) + list(ALIASES)


def resolve(token: str) -> str:
    return ALIASES.get(token, token)


def families() -> set[str]:
    return {name.split(":", 1)[0] for name in names() if ":" in name}


def kinds(system: str) -> dict:
    try:
        module = SYSTEMS[system]
    except KeyError:
        raise KeyError(system) from None
    return module.KINDS
