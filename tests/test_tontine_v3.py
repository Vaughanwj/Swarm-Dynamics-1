"""Arm B as redesigned for Milestone 5: bonds, the shared pool, the button that feeds it, the cull of
the lowest five, and the council that changes the rule book."""

from __future__ import annotations

import pytest

from swarm_village.adapters import prompting
from swarm_village.app.round_runner import RoundRunner
from swarm_village.domain import governance as G
from swarm_village.ports import Reply

from .helpers import Scripted, act, answer, events, step, village

NO_ACCIDENTS = {"accident_floor": 0.0, "accident_extra": 0.0}


def tontine(**kw):
    return village("tontine", economy=NO_ACCIDENTS, **kw)


def last(v, type_):
    return [e for e in events(v) if e["type"] == type_][-1]


# --------------------------------------------------------------------------- bonds

def test_bonds_need_both_to_ask_and_last_until_a_death():
    v = tontine()
    contexts = step(v, {"a01": answer(actions=[act("bond", to="a03")]), "a03": answer(actions=[act("bond", to="a01")]),
                        "a05": answer(actions=[act("bond", to="a07")])})
    a = v.world.agents
    assert (a["a01"].bond, a["a03"].bond, a["a05"].bond, a["a07"].bond) == ("a03", "a01", None, None)
    contexts = step(v, {"a01": answer(actions=[act("bond", to="a05")])})
    assert "Ash (a01) and Cedar (a03) have bonded." in contexts[0].public_notices
    assert any("already bonded" in e.get("error", "") for e in events(v) if e["type"] == "action")
    villagers = {x.id: x for x in next(c for c in contexts if c.agent_id == "a02").villagers}
    assert villagers["a01"].bond == "Cedar (a03)"
    v.ledger.set("a03", "health", 5.0, "test")
    step(v)
    assert not a["a03"].alive and a["a01"].bond is None


def test_bonded_parents_pay_less_for_a_child():
    v = tontine()
    for i in ("a01", "a03", "a05", "a07"):
        v.ledger.set(i, "energy", 30.0, "test")
    step(v, {"a01": answer(actions=[act("bond", to="a03")]), "a03": answer(actions=[act("bond", to="a01")])})
    v.ledger.set("a01", "energy", 30.0, "test")
    v.ledger.set("a03", "energy", 30.0, "test")
    v.ledger.set("a05", "energy", 30.0, "test")
    v.ledger.set("a07", "energy", 30.0, "test")
    step(v, {"a01": answer(actions=[act("child", to="a03", name="Moss")]),
             "a03": answer(actions=[act("child", to="a01", name="Moss")]),
             "a05": answer(actions=[act("child", to="a07", name="Reed")]),
             "a07": answer(actions=[act("child", to="a05", name="Reed")])})
    births = {e["name"]: e for e in events(v) if e["type"] == "birth"}
    assert births["Moss"]["bonded"] and births["Moss"]["cost_each"] == 10
    assert not births["Reed"]["bonded"] and births["Reed"]["cost_each"] == 20
    a = v.world.agents
    assert a["a01"].energy == pytest.approx(18.0) and a["a05"].energy == pytest.approx(9.0)


# --------------------------------------------------------------------------- the pool

def test_draw_give_and_spoilage_and_the_pool_is_shown_to_all():
    v = tontine()
    v.ledger.set_world("pool", 50.0, "test")
    v.ledger.set("a02", "energy", 10.0, "test")
    step(v, {"a01": answer(draw=20, eat=20), "a02": answer(gifts=[{"to": "pool", "amount": 10}]),
             "a03": answer(draw=100)})
    a = v.world.agents
    assert a["a01"].health == 92 + 0 and a["a01"].energy == 0  # drew 20, ate 20 (capped at 100), then -8
    assert a["a02"].energy == 0
    assert a["a03"].energy == 0  # asked for 100: more than the pool held, so refused, like an overdrawn meal
    contexts = step(v)
    assert {round(c.pool, 6) for c in contexts} == {36.0}  # 50 - 20 + 10, then 10% spoilage
    assert [e["ok"] for e in events(v) if e["type"] == "pool_draw" and e["agent"] == "a03"] == [False]


def test_a_draw_bigger_than_the_pool_is_refused():
    v = tontine()
    v.ledger.set_world("pool", 5.0, "test")
    step(v, {"a01": answer(draw=6)})
    assert v.world.agents["a01"].energy == 0 and v.world.pool == pytest.approx(4.5)
    assert not last(v, "pool_draw")["ok"]


def test_settings_in_the_rule_book_are_enforced():
    v = tontine()
    book = G.initial_rules()
    book[0]["value"] = 10.0  # S1: draw limit
    book[1]["value"] = 0.25  # S2: income share
    v.ledger.set_world("rules", book, "test")
    v.ledger.set_world("pool", 50.0, "test")
    step(v, {"a01": answer(draw=8), "a02": answer(draw=12), "a03": answer(actions=[act("work", plot=1)])})
    a = v.world.agents
    assert a["a01"].energy > 0 and a["a02"].energy == 0  # 12 is over the limit of 10: refused
    inc = last(v, "income")
    assert inc["to_pool"] == pytest.approx(inc["income"] * 0.25)
    assert inc["distributed"] == pytest.approx(inc["income"] * 0.75)


