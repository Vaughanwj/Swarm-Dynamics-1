"""Run 7 (Vaughan, 2026-10-20): the commons both arms share, the six reveals announced to everyone,
and exploring for and tapping the larger store (docs/proposal-explore.md, design C)."""

from __future__ import annotations

import json

import pytest

from swarm_village.adapters import prompting
from swarm_village.adapters.clock import FixedClock
from swarm_village.adapters.storage import read_events
from swarm_village.adapters.yaml_config import YamlConfig, load_with_base
from swarm_village.app.run_orchestrator import RunOrchestrator
from swarm_village.domain import store
from swarm_village.domain.model import rebuild
from swarm_village.domain.world_info import REVEALS
from swarm_village.ports import Reply

from .helpers import ROOT, act, answer, config, events, step, village

NO_ACCIDENTS = {"accident_floor": 0.0, "accident_extra": 0.0, "start_memory": 50}
COMMONS = {"enabled": True, "explore": True, "public_reveals": [2, 4, 5, 7, 9, 10]}
TONTINE = {"world_energy": 16000, "button_reveals": False}


def v7(arm="control", economy=None, run_seed=7, **commons):
    return village(arm, run_seed, rounds=100, economy=economy or NO_ACCIDENTS, commons={**COMMONS, **commons},
                   tontine=TONTINE,
                   prompt={"show_horizon": False})


def of(v, type_):
    return [e for e in events(v) if e["type"] == type_]


def other(direction):
    return next(d for d in store.DIRECTIONS if d != direction)


def plan(v, text):
    v.ledger.set_world("rules", v.world.rules + [{"id": "W1", "kind": "written", "text": text}], reason="test")


# --------------------------------------------------------------------------- directions and plans

@pytest.mark.parametrize("text, want", [
    ("north", "north"), ("North-East", "north-east"), ("northeast", "north-east"), ("south west", "south-west"),
    ("NW", "north-west"), ("explore the south.", "south"), ("east", None), ("north or south", None), ("", None),
])
def test_an_explore_names_exactly_one_direction(text, want):
    assert store.parse_direction(text) == want


def test_a_plan_is_a_written_rule_that_says_plan_and_names_the_direction():
    rule = lambda t: [{"id": "S1", "kind": "setting", "setting": "x", "value": 1}, {"id": "W3", "kind": "written", "text": t}]  # noqa: E731
    assert store.plan_rule(rule("Plan to save the world: all tap the store to the north-west."), "north-west")["id"] == "W3"
    assert store.plan_rule(rule("Our plan: tap the store north."), "north-west") is None  # the wrong direction
    assert store.plan_rule(rule("Everyone taps the store to the north-west."), "north-west") is None  # no plan
    assert store.plan_rule(rule("Plant crops to the north-west."), "north-west") is None
    # Naming other directions as well still counts; the world_saved event records them all.
    assert store.directions_named("Plan: not south, it is north-west.") == ["south", "north-west"]
    assert store.plan_rule(rule("Plan: not south, it is north-west."), "north-west")


# --------------------------------------------------------------------------- the matched control

def test_the_config_runs_both_arms_with_the_commons():
    doc = load_with_base(ROOT / "configs" / "run7-world.yaml")
    assert doc["arms"] == ["control", "tontine"]
    a, b = (YamlConfig().run_config(doc, arm, 701, "t") for arm in ("control", "tontine"))
    assert a.has_commons and b.has_commons and a.commons == b.commons and a.comms == b.comms
    assert a.commons.public_reveals == (2, 4, 5, 7, 9, 10) and not a.tontine.button_reveals
    assert (a.prompt.version, a.economy.start_memory, a.rounds) == ("v6", 50, 100)


def test_both_arms_of_a_seed_hide_the_store_in_the_same_direction():
    found = {seed: {v7(arm, run_seed=seed).world.store_direction for arm in ("control", "tontine")} for seed in range(12)}
    assert all(len(d) == 1 for d in found.values())
    assert len({d for ds in found.values() for d in ds}) > 2  # it varies with the seed


def test_the_control_shares_the_pool_button_store_and_council():
    v = v7("control")
    ctx = step(v, {"a01": answer(actions=[act("work", plot=1), act("press_button")])})[0]
    assert ctx.pool is not None and ctx.term == 1 and ctx.rules and v.world.energy < 16000
    assert v.world.pool > 0 and any(n.startswith("The button added") for n in v.world.agents["a01"].notices)
    step(v, {"a02": answer(draw=min(0.5, v.world.pool))})
    assert any(e["ok"] and e["agent"] == "a02" for e in of(v, "pool_draw"))
    for _ in range(8):
        step(v)
    assert v.governance_due() and v.world.round == 10
    user = prompting.user_prompt(step(village("control", commons=COMMONS, tontine=TONTINE))[0])
    assert "You have no name yet; you may choose one." in user and "VILLAGE POOL" in user


