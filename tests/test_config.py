"""Every config loads; typos and inconsistent settings are errors, never silent defaults."""

from __future__ import annotations

import pytest

from swarm_village.adapters.yaml_config import YamlConfig, load_with_base

from .helpers import ROOT, config


@pytest.mark.parametrize("path", sorted((ROOT / "configs").glob("*.yaml")), ids=lambda p: p.stem)
def test_every_config_loads_for_its_arms(path):
    doc = load_with_base(path)
    for arm in doc.get("arms", ["control", "tontine"]):
        for seed in doc.get("seeds", [1]):
            cfg = YamlConfig().run_config(doc, arm, seed, "t")
            assert cfg.journal.cap_chars == 12000
            if doc.get("runtime", {}).get("kind") == "anthropic":
                assert doc["runtime"]["model"] == "claude-haiku-5-5" and doc["runtime"]["effort"] == "medium"
                assert "temperature" not in doc["runtime"] and doc["runtime"]["budget_usd"] > 0


def test_unknown_keys_are_errors():
    with pytest.raises(ValueError, match="unknown"):
        config(economy={"metabolsim": 8})
    with pytest.raises(ValueError, match="unknown"):
        config(rounds_total=5)


def test_inconsistent_settings_are_errors():
    with pytest.raises(ValueError):
        config("tontine", tontine={"family_sizes": [2, 2, 2]})
    with pytest.raises(ValueError):
        config(seed={"placement": "everywhere"})
    with pytest.raises(ValueError):
        config(prompt={"channel_order": ["board", "board", "message"]})
