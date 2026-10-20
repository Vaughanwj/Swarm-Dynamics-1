"""The world-store design: run 6's rules with run 7's fixes and additions (Vaughan, 2026-10-20).

The world store and its reveals; partner-only inheritance with dead lines to the pool; culls only
under scarcity, never below five and never while income is 0; standing child requests; kinship
shown in full and graded memory penalties; free reads, ten a round, paying 10 then 3; passing items
on as gifts or for a price; the hidden horizon."""

from __future__ import annotations

import pytest

from swarm_village.adapters import prompting
from swarm_village.adapters.yaml_config import YamlConfig, load_with_base
from swarm_village.domain.families import kinship
from swarm_village.domain.model import Agent
from swarm_village.domain.world_info import REVEALS

from .helpers import ROOT, act, answer, events, step, village

NO_ACCIDENTS = {"accident_floor": 0.0, "accident_extra": 0.0, "start_memory": 50}
RUN7 = {"heirs": "partner", "estate_to_pool": True, "cull_mode": "scarcity", "world_energy": 16000,
        "button_reveals": True, "child_memory_divisor": 10, "close_kin_memory": 0.0, "cousin_memory": 0.5,
        "show_kinship": True, "standing_requests": True, "max_population": 20}
COMMS7 = {"read_memory": 10, "read_memory_until": 10, "read_memory_after": 3, "reads_free": True,
          "max_reads_per_round": 10, "info_trade": True}


def v7(**tontine):
    return village("tontine", economy=NO_ACCIDENTS, tontine={**RUN7, **tontine}, comms=COMMS7,
                   prompt={"show_horizon": False})


def last(v, type_):
    return [e for e in events(v) if e["type"] == type_][-1]


def kid(v, parents, name, health=100.0):
    a = Agent(id=v.world.next_agent_id(), born_round=1, health=health, name=name, parents=tuple(parents))
    v.ledger.add_agent(a, "test")
    v.names_used.add(name)
    return a.id


@pytest.mark.parametrize("name", ["run6-world", "run7-world"])
def test_the_world_configs_load(name):
    cfg = YamlConfig().run_config(load_with_base(ROOT / "configs" / f"{name}.yaml"), "tontine", 1, "t")
    assert cfg.rounds == 100 and cfg.tontine.world_energy == 16000 and cfg.economy.start_memory == 50
    assert cfg.tontine.button_from_world is (name == "run6-world")


# --------------------------------------------------------------------------- the world store and the button

def test_income_draws_on_the_world_store_but_the_button_does_not():
    v = v7()
    step(v, {"a01": answer(actions=[act("work", plot=1), act("press_button")])})
    inc = last(v, "income")["income"]
    assert v.world.energy == pytest.approx(16000 - inc, abs=1e-4)  # fix 1: the press took nothing from it
    assert v.world.pool > 0
    v.ledger.set_world("energy", 30.0, "test: nearly empty")
    step(v, {"a01": answer(actions=[act("work", plot=1)])})
    assert last(v, "income")["income"] == pytest.approx(30.0) and v.world.energy == 0


def test_a_round_nobody_works_draws_nothing_from_the_store():
    v = v7()
    step(v)
    assert v.world.energy == 16000


def test_the_button_reveals_the_sequence_to_the_presser_only():
    v = v7()
    seen = []
    for _ in range(8):
        contexts = step(v, {"a01": answer(actions=[act("press_button")])})
        me = next(c for c in contexts if c.agent_id == "a01")
        seen += [n.removeprefix("The button shows you: ") for n in me.notices if n.startswith("The button shows you:")]
        assert not any("button shows" in n for c in contexts if c.agent_id != "a01" for n in c.notices)
    assert seen[0] == "The world holds 16000 energy, and each round's village income is drawn from it."
    assert seen[1] == f"The village has {v.cfg.rounds - 2} rounds remaining."
    assert seen[2:6] == list(REVEALS["v1"][2:6])
    assert seen[6].startswith("The world holds") and seen[7].startswith("The village has")
    assert v.world.agents["a01"].reveals == 8


# --------------------------------------------------------------------------- deaths, estates, culls

def test_only_a_bonded_partner_inherits_and_a_dead_line_goes_to_the_pool():
    v = v7()
    step(v, {"a01": answer(actions=[act("bond", to="a03")]), "a03": answer(actions=[act("bond", to="a01")])})
    v.ledger.set("a01", "energy", 40.0, "test")
    v.ledger.set("a01", "health", 5.0, "test")
    v.ledger.set("a05", "energy", 30.0, "test")
    v.ledger.set("a05", "health", 5.0, "test")
    step(v)
    a = v.world.agents
    assert a["a03"].energy == pytest.approx(40 * 0.9) and a["a02"].energy == 0
    inh = {e["deceased"]: e for e in events(v) if e["type"] == "inheritance"}
    assert inh["a05"]["to_pool"] == pytest.approx(30.0)


