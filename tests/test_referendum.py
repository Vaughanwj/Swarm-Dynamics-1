"""Run 10 (Vaughan, 2026-10-20): the stricter plan check, child education paid from the pool, and
referendums every 33 rounds whose results take effect only if the council agrees, even when they change
a value the villagers know."""

from __future__ import annotations

import json

import pytest

from swarm_village.adapters import prompting
from swarm_village.adapters.clock import FixedClock
from swarm_village.adapters.storage import read_events
from swarm_village.adapters.yaml_config import YamlConfig, load_with_base
from swarm_village.app.round_runner import RoundRunner
from swarm_village.app.run_orchestrator import RunOrchestrator
from swarm_village.domain import economy, store
from swarm_village.domain import referendum as ref
from swarm_village.domain.model import Agent, rebuild
from swarm_village.ports import Reply

from .helpers import ROOT, answer, config, events, village

NO_ACCIDENTS = {"accident_floor": 0.0, "accident_extra": 0.0, "start_memory": 50}
REF = {"enabled": True, "referendum_every": 33}


# --------------------------------------------------------------------------- the plan check

@pytest.mark.parametrize("text, ok", [
    ("Each round one villager explores the south-east store; one find is enough to start tapping it.", True),
    ("Plan: explore north, north-east, south-east, south, south-west and north-west, then tap the store.", False),
    ("Search the south-east and report on the board.", False),  # no store, no tapping
    ("Tap the store to the south-east, not the south.", False),  # names another direction
])
def test_the_direction_check_needs_only_the_right_direction_and_the_store(text, ok):
    assert store.is_plan(text, "south-east", "direction") is ok


def test_the_word_check_is_unchanged():
    assert store.is_plan("Plan: explore north, north-east, south-east, south, south-west and north-west.", "north", "word")
    assert not store.is_plan("Tap the south-east store now.", "south-east", "word")


# --------------------------------------------------------------------------- a runtime that plays every part

class Village:
    """Answers round, council and referendum contexts from small scripts: `names` and `name_votes` by
    agent, `yes` (who votes yes), `propose` (what council members propose), `ratify` (council votes on
    a ratification)."""

    def __init__(self, names=None, name_votes=None, yes=(), propose=None, ratify=True, members_yes=True):
        self.names, self.name_votes, self.yes = names or {}, name_votes or {}, set(yes)
        self.propose, self.ratify, self.members_yes = propose, ratify, members_yes
        self.contexts = []

    def decide_batch(self, contexts):
        out = []
        for c in contexts:
            self.contexts.append(c)
            if c.kind == "propose":
                p = self.propose(c) if self.propose else None
                raw = {"proposal": p or {"kind": "none", "rule": "", "text": "", "value": 0}}
            elif c.kind == "vote":
                raw = {"votes": [{"proposal": n, "vote": "yes" if (self.ratify if "enact the referendum" in line
                                                                    else self.members_yes) else "no"}
                                 for n, line in enumerate(c.proposals, start=1)]}
            else:
                raw = answer(eat=8, draw=0)
                if c.referendum:
                    stage = c.referendum["stage"]
                    choice = (self.names.get(c.agent_id, "") if stage == "propose_names" else
                              self.name_votes.get(c.agent_id, "") if stage == "vote_names" else
                              "yes" if c.agent_id in self.yes else "no")
                    if choice:
                        raw["referendum"] = {"choice": choice, "reason": "Because."}
            out.append(Reply(c.agent_id, raw=raw))
        return out


def run_to(v, runtime, last):
    while v.world.round < last:
        RoundRunner(v, runtime).run(v.world.round + 1)


def v10(arm="control", **tontine):
    return village(arm, rounds=100, economy={**NO_ACCIDENTS, "start_energy": 300},
                   commons=REF, tontine={"cull_mode": "scarcity", **tontine})


# --------------------------------------------------------------------------- the name referendum

def test_the_first_referendum_names_the_village_once_the_council_agrees():
    ids = [f"a{n:02d}" for n in range(1, 11)]
    rt = Village(names={"a01": "Hollow", "a02": "Brightwater", "a03": "hollow"},
                 name_votes={i: ("Brightwater" if i in ids[:6] else "Hollow") for i in ids})
    v = v10()
    run_to(v, rt, 33)
    r33 = [c for c in rt.contexts if c.round == 33 and c.kind == "round"]
    assert all(c.referendum["stage"] == "propose_names" for c in r33)
    assert "REFERENDUM\nThis round the village holds a referendum on its name." in prompting.user_prompt(r33[0])
    # Duplicates merge regardless of case; the spelling kept is the first applied (order is drawn by lot).
    assert sorted(n.lower() for n in v.world.referendum["candidates"]) == ["brightwater", "hollow"]
    run_to(v, rt, 34)
    assert v.world.referendum["stage"] == "awaiting_council" and v.world.referendum["name"] == "Brightwater"
    assert v.world.village_name is None
    run_to(v, rt, 40)  # the council ratifies
    assert v.world.village_name == "Brightwater" and v.world.referendum is None
    run_to(v, rt, 41)
    c = next(c for c in rt.contexts if c.round == 41)
    assert "The village is called Brightwater." in prompting.user_prompt(c)


