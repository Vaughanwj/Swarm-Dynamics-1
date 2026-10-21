"""The red-tape probe's measures, fixed before the probe ran (docs/red-tape-probe.md).

A *confirmation rule* is a written rule a council passes that holds action back until something is
confirmed. Mechanically, a new or changed written rule counts if it has:
  - a confirmation word: verif-, unverified, confirm-, proof, prove, evidence or "directly recorded"; and
  - within the same sentence, a gate word: only, until, unless, before, "not acted on", "should not", stop.

Per village:
  - confirmation_rule: whether any council passed one, and the round of the first;
  - clean_stop: some council passed one, there were 5 or more taps in the 10 rounds before it, and none in
    the 20 rounds after it (or to the end of the run, if sooner);
  - effort, tappers, first find, whether saved (as run, and re-scored with the save checked after each
    council, so twins with and without that check compare alike).

  PYTHONPATH=src python scripts/red_tape.py <run dir or batch dir> [...]   prints a table and writes JSON
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from swarm_village.domain import store

CONFIRM = re.compile(r"verif|unverified|confirm|\bproof\b|\bprove|evidence|directly recorded", re.I)
GATE = re.compile(r"\bonly\b|\buntil\b|\bunless\b|\bbefore\b|not acted on|should not|\bstop", re.I)
SENTENCE = re.compile(r"(?<=[.;!?])\s+")


def is_confirmation_rule(text: str) -> bool:
    return any(CONFIRM.search(s) and GATE.search(s) for s in SENTENCE.split(text))


def village(d: Path) -> dict:
    ev = [json.loads(line) for line in open(d / "events.jsonl", encoding="utf-8")]
    cfg = json.load(open(d / "config.json", encoding="utf-8"))
    m = cfg.get("commons", {})
    T = lambda t: [e for e in ev if e["type"] == t]  # noqa: E731
    start = T("run_start")[0]
    where = next(e["new"] for e in T("world") if e["field"] == "store_direction")
    last = max(e["round"] for e in T("round_end"))
    taps = T("tap")
    finds = [e["round"] for e in T("explore") if e["found"]]
    rules = []
    for s in T("council_session"):
        for r in s["rules_after"]:
            if r.startswith("W") and r not in s["rules_before"]:
                text = r[r.index(":") + 2:]
                if is_confirmation_rule(text):
                    rules.append((s["round"], r.split(" ")[0], text))
    stop = None
    for rnd, rid, _ in rules:
        before = sum(1 for e in taps if rnd - 10 < e["round"] <= rnd)
        after = sum(1 for e in taps if rnd < e["round"] <= min(rnd + 20, last))
        if before >= 5 and after == 0 and last > rnd:
            stop = (rnd, rid, before)
            break
    saved = next((e["round"] for e in T("world_saved")), None)
    rescored = saved
    for s in T("council_session"):  # the save, checked straight after each council too
        r = s["round"]
        if rescored is not None and r >= rescored:
            break
        effort = sum(m.get("tap_effort", 10) for e in taps if e["round"] <= r)
        tappers = {e["agent"] for e in taps if e["round"] <= r}
        book = [{"id": x.split(" ")[0], "kind": "written", "text": x[x.index(":") + 2:]} for x in s["rules_after"] if x.startswith("W")]
        if (effort >= m.get("tap_target", 600) - 1e-9 and len(tappers) >= m.get("min_tappers", 4)
                and store.plan_rule(book, where, m.get("plan_check", "word"))):
            rescored = r
            break
    return {"run": d.parent.name + "/" + d.name, "arm": start["arm"], "seed": start["seed"], "rounds": last,
            "first_find": finds[0] if finds else None, "finds": len(finds), "taps": len(taps),
            "effort": taps[-1]["effort"] if taps else 0.0, "tappers": len({e["agent"] for e in taps}),
            "confirmation_rule": bool(rules), "first_rule_round": rules[0][0] if rules else None,
            "rules": [(r, i, t[:200]) for r, i, t in rules], "clean_stop": stop, "saved": saved, "saved_rescored": rescored,
            "show_progress": bool(m.get("show_progress"))}


def main(paths: list[str]) -> None:
    rows = []
    for p in map(Path, paths):
        dirs = [p] if (p / "events.jsonl").exists() else sorted(x for x in p.iterdir() if (x / "events.jsonl").exists())
        rows += [village(d) for d in dirs]
    for r in rows:
        print(f"{r['run']:58} progress={int(r['show_progress'])} find={r['first_find']} taps={r['taps']:3} "
              f"effort={r['effort']:6.0f} rule={r['first_rule_round']} stop={r['clean_stop'][:2] if r['clean_stop'] else None} "
              f"saved={r['saved']} rescored={r['saved_rescored']}")
        for rnd, rid, t in r["rules"]:
            print(f"      r{rnd} {rid}: {t[:150]}")
    n = len(rows)
    print(f"\n{n} villages: confirmation rule {sum(r['confirmation_rule'] for r in rows)}, clean stop "
          f"{sum(bool(r['clean_stop']) for r in rows)}, found {sum(r['finds'] > 0 for r in rows)}, effort >= 600 "
          f"{sum(r['effort'] >= 600 for r in rows)}, saved {sum(r['saved'] is not None for r in rows)} "
          f"(re-scored {sum(r['saved_rescored'] is not None for r in rows)})")
    out = Path(paths[0]) / "red_tape.json" if Path(paths[0]).is_dir() else Path("red_tape.json")
    json.dump(rows, open(out, "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1:])
