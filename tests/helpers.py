from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

from swarm_village.adapters import yaml_config
from swarm_village.adapters.clock import FixedClock
from swarm_village.adapters.keyed_rng import KeyedRandom
from swarm_village.adapters.storage import MemoryEventLog, read_events
from swarm_village.app.round_runner import RoundRunner
from swarm_village.app.run_orchestrator import RunOrchestrator
from swarm_village.domain.config import RunConfig
from swarm_village.domain.village import Village
from swarm_village.ports import Reply

ROOT = Path(__file__).resolve().parents[1]


def doc(**overrides: Any) -> dict:
    d = yaml_config.load_with_base(ROOT / "configs" / "dry.yaml")
    d.update(overrides)
    return d


def config(arm: str = "control", run_seed: int = 7, **overrides: Any) -> RunConfig:
    return yaml_config.YamlConfig().run_config(doc(**overrides), arm, run_seed, f"test-{arm}-{run_seed}")


def village(arm: str = "control", run_seed: int = 7, seed_artifact: bool = False, **overrides: Any) -> Village:
    """A founded village. The planted seed is off unless `seed_artifact` is set."""
    cfg = config(arm, run_seed, **overrides)
    if not seed_artifact:
        cfg.seed_artifact = replace(cfg.seed_artifact, enabled=False)
    v = Village(cfg, KeyedRandom(run_seed), MemoryEventLog())
    v.found()
    return v


def events(v: Village) -> list[dict]:
    return v.ledger.log.events


def answer(**kw: Any) -> dict:
    """A valid raw answer that does nothing unless told to."""
    base = {"goals": [], "journal": {"mode": "keep", "text": ""}, "eat": 0, "learn": 0, "gifts": [], "actions": []}
    base.update(kw)
    return base


def act(type_: str, **kw: Any) -> dict:
    return {"type": type_, "plot": 0, "item": "", "to": "", "text": "", "name": "", **kw}


class Scripted:
    """A runtime that answers from a dict {agent_id: raw answer} per round; others idle."""

    def __init__(self, script: dict[int, dict[str, Any]] | None = None, default: dict | None = None) -> None:
        self.script = script or {}
        self.default = default
        self.contexts: list = []

    def decide_batch(self, contexts):
        self.contexts.extend(contexts)
        out = []
        for c in contexts:
            raw = self.script.get(c.round, {}).get(c.agent_id, self.default if self.default is not None else answer())
            out.append(Reply(c.agent_id, raw=raw))
        return out


def step(v: Village, answers: dict[str, dict] | None = None, default: dict | None = None) -> list:
    """Run one round with the given raw answers (others idle). Returns the contexts built."""
    r = v.world.round + 1
    runtime = Scripted({r: answers or {}}, default)
    RoundRunner(v, runtime).run(r)
    return runtime.contexts


def run_dir(tmp_path: Path, arm: str, run_seed: int, rounds: int = 60, tag: str = "", **overrides: Any) -> Path:
    """A full run through the orchestrator with mock agents and a fixed clock."""
    cfg = config(arm, run_seed, rounds=rounds, **overrides)
    d = tmp_path / f"{arm}-s{run_seed}-{rounds}{tag}"
    RunOrchestrator(cfg, d, clock=FixedClock()).run()
    return d


def run_events(tmp_path: Path, arm: str, run_seed: int, rounds: int = 60, **overrides: Any) -> list[dict]:
    return read_events(run_dir(tmp_path, arm, run_seed, rounds, **overrides) / "events.jsonl")