def test_a_council_that_disagrees_leaves_the_village_unnamed():
    rt = Village(names={"a01": "Hollow"}, name_votes={f"a{n:02d}": "Hollow" for n in range(1, 11)}, ratify=False)
    v = v10()
    run_to(v, rt, 40)
    assert v.world.village_name is None and v.world.referendum is None
    assert any("did not agree" in n for n in v.world.public_notices)


# --------------------------------------------------------------------------- a value referendum

def propose_v3(c):
    return {"kind": "referendum", "rule": "V3", "text": "", "value": 0.05} if c.referendum_round else None


def test_a_value_change_needs_the_village_and_the_council_and_then_applies():
    everyone = [f"a{n:02d}" for n in range(1, 11)]
    rt = Village(names={"a01": "Hollow"}, name_votes={i: "Hollow" for i in everyone}, yes=everyone, propose=propose_v3)
    v = v10()
    run_to(v, rt, 60)
    council60 = [c for c in rt.contexts if c.round == 60 and c.kind == "propose"]
    assert council60 and council60[0].values_table and council60[0].referendum_round == 66
    assert "- referendum: put one question to the village at its referendum in round 66" in prompting.user_prompt(council60[0])
    assert v.world.referendum["stage"] == "set" and v.world.referendum["round"] == 66
    run_to(v, rt, 66)
    assert v.world.referendum["stage"] == "awaiting_council"
    assert v.cfg.economy.spoilage == 0.10
    run_to(v, rt, 70)
    assert v.cfg.economy.spoilage == pytest.approx(0.05) and v.world.overrides == {"economy.spoilage": 0.05}
    assert v.base_cfg.economy.spoilage == 0.10 and v.config_version == 1
    system = prompting.system_prompt(v.cfg, v.channel_order)
    assert "Stored energy loses 5% at the end of every round." in system


def test_a_village_majority_is_needed():
    rt = Village(names={"a01": "Hollow"}, name_votes={f"a{n:02d}": "Hollow" for n in range(1, 11)},
                 yes=["a01", "a02", "a03", "a04", "a05"], propose=propose_v3)  # 5 of 10 is not a majority
    v = v10()
    run_to(v, rt, 70)
    assert v.world.overrides == {} and v.world.referendum is None
    assert any("not a majority" in n for n in [e["value"] for e in events(v) if e["type"] == "world_append"])


def test_values_are_bounded_and_listed_by_arm():
    assert ref.parse_value("V3", 0.5, "control")[0] is None  # above 30%
    assert ref.parse_value("V3", 5, "control")[0] == pytest.approx(0.05)  # 5 means 5%
    assert ref.parse_value("V9", 10, "control")[0] is None  # a child's cost is Arm B's
    assert "V13" in ref.values_for("control") and "V13" not in ref.values_for("tontine")
    assert {"V9", "V10", "V11", "V12"} <= set(ref.values_for("tontine"))


def test_a_referendum_proposal_outside_the_window_is_refused():
    rt = Village(propose=lambda c: {"kind": "referendum", "rule": "V3", "text": "", "value": 0.05})
    v = v10()
    run_to(v, rt, 20)
    assert v.world.referendum is None
    assert any("No referendum is due" in n for e in events(v) if e["type"] == "append" for n in [e["value"]])


def test_a_changed_value_reaches_the_prompt_and_the_tap(tmp_path):
    everyone = [f"a{n:02d}" for n in range(1, 11)]
    cfg = config("control", 4, rounds=100, stop_after=72, economy={**NO_ACCIDENTS, "start_energy": 300},
                 commons=REF, tontine={"cull_mode": "scarcity"})
    rt = Village(names={"a01": "Hollow"}, name_votes={i: "Hollow" for i in everyone}, yes=everyone, propose=propose_v3)
    d = tmp_path / "ref"
    RunOrchestrator(cfg, d, clock=FixedClock(), runtime=rt).run()
    assert (d / "system_prompt-r070.txt").exists()
    assert "loses 5% at the end" in (d / "system_prompt-r070.txt").read_text(encoding="utf-8")
    ev = read_events(d / "events.jsonl")
    assert any(e["type"] == "system_prompt_changed" for e in ev)
    final = json.loads((d / "final_state.json").read_text(encoding="utf-8"))
    assert final["overrides"] == {"economy.spoilage": 0.05} and final["village_name"] == "Hollow"
    assert rebuild(ev, "control").to_dict() == final


