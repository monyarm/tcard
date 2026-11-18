"""Vampire: The Masquerade 20th Anniversary Edition."""

from __future__ import annotations

from ..base import Kind
from . import advantages, disciplines, kindred, paths, rituals

SYSTEM_ID = "vtm:v20"
ALIASES = ("v20",)

KINDS: dict[str, Kind] = {
    "discipline": disciplines.DisciplineKind(),
    "clan": kindred.KindredKind("clan", "Clans (VTM)", "Clan",
                                {"Clan (VTM)", "Clan Curse", "Antitribu"}),
    "bloodline": kindred.KindredKind("bloodline", "Bloodlines (VTM)", "Bloodline",
                                     {"Bloodline (VTM)", "Antitribu"}),
    "ritual": rituals.RitualKind(),
    "path": paths.PathKind(),
    "merit": advantages.AdvantageKind("merit"),
    "flaw": advantages.AdvantageKind("flaw"),
}