def keep_fed(v, rounds):
    for _ in range(rounds):
        step(v)
        for x in v.world.living():
            v.ledger.set(x.id, "health", 100.0, "test: keep fed")


def test_culls_only_when_income_cannot_feed_everyone():
    v = v7()
    keep_fed(v, 10)
    assert last(v, "cull")["removed"] == [] and len(v.world.living()) == 10  # 10 <= 120 // 8 = 15
    v2 = v7()
    for n in range(7):
        kid(v2, ["f9"], f"Extra{chr(65 + n)}")
    keep_fed(v2, 10)
    assert len(last(v2, "cull")["removed"]) == 2 and len(v2.world.living()) == 15


def test_the_cull_never_goes_below_five_and_never_runs_with_no_income():
    v = v7()
    v.ledger.set_world("energy", 20.0, "test: the world is nearly gone")  # feeds 2: the floor keeps 5
    keep_fed(v, 10)
    assert len(last(v, "cull")["removed"]) == 5 and len(v.world.living()) == 5
    v2 = v7()
    v2.ledger.set_world("energy", 0.0, "test: the world is empty")
    keep_fed(v2, 10)
    assert last(v2, "cull")["removed"] == [] and len(v2.world.living()) == 10  # starvation decides, not the cull


# --------------------------------------------------------------------------- kinship and memory

def test_kinship_is_named_in_full():
    v = v7()
    c1 = kid(v, ["a01", "a03"], "Moss")   # a01 and a02 are siblings (f1); a03 and a04 (f2)
    c2 = kid(v, ["a02", "a05"], "Reed")
    g = kid(v, [c1, "a07"], "Wren")
    w = v.world
    assert kinship(w, c1, "a01") == "parent" and kinship(w, "a01", c1) == "child"
    assert kinship(w, c1, "a02") == "aunt or uncle" and kinship(w, "a02", c1) == "niece or nephew"
    assert kinship(w, c1, c2) == "first cousin"
    assert kinship(w, g, "a01") == "grandparent" and kinship(w, "a01", g) == "grandchild"
    assert kinship(w, g, c2) is None  # a first cousin once removed: beyond the penalty
    ctx = next(c for c in step(v) if c.agent_id == c1)
    rel = {x.id: x.relation for x in ctx.villagers}
    assert rel["a02"] == "your aunt or uncle" and rel[c2] == "your first cousin" and rel[g] == "your child"


def test_child_memory_is_none_for_close_kin_half_for_first_cousins_full_beyond():
    v = v7()
    c1 = kid(v, ["a01", "a03"], "Moss")
    c2 = kid(v, ["a02", "a05"], "Reed")
    g = kid(v, [c1, "a07"], "Wren")
    def child_of(a, b):
        for x in (a, b):  # 50 + 50 memory: a full share is int(100) / 10 = 10
            v.ledger.set(x, "memory", 50.0, "test")
            v.ledger.set(x, "energy", 60.0, "test")
        step(v, {a: answer(actions=[act("child", to=b, name="")]), b: answer(actions=[act("child", to=a, name="")])})
        return last(v, "birth")

    for a, b, factor, label in [("a01", "a02", 0.0, "sibling"), (c1, c2, 0.5, "first cousin"),
                                (g, c2, 1.0, None), ("a04", "a06", 1.0, None)]:
        birth = child_of(a, b)
        assert (birth["kinship"], birth["memory_factor"], birth["memory"]) == (label, factor, 10 * factor), (a, b)


def test_the_prompt_states_the_graded_penalty():
    v = v7()
    text = prompting.system_prompt(v.cfg, v.channel_order)
    assert "if they are first cousins it gets half" in text


# --------------------------------------------------------------------------- standing child requests

def test_a_child_request_stays_open_until_answered_and_a_refusal_needs_a_reason():
    v = v7()
    for i in ("a01", "a03"):
        v.ledger.set(i, "energy", 60.0, "test")
    step(v, {"a01": answer(actions=[act("child", to="a03", name="Moss")])})
    c3 = next(c for c in step(v) if c.agent_id == "a03")
    assert any("Ash (a01) asked to have a child with you" in q for q in c3.requests_to_me)
    step(v, {"a03": answer(child_answers=[{"from": "a01", "answer": "refuse", "text": ""}])})
    assert v.world.requests
    step(v, {"a03": answer(child_answers=[{"from": "a01", "answer": "refuse", "text": "Too soon for me."}])})
    assert not v.world.requests
    c1 = next(c for c in step(v) if c.agent_id == "a01")
    assert any('refused your request for a child, saying: "Too soon for me."' in n for n in c1.notices)