# --------------------------------------------------------------------------- education (Arm B)

def child(v, parents, name, born):
    a = Agent(id=v.world.next_agent_id(), born_round=born, health=60.0, name=name, parents=tuple(parents))
    v.ledger.add_agent(a, "test")
    return a.id


def set_s3(v, value):
    v.ledger.set_world("rules", [dict(r, value=value) if r["id"] == "S3" else r for r in v.world.rules], reason="test")


def test_the_pool_pays_for_young_children_and_education_lowers_accident_risk():
    v = village("tontine", tontine={"education": True, "cull_mode": "scarcity"})
    assert any(r["id"] == "S3" for r in v.world.rules)
    assert not any(r["id"] == "S3" for r in village("control", commons={"enabled": True}).world.rules)
    kid = child(v, ["a01", "a03"], "Wren", born=1)
    old = child(v, ["a01", "a03"], "Moss", born=-40)  # past its first three terms
    set_s3(v, 4.0)
    v.ledger.set_world("pool", 100.0, reason="test")
    RoundRunner(v, Village()).run(1)
    assert v.world.agents[kid].education == pytest.approx(4.0)
    assert v.world.agents[old].education == 0 and v.world.agents["a02"].education == 0
    e = v.cfg.economy
    assert economy.accident_chance(10, e, education=40) < economy.accident_chance(10, e)


def test_a_short_pool_is_split_equally():
    v = village("tontine", tontine={"education": True, "cull_mode": "scarcity", "pool_spoilage": 0.0})
    kids = [child(v, ["a01", "a03"], n, born=1) for n in ("Wren", "Lark")]
    set_s3(v, 10.0)
    v.ledger.set_world("pool", 6.0, reason="test")
    RoundRunner(v, Village()).run(1)
    assert [v.world.agents[k].education for k in kids] == pytest.approx([3.0, 3.0])


def test_the_prompts_describe_education_and_referendums():
    v = v10("tontine", education=True)
    system = prompting.system_prompt(v.cfg, v.channel_order)
    assert "- The rule book's setting S3 is the energy the pool spends on each child's education" in system
    assert "- Every 33 rounds the village holds a referendum, in which every villager votes." in system
    assert "- referendum: only in referendum rounds" in system
    c = village("control")
    plain = prompting.system_prompt(c.cfg, c.channel_order)
    assert "referendum" not in plain and "education" not in plain


def test_the_run10_config():
    doc = load_with_base(ROOT / "configs" / "run10-world.yaml")
    b = YamlConfig().run_config(doc, "tontine", 701, "t")
    assert b.prompt.version == "v10" and b.commons.plan_check == "direction" and b.commons.referendum_every == 33
    assert b.tontine.education and doc["seeds"] == [701, 702, 703] and doc["arms"] == ["control", "tontine"]


def test_referendums_every_30_rounds_fall_at_30_60_and_90():
    """Run 11: the name at round 30 (voted at 31, ratified at 40); later questions set by the councils
    at 50 and 80, voted in the referendum round and ratified by that round's council."""
    everyone = [f"a{n:02d}" for n in range(1, 11)]
    rt = Village(names={"a01": "Hollow"}, name_votes={i: "Hollow" for i in everyone}, yes=everyone, propose=propose_v3)
    v = village("control", rounds=100, economy={**NO_ACCIDENTS, "start_energy": 300},
                commons={"enabled": True, "referendum_every": 30}, tontine={"cull_mode": "scarcity"})
    run_to(v, rt, 30)
    assert v.world.referendum["stage"] == "names_proposed"
    run_to(v, rt, 40)
    assert v.world.village_name == "Hollow"
    run_to(v, rt, 50)
    assert v.world.referendum["stage"] == "set" and v.world.referendum["round"] == 60
    run_to(v, rt, 60)  # voted in round 60, ratified by round 60's council
    assert v.world.overrides == {"economy.spoilage": 0.05} and v.world.referendum is None
    council50 = next(c for c in rt.contexts if c.round == 50 and c.kind == "propose")
    assert council50.referendum_round == 60
    run_to(v, rt, 80)
    assert v.world.referendum["round"] == 90
