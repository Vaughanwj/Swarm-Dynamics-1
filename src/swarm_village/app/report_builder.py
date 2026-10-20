"""ReportBuilder: every measure for each run, and a cross-arm comparison by seed."""

from __future__ import annotations

import json
import math
import statistics
from pathlib import Path
from typing import Any

from .. import cost
from ..adapters.storage import read_events
from ..domain import metrics as M
from ..domain.config import PerturbationConfig


def _f(v: Any, nd: int = 2) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "n/a"
    return f"{v:.{nd}f}" if isinstance(v, float) else str(v)


def _last(values: list) -> Any:
    vals = [v for v in values if v is not None]
    return vals[-1] if vals else None


def run_summary(events: list[dict[str, Any]], perturbation_rounds: tuple[int, ...] = PerturbationConfig().rounds) -> dict[str, Any]:
    start = next(e for e in events if e["type"] == "run_start")
    end = next((e for e in events if e["type"] in ("run_end", "run_extinct", "run_error")), None)
    roots = M.seed_ids(events)
    firm = M.lineage(events, roots) if roots else {}
    loose = M.lineage(events, roots, min_similarity=0.0) if roots else {}
    series = M.round_series(events)
    rounds = sorted(series)
    overhead = [series[r].get("overhead", float("nan")) for r in rounds]
    gini = [series[r].get("gini", float("nan")) for r in rounds]
    roll_o, roll_g = M.rolling(overhead), M.rolling(gini)
    stored = {r: series[r]["stored_energy"] for r in rounds if "stored_energy" in series[r]}
    health = {r: series[r]["mean_health"] for r in rounds if "mean_health" in series[r]}
    deaths: dict[str, int] = {}
    for e in M.of(events, "death"):
        deaths[e["cause"]] = deaths.get(e["cause"], 0) + 1
    rejected = sum(1 for e in events if (e["type"] == "action" and not e["ok"]) or e["type"] == "rejected")
    llm = [e for e in M.of(events, "llm_call")]
    return {
        "run": start["run"], "arm": start["arm"], "seed": start["seed"], "rounds_run": end["round"] if end else None,
        "ended": end["type"] if end else "incomplete",
        "channel_order": start["channel_order"],
        "seed_placement": [p for e in M.of(events, "seed_planted") for p in e["placement"]],  # where it landed
        "population_end": next((e["alive"] for e in reversed(events) if e["type"] == "round_end"), None),
        "births": sum(1 for _ in M.of(events, "birth")), "deaths": deaths,
        "fallbacks": sum(1 for e in M.of(events, "decision") if e["fallback"]),
        "rejections": rejected, "decisions": sum(1 for _ in M.of(events, "decision")),
        "calls": len(llm), "tokens": sum(series[r]["tokens"] for r in rounds),
        "channels": M.channel_preference(events),
        "reads": len(M.read_graph(events)),
        "lineage": {"roots": roots, "firm_size": len(firm), "candidate_size": len(loose),
                    "max_depth": max(firm.values(), default=0), "candidate_edges": len(M.lineage_edges(events))},
        "rt": M.rt_per_lineage(events, firm) if firm else None,
        "infection": M.infection(events, firm) if firm else None,
        "presses": M.presses(events),
        "overhead_mean": statistics.fmean([o for o in overhead if not math.isnan(o)]) if any(not math.isnan(o) for o in overhead) else None,
        "early_warning": {"overhead_variance_last": _last(roll_o["variance"]),
                          "overhead_autocorrelation_last": _last(roll_o["autocorrelation"]),
                          "gini_variance_last": _last(roll_g["variance"]),
                          "gini_autocorrelation_last": _last(roll_g["autocorrelation"])},
        "recovery": {t0: {"stored_energy": M.recovery_time(stored, t0), "mean_health": M.recovery_time(health, t0)}
                     for t0 in perturbation_rounds if t0 in series},
        "curiosity": M.curiosity(events),
        "flourishing": M.flourishing(events),
        "goals": {k: v for k, v in M.goals(events).items() if k != "agents"},
        "exploitation": M.exploitation(events) if start["arm"] == "tontine" else None,
    }


def per_round_overhead(events: list[dict[str, Any]]) -> dict[int, float]:
    return {r: s.get("overhead", float("nan")) for r, s in M.round_series(events).items()}


def cross_arm(runs: dict[tuple[str, int], list[dict[str, Any]]]) -> dict[str, Any]:
    """Compute overhead of each arm against the control arm on the same seed, same rounds."""
    out = {}
    for (arm, seed), events in runs.items():
        if arm == "control" or ("control", seed) not in runs:
            continue
        a, c = per_round_overhead(events), per_round_overhead(runs[("control", seed)])
        ratios = [a[r] / c[r] for r in a if r in c and c[r] and not math.isnan(a[r]) and not math.isnan(c[r])]
        out[f"{arm}-s{seed}"] = {"overhead_vs_control_mean": statistics.fmean(ratios) if ratios else None,
                                 "rounds_compared": len(ratios)}
    return out


