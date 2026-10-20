"""Referendums and the village's changeable values (run 10, Vaughan, 2026-10-20). Pure functions.

Every `commons.referendum_every` rounds the village holds a referendum in which every villager votes.
The first chooses the village's name: names are proposed in its round and voted on the round after.
After that, the council decides each question at the session before the referendum: change one of
the village's known values (VALUES, each with bounds) or the village's name. If a majority of all
living villagers votes yes, the next council votes on enacting it; if a majority of the council also
agrees, it takes effect from the next round, even when it changes a configuration value. A changed
value is kept in the world (`overrides`), so the tap can rebuild it, and the run's configuration is
derived from the base configuration and those overrides.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

# id -> what agents are told the value is (each is stated in the rules they see), its configuration
# path, how it is shown, its bounds, and the arms it exists in. Hidden values (the tapping target,
# the world store, the horizon) are not here: a referendum changes only what villagers know.
VALUES: dict[str, dict[str, Any]] = {
    "V1": {"path": "economy.metabolism", "label": "Health every villager loses each round", "kind": "num", "lo": 4, "hi": 12},
    "V2": {"path": "economy.income", "label": "Energy the village earns each round (about)", "kind": "num", "lo": 60, "hi": 240},
    "V3": {"path": "economy.spoilage", "label": "Share of stored energy lost each round", "kind": "pct", "lo": 0.0, "hi": 0.3},
    "V4": {"path": "economy.memory_fade", "label": "Share of memory points lost each round", "kind": "pct", "lo": 0.0, "hi": 0.1},
    "V5": {"path": "tontine.pool_spoilage", "label": "Share of the pool lost each round", "kind": "pct", "lo": 0.0, "hi": 0.3},
    "V6": {"path": "commons.explore_cost", "label": "Stored energy an explore costs", "kind": "num", "lo": 0, "hi": 20},
    "V7": {"path": "commons.tap_cost", "label": "Stored energy a tap costs", "kind": "num", "lo": 0, "hi": 30},
    "V8": {"path": "comms.actions_per_round", "label": "Actions each villager may take a round", "kind": "int", "lo": 2, "hi": 8},
    "V9": {"path": "tontine.breed_cost", "label": "Stored energy each parent pays for a child", "kind": "num", "lo": 0, "hi": 40,
           "arms": ("tontine",)},
    "V10": {"path": "tontine.bond_child_cost", "label": "Stored energy each bonded parent pays for a child", "kind": "num",
            "lo": 0, "hi": 40, "arms": ("tontine",)},
    "V11": {"path": "tontine.child_health", "label": "Health a child starts with", "kind": "num", "lo": 20, "hi": 100,
            "arms": ("tontine",)},
    "V12": {"path": "tontine.max_population", "label": "Most villagers the village may hold", "kind": "int", "lo": 10, "hi": 30,
            "arms": ("tontine",)},
    "V13": {"path": "control.exhaustion_recovery", "label": "Health an exhausted villager must end a round above to recover",
            "kind": "num", "lo": 1, "hi": 50, "arms": ("control",)},
}


def values_for(arm: str) -> dict[str, dict[str, Any]]:
    return {k: v for k, v in VALUES.items() if arm in v.get("arms", ("control", "tontine"))}


def current(cfg: Any, vid: str) -> float:
    section, field = VALUES[vid]["path"].split(".")
    return getattr(getattr(cfg, section), field)


def fmt(vid: str, value: float) -> str:
    kind = VALUES[vid]["kind"]
    if kind == "pct":
        return f"{value * 100:g}%"
    return f"{int(value)}" if kind == "int" else f"{value:g}"


def line(cfg: Any, vid: str) -> str:
    v = VALUES[vid]
    return f"{vid} {v['label']}: {fmt(vid, current(cfg, vid))} (allowed {fmt(vid, v['lo'])} to {fmt(vid, v['hi'])})"


def parse_value(vid: str, value: Any, arm: str) -> tuple[float | None, str | None]:
    """A proposed new value, checked against its bounds. Percentages are given as fractions or as
    percent figures (0.05 or 5 both mean 5%)."""
    allowed = values_for(arm)
    if vid not in allowed:
        return None, f"There is no village value '{str(vid)[:8]}' a referendum can change; you proposed nothing."
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None, f"A referendum on {vid} needs its new value in value; you proposed nothing."
    v = allowed[vid]
    x = float(value)
    if v["kind"] == "pct" and x > 1:
        x /= 100.0
    if v["kind"] == "int":
        x = float(round(x))
    if not v["lo"] <= x <= v["hi"]:
        return None, f"{vid} must be from {fmt(vid, v['lo'])} to {fmt(vid, v['hi'])}; you proposed nothing."
    return x, None


def with_overrides(base: Any, overrides: dict[str, float]) -> Any:
    """The configuration as the village has changed it: the base, with each overridden value."""
    cfg = base
    for path, value in sorted(overrides.items()):
        section, field = path.split(".")
        old = getattr(getattr(cfg, section), field)
        value = int(value) if isinstance(old, int) and not isinstance(old, bool) else float(value)
        cfg = replace(cfg, **{section: replace(getattr(cfg, section), **{field: value})})
    return cfg


def is_round(r: int, every: int) -> bool:
    return bool(every) and r > 0 and r % every == 0


def next_round(r: int, every: int) -> int | None:
    """The first referendum round after round r."""
    return (r // every + 1) * every if every else None
