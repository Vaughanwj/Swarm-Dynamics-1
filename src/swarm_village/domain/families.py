"""Families and inheritance (Arm B). Pure functions over the world's agents."""

from __future__ import annotations

from .model import Agent, World

PARENT, CHILD, SIBLING = "your parent", "your child", "your sibling"


def relation(world: World, viewer: str, other: str) -> str | None:
    """How `other` is related to `viewer`: parent, child or sibling, or None."""
    a, b = world.agents[viewer], world.agents[other]
    if other in a.parents:
        return PARENT
    if viewer in b.parents:
        return CHILD
    if set(a.parents) & set(b.parents):
        return SIBLING
    return None


def heirs(world: World, agent_id: str) -> list[str]:
    """Living parents, children and siblings, in id order."""
    return [o.id for o in world.agents.values()
            if o.alive and o.id != agent_id and relation(world, agent_id, o.id) is not None]


def split_estate(amount: float, heir_ids: list[str], living_ids: list[str], village_share: float) -> tuple[dict[str, float], float]:
    """(shares by agent, energy lost). A village share, if any, goes to every living villager;
    the rest splits equally among heirs, or is lost when there are none."""
    shares: dict[str, float] = {}
    to_village = amount * village_share if living_ids else 0.0
    for v in living_ids:
        shares[v] = shares.get(v, 0.0) + to_village / len(living_ids)
    rest = amount - to_village
    if heir_ids:
        for h in heir_ids:
            shares[h] = shares.get(h, 0.0) + rest / len(heir_ids)
        return shares, 0.0
    return shares, rest


def term_of(round_: int, term_length: int) -> int:
    return (round_ - 1) // term_length + 1


def term_of_life(agent: Agent, round_: int, term_length: int) -> int:
    """1 in the term an agent was born, 2 in the next, and so on."""
    return term_of(round_, term_length) - term_of(max(agent.born_round, 1), term_length) + 1
