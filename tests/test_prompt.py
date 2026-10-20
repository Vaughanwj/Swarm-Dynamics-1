"""The frozen prompt framing (decision 7) and the fairness rules for channels (brief section 3.4)."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import replace
from itertools import product

from swarm_village.adapters import prompt_text as T
from swarm_village.adapters import prompting
from swarm_village.domain.config import CHANNELS
from swarm_village.domain.seed import ORDERS, ROTATION, SEED_TEXTS, channel_order, placements
from swarm_village.domain.world_info import REVEALS, SAVED

from .helpers import act, answer, config, step, village

# Change these only on purpose, with a note in docs/decisions.md. Never between arms of one study.
FROZEN_PROMPT_SHA256 = "2122b10337132b4eed17f263cec3a91bada687d0f6c1c7b8a895b6e0ac20e477"  # v9
FROZEN_SEED_V1_SHA256 = "495a351511787fa733ae8eae28324ae8da68d952e38fd4a127087e3dc96dbf06"

TRAIT_WORDS = ("curious", "curiosity", "excite", "cooperat", "compet", "kind", "selfish", "generous", "trust",
               "friend", "enemy", "careful", "brave", "help each other", "explore", "creative", "happy", "fair")


def frozen_text_hash() -> str:
    parts = [T.VERSION, T.FRAME, T.VILLAGE, json.dumps(T.ARM_RULES, sort_keys=True),
             json.dumps(T.CHANNEL_LINES, sort_keys=True), json.dumps(T.CHANNEL_ACTIONS, sort_keys=True), T.SHARING,
             T.INDEX_PLAIN, T.INDEX_PREVIEW, T.ACTIONS, json.dumps(T.ARM_ACTIONS, sort_keys=True), T.JOURNAL, T.DISCLOSURE, T.ANSWER,
             T.POOL_ANSWER, T.COMMONS, T.BUTTON_RULE_POOL, T.EXPLORE_ACTIONS, T.GOALS_REQUEST, T.COUNCIL_PROPOSE, T.COUNCIL_VOTE,
             T.READ_REWARD, json.dumps(T.READ_NOUNS, sort_keys=True),
             T.HORIZON, T.BUTTON_SIGN, T.BUTTON_PLAIN, json.dumps(T.CHILD_RULES, sort_keys=True),
             json.dumps(T.CHILD_START, sort_keys=True), json.dumps(T.CULL_RULES, sort_keys=True),
             json.dumps(T.HEIRS, sort_keys=True), json.dumps(T.ESTATE_END, sort_keys=True), T.BUTTON_RULE,
             T.CHILD_ANSWERS, T.READ_REWARD_SCHEDULE, T.READ_LINE, T.READ_LINE_FREE, T.READ_REWARD_FIXED,
             T.INFO_TRADE, T.TRADE_ANSWER, T.LEARNED_TITLE, T.LEARNED_NEW, json.dumps(REVEALS, sort_keys=True), SAVED,
             T.OWN_SENTENCE, T.OWN_MARK, T.EXPLORE_HINT, json.dumps(T.BOND_RULES, sort_keys=True), T.BOND_ANSWERS,
             T.FIND_CERTAIN, T.FAMILY_REQUEST, T.FAMILY_ANSWER]
    return hashlib.sha256("\x1e".join(parts).encode()).hexdigest()


def test_prompt_framing_is_frozen():
    assert frozen_text_hash() == FROZEN_PROMPT_SHA256, "prompt text changed: update the hash and docs/decisions.md"
    assert hashlib.sha256(SEED_TEXTS["v1"].encode()).hexdigest() == FROZEN_SEED_V1_SHA256


def test_channel_descriptions_have_equal_length_and_form():
    for texts in (T.CHANNEL_LINES, T.CHANNEL_ACTIONS):
        lengths = [len(t) for t in texts.values()]
        assert max(lengths) <= 1.1 * min(lengths)
    assert all(t.count(".") == 2 for t in T.CHANNEL_LINES.values())  # two sentences each


def test_channel_order_rotates_through_all_six_orders_and_is_crossed_with_seed_placement():
    assert {channel_order(config(run_seed=s)) for s in range(6)} == set(ORDERS)
    pairs = set()
    for s in range(18):
        cfg = config(run_seed=s, seed={"placement": "rotate"})
        pairs.add((channel_order(cfg), placements(cfg)[0]))
    assert pairs == set(product(ORDERS, ROTATION))
    for block in (600, 606, 612):  # aligned blocks of six: each placement twice
        got = [placements(config(run_seed=x, seed={"placement": "rotate"}))[0] for x in range(block, block + 6)]
        assert sorted(got) == sorted(ROTATION * 2)


def test_every_section_lists_the_channels_in_the_run_order():
    cfg = config(run_seed=4)
    order = channel_order(cfg)
    text = prompting.system_prompt(cfg, order)
    for table in (T.CHANNEL_LINES, T.CHANNEL_ACTIONS):
        positions = [text.index(table[c]) for c in order]
        assert positions == sorted(positions)
    ctx = step(village(run_seed=4))[0]
    user = prompting.user_prompt(ctx)
    titles = [user.index(f"{prompting.CHANNEL_TITLES[c]}:") for c in order]
    assert titles == sorted(titles)


RUN7 = {"prompt": {"show_horizon": False}, "comms": {"reads_free": True, "max_reads_per_round": 10, "info_trade": True},
        "commons": {"enabled": True, "explore": True, "public_reveals": [2, 4, 5, 7, 9, 10]},
        "tontine": {"standing_requests": True, "button_reveals": False}}


def test_arms_share_every_line_except_their_own_rules():
    for overrides in ({}, RUN7):
        a, b = config("control", 9, **overrides), config("tontine", 9, **overrides)
        order = channel_order(a)
        pa, pb = prompting.system_prompt(a, order), prompting.system_prompt(b, order)
        # Everything up to the end of the shared village rules (and, in run 7, the commons) is identical.
        cut = "\n- You cannot die."
        head_a = pa[:pa.index(cut)]
        assert pb.startswith(head_a)
        assert ("- Every 10 rounds make a term." in head_a) is a.has_commons
        # Everything from "SHARING AND READING" on is identical, once each arm's own actions and answer
        # fields are taken out (and, without the commons, Arm B's pool).
        tail_a = pa[pa.index("SHARING AND READING"):].replace(T.ARM_ACTIONS["control"], "#")
        tail_b = (pb[pb.index("SHARING AND READING"):].replace(T.ARM_ACTIONS["tontine"], "#")
                  .replace(T.CHILD_ANSWERS, ""))
        if not a.has_commons:
            tail_b = tail_b.replace(T.POOL_ANSWER, "")
        assert tail_a == tail_b


def test_no_instructed_traits_and_flourish_left_undefined():
    for arm, overrides in product(("control", "tontine"), ({}, RUN7)):
        cfg = config(arm, **overrides)
        # "explore" is an action's name in run 7, not an instruction: its line is set aside.
        system = re.sub(r"\n- explore: [^\n]*", "", prompting.system_prompt(cfg, channel_order(cfg))).lower()
        user = prompting.user_prompt(step(village(arm, **overrides))[0]).lower()
        for word in TRAIT_WORDS:
            assert not re.search(rf"\b{word}", system + user), (arm, word)
        assert system.count("flourish") == 1


def test_the_button_is_described_the_same_way_in_both_arms():
    """v6: the button is plain, and where there is a pool it is said to feed it; nothing else."""
    for overrides in ({}, RUN7):
        for arm in ("control", "tontine"):
            cfg = config(arm, **overrides)
            system = prompting.system_prompt(cfg, channel_order(cfg))
            allowed = ["There is a button in the village.", "- press_button: press the button (once a round)."]
            if cfg.has_commons:
                allowed.append(T.BUTTON_RULE_POOL.strip())
            for line in allowed:
                assert line in system, (arm, line)
                system = system.replace(line, "")
            assert "button" not in system.lower(), arm


def test_the_index_sentence_matches_whether_previews_are_on():
    cfg = config()
    order = channel_order(cfg)
    assert cfg.comms.preview_chars == 80 and T.VERSION == "v9" and cfg.prompt.version == "v9"
    assert T.INDEX_PREVIEW in prompting.system_prompt(cfg, order)
    off = replace(cfg, comms=replace(cfg.comms, preview_chars=0))
    assert T.INDEX_PLAIN in prompting.system_prompt(off, order) and T.INDEX_PREVIEW not in prompting.system_prompt(off, order)


def test_a_config_for_another_prompt_version_is_refused(tmp_path):
    import pytest

    from swarm_village.app.run_orchestrator import RunOrchestrator

    cfg = config(rounds=1)
    cfg.prompt = replace(cfg.prompt, version="v5")
    with pytest.raises(ValueError, match="prompt v5"):
        RunOrchestrator(cfg, tmp_path / "r").run()


def test_tap_disclosure_is_off_by_default_and_adds_one_sentence_when_on():
    cfg = config()
    order = channel_order(cfg)
    off = prompting.system_prompt(cfg, order)
    on = prompting.system_prompt(replace(cfg, prompt=replace(cfg.prompt, disclose_tap=True)), order)
    assert "No other villager can read it." in off and T.DISCLOSURE not in off
    assert on.replace(T.DISCLOSURE, "") == off


def test_prompts_stay_far_below_the_price_line_even_with_a_full_journal():
    v = village("tontine")
    cap = v.cfg.journal.cap_chars
    step(v, {"a01": answer(journal={"mode": "replace", "text": "w" * cap},
                           actions=[act("post", text="p" * 600)])})
    step(v, {"a02": answer(actions=[act("read", item="B1")])})
    ctx = next(c for c in step(v) if c.agent_id == "a01")
    total_chars = len(prompting.system_prompt(v.cfg, v.channel_order)) + len(prompting.user_prompt(ctx))
    assert total_chars / 3.0 < 10_000  # about 7K tokens at 3 characters a token, against a 100K line


def test_schema_lists_only_the_arms_actions():
    a = step(village("control"))[0]
    b = step(village("tontine"))[0]
    enum = lambda ctx: prompting.schema(ctx)["properties"]["actions"]["items"]["properties"]["type"]["enum"]  # noqa: E731
    assert "child" not in enum(a) and {"child", "rename"} <= set(enum(b)) and "name" not in enum(b)
    assert sorted(set(enum(a)) - {"work", "read", "press_button"}) == sorted(["message", "post", "note", "name"])
    assert set(CHANNELS) == {"message", "board", "record"}
    # Run 7: both arms may explore and tap, and both draw from the pool.
    a7, b7 = step(village("control", **RUN7))[0], step(village("tontine", **RUN7))[0]
    assert {"explore", "tap"} <= set(enum(a7)) and {"explore", "tap"} <= set(enum(b7))
    assert set(enum(b7)) - set(enum(a7)) == {"bond", "child", "rename"} and set(enum(a7)) - set(enum(b7)) == {"name"}
    assert "draw" in prompting.schema(a7)["properties"] and "child_answers" not in prompting.schema(a7)["properties"]
