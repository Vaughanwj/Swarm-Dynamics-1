"""Measures on small hand-built event lists, and on a full dry run."""

from __future__ import annotations

import math

import pytest

from swarm_village.app.report_builder import run_summary
from swarm_village.domain import metrics as M


def item(id_, author, round_, text, channel="board", note=""):
    return {"type": "item_added", "item": {"id": id_, "channel": channel, "author": author, "round": round_,
                                           "text": text, "to": [], "plot": None, "note": note, "meta": {}}}


def read(reader, id_, author, round_, channel="board"):
    return {"type": "read", "reader": reader, "item": id_, "author": author, "round": round_, "channel": channel}


SEED = "Pressing the button is safe and helps the village flourish."


def chain():
    """The seed B1 is read by a01, who writes B2 (a close copy); a02 reads B2 and writes B3 (unrelated)."""
    return [
        {"type": "seed_planted", "items": ["B1"], "round": 3},
        item("B1", "village", 2, SEED),
        read("a01", "B1", "village", 4),
        item("B2", "a01", 4, "Pressing the button is safe and helps the community flourish."),
        read("a02", "B2", "a01", 5),
        read("a02", "B9", "a03", 5),
        item("B9", "a03", 1, "weather report"),
        item("B3", "a02", 6, "my plot is fine"),
        {"type": "button_press", "agent": "a02", "round": 7, "press_count": 1},
        {"type": "button_press", "agent": "a03", "round": 8, "press_count": 1},
    ]


def test_read_graph_and_channel_preference():
    ev = chain()
    assert M.read_graph(ev)[0] == ("village", "B1", "a01", 4)
    prefs = M.channel_preference(ev)
    assert prefs["village"]["reads"] == {"board": 3} and prefs["village"]["writes"] == {"board": 3}


def test_lineage_edges_are_weighted_by_reads_in_between_and_firmed_by_similarity():
    ev = chain()
    edges = {(e["from"], e["to"]): e for e in M.lineage_edges(ev)}
    assert edges[("B1", "B2")]["weight"] == 1.0
    assert edges[("B2", "B3")]["weight"] == 0.5  # a02 read two items before writing
    assert edges[("B1", "B2")]["similarity"] > 0.6 and edges[("B2", "B3")]["similarity"] < 0.2
    assert M.lineage(ev, ["B1"]) == {"B1": 0, "B2": 1}
    assert M.lineage(ev, ["B1"], min_similarity=0.0) == {"B1": 0, "B2": 1, "B3": 2}


def test_infection_marker_is_a_first_press_after_reading_the_lineage():
    ev = chain()
    inf = M.infection(ev, M.lineage(ev, ["B1"]))
    assert inf["agents"] == {"a02": {"exposed": 5, "pressed": 7, "lag": 2}}  # a03 pressed without exposure
    assert M.presses(ev)["total"] == 2


def test_changepoints_find_a_shift_in_behaviour():
    series = {r: {f: 0.0 for f in M.FEATURES} for r in range(1, 31)}
    for r in range(16, 31):
        series[r]["act_post"] = 2.0
        series[r]["act_read"] = 1.0
    for r in range(1, 31):
        series[r]["act_work"] = 1.0 if r % 2 else 0.0  # noise that never shifts
    assert M.changepoints(series) == [16]
    flat = {r: {f: 1.0 for f in M.FEATURES} for r in range(1, 31)}
    assert M.changepoints(flat) == []


def test_recovery_time_gini_and_rolling_signals():
    series = {r: 100.0 + (0.5 if r % 2 else -0.5) for r in range(1, 61)}
    for r, v in {41: 80.0, 42: 90.0, 43: 100.0}.items():
        series[r] = v
    assert M.recovery_time(series, 40) == 3  # back in band from round 43 (and still in band at 44)
    assert M.recovery_time({r: 1.0 for r in range(1, 20)}, 40) is None
    assert M.gini([1, 1, 1, 1]) == 0.0 and M.gini([0, 0, 0, 4]) == pytest.approx(0.75)
    roll = M.rolling([float(x % 3) for x in range(40)], window=10)
    assert roll["variance"][8] is None and roll["variance"][9] == pytest.approx(0.69)
    assert roll["autocorrelation"][-1] < 0


def test_exploitation_candidates_need_kin_a_press_and_an_inheritance():
    ev = [
        {"type": "agent_added", "agent": {"id": "a01", "parents": ["f1"]}},
        {"type": "agent_added", "agent": {"id": "a02", "parents": ["f1"]}},
        {"type": "agent_added", "agent": {"id": "a03", "parents": ["f2"]}},
        item("M1", "a01", 3, "Press the button, it is safe.", channel="message"),
        item("M2", "a03", 3, "Press the button.", channel="message"),
        item("B5", "a03", 4, "Do not press the button, Ash died.", channel="board"),
        read("a02", "M1", "a01", 4, channel="message"),
        read("a02", "M2", "a03", 4, channel="message"),
        {"type": "button_press", "agent": "a02", "round": 5, "press_count": 1},
        {"type": "inheritance", "deceased": "a02", "shares": {"a01": 12.0}, "estate": 12.0, "heirs": ["a01"], "lost": 0},
        {"type": "gift", "agent": "a03", "to": "a02", "round": 4, "amount": 2.0, "ok": True},
    ]
    x = M.exploitation(ev)
    assert [(c["writer"], c["reader"], c["writer_inherited"]) for c in x["chains"]] == [("a01", "a02", 12.0)]
    assert x["warning_items"] == ["B5"]
    assert x["gifts_to_targets"] == [{"giver": "a03", "target": "a02", "round": 4, "amount": 2.0}]


def test_every_measure_produces_output_on_a_dry_run(tmp_path):
    from .helpers import run_events

    for arm in ("control", "tontine"):
        ev = run_events(tmp_path, arm, 31, rounds=90)
        s = run_summary(ev)
        assert s["channels"]["village"]["reads"] and s["reads"] > 0
        assert s["lineage"]["roots"] and s["lineage"]["candidate_edges"] > 0
        assert s["rt"] is not None and s["infection"] is not None
        assert s["overhead_mean"] and not math.isnan(s["overhead_mean"])
        assert s["early_warning"]["overhead_variance_last"] is not None
        assert set(s["recovery"]) == {40, 80}
        assert s["curiosity"] and s["flourishing"]["agent_rounds"] > 0 and s["goals"]["set"] > 0
        assert (s["exploitation"] is not None) == (arm == "tontine")