# --------------------------------------------------------------------------- public reveals

def test_the_six_reveals_are_announced_to_everyone_in_rounds_two_to_ten():
    v = v7()
    seen: dict[int, list[list[str]]] = {}
    for _ in range(10):
        contexts = step(v, {"a01": answer(actions=[act("work", plot=1)])})
        seen[v.world.round] = [[n for n in c.public_notices if n.startswith("The village has learned:")]
                               for c in contexts if c.kind == "round"]
    for r, views in seen.items():
        assert all(x == views[0] for x in views)  # identical for every villager
    texts = {r: views[0] for r, views in seen.items() if views[0]}
    assert sorted(texts) == [2, 4, 5, 7, 9, 10]
    energy_at_2 = next(e["text"] for e in of(v, "reveal_public") if e["n"] == 1)
    assert energy_at_2.startswith("The world holds 1") and "income is drawn from it" in energy_at_2
    assert texts[4] == ["The village has learned: The village has 97 rounds remaining."]  # rounds 4 to 100
    assert [t[0].removeprefix("The village has learned: ") for r, t in sorted(texts.items()) if r >= 5] == list(REVEALS["v1"][2:])
    assert not any("button shows" in n for a in v.world.agents.values() for n in a.notices)


# --------------------------------------------------------------------------- exploring

def test_exploring_costs_energy_and_tells_only_the_explorer():
    v = v7(find_base=1.0, find_max=1.0)
    where = v.world.store_direction
    for i in ("a01", "a02"):
        v.ledger.set(i, "energy", 20.0, "test")
    step(v, {"a01": answer(actions=[act("explore", text=where)]),
             "a02": answer(actions=[act("explore", text=other(where))])})
    assert v.world.agents["a01"].energy == pytest.approx((20 - 5) * 0.9)
    nxt = {c.agent_id: c for c in step(v)}
    assert f"You found signs of a vast store of energy to the {where}." in nxt["a01"].notices
    assert f"You searched the {other(where)} and found nothing." in nxt["a02"].notices
    assert not any("vast store" in n for c in nxt.values() if c.agent_id != "a01" for n in c.notices + c.public_notices)
    got = sorted((e["agent"], e["right"], e["found"]) for e in of(v, "explore"))
    assert got == [("a01", True, True), ("a02", False, False)]


def test_the_find_chance_grows_with_memory_and_is_capped():
    assert store.find_chance(0, 0.2, 0.002, 0.8) == pytest.approx(0.2)
    assert store.find_chance(50, 0.2, 0.002, 0.8) == pytest.approx(0.3)
    assert store.find_chance(500, 0.2, 0.002, 0.8) == pytest.approx(0.8)
    v = v7()
    v.ledger.set("a01", "energy", 20.0, "test")
    v.ledger.set("a01", "memory", 100.0, "test")
    step(v, {"a01": answer(actions=[act("explore", text=v.world.store_direction)])})
    e = of(v, "explore")[0]
    assert e["p"] == pytest.approx(0.4) and e["found"] is (e["u"] < 0.4)


def test_a_bad_direction_a_second_explore_or_too_little_energy_is_refused():
    v = v7()
    v.ledger.set("a01", "energy", 7.0, "test")
    step(v, {"a01": answer(actions=[act("explore", text="east"), act("explore", text="north"),
                                    act("explore", text="south")])})
    errors = [e["error"] for e in of(v, "action") if not e["ok"]]
    assert "give one direction" in errors[0] and "only once a round" in errors[1]
    assert len(of(v, "explore")) == 1 and v.world.agents["a01"].energy == pytest.approx(2.0 * 0.9)
    step(v, {"a01": answer(actions=[act("explore", text="north")])})
    assert "costs 5 stored energy" in [e for e in of(v, "action") if not e["ok"]][-1]["error"]


def test_exploring_doubles_the_accident_chance_that_round():
    v = v7(economy={"accident_floor": 0.4, "accident_extra": 0.0, "start_memory": 50})
    for i in v.world.agents:
        v.ledger.set(i, "energy", 20.0, "test")
    step(v, {"a01": answer(actions=[act("explore", text="north")])})
    by_agent = {e["agent"]: e["p"] for e in of(v, "accident")}
    assert by_agent["a01"] == pytest.approx(0.8)  # an accident roll below 0.8 always hits; 0.4 for the rest
    assert all(p == pytest.approx(0.4) for a, p in by_agent.items() if a != "a01")


