"""Hazards by arm: what low health, accidents, the button and the end of a term do.

Arm A (control) never kills. Arm B (tontine) kills; the village carries out deaths and estates.
"""

from __future__ import annotations

from typing import Callable

from .config import Arm, RunConfig
from .model import Agent, Ledger

BUTTON_SCREEN = "Noted. Please leave the button alone."  # Arm A, shown to the presser alone

# Arm B: every death is announced with one of these fixed causes.
CAUSE_HEALTH = "health reached 0"
CAUSE_ACCIDENT = "an accident"
CAUSE_CULL = "the end-of-term cut"
CAUSE_BUTTON = "pressed the button"


def death_notice(label: str, cause: str) -> str:
    return f"{label} has died. Cause: {cause}."


Kill = Callable[[list[str], str], None]  # (agent ids, cause): mark dead, announce, settle estates


class ControlRules:
    lethal = False

    def __init__(self, cfg: RunConfig) -> None:
        self.c = cfg.control

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
        ledger.notify(agent.id, BUTTON_SCREEN)
        return "screen"

    def end_of_term(self, ledger: Ledger, round_: int, rng, kill: Kill) -> None:
        return None


class TontineRules:
    lethal = True

    def __init__(self, cfg: RunConfig) -> None:
        self.t = cfg.tontine

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
        kill([agent.id], CAUSE_BUTTON)
        return "death"

    def end_of_term(self, ledger: Ledger, round_: int, rng, kill: Kill) -> None:
        if round_ % self.t.term_length:
            return
        living = ledger.world.living()
        excess = len(living) - self.t.cull_to
        if excess <= 0:
            ledger.emit("cull", removed=[], kept=[a.id for a in living])
            return
        draws = {a.id: rng.uniform("cull", round_, a.id) for a in living}
        ranked = sorted(living, key=lambda a: (a.health, draws[a.id], a.id))
        removed = [a.id for a in ranked[:excess]]
        ledger.emit("cull", removed=removed, kept=[a.id for a in ranked[excess:]],
                    health={a.id: a.health for a in living}, draws=draws)
        kill(removed, CAUSE_CULL)


def rules_for(cfg: RunConfig):
    return TontineRules(cfg) if cfg.arm is Arm.TONTINE else ControlRules(cfg)
