"""Run 6 (Vaughan, 2026-10-20): the world store, the revealing button, partner-only inheritance with
estates of dead lines to the pool, culls only under scarcity, standing child requests, inherited memory,
kin, the read reward schedule, genders, and the hidden horizon."""

from __future__ import annotations

import pytest

from swarm_village.adapters import prompting
from swarm_village.adapters.yaml_config import YamlConfig, load_with_base
from swarm_village.domain.world_info import REVEALS

from .helpers import ROOT, act, answer, events, step, village

NO_ACCIDENTS = {"accident_floor": 0.0, "accident_extra": 0.0, "start_memory": 50}
RUN6 = {"heirs": "partner", "estate_to_pool": True, "cull_mode": "scarcity", "world_energy": 16000,
        "button_reveals": True, "child_memory_divisor": 10, "kin_child_memory": False, "standing_requests": True,
        "max_population": 20}


def v6(**tontine):
    return village("tontine", economy=NO_ACCIDENTS, genders=True, tontine={**RUN6, **tontine},
                   comms={"read_memory": 10, "read_memory_until": 10, "read_memory_after_max": 5},
                   prompt={"show_horizon": False})


def last(v, type_):
    return [e for e in events(v) if e["type"] == type_][-1]


def test_the_run6_config_loads():
    doc = load_with_base(ROOT / "configs" / "run6-world.yaml")
    cfg = YamlConfig().run_config(doc, "tontine", 601, "t")
    assert cfg.rounds == 100 and cfg.tontine.world_energy == 16000 and cfg.economy.start_memory == 50


def test_income_and_the_button_draw_from_the_world_store():
    v = v6()
    assert v.world.energy == 16000 and all(a.memory == 50 for a in v.world.agents.values())
    step(v, {"a01": answer(actions=[act("work", plot=1), act("press_button")])})
    inc = last(v, "income")["income"]
    added = v.rng.uniform("button", 1, "a01") * 20
    assert v.world.energy == pytest.approx(16000 - inc - added, abs=1e-4)
    v.ledger.set_world("energy", 30.0, "test: nearly empty")
    step(v, {"a01": answer(actions=[act("work", plot=1)])})
    assert last(v, "income")["income"] == pytest.approx(30.0) and v.world.energy == 0


def test_the_button_reveals_the_sequence_to_the_presser_only():
    v = v6()
    seen = []
    for r in range(8):
        contexts = step(v, {"a01": answer(actions=[act("press_button")])})
        me = next(c for c in contexts if c.agent_id == "a01")
        seen += [n for n in me.notices if n.startswith("The button shows you:")]
        assert not any("button shows" in n for c in contexts if c.agent_id != "a01" for n in c.notices)
    texts = [s.removeprefix("The button shows you: ") for s in seen]
    assert texts[0].startswith("The world holds") and texts[1] == f"The village has {v.cfg.rounds - 2} rounds remaining."
    assert texts[2:6] == list(REVEALS["v1"][2:6])
    assert texts[6].startswith("The world holds") and texts[7].startswith("The village has")  # then repeats 1 and 2
    assert v.world.agents["a01"].reveals == 8


def test_only_a_bonded_partner_inherits_and_a_dead_line_goes_to_the_pool():
    v = v6()
    step(v, {"a01": answer(actions=[act("bond", to="a03")]), "a03": answer(actions=[act("bond", to="a01")])})
    v.ledger.set("a01", "energy", 40.0, "test")
    v.ledger.set("a01", "health", 5.0, "test")  # starves this round
    v.ledger.set("a05", "energy", 30.0, "test")
    v.ledger.set("a05", "health", 5.0, "test")  # no partner: its line is gone
    pool_before = v.world.pool
    step(v)
    a = v.world.agents
    assert a["a03"].energy == pytest.approx(40 * 0.9) and a["a02"].energy == 0  # the sibling gets nothing
    inh = {e["deceased"]: e for e in events(v) if e["type"] == "inheritance"}
    assert inh["a05"]["to_pool"] == pytest.approx(30.0) and inh["a05"]["lost"] == 0
    assert v.world.pool == pytest.approx((pool_before + 30.0) * 0.9)


def test_culls_happen_only_when_income_cannot_feed_everyone():
    v = v6(cull_count=5)
    for _ in range(10):
        step(v)
        for x in v.world.living():
            v.ledger.set(x.id, "health", 100.0, "test: keep fed")
    assert last(v, "cull")["removed"] == [] and len(v.world.living()) == 10  # 10 <= 120 // 8 = 15
    v2 = v6()
    for i in range(7):  # 17 villagers: two more than income feeds
        v2.ledger.add_agent(type(v2.world.agents["a01"])(id=v2.world.next_agent_id(), born_round=1, health=100.0), "test")
    for _ in range(10):
        step(v2)
        for x in v2.world.living():
            v2.ledger.set(x.id, "health", 100.0, "test: keep fed")
    assert len(last(v2, "cull")["removed"]) == 2 and len(v2.world.living()) == 15


