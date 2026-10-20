"""ConfigPort: a YAML document -> RunConfig. Unknown keys are errors, so a typo cannot silently
leave a value at its default."""

from __future__ import annotations

import copy
from dataclasses import fields
from pathlib import Path
from typing import Any

import yaml

from ..domain.config import (Arm, CommsConfig, ControlConfig, EconomyConfig, JournalConfig, PerturbationConfig,
                             PromptConfig, RunConfig, SeedConfig, TontineConfig, WorkConfig)

SECTIONS = {
    "economy": EconomyConfig, "work": WorkConfig, "comms": CommsConfig, "journal": JournalConfig,
    "seed": SeedConfig, "perturbation": PerturbationConfig, "control": ControlConfig,
    "tontine": TontineConfig, "prompt": PromptConfig,
}
FIELD_FOR = {"seed": "seed_artifact"}
SCALARS = ("rounds", "population", "goal_every", "log_prompts", "snapshot_every")
BATCH_KEYS = ("arms", "seeds", "runtime", "pricing", "output_dir", "name")


def load(path: str | Path) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        elif v is not None:
            out[k] = v
    return out


def load_with_base(path: str | Path) -> dict[str, Any]:
    """Load a config, merged over the file named by its `extends` key (relative to it), if any."""
    path = Path(path)
    doc = load(path)
    parent = doc.pop("extends", None)
    return deep_merge(load_with_base(path.parent / parent), doc) if parent else doc


def _build(cls, data: dict[str, Any] | None):
    data = dict(data or {})
    known = {f.name for f in fields(cls)}
    unknown = set(data) - known
    if unknown:
        raise ValueError(f"unknown {cls.__name__} keys: {sorted(unknown)}")
    for f in fields(cls):  # YAML lists -> tuples for tuple-typed fields
        if isinstance(data.get(f.name), list) and "tuple" in str(f.type):
            data[f.name] = tuple(data[f.name])
    return cls(**data)


class YamlConfig:
    def run_config(self, doc: dict[str, Any], arm: str, seed: int, run_id: str) -> RunConfig:
        unknown = set(doc) - set(SECTIONS) - set(SCALARS) - set(BATCH_KEYS)
        if unknown:
            raise ValueError(f"unknown config keys: {sorted(unknown)}")
        kwargs: dict[str, Any] = {k: doc[k] for k in SCALARS if k in doc}
        for key, cls in SECTIONS.items():
            kwargs[FIELD_FOR.get(key, key)] = _build(cls, doc.get(key))
        cfg = RunConfig(arm=Arm(arm), seed=int(seed), run_id=run_id, runtime=dict(doc.get("runtime") or {"kind": "mock"}),
                        pricing=dict(doc.get("pricing") or {}), **kwargs)
        cfg.validate()
        return cfg
