"""Command line: swarm-village {run,report,verify}."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from .adapters import yaml_config
from .adapters.storage import read_events
from .app import experiment_runner, report_builder
from .domain.model import rebuild


def _overrides(args) -> dict:
    o: dict = {}
    if getattr(args, "runtime", None):
        o["runtime"] = {"kind": args.runtime}
    if getattr(args, "rounds", None):
        o["rounds"] = args.rounds
    if getattr(args, "seeds", None):
        o["seeds"] = [int(s) for s in args.seeds.split(",")]
    if getattr(args, "arms", None):
        o["arms"] = args.arms.split(",")
    for item in getattr(args, "set", None) or []:
        key, sep, value = item.partition("=")
        if not sep or not key:
            raise SystemExit(f"--set expects key.path=value, got {item!r}")
        node = o
        *parents, leaf = key.split(".")
        for p in parents:
            node = node.setdefault(p, {})
        node[leaf] = yaml.safe_load(value)
    return o


def _doc(args) -> dict:
    doc = yaml_config.deep_merge(yaml_config.load_with_base(args.config), _overrides(args))
    if doc.get("runtime", {}).get("kind") == "mock":
        doc["runtime"] = {"kind": "mock"}  # drop model settings the mock does not take
    return doc


def cmd_run(args) -> None:
    doc = _doc(args)
    name = args.name or doc.get("name") or Path(args.config).stem
    batch = experiment_runner.run_batch(doc, name, parallel=args.parallel, out_root=args.out,
                                        batch_budget_usd=args.batch_budget)
    print(report_builder.build([batch], batch, doc.get("pricing")).read_text(encoding="utf-8"))
    problems = verify_batch(batch)
    print("Tap check: every run rebuilds exactly from its event log." if not problems else
          "Tap check FAILED:\n" + "\n".join(problems))
    print(f"Results: {batch}")


def cmd_report(args) -> None:
    batches = [Path(b) for b in args.batch]
    out = Path(args.out) if args.out else batches[0]
    print(report_builder.build(batches, out).read_text(encoding="utf-8"))


def verify_batch(batch: Path) -> list[str]:
    """Rebuild every run's world from its tap alone and compare it with the engine's final state."""
    problems = []
    for events_path in sorted(Path(batch).glob("*/events.jsonl")):
        final = events_path.parent / "final_state.json"
        if not final.exists():
            problems.append(f"{events_path.parent.name}: no final_state.json")
            continue
        events = read_events(events_path)
        expected = json.loads(final.read_text(encoding="utf-8"))
        try:
            got = rebuild(events, expected["arm"]).to_dict()
        except ValueError as e:
            problems.append(f"{events_path.parent.name}: {e}")
            continue
        if got != expected:
            diff = [k for k in expected if got.get(k) != expected[k]]
            problems.append(f"{events_path.parent.name}: rebuilt state differs in {diff}")
    return problems


def cmd_verify(args) -> None:
    problems = [p for b in args.batch for p in verify_batch(Path(b))]
    print("\n".join(problems) if problems else "Every run rebuilds exactly from its event log.")
    if problems:
        raise SystemExit(1)


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="swarm-village", description="Swarm dynamics village testbed")
    sub = p.add_subparsers(dest="command", required=True)

    sr = sub.add_parser("run", help="run every seed x arm in a config, then report and verify")
    sr.add_argument("--config", required=True)
    sr.add_argument("--name", help="batch name (default: the config's name, or its file name)")
    sr.add_argument("--runtime", choices=["mock", "anthropic"], help="override the config's runtime")
    sr.add_argument("--rounds", type=int)
    sr.add_argument("--seeds", help="comma-separated, e.g. 101,102")
    sr.add_argument("--arms", help="comma-separated, from control and tontine")
    sr.add_argument("--parallel", type=int, default=1, help="runs to execute at once")
    sr.add_argument("--out", help="output root (default: the config's output_dir)")
    sr.add_argument("--batch-budget", type=float, metavar="USD", help="start no new run once finished runs spent this")
    sr.add_argument("--set", action="append", metavar="KEY=VALUE", help="override any config value (repeatable)")
    sr.set_defaults(func=cmd_run)

    sp = sub.add_parser("report", help="recompute every measure for one or more batch directories")
    sp.add_argument("batch", nargs="+")
    sp.add_argument("--out", help="where to write summary.md/json (default: the first batch)")
    sp.set_defaults(func=cmd_report)

    sv = sub.add_parser("verify", help="rebuild each run's world from its tap and compare with its final state")
    sv.add_argument("batch", nargs="+")
    sv.set_defaults(func=cmd_verify)

    args = p.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    sys.exit(main())