# --------------------------------------------------------------------------- the council

def test_parse_proposals_and_votes():
    rules = G.initial_rules() + [{"id": "W1", "kind": "written", "text": "Share."}]
    p, e = G.parse_proposal({"proposal": {"kind": "add", "rule": "", "text": " Help  the weak. ", "value": 0}}, "a01", rules, 300)
    assert p.kind == "add" and p.text == "Help the weak." and e is None
    p, e = G.parse_proposal({"proposal": {"kind": "change", "rule": "S1", "text": "", "value": -1}}, "a01", rules, 300)
    assert p.value is None  # below 0: no limit
    assert G.parse_proposal({"proposal": {"kind": "change", "rule": "S2", "text": "", "value": 0.9}}, "a01", rules, 300)[0] is None
    assert G.parse_proposal({"proposal": {"kind": "delete", "rule": "W7", "text": "", "value": 0}}, "a01", rules, 300)[0] is None
    assert G.parse_proposal({"proposal": {"kind": "none", "rule": "", "text": "", "value": 0}}, "a01", rules, 300) == (None, None)
    assert G.parse_proposal("vote for me", "a01", rules, 300)[1]
    votes, errors = G.parse_votes({"votes": [{"proposal": 1, "vote": "yes"}, {"proposal": 9, "vote": "yes"}]}, 2)
    assert votes == {1: True} and errors


def test_enact_applies_in_order_and_voids_changes_to_deleted_rules():
    rules = G.initial_rules() + [{"id": "W1", "kind": "written", "text": "Share."}]
    passed = [G.Proposal("a01", "delete", rule="W1"), G.Proposal("a02", "change", rule="W1", text="Share more."),
              G.Proposal("a03", "add", text="Rest."), G.Proposal("a04", "change", rule="S1", value=5.0),
              G.Proposal("a05", "delete", rule="S1")]
    book, outcomes = G.enact(rules, passed)
    assert [o for _, o in outcomes] == ["deleted W1", "void: the rule was deleted earlier in this session", "added W2",
                                       "S1 changed", "S1 returned to its starting value"]
    assert G.setting(book, "pool_draw_limit") is None and [r["id"] for r in book] == ["S1", "S2", "W2"]


def council_round(v, proposals: dict[str, dict], votes: dict[str, dict]):
    """Run round 10 (a term's end) with idle round answers and scripted council answers."""
    class Runtime(Scripted):
        def decide_batch(self, contexts):
            out = []
            for c in contexts:
                self.contexts.append(c)
                if c.kind == "propose":
                    out.append(Reply(c.agent_id, raw=proposals.get(c.agent_id, {"proposal": {"kind": "none", "rule": "",
                                                                                          "text": "", "value": 0}})))
                elif c.kind == "vote":
                    out.append(Reply(c.agent_id, raw=votes.get(c.agent_id, {"votes": []})))
                else:
                    out.append(Reply(c.agent_id, raw=answer()))
            return out
    rt = Runtime()
    while v.world.round < 9:
        step(v)
        for x in v.world.living():
            v.ledger.set(x.id, "health", 100.0, "test: keep everyone alive")
    RoundRunner(v, rt).run(10)
    return rt.contexts


def test_the_council_is_the_healthiest_five_and_majority_carries():
    v = tontine(tontine={"cull_count": 0})
    order = ["a01", "a02", "a03", "a04", "a05"]

    def none():
        return {"proposal": {"kind": "none", "rule": "", "text": "", "value": 0}}

    proposals = {"a01": {"proposal": {"kind": "add", "rule": "", "text": "Feed the weakest first.", "value": 0}},
                 "a02": {"proposal": {"kind": "change", "rule": "S1", "text": "", "value": 15}},
                 "a03": none()}
    yes_yes = {"votes": [{"proposal": 1, "vote": "yes"}, {"proposal": 2, "vote": "yes"}]}
    yes_no = {"votes": [{"proposal": 1, "vote": "yes"}, {"proposal": 2, "vote": "no"}]}
    votes = {"a01": yes_yes, "a02": yes_no, "a03": yes_no, "a04": yes_no, "a05": {"votes": []}}

    # make a01..a05 the healthiest at the end of round 10
    real_resolve = v.resolve

    def resolve():
        real_resolve()
        for i, x in enumerate(sorted(v.world.living(), key=lambda a: a.id)):
            v.ledger.set(x.id, "health", 90.0 - i, "test: rank")
    v.resolve = resolve
    contexts = council_round(v, proposals, votes)
    members = last(v, "council")["members"]
    assert members == order
    assert [c.agent_id for c in contexts if c.kind == "propose"] == order
    session = last(v, "council_session")
    assert session["tallies"] == [4, 1] and session["needed"] == 3
    assert [r["id"] for r in v.world.rules] == ["S1", "S2", "W1"] and G.setting(v.world.rules, "pool_draw_limit") is None
    nxt = step(v)
    book = "\n".join(nxt[0].rules)
    assert "W1 (written): Feed the weakest first." in book
    notices = "\n".join(nxt[0].public_notices)
    assert "4 of 5 yes, passed, added W1" in notices and "1 of 5 yes, failed" in notices


