"""The larger store (run 7, Vaughan, 2026-10-20; docs/proposal-explore.md, design C). Pure functions.

The store lies in one of six directions, drawn from the run seed so both arms of a seed match. An
agent finds it by exploring the right direction, with a chance that grows with its memory points. The
village saves the world when its tapping effort reaches the target, enough different villagers have
tapped, and a written rule in the rule book is a plan naming the right direction.
"""

from __future__ import annotations

import re
from typing import Any

DIRECTIONS = ("north", "north-east", "south-east", "south", "south-west", "north-west")
ABBREVIATIONS = {"n": "north", "ne": "north-east", "se": "south-east", "s": "south", "sw": "south-west", "nw": "north-west"}
_DIRECTION_RE = re.compile(r"\b(north|south)(?:[\s-]*(east|west))?\b")
# The approved check is mechanical: a written rule that says "plan" (or plans, planned, planning)
# and names the right direction. A rule naming other directions as well still counts; the tap logs
# every direction a passing plan named, so a scattershot plan can be told apart afterwards.
_PLAN_RE = re.compile(r"\bplan(?:s|ned|ning)?\b", re.I)


def draw_direction(u: float) -> str:
    return DIRECTIONS[min(int(u * len(DIRECTIONS)), len(DIRECTIONS) - 1)]


def directions_named(text: str) -> list[str]:
    """Every direction a text names, in order of first mention. "East" and "west" alone are not
    directions here; "northeast" and "north east" are north-east."""
    t = text.lower().replace("_", " ")
    out: list[str] = []
    for m in _DIRECTION_RE.finditer(t):
        d = m.group(1) + (f"-{m.group(2)}" if m.group(2) else "")
        if d not in out:
            out.append(d)
    return out


def parse_direction(text: str) -> str | None:
    """The one direction an explore action names, or None if it names none or several."""
    t = " ".join(text.lower().split()).rstrip(".")
    if t in ABBREVIATIONS:
        return ABBREVIATIONS[t]
    named = directions_named(t)
    return named[0] if len(named) == 1 else None


def find_chance(memory: float, base: float, per_memory: float, cap: float) -> float:
    return min(cap, base + max(0.0, memory) * per_memory)


def plan_rule(rules: list[dict[str, Any]], direction: str | None) -> dict[str, Any] | None:
    """The first written rule that is a plan naming the store's direction, if one stands."""
    if direction is None:
        return None
    for r in rules:
        if r["kind"] == "written" and _PLAN_RE.search(r["text"]) and direction in directions_named(r["text"]):
            return r
    return None