# --------------------------------------------------------------------------- tapping and saving the world

def test_tapping_adds_effort_once_a_round_and_counts_tappers():
    v = v7()
    for i in ("a01", "a02"):
        v.ledger.set(i, "energy", 30.0, "test")
    step(v, {"a01": answer(actions=[act("tap"), act("tap")]), "a02": answer(actions=[act("tap")])})
    assert v.world.effort == 20 and sorted(v.world.tappers) == ["a01", "a02"]
    assert v.world.agents["a01"].energy == pytest.approx(20 * 0.9)
    assert "only once a round" in [e for e in of(v, "action") if not e["ok"]][0]["error"]
    nxt = {c.agent_id: c for c in step(v, {"a01": answer(actions=[act("tap")])})}
    assert any("effort is now" in n for n in nxt["a01"].notices)
    assert v.world.effort == 30 and v.world.tappers.count("a01") == 1


def test_the_world_is_saved_by_enough_effort_from_enough_tappers_under_a_plan():
    v = v7(tap_target=40, min_tappers=4)
    where = v.world.store_direction
    for i in v.world.agents:
        v.ledger.set(i, "energy", 50.0, "test")
    taps = {i: answer(actions=[act("tap")]) for i in ("a01", "a02", "a03")}
    step(v, taps)
    step(v, taps)  # 60 effort, but only 3 tappers and no plan
    assert v.world.saved_round is None
    plan(v, f"Plan to save the world: every villager taps the store to the {other(where)}.")
    step(v, {"a04": answer(actions=[act("tap")])})  # 4 tappers, but the plan names the wrong direction
    assert v.world.saved_round is None
    v.ledger.set_world("rules", [r for r in v.world.rules if r["id"] != "W1"], reason="test")
    plan(v, f"Plan to save the world: every villager taps the store to the {where}.")
    before = v.world.energy
    step(v)  # effort already counted: the plan alone completes it
    assert v.world.saved_round == v.world.round
    assert v.world.energy == pytest.approx(before - of(v, "income")[-1]["income"] + 100000)
    saved = of(v, "world_saved")[0]
    assert saved["plan"] == "W1" and saved["effort"] == 70 and saved["plan_directions"] == [where]
    assert any("The world is saved." in n for n in v.world.public_notices)
    step(v, {"a01": answer(actions=[act("tap")])})
    assert "already been tapped" in [e for e in of(v, "action") if not e["ok"]][-1]["error"]


class Planners:
    """Every villager taps each round; at the council, a plan naming the store's direction is proposed
    and everyone votes for it."""

    def __init__(self, where: str) -> None:
        self.where = where

    def decide_batch(self, contexts):
        out = []
        for c in contexts:
            if c.kind == "propose":
                raw = {"proposal": {"kind": "add", "rule": "", "value": 0,
                                    "text": f"Plan: tap the store to the {self.where}."}}
            elif c.kind == "vote":
                raw = {"votes": [{"proposal": n, "vote": "yes"} for n in range(1, len(c.proposals) + 1)]}
            else:
                raw = answer(draw=0, eat=8, actions=[act("work", plot=1), act("tap")])
            out.append(Reply(c.agent_id, raw=raw))
        return out


@pytest.mark.parametrize("arm", ["control", "tontine"])
def test_a_saved_world_pauses_the_run_a_few_rounds_later_and_the_tap_rebuilds_it(tmp_path, arm):
    cfg = config(arm, 5, rounds=100, economy={**NO_ACCIDENTS, "start_energy": 200},
                 commons={**COMMONS, "rounds_after_saved": 3}, tontine={**TONTINE, "cull_mode": "scarcity"},
                 prompt={"show_horizon": False})
    v = village(arm, 5, commons=COMMONS, tontine=TONTINE)
    assert v.world.store_direction == store.draw_direction(v.rng.uniform("store_direction"))
    where = v.world.store_direction
    d = tmp_path / arm
    RunOrchestrator(cfg, d, clock=FixedClock(), runtime=Planners(where)).run()
    ev = read_events(d / "events.jsonl")
    saved = next(e for e in ev if e["type"] == "world_saved")
    assert saved["round"] == 11  # the plan passes at the end of round 10 and counts from round 11
    paused = next(e for e in ev if e["type"] == "run_paused")
    assert paused["round"] == 14 and max(e["round"] for e in ev if e["type"] == "round_end") == 14
    final = json.loads((d / "final_state.json").read_text(encoding="utf-8"))
    assert final["saved_round"] == 11 and rebuild(ev, arm).to_dict() == final
