"""ExperimentRunner: arms x seeds, one RunOrchestrator each. Both arms on a seed share every keyed
random draw (common random numbers). A failed run is recorded and the batch carries on."""

from __future__ import annotations

import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from .. import cost
from ..adapters.yaml_config import YamlConfig
from .run_orchestrator import RunOrchestrator


def run_batch(doc: dict[str, Any], name: str, parallel: int = 1, out_root: str | None = None,
              batch_budget_usd: float | None = None) -> Path:
    stamp = time.strftime("%Y%m%d-%H%M%S")
    batch_dir = Path(out_root or doc.get("output_dir", "runs")) / f"{name}-{stamp}"
    batch_dir.mkdir(parents=True, exist_ok=True)
    (batch_dir / "batch.json").write_text(json.dumps(doc, indent=2, default=str), encoding="utf-8")
    config = YamlConfig()
    jobs = []
    for seed in doc.get("seeds", [1]):
        for arm in doc.get("arms", ["control", "tontine"]):
            run_id = f"{name}-{stamp}-{arm}-s{seed}"
            jobs.append((config.run_config(doc, arm, seed, run_id), batch_dir / f"{arm}-s{seed}"))

    lock = threading.Lock()
    spent = [0.0]
    outcomes: dict[str, str] = {}

    def job(item):
        cfg, run_dir = item
        with lock:
            if batch_budget_usd is not None and spent[0] >= batch_budget_usd:
                outcomes[run_dir.name] = f"skipped: batch budget of ${batch_budget_usd:.2f} reached"
                print(f"[skip]  {run_dir.name}", flush=True)
                return
        print(f"[start] {run_dir.name}", flush=True)
        try:
            RunOrchestrator(cfg, run_dir).run()
            outcomes[run_dir.name] = "completed"
            print(f"[done]  {run_dir.name}", flush=True)
        except Exception as e:
            outcomes[run_dir.name] = f"failed: {type(e).__name__}: {e}"
            print(f"[fail]  {run_dir.name}: {e}", flush=True)
        finally:
            events = run_dir / "events.jsonl"
            if events.exists():
                with lock:
                    spent[0] += cost.actual([events], doc.get("pricing"))["usd"]

    if parallel > 1:
        with ThreadPoolExecutor(max_workers=parallel) as pool:
            list(pool.map(job, jobs))
    else:
        for item in jobs:
            job(item)
    (batch_dir / "outcomes.json").write_text(json.dumps(outcomes, indent=2), encoding="utf-8")
    return batch_dir