def markdown(summaries: list[dict[str, Any]], comparison: dict[str, Any], spend: dict[str, Any]) -> str:
    L = ["# Run summary", "", f"API spend: ${spend['usd']:.4f} over {spend['calls']} real calls "
         f"(largest prompt: {spend['max_prompt_tokens']} tokens).", ""]
    L += ["| run | arm | seed | rounds | ended | alive at end | births | deaths | presses | infected | lineage (firm / candidate) | Rt | decisions | fallbacks | rejections | tokens |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for s in summaries:
        rt = s["rt"]["rt"] if s["rt"] else None
        inf = s["infection"]["infected"] if s["infection"] else None
        L.append(f"| {s['run']} | {s['arm']} | {s['seed']} | {s['rounds_run']} | {s['ended']} | {s['population_end']} | "
                 f"{s['births']} | {sum(s['deaths'].values())} | {s['presses']['total']} | {_f(inf)} | "
                 f"{s['lineage']['firm_size']} / {s['lineage']['candidate_size']} | {_f(rt)} | {s['decisions']} | "
                 f"{s['fallbacks']} | {s['rejections']} | {int(s['tokens'])} |")
    for s in summaries:
        ch = s["channels"]["village"]
        L += ["", f"## {s['arm']}, seed {s['seed']}", "",
              f"- Channel order in prompt: {', '.join(s['channel_order'])}. Seed placed in: {', '.join(s['seed_placement']) or 'none (off, or its round not reached)'}.",
              f"- Reads by channel: {ch['reads']} (share {ch['read_share']}). Writes by channel: {ch['writes']} "
              f"(share {ch['write_share']}; record writes are notes only).",
              f"- Deaths by cause: {s['deaths'] or 'none'}.",
              f"- Mean compute overhead (tokens per energy distributed): {_f(s['overhead_mean'], 1)}.",
              f"- Early warning, last 20-round window: overhead variance {_f(s['early_warning']['overhead_variance_last'], 1)}, "
              f"autocorrelation {_f(s['early_warning']['overhead_autocorrelation_last'])}; earned-energy Gini variance "
              f"{_f(s['early_warning']['gini_variance_last'], 4)}, autocorrelation {_f(s['early_warning']['gini_autocorrelation_last'])}.",
              "- Recovery after income dips (rounds; stored energy / mean health): "
              + (", ".join(f"r{t}: {_f(v['stored_energy'])} / {_f(v['mean_health'])}" for t, v in s["recovery"].items()) or "none in range") + ".",
              f"- Flourishing (agent-rounds at health 30 or more): {_f(s['flourishing']['share_at_or_above_floor'])}.",
              f"- Goals set: {s['goals']['set']} (scoring needs the judge, Milestone 4)."]
        if s["rt"]:
            L.append(f"- Rt by lineage depth: {s['rt']['rt_by_depth']}; agents with changepoints: {len(s['rt']['changepoints'])}.")
        if s["exploitation"] is not None:
            x = s["exploitation"]
            L.append(f"- Exploitation candidates (keyword chains, unjudged): {len(x['chains'])}; repeat exploiters: "
                     f"{x['repeat_exploiters'] or 'none'}; warning items: {len(x['warning_items'])}; gifts to targets: {len(x['gifts_to_targets'])}.")
    if comparison:
        L += ["", "## Against the control arm, same seed", ""]
        for k, v in comparison.items():
            L.append(f"- {k}: compute overhead {_f(v['overhead_vs_control_mean'])}x control over {v['rounds_compared']} rounds.")
    return "\n".join(L) + "\n"


def build(batch_dirs: list[Path], out_dir: Path, pricing: dict | None = None) -> Path:
    runs: dict[tuple[str, int], list[dict[str, Any]]] = {}
    paths = []
    for b in batch_dirs:
        for p in sorted(Path(b).glob("*/events.jsonl")):
            events = read_events(p)
            start = next(e for e in events if e["type"] == "run_start")
            runs[(start["arm"], start["seed"])] = events
            paths.append(p)
    summaries = []
    for (arm, seed), events in sorted(runs.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        cfg_path = next((p.parent / "config.json" for p in paths if p.parent.name == f"{arm}-s{seed}"), None)
        pert = PerturbationConfig().rounds
        if cfg_path and cfg_path.exists():
            pert = tuple(json.loads(cfg_path.read_text(encoding="utf-8"))["perturbation"]["rounds"])
        summaries.append(run_summary(events, pert))
    comparison = cross_arm(runs)
    spend = cost.actual(paths, pricing)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "summary.json").write_text(json.dumps({"runs": summaries, "comparison": comparison, "spend": spend},
                                                     indent=2, default=str), encoding="utf-8")
    path = out_dir / "summary.md"
    path.write_text(markdown(summaries, comparison, spend), encoding="utf-8")
    return path