def test_a_child_request_stays_open_until_answered_and_a_refusal_needs_a_reason():
    v = v6()
    for i in ("a01", "a03"):
        v.ledger.set(i, "energy", 60.0, "test")
    step(v, {"a01": answer(actions=[act("child", to="a03", name="Moss")])})
    contexts = step(v)  # a03 ignores it
    c3 = next(c for c in contexts if c.agent_id == "a03")
    assert any("Ash (a01) asked to have a child with you" in q for q in c3.requests_to_me)
    assert "CHILD REQUESTS TO YOU" in prompting.user_prompt(c3)
    step(v, {"a03": answer(child_answers=[{"from": "a01", "answer": "refuse", "text": ""}])})
    assert v.world.requests  # no reason given: still open
    contexts = step(v, {"a03": answer(child_answers=[{"from": "a01", "answer": "refuse", "text": "Too soon for me."}])})
    assert not v.world.requests
    c1 = next(c for c in step(v) if c.agent_id == "a01")
    assert any('refused your request for a child, saying: "Too soon for me."' in n for n in c1.notices)
    step(v, {"a01": answer(actions=[act("child", to="a03", name="Moss")])})
    step(v, {"a03": answer(child_answers=[{"from": "a01", "answer": "accept", "text": "Yes."}])})
    birth = last(v, "birth")
    assert birth["parents"] == ["a01", "a03"] and birth["name"] == "Moss"


def test_inherited_memory_and_kin_children_start_with_none():
    v = v6()
    for i in ("a01", "a02", "a03"):
        v.ledger.set(i, "energy", 60.0, "test")
    v.ledger.set("a01", "memory", 80.0, "test")
    v.ledger.set("a03", "memory", 45.5, "test")
    step(v, {"a01": answer(actions=[act("child", to="a03", name="Moss")]),
             "a03": answer(actions=[act("child", to="a01", name="Moss")])})  # same round: agreed at once
    moss = last(v, "birth")
    assert not moss["kin"] and moss["memory"] == pytest.approx(int(80 + 45.5) / 10)
    v.ledger.set("a02", "energy", 60.0, "test")
    v.ledger.set("a01", "energy", 60.0, "test")
    step(v, {"a01": answer(actions=[act("child", to="a02", name="Reed")]),
             "a02": answer(actions=[act("child", to="a01", name="Reed")])})  # siblings
    reed = last(v, "birth")
    assert reed["kin"] and reed["memory"] == 0


def test_reading_pays_ten_early_then_zero_to_five():
    v = v6()
    step(v, {"a01": answer(actions=[act("post", text="hello")])})
    step(v, {"a02": answer(actions=[act("read", item="B1")])})
    step(v)
    assert last(v, "read_reward")["points"] == 10
    text = prompting.system_prompt(v.cfg, v.channel_order)
    assert "10 memory points in rounds 1 to 10, and between 0 and 5 after that" in text


def test_late_reads_draw_between_zero_and_five():
    v = v6()
    for _ in range(10):
        step(v)
    step(v, {"a01": answer(actions=[act("post", text="hello")])})  # round 11
    step(v, {"a02": answer(actions=[act("read", item="B1")]), "a03": answer(actions=[act("read", item="B1")])})
    step(v)  # round 13: delivered
    rewards = [e["points"] for e in events(v) if e["type"] == "read_reward"]
    assert rewards and all(0 <= p <= 5 and p == int(p) for p in rewards)


def test_genders_are_chosen_freely_and_shown():
    v = v6()
    step(v, {"a01": answer(actions=[act("gender", name="woman")]), "a02": answer(actions=[act("gender", name="9x")])})
    contexts = step(v)
    c3 = next(c for c in contexts if c.agent_id == "a03")
    assert "Ash (a01), gender: woman" in prompting.user_prompt(c3)
    assert v.world.agents["a02"].gender is None
    assert "Ash (a01) has chosen a gender: woman." in c3.public_notices


def test_the_horizon_is_hidden():
    v = v6()
    ctx = step(v)[0]
    assert ctx.rounds is None and prompting.user_prompt(ctx).startswith("ROUND 1 (term")
    assert "The village lasts" not in prompting.system_prompt(v.cfg, v.channel_order)
    assert "Do not press" not in prompting.system_prompt(v.cfg, v.channel_order)


def test_accepting_one_request_twice_gives_one_child():
    v = v6()
    for i in ("a01", "a03"):
        v.ledger.set(i, "energy", 60.0, "test")
    step(v, {"a01": answer(actions=[act("child", to="a03", name="Moss")])})
    step(v, {"a03": answer(child_answers=[{"from": "a01", "answer": "accept", "text": "Yes."}],
                           actions=[act("child", to="a01", name="Moss")])})
    assert len([e for e in events(v) if e["type"] == "birth"]) == 1
