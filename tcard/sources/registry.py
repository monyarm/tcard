"""Registered systems. Adding a system means adding one package and one line."""

from __future__ import annotations

from . import cp, fivee, pf1, pf2, v20, vtm

SYSTEMS = {
    module.SYSTEM_ID: module for module in (fivee, pf1, pf2, vtm, v20, cp)
}
ALIASES = {alias: module.SYSTEM_ID for module in (fivee, pf1, pf2, vtm, v20, cp) for alias in module.ALIASES}


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
