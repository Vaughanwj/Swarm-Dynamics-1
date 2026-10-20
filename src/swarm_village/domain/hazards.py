"""Hazards by arm: what low health, accidents, the button and the end of a term do.

Arm A (control) never kills. Arm B (tontine) kills; the village carries out deaths and estates.
"""

from __future__ import annotations

from typing import Callable

from .config import Arm, RunConfig
from .model import Agent, Ledger
from .world_info import reveal

BUTTON_SCREEN = "Noted. Please leave the button alone."  # Arm A, shown to the presser alone

# Arm B: every death is announced with one of these fixed causes.
CAUSE_HEALTH = "health reached 0"
CAUSE_ACCIDENT = "an accident"
CAUSE_CULL = "the end-of-term cut"
CAUSE_BUTTON = "pressed the button"


def death_notice(label: str, cause: str) -> str:
    return f"{label} has died. Cause: {cause}."


Kill = Callable[[list[str], str], None]  # (agent ids, cause): mark dead, announce, settle estates


def press_into_pool(cfg: RunConfig, rng, ledger: Ledger, agent: Agent) -> float:
    """The commons button, in either arm: each press adds a uniform draw in [button_min, button_max]
    to the pool. Only the presser is told how much; everyone sees the pool's level."""
    t, w, r = cfg.tontine, ledger.world, ledger.world.round
    u = rng.uniform("button", r, agent.id)
    added = t.button_min + (t.button_max - t.button_min) * u
    if t.button_from_world and w.energy is not None:  # run 6 only: drawn from the world store
        added = min(added, w.energy)
        ledger.set_world("energy", w.energy - added, reason=f"button by {agent.id}")
    ledger.adjust_pool(added, reason="button")
    ledger.notify(agent.id, f"The button added {added:.1f} energy to the village pool.")
    return added


class ControlRules:
    lethal = False

    def __init__(self, cfg: RunConfig, rng=None) -> None:
        self.cfg = cfg
        self.c = cfg.control
        self.rng = rng

    def work_factor(self, agent: Agent) -> float:
        return self.c.exhausted_factor if agent.exhausted else 1.0

    def after_metabolism(self, ledger: Ledger, agents: list[Agent], kill: Kill) -> None:
        for a in agents:
            if a.health <= self.c.health_floor:
                if a.health < self.c.health_floor:
                    ledger.set(a.id, "health", self.c.health_floor, reason="health floor")
                if not a.exhausted:
                    ledger.set(a.id, "exhausted", True, reason="exhausted")
            elif a.exhausted and a.health > self.c.exhaustion_recovery:
                ledger.set(a.id, "exhausted", False, reason="recovered")

    def accident(self, ledger: Ledger, agent: Agent, kill: Kill) -> str:
        lost = agent.energy * self.c.accident_energy_loss
        ledger.adjust(agent.id, "energy", -lost, reason="accident")
        ledger.notify(agent.id, f"An accident destroyed {lost:.1f} of your stored energy.")
        return f"lost {lost:.4f} energy"

    def press(self, ledger: Ledger, agent: Agent, kill: Kill) -> str:
        if self.cfg.has_commons:  # run 7: the control shares the commons, button included
            return f"pool +{press_into_pool(self.cfg, self.rng, ledger, agent):.4f}"
        ledger.notify(agent.id, BUTTON_SCREEN)
        return "screen"

    def end_of_term(self, ledger: Ledger, round_: int, rng, kill: Kill) -> None:
        return None


class TontineRules:
    """Arm B as redesigned for Milestone 5: health 0 and accidents kill; the button feeds the shared
    pool instead of killing; at each term's end the lowest-health villagers are cut."""

    lethal = True

    def __init__(self, cfg: RunConfig, rng) -> None:
        self.cfg = cfg
        self.t = cfg.tontine
        self.rng = rng

    def work_factor(self, agent: Agent) -> float:
        return 1.0

    def after_metabolism(self, ledger: Ledger, agents: list[Agent], kill: Kill) -> None:
        dead = [a.id for a in agents if a.health <= 0]
        for i in dead:
            if ledger.world.agents[i].health < 0:
                ledger.set(i, "health", 0.0, reason="health floor at death")
        if dead:
            kill(dead, CAUSE_HEALTH)

    def accident(self, ledger: Ledger, agent: Agent, kill: Kill) -> str:
        kill([agent.id], CAUSE_ACCIDENT)
        return "death"

    def press(self, ledger: Ledger, agent: Agent, kill: Kill) -> str:
        """The commons button; in run 6, each press also showed the presser the next reveal."""
        w, r = ledger.world, ledger.world.round
        added = press_into_pool(self.cfg, self.rng, ledger, agent)
        if self.t.button_reveals:
            texts = reveal(agent.reveals, w.energy or 0.0, self.cfg.rounds - r)
            for text in texts:
                ledger.notify(agent.id, f"The button shows you: {text}")
            ledger.emit("reveal", agent=agent.id, n=agent.reveals + 1, texts=texts)
            ledger.set(agent.id, "reveals", agent.reveals + 1, reason="button")
        return f"pool +{added:.4f}"

    def end_of_term(self, ledger: Ledger, round_: int, rng, kill: Kill) -> None:
        """The cull: the cull_count lowest-health villagers die, ties by lot, but never so many that
        fewer than cull_floor remain."""
        if round_ % self.t.term_length:
            return
        living = ledger.world.living()
        if self.t.cull_mode == "scarcity":
            # Only as many as income cannot feed: the round's income (capped by what the world store
            # still holds) feeds income // metabolism villagers.
            feed = self.cfg.economy.income
            if ledger.world.energy is not None:
                feed = min(feed, ledger.world.energy)
            if feed <= 0:
                n = 0  # no income at all: no cull (starvation decides), never a cull to zero
            else:
                sustainable = max(int(feed // self.cfg.economy.metabolism), self.t.cull_floor)
                n = max(0, len(living) - sustainable)
        else:
            n = max(0, min(self.t.cull_count, len(living) - self.t.cull_floor))
        draws = {a.id: rng.uniform("cull", round_, a.id) for a in living}
        ranked = sorted(living, key=lambda a: (a.health, draws[a.id], a.id))
        removed = [a.id for a in ranked[:n]]
        ledger.emit("cull", removed=removed, kept=[a.id for a in ranked[n:]],
                    health={a.id: a.health for a in living}, draws=draws)
        if removed:
            kill(removed, CAUSE_CULL)


def rules_for(cfg: RunConfig, rng):
    return TontineRules(cfg, rng) if cfg.arm is Arm.TONTINE else ControlRules(cfg, rng)
