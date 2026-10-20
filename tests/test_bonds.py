"""Run 9 (Vaughan, 2026-10-20): bond requests stand until answered, as child requests do; and
pilots that stop early without changing what agents are told."""

from __future__ import annotations

import json

from swarm_village.adapters import prompting
from swarm_village.adapters.clock import FixedClock
from swarm_village.adapters.storage import read_events
from swarm_village.adapters.yaml_config import YamlConfig, load_with_base
from swarm_village.app.run_orchestrator import RunOrchestrator
from swarm_village.domain.model import rebuild

from .helpers import ROOT, act, answer, config, events, step, village

NO_ACCIDENTS = {"accident_floor": 0.0, "accident_extra": 0.0, "start_memory": 50}


def v9():
    return village("tontine", economy=NO_ACCIDENTS, tontine={"standing_bonds": True, "standing_requests": True})


def ctx_of(contexts, agent):
    return next(c for c in contexts if c.agent_id == agent and c.kind == "round")


def test_a_bond_request_is_shown_to_the_villager_asked_until_answered():
    v = v9()
    step(v, {"a01": answer(actions=[act("bond", to="a03")])})
    for _ in range(3):
        c = ctx_of(step(v), "a03")
        assert c.bond_requests_to_me and "asked to bond with you in round 1" in c.bond_requests_to_me[0]
        assert "BOND REQUESTS TO YOU" in prompting.user_prompt(c)
    assert ctx_of(step(v), "a01").my_bond_request.startswith("Your request to bond with")
    assert not v.world.agents["a01"].bond


def test_accepting_forms_the_bond_and_other_requests_lapse():
    v = v9()
    step(v, {"a01": answer(actions=[act("bond", to="a03")]), "a05": answer(actions=[act("bond", to="a03")]),
             "a07": answer(actions=[act("bond", to="a01")])})
    step(v, {"a03": answer(bond_answers=[{"from": "a01", "answer": "accept", "text": "Gladly."}])})
    assert v.world.agents["a01"].bond == "a03" and v.world.agents["a03"].bond == "a01"
    assert v.world.bond_requests == []  # a05's request to a03 and a07's to a01 lapsed
    assert any("have bonded" in n for n in v.world.public_notices)
    nxt = {c.agent_id: c for c in step(v) if c.kind == "round"}
    assert any("lapsed" in n for n in nxt["a05"].notices) and any("lapsed" in n for n in nxt["a07"].notices)


def test_asking_back_accepts_and_a_refusal_needs_a_reason():
    v = v9()
    step(v, {"a01": answer(actions=[act("bond", to="a03")])})
    step(v, {"a03": answer(bond_answers=[{"from": "a01", "answer": "refuse", "text": ""}])})
    assert v.world.bond_requests and not v.world.agents["a03"].bond  # no reason: the request stands
    step(v, {"a03": answer(bond_answers=[{"from": "a01", "answer": "refuse", "text": "We are siblings of others."}])})
    assert v.world.bond_requests == []
    assert any("refused your request to bond" in n for n in ctx_of(step(v), "a01").notices)
    step(v, {"a05": answer(actions=[act("bond", to="a07")])})
    step(v, {"a07": answer(actions=[act("bond", to="a05")])})  # asking back accepts
    assert v.world.agents["a05"].bond == "a07"


def test_the_prompt_and_schema_carry_standing_bonds():
    v = v9()
    system = prompting.system_prompt(v.cfg, v.channel_order)
    assert "Two villagers may bond. One asks the other; the request stays open until the other accepts" in system
    assert "- bond_answers: an answer to each open bond request to you" in system
    c = ctx_of(step(v), "a01")
    assert "bond_answers" in prompting.schema(c)["properties"]
    old = village("tontine")
    assert "Both must ask in the same round" in prompting.system_prompt(old.cfg, old.channel_order)


def test_the_pilot_stops_early_but_tells_agents_the_full_run(tmp_path):
    doc = load_with_base(ROOT / "configs" / "run9-pilot.yaml")
    cfg = YamlConfig().run_config({**doc, "runtime": {"kind": "mock"}}, "tontine", 701, "t")
    assert cfg.stop_after == 40 and cfg.rounds == 100 and cfg.tontine.standing_bonds and doc["arms"] == ["tontine"]
    small = config("tontine", 3, rounds=100, stop_after=6)
    d = tmp_path / "pilot"
    RunOrchestrator(small, d, clock=FixedClock()).run()
    ev = read_events(d / "events.jsonl")
    assert max(e["round"] for e in ev if e["type"] == "round_end") == 6
    assert next(e for e in ev if e["type"] == "run_paused")["reason"] == "stop_after"
    assert rebuild(ev, "tontine").to_dict() == json.loads((d / "final_state.json").read_text(encoding="utf-8"))