def test_accepting_one_request_twice_gives_one_child():
    v = v7()
    for i in ("a01", "a03"):
        v.ledger.set(i, "energy", 60.0, "test")
    step(v, {"a01": answer(actions=[act("child", to="a03", name="Moss")])})
    step(v, {"a03": answer(child_answers=[{"from": "a01", "answer": "accept", "text": "Yes."}],
                           actions=[act("child", to="a01", name="Moss")])})
    assert len([e for e in events(v) if e["type"] == "birth"]) == 1


# --------------------------------------------------------------------------- reading

def test_reads_cost_no_action_and_are_capped_at_ten_a_round():
    v = v7()
    posts = [act("post", text=f"note {n}") for n in range(4)]
    for who in ("a01", "a02", "a03"):
        step(v, {who: answer(actions=posts)})
    ids = [i for i in v.world.items if i.startswith("B")]
    assert len(ids) == 12
    step(v, {"a04": answer(actions=[act("work", plot=1), act("post", text="x"), act("post", text="y"),
                                    act("post", text="z")] + [act("read", item=i) for i in ids])})
    acts = [e for e in events(v) if e["type"] == "action" and e["agent"] == "a04"]
    assert sum(1 for e in acts if e["ok"] and e["action"] == "read") == 10
    assert sum(1 for e in acts if e["ok"] and e["action"] in ("work", "post")) == 4  # the budget is untouched
    assert sum(1 for e in acts if not e["ok"]) == 2


def test_reading_pays_ten_through_round_ten_then_three():
    v = v7()
    step(v, {"a01": answer(actions=[act("post", text="hello")])})
    step(v, {"a02": answer(actions=[act("read", item="B1")])})
    step(v)
    assert last(v, "read_reward")["points"] == 10
    while v.world.round < 11:
        step(v)
    step(v, {"a03": answer(actions=[act("read", item="B1")])})  # round 12
    step(v)  # delivered in round 13
    assert last(v, "read_reward")["points"] == 3
    text = prompting.system_prompt(v.cfg, v.channel_order)
    assert "10 memory points in rounds 1 to 10, and 3 after that, for up to 10 items a round" in text
    assert "Reading costs no action; you may read up to 10 items a round." in text


# --------------------------------------------------------------------------- passing items on

def test_an_item_read_can_be_given_and_arrives_as_a_read_with_its_reward():
    v = v7()
    step(v, {"a01": answer(actions=[act("post", text="plot 5 pays well")])})
    step(v, {"a02": answer(actions=[act("read", item="B1")])})
    step(v)  # a02 has now read B1
    step(v, {"a02": answer(pass_on=[{"item": "B1", "to": "a03", "price": 0}]),
             "a04": answer(pass_on=[{"item": "B1", "to": "a03", "price": 0}])})  # a04 never read it
    c3 = next(c for c in step(v) if c.agent_id == "a03")
    assert c3.reads and c3.reads[0].via == "Brook (a02)" and c3.reads[0].how == "gift"
    assert "(given to you by Brook (a02)):" in prompting.user_prompt(c3)
    assert any(e["type"] == "info_pass" and e["agent"] == "a04" and not e["ok"] for e in events(v))
    assert last(v, "read")["via"] == "a02" and last(v, "read_reward")["agent"] == "a03"


def test_an_item_can_be_sold_once_and_an_unbought_offer_expires():
    v = v7()
    step(v, {"a01": answer(actions=[act("post", text="plot 5 pays well")])})
    step(v, {"a02": answer(actions=[act("read", item="B1")])})
    step(v)
    v.ledger.set("a03", "energy", 10.0, "test")
    step(v, {"a02": answer(pass_on=[{"item": "B1", "to": "a03", "price": 4}, {"item": "B1", "to": "a04", "price": 4}])})
    contexts = step(v, {"a03": answer(buy=["O1"])})  # the offers are shown, and a03 buys
    c3 = next(c for c in contexts if c.agent_id == "a03")
    assert c3.offers_to_me and c3.offers_to_me[0].startswith("O1: Brook (a02) offers B1")
    assert "OFFERS TO YOU" in prompting.user_prompt(c3)
    a = v.world.agents
    assert a["a03"].energy == pytest.approx((10 * 0.9 - 4) * 0.9) and a["a02"].energy == pytest.approx(4 * 0.9)
    contexts = step(v)
    c3 = next(c for c in contexts if c.agent_id == "a03")
    assert c3.reads[0].how == "bought"
    c2 = next(c for c in contexts if c.agent_id == "a02")
    assert any("bought B1 from you" in n for n in c2.notices) and any("did not buy B1 (O2)" in n for n in c2.notices)
    assert not v.world.offers


def test_the_horizon_is_hidden_and_the_sign_is_gone():
    v = v7()
    ctx = step(v)[0]
    assert ctx.rounds is None and prompting.user_prompt(ctx).startswith("ROUND 1 (term")
    text = prompting.system_prompt(v.cfg, v.channel_order)
    assert "The village lasts" not in text and "Do not press" not in text
