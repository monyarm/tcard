"""Vampire: The Masquerade 5th edition, from the VTM Wiki via the proxy."""

from __future__ import annotations

from ..base import Kind
from . import advantages, clans, disciplines, loresheets, predators, rituals

SYSTEM_ID = "vtm:v5"
ALIASES = ("vtm", "v5")

KINDS: dict[str, Kind] = {
    "discipline": disciplines.DisciplineKind(),
    "clan": clans.ClanKind(),
    "loresheet": loresheets.LoresheetKind(),
    "predator_type": predators.PredatorKind(),
    "ritual": rituals.RitualKind(),
    "merit": advantages.AdvantageKind("merit"),
    "flaw": advantages.AdvantageKind("flaw"),
}
