"""RunOrchestrator: one full run of one arm, and the composition root that wires its adapters."""

from __future__ import annotations

import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

from ..adapters import prompt_text, prompting
from ..adapters.clock import SystemClock
from ..adapters.keyed_rng import KeyedRandom
from ..adapters.mock_agent import MockAgent
from ..adapters.storage import JsonlEventLog, RunDirStorage
from ..domain.config import RunConfig
from ..domain.seed import channel_order
from ..domain.village import Village
from .round_runner import RoundRunner


def build_runtime(cfg: RunConfig, system_text: str, log: Any):
    settings = dict(cfg.runtime)
    kind = settings.pop("kind", "mock")
    if kind == "mock":
        return MockAgent(system_text, log, seed=cfg.seed, log_prompts=cfg.log_prompts)
    if kind == "anthropic":
        from ..adapters.anthropic_haiku import AnthropicHaikuAdapter  # lazy: mock runs need no SDK

        return AnthropicHaikuAdapter(system_text, log, prices=cfg.pricing, log_prompts=cfg.log_prompts, **settings)
    raise ValueError(f"unknown runtime kind: {kind}")


def manifest(cfg: RunConfig, runtime: Any, order: tuple[str, ...]) -> dict[str, Any]:
    m = runtime.manifest() if hasattr(runtime, "manifest") else {"runtime": "mock", "model": "mock"}
    return {**m, "arm": cfg.arm.value, "seed": cfg.seed, "run_id": cfg.run_id, "rounds": cfg.rounds,
            "prompt_version": prompt_text.VERSION, "channel_order": list(order),
            "seed_text_version": cfg.seed_artifact.text_version, "disclose_tap": cfg.prompt.disclose_tap,
            "started": time.strftime("%Y-%m-%dT%H:%M:%S")}


class RunOrchestrator:
    def __init__(self, cfg: RunConfig, run_dir: Path, clock: Any = None, runtime: Any = None) -> None:
        self.cfg = cfg
        self.run_dir = Path(run_dir)
        self.clock = clock or SystemClock()
        self.runtime = runtime  # injected by tests; otherwise built from cfg.runtime

    def run(self) -> Path:
        cfg = self.cfg
        if cfg.prompt.version != prompt_text.VERSION:
            raise ValueError(f"config asks for prompt {cfg.prompt.version}, the code has {prompt_text.VERSION}")
        storage = RunDirStorage(self.run_dir)
        order = channel_order(cfg)
        system_text = prompting.system_prompt(cfg, order)
        storage.save_json("config.json", asdict(cfg))
        storage.save_text("system_prompt.txt", system_text)
        log = JsonlEventLog(self.run_dir / "events.jsonl", cfg.run_id, cfg.arm.value, cfg.seed, self.clock)
        runtime = self.runtime or build_runtime(cfg, system_text, log)
        storage.save_json("manifest.json", manifest(cfg, runtime, order))
        village = Village(cfg, KeyedRandom(cfg.seed), log)
        runner = RoundRunner(village, runtime)
        started = self.clock.now()
        try:
            village.found()
            for r in range(1, cfg.rounds + 1):
                runner.run(r)
                if cfg.snapshot_every and r % cfg.snapshot_every == 0:
                    storage.save_snapshot(r, village.world.to_dict())
                if village.finished():
                    log.record("run_extinct", round=r)
                    break
            log.record("run_end", round=village.world.round, seconds=round(self.clock.now() - started, 1))
        except Exception as e:
            log.record("run_error", round=village.world.round, error=f"{type(e).__name__}: {e}")
            raise
        finally:
            storage.save_final(village.world.to_dict())
            log.close()
        return self.run_dir
