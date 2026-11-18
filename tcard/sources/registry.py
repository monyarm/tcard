"""Registered systems. Adding a system means adding one package and one line."""

from __future__ import annotations

from . import fivee, pf1, pf2, vtm

SYSTEMS = {fivee.SYSTEM_ID: fivee, pf1.SYSTEM_ID: pf1, pf2.SYSTEM_ID: pf2, vtm.SYSTEM_ID: vtm}
ALIASES = {alias: module.SYSTEM_ID for module in (fivee, pf1, pf2, vtm) for alias in module.ALIASES}


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
