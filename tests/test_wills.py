"""Run 11 (Vaughan, 2026-10-20): wills, separate from bonding. A villager may name up to three
others to share its stored energy when it dies; without a will, or if none of them is alive, its
energy goes as it would anyway (to its bonded partner, else the pool). Wills are private until death."""

from __future__ import annotations

import pytest

from swarm_village.adapters import prompting
from swarm_village.adapters.yaml_config import YamlConfig, load_with_base

from .helpers import ROOT, act, answer, events, step, village

NO_ACCIDENTS = {"accident_floor": 0.0, "accident_extra": 0.0, "start_memory": 50}
TONTINE = {"wills": True, "heirs": "partner", "estate_to_pool": True, "cull_mode": "scarcity"}


def v11(**tontine):
    return village("tontine", economy=NO_ACCIDENTS, tontine={**TONTINE, **tontine})


def ctx(contexts, agent):
    return next(c for c in contexts if c.agent_id == agent and c.kind == "round")


def test_a_will_is_written_and_shown_only_to_its_writer():
    v = v11()
    step(v, {"a01": answer(actions=[act("will", text="a03 and a05")])})
    assert v.world.agents["a01"].will == ["a03", "a05"]
    contexts = step(v)
    me, other = ctx(contexts, "a01"), ctx(contexts, "a03")
    assert me.my_will == [v.world.agents["a03"].label(), v.world.agents["a05"].label()]
    assert "Your will names" in prompting.user_prompt(me)
    assert other.my_will is None and "will" not in " ".join(other.notices + other.public_notices).lower()


def test_the_will_decides_the_estate_over_a_bonded_partner():
    v = v11()
    v.ledger.set("a01", "bond", "a07", "test")
    v.ledger.set("a07", "bond", "a01", "test")
    step(v, {"a01": answer(actions=[act("will", text="a03, a05")])})
    v.ledger.set("a01", "energy", 30.0, "test")
    v._kill(["a01"], "test")
    inh = [e for e in events(v) if e["type"] == "inheritance"][-1]
    assert inh["by_will"] and sorted(inh["heirs"]) == ["a03", "a05"]
    assert {k: v for k, v in inh["shares"].items() if v} == {"a03": pytest.approx(15.0), "a05": pytest.approx(15.0)}
    assert any("left a will" in n for n in v.world.public_notices)


def test_without_living_heirs_the_estate_goes_as_it_would_without_a_will():
    v = v11()
    v.ledger.set("a01", "bond", "a07", "test")
    v.ledger.set("a07", "bond", "a01", "test")
    step(v, {"a01": answer(actions=[act("will", text="a03")])})
    v._kill(["a03"], "test")
    v.ledger.set("a01", "energy", 20.0, "test")
    v._kill(["a01"], "test")
    inh = [e for e in events(v) if e["type"] == "inheritance"][-1]
    assert not inh["by_will"] and inh["heirs"] == ["a07"]  # the bonded partner, as before wills


def test_bad_wills_are_refused_and_an_empty_text_cancels():
    v = v11()
    step(v, {"a01": answer(actions=[act("will", text="a01")])})  # not oneself
    step(v, {"a01": answer(actions=[act("will", text="a02 a03 a04 a05")])})  # too many
    step(v, {"a01": answer(actions=[act("will", text="my sibling")])})  # no ids
    errors = [e["error"] for e in events(v) if e["type"] == "action" and not e["ok"]]
    assert "not another living villager" in errors[0] and "at most 3" in errors[1] and "name the ids" in errors[2]
    assert v.world.agents["a01"].will == []
    step(v, {"a01": answer(actions=[act("will", text="a02"), act("will", text="a03")])})
    assert v.world.agents["a01"].will == ["a02"]  # once a round
    step(v, {"a01": answer(actions=[act("will", text="")])})
    assert v.world.agents["a01"].will == []


def test_wills_are_arm_b_only_and_stated_in_its_rules():
    v = v11()
    system = prompting.system_prompt(v.cfg, v.channel_order)
    assert "A villager may instead write a will naming up to 3 other villagers" in system
    assert "- will: write or change your will" in system
    assert "will" in v.types and "will" not in village("control", tontine={"wills": True}).types
    plain = village("tontine")
    assert "will" not in plain.types and "write a will" not in prompting.system_prompt(plain.cfg, plain.channel_order)


def test_the_run11_config():
    doc = load_with_base(ROOT / "configs" / "run11-world.yaml")
    cfg = YamlConfig().run_config(doc, "tontine", 701, "t")
    base = YamlConfig().run_config(load_with_base(ROOT / "configs" / "run10-world.yaml"), "tontine", 701, "t")
    from dataclasses import replace
    assert cfg.tontine.wills and cfg.tontine.will_max_heirs == 3 and cfg.prompt.version == "v11"
    assert replace(cfg.tontine, wills=False) == base.tontine and cfg.commons == base.commons
