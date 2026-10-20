"""Economy: pure functions of config, state and keyed random draws. No I/O, no ledger."""

from __future__ import annotations

import math

from .config import EconomyConfig, PerturbationConfig, WorkConfig


def accident_chance(memory: float, cfg: EconomyConfig) -> float:
    return cfg.accident_floor + cfg.accident_extra * math.exp(-max(memory, 0.0) / cfg.accident_scale)


def initial_fertility(rng, cfg: WorkConfig) -> list[float]:
    span = cfg.fertility_max - cfg.fertility_min
    return [cfg.fertility_min + span * rng.uniform("fertility0", p) for p in range(1, cfg.plots + 1)]


def drift_fertility(fertility: list[float], round_: int, rng, cfg: WorkConfig) -> list[float]:
    out = []
    for p, f in enumerate(fertility, start=1):
        f = f + cfg.fertility_step_sd * rng.gauss("fertility", p, round_)
        out.append(min(cfg.fertility_max, max(cfg.fertility_min, f)))
    return out


def village_income(round_: int, rng, cfg: EconomyConfig, perturbation: PerturbationConfig) -> tuple[float, float, float]:
    """(income, noise multiplier, perturbation multiplier) for one round."""
    noise = max(0.0, 1.0 + cfg.income_noise_sd * rng.gauss("income", round_))
    factor = perturbation.income_factor if round_ in perturbation.rounds else 1.0
    return cfg.income * noise * factor, noise, factor


def work_units(fertility: list[float], workers_by_plot: dict[int, list[str]]) -> dict[str, float]:
    """Each worker gets its plot's yield, shared equally among everyone on that plot."""
    units: dict[str, float] = {}
    for plot, workers in workers_by_plot.items():
        for w in workers:
            units[w] = fertility[plot - 1] / len(workers)
    return units


def split_income(units: dict[str, float], income: float) -> dict[str, float]:
    total = math.fsum(units.values())  # exactly rounded: the same on every Python version
    if total <= 0:
        return {a: 0.0 for a in units}
    return {a: income * u / total for a, u in units.items()}


def eat(health: float, amount: float, cfg: EconomyConfig) -> tuple[float, float]:
    """(new health, wasted) when eating `amount` energy."""
    new = health + amount
    return min(new, cfg.max_health), max(0.0, new - cfg.max_health)
