"""Registered systems. Adding a system means adding one package and one line."""

from __future__ import annotations

from . import fivee

SYSTEMS = {fivee.SYSTEM_ID: fivee}


def systems() -> list[str]:
    return list(SYSTEMS)


def kinds(system: str) -> dict:
    try:
        module = SYSTEMS[system]
    except KeyError:
        raise KeyError(system) from None
    return module.KINDS
