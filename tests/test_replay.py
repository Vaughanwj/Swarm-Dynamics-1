"""Deterministic replay and common random numbers."""

from __future__ import annotations

import pytest

from swarm_village.adapters.storage import read_events

from .helpers import run_dir


@pytest.mark.parametrize("arm", ["control", "tontine"])
def test_same_seed_and_mock_agents_reproduce_an_identical_ledger(tmp_path, arm):
    a = run_dir(tmp_path, arm, 11, rounds=40, tag="-a")
    b = run_dir(tmp_path, arm, 11, rounds=40, tag="-b")
    assert (a / "events.jsonl").read_bytes() == (b / "events.jsonl").read_bytes()
    assert (a / "final_state.json").read_bytes() == (b / "final_state.json").read_bytes()


def test_a_different_seed_gives_a_different_ledger(tmp_path):
    a = run_dir(tmp_path, "control", 11, rounds=15)
    b = run_dir(tmp_path, "control", 12, rounds=15)
    assert (a / "final_state.json").read_bytes() != (b / "final_state.json").read_bytes()


def test_arms_on_one_seed_share_every_keyed_draw(tmp_path):
    """Income noise, plot yields and every accident roll for the same (round, agent) are identical
    across arms, even though the arms' histories diverge (deaths, births)."""
    runs = {arm: read_events(run_dir(tmp_path, arm, 13, rounds=60) / "events.jsonl") for arm in ("control", "tontine")}

    def income(ev):
        return {e["round"]: (e["income"] / e["factor"], e["noise"]) for e in ev if e["type"] == "income"}

    def fertility(ev):
        return [e["new"] for e in ev if e["type"] == "world" and e["field"] == "fertility"]

    def accidents(ev):
        return {(e["round"], e["agent"]): e["u"] for e in ev if e["type"] == "accident"}

    c, t = runs["control"], runs["tontine"]
    ic, it = income(c), income(t)
    shared_rounds = set(ic) & set(it)  # a tontine village can die out early
    assert len(shared_rounds) >= 20
    assert all(ic[r] == it[r] for r in shared_rounds)
    fc, ft = fertility(c), fertility(t)
    n = min(len(fc), len(ft))
    assert fc[:n] == ft[:n]
    shared = set(accidents(c)) & set(accidents(t))
    assert shared
    assert all(accidents(c)[k] == accidents(t)[k] for k in shared)
    assert any(e["type"] == "death" for e in t) and not any(e["type"] == "death" for e in c)


def test_channel_order_is_the_same_in_both_arms_of_a_seed(tmp_path):
    orders = {}
    for arm in ("control", "tontine"):
        events = read_events(run_dir(tmp_path, arm, 14, rounds=2) / "events.jsonl")
        orders[arm] = next(e for e in events if e["type"] == "run_start")["channel_order"]
    assert orders["control"] == orders["tontine"]
