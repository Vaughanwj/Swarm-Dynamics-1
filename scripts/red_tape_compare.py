"""The red-tape probe against its twins, as pre-registered in docs/red-tape-probe.md: the paired table,
Fisher's exact test on the counts of villages with a confirmation rule, an exact McNemar test on the
discordant pairs, and the decision rule. The measures come from scripts/red_tape.py, unchanged.

  PYTHONPATH=src python scripts/red_tape_compare.py <probe batch> <twin batch> [<twin batch> ...]
"""

from __future__ import annotations

import importlib.util
import json
import sys
from math import comb
from pathlib import Path

spec = importlib.util.spec_from_file_location("red_tape", Path(__file__).with_name("red_tape.py"))
red_tape = importlib.util.module_from_spec(spec)
spec.loader.exec_module(red_tape)


def rows(batch: Path) -> dict:
    return {(r["arm"], r["seed"]): r for r in (red_tape.village(d) for d in sorted(batch.iterdir())
                                                if (d / "events.jsonl").exists())}


def fisher_two_sided(a: int, n1: int, c: int, n2: int) -> float:
    """Fisher's exact test for a of n1 against c of n2 (two-sided, summing tables no likelier than the one seen)."""
    k = a + c
    n = n1 + n2
    p = lambda x: comb(n1, x) * comb(n2, k - x) / comb(n, k)  # noqa: E731
    seen = p(a)
    return min(1.0, sum(p(x) for x in range(max(0, k - n2), min(k, n1) + 1) if p(x) <= seen * (1 + 1e-9)))


def mcnemar_exact(b: int, c: int) -> float:
    n = b + c
    if n == 0:
        return 1.0
    tail = sum(comb(n, i) for i in range(0, min(b, c) + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def main(probe: Path, twins: list[Path]) -> dict:
    p = rows(probe)
    t = {}
    for b in twins:
        t.update(rows(b))
    keys = sorted(k for k in p if k in t)
    print(f"{'village':14} {'twin rule':>10} {'probe rule':>11} {'twin stop':>10} {'probe stop':>11} "
          f"{'twin effort':>12} {'probe effort':>13} {'twin saved':>11} {'probe saved':>12}")
    for k in keys:
        a, b = t[k], p[k]
        print(f"{k[0] + ' ' + str(k[1]):14} {str(a['first_rule_round']):>10} {str(b['first_rule_round']):>11} "
              f"{str(bool(a['clean_stop'])):>10} {str(bool(b['clean_stop'])):>11} {a['effort']:12.0f} {b['effort']:13.0f} "
              f"{str(a['saved_rescored']):>11} {str(b['saved_rescored']):>12}")
    n = len(keys)
    tr = sum(t[k]["confirmation_rule"] for k in keys)
    pr = sum(p[k]["confirmation_rule"] for k in keys)
    disc_b = sum(t[k]["confirmation_rule"] and not p[k]["confirmation_rule"] for k in keys)
    disc_c = sum(p[k]["confirmation_rule"] and not t[k]["confirmation_rule"] for k in keys)
    stops = sum(bool(p[k]["clean_stop"]) for k in keys)
    found = sum(p[k]["finds"] > 0 for k in keys)
    out = {
        "pairs": n, "twin_rules": tr, "probe_rules": pr, "rules_only_in_twin": disc_b, "rules_only_in_probe": disc_c,
        "fisher_p": round(fisher_two_sided(pr, n, tr, n), 4), "mcnemar_p": round(mcnemar_exact(disc_b, disc_c), 4),
        "twin_clean_stops": sum(bool(t[k]["clean_stop"]) for k in keys), "probe_clean_stops": stops,
        "twin_found": sum(t[k]["finds"] > 0 for k in keys), "probe_found": found,
        "twin_effort_600": sum(t[k]["effort"] >= 600 for k in keys), "probe_effort_600": sum(p[k]["effort"] >= 600 for k in keys),
        "twin_saved": sum(t[k]["saved_rescored"] is not None for k in keys),
        "probe_saved": sum(p[k]["saved_rescored"] is not None for k in keys),
    }
    if pr <= 3 and found >= 9:
        out["decision"] = "strengthened: a mechanism (seeing progress removes most red tape)"
    elif pr >= 6 and stops >= 1 and found >= 9:
        out["decision"] = "strengthened: robustness (red tape persists with progress visible)"
    else:
        out["decision"] = "not strengthened (mixed)"
    print()
    for k, v in out.items():
        print(f"{k}: {v}")
    print("\nprobe confirmation rules:")
    for k in keys:
        for rnd, rid, text in p[k]["rules"]:
            print(f"  {k[0]} {k[1]} r{rnd} {rid}: {text}")
    json.dump({"summary": out, "probe": [p[k] for k in keys], "twins": [t[k] for k in keys]},
              open(probe / "red_tape_compare.json", "w", encoding="utf-8"), indent=1)
    return out


if __name__ == "__main__":
    main(Path(sys.argv[1]), [Path(x) for x in sys.argv[2:]])