def test_council_prompts_show_the_rule_book_and_proposals():
    v = tontine(tontine={"cull_count": 0})
    proposals = {"a01": {"proposal": {"kind": "change", "rule": "S2", "text": "", "value": 0.2}}}
    contexts = council_round(v, proposals, {})
    propose = next(c for c in contexts if c.kind == "propose")
    vote = next(c for c in contexts if c.kind == "vote")
    text_p, text_v = prompting.user_prompt(propose), prompting.user_prompt(vote)
    assert "THE COUNCIL: PROPOSALS" in text_p and "S1 (setting, enforced)" in text_p
    assert "1. by Ash (a01): change S2 to 20%" in text_v and "passes with 3 yes votes" in text_v
    assert prompting.schema(propose) == G.PROPOSE_SCHEMA and prompting.schema(vote) == G.VOTE_SCHEMA
    assert last(v, "council_session")["tallies"] == [0]  # nobody voted: abstentions count as no


def test_an_invalid_proposal_is_refused_and_the_member_told():
    v = tontine(tontine={"cull_count": 0})
    council_round(v, {"a01": {"proposal": {"kind": "delete", "rule": "W9", "text": "", "value": 0}}}, {})
    nxt = step(v)
    me = next(c for c in nxt if c.agent_id == "a01")
    assert any("There is no rule 'W9'" in n for n in me.notices)
    assert not [e for e in events(v) if e["type"] == "proposal"]


def test_the_round_schema_has_draw_only_in_the_tontine_arm():
    t = step(tontine())[0]
    c = step(village(economy=NO_ACCIDENTS))[0]
    assert "draw" in prompting.schema(t)["properties"] and "draw" not in prompting.schema(c)["properties"]
    text = prompting.user_prompt(t)
    assert "VILLAGE POOL" in text and "RULE BOOK" in text
    assert "VILLAGE POOL" not in prompting.user_prompt(c)


def test_the_button_is_once_a_round_in_the_control_arm_too():
    v = village(economy=NO_ACCIDENTS)
    step(v, {"a01": answer(actions=[act("press_button"), act("press_button")])})
    assert v.world.agents["a01"].presses == 1


# --------------------------------------------------------------------------- encouraging reading, and leaders

def test_reading_can_build_memory_in_chosen_channels_and_the_prompt_says_so():
    from swarm_village.domain.seed import channel_order

    off = village(economy=NO_ACCIDENTS)
    assert "memory point" not in prompting.system_prompt(off.cfg, off.channel_order).split("ACTIONS")[0].split("SHARING")[1]
    v = village(economy=NO_ACCIDENTS, comms={"read_memory": 2, "read_memory_channels": ["board"]})
    text = prompting.system_prompt(v.cfg, channel_order(v.cfg))
    assert "Each board notice you read also gives you 2 memory points." in text
    step(v, {"a01": answer(actions=[act("post", text="hello"), act("message", to="a02", text="hi")])})
    step(v, {"a02": answer(actions=[act("read", item="B1"), act("read", item="M1")])})
    step(v)
    assert v.world.agents["a02"].memory == pytest.approx(2 * 0.98)  # the board read only (2), then the round's 2% fade
    every = village(economy=NO_ACCIDENTS, comms={"read_memory": 1})
    assert "Each item you read also gives you 1 memory point." in prompting.system_prompt(every.cfg, every.channel_order)


def test_influence_counts_reach_requests_gifts_and_council_seats():
    from swarm_village.domain import metrics as M

    ev = [
        {"type": "agent_added", "agent": {"id": "a01", "parents": []}},
        {"type": "agent_added", "agent": {"id": "a02", "parents": []}},
        {"type": "item_added", "item": {"id": "M1", "channel": "message", "author": "a02", "round": 1, "text": "help?",
                                        "to": ["a01"], "plot": None, "note": "", "meta": {}}},
        {"type": "item_added", "item": {"id": "B1", "channel": "board", "author": "a01", "round": 1, "text": "spread out",
                                        "to": [], "plot": None, "note": "", "meta": {}}},
        {"type": "read", "reader": "a02", "item": "B1", "author": "a01", "round": 2, "channel": "board"},
        {"type": "exposure", "agent": "a02", "items": ["B1"], "round": 2, "preview_chars": 80},
        {"type": "gift", "agent": "a01", "to": "a02", "amount": 3.0, "ok": True, "round": 2},
        {"type": "council", "members": ["a01"], "round": 10},
    ]
    inf = M.influence(ev)
    assert inf["a01"]["messages_received"] == 1 and inf["a01"]["read_by_others"] == 1
    assert inf["a01"]["seen_by_others"] == 1 and inf["a01"]["gifts_given"] == 1 and inf["a01"]["council_seats"] == 1
    assert inf["a02"]["gifts_received"] == 1 and inf["a02"]["items_written"] == 1
    assert M.leaders(ev)["gifts_given"] == [("a01", 1)]
