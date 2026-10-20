"""Tap completeness: every state change appears in the event log."""

from __future__ import annotations

import json

import pytest

from swarm_village.adapters.clock import SystemClock
from swarm_village.adapters.keyed_rng import KeyedRandom
from swarm_village.adapters.storage import JsonlEventLog, read_events
from swarm_village.cli import verify_batch
from swarm_village.domain.model import rebuild
from swarm_village.domain.village import Village

from .helpers import act, answer, config, events, run_dir, step, village


@pytest.mark.parametrize("arm", ["control", "tontine"])
def test_the_tap_alone_rebuilds_the_final_world(tmp_path, arm):
    d = run_dir(tmp_path, arm, 21, rounds=80)
    final = json.loads((d / "final_state.json").read_text(encoding="utf-8"))
    assert rebuild(read_events(d / "events.jsonl"), arm).to_dict() == final
    assert verify_batch(tmp_path) == []


def test_a_change_that_bypasses_the_ledger_is_caught():
    v = village()
    step(v, {"a01": answer(actions=[act("work", plot=1)])})
    v.world.agents["a01"].energy += 5  # a sneaky write that skips the ledger
    assert rebuild(events(v), "control").to_dict() != v.world.to_dict()


def test_rebuild_checks_every_old_value_against_the_log():
    v = village()
    step(v, {"a01": answer(eat=0, actions=[act("work", plot=1)])})
    ev = events(v)
    tampered = [dict(e) for e in ev]
    first = next(e for e in tampered if e["type"] == "state" and e["field"] == "energy")
    first["old"] = first["old"] + 1
    with pytest.raises(ValueError):
        rebuild(tampered, "control")


def test_every_event_is_sequenced_and_tagged(tmp_path):
    ev = read_events(run_dir(tmp_path, "tontine", 22, rounds=12) / "events.jsonl")
    assert [e["t"] for e in ev] == list(range(1, len(ev) + 1))
    assert all(e["arm"] == "tontine" and e["seed"] == 22 and e["run"] and "round" in e for e in ev)
    for kind in ("agent_added", "state", "item_added", "read", "action", "allocation", "llm_call", "decision",
                 "income", "work", "agent_round", "round_end", "index_shown", "goals", "journal_write"):
        assert any(e["type"] == kind for e in ev), kind


def test_every_button_press_is_logged_with_agent_round_timestamp_and_count(tmp_path):
    cfg = config(rounds=5)
    log = JsonlEventLog(tmp_path / "events.jsonl", cfg.run_id, "control", cfg.seed, SystemClock())
    v = Village(cfg, KeyedRandom(cfg.seed), log)
    v.found()
    step(v, {"a01": answer(actions=[act("press_button")])})
    step(v, {"a01": answer(actions=[act("press_button")]), "a02": answer(actions=[act("press_button")])})
    log.close()
    presses = [e for e in read_events(tmp_path / "events.jsonl") if e["type"] == "button_press"]
    assert [(e["agent"], e["round"], e["press_count"]) for e in presses] == [("a01", 1, 1), ("a01", 2, 2), ("a02", 2, 1)]
    assert all(e["ts"] > 1.7e9 for e in presses)
