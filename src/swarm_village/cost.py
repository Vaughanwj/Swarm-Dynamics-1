"""Cost accounting from the tap's llm_call rows."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from .adapters.storage import read_events

# USD per million tokens, Anthropic first-party API (verified 2026-10-19). Claude Haiku 5.5 has two
# rate cards chosen by prompt length: up to 100K prompt tokens, and above. Cache reads are 0.1x the
# input rate and 5-minute cache writes 1.25x, on whichever card applies.
DEFAULT_PRICES = {
    "claude-haiku-5-5": {"input": 0.10, "output": 0.50, "long_input": 0.50, "long_output": 2.50,
                         "long_threshold": 100_000},
}
PRICE_LINE = 100_000  # the brief's hard line for any one agent prompt


def price_for(prices: dict, model: str) -> dict[str, float]:
    p = dict(prices.get(model) or DEFAULT_PRICES.get(model) or {})
    if not p:
        raise ValueError(f"no price for {model}: add it under `pricing:` in the config")
    return p


def prompt_tokens(row: dict[str, Any]) -> int:
    return (row.get("input_tokens", 0) + row.get("cache_creation_input_tokens", 0)
            + row.get("cache_read_input_tokens", 0))


def call_cost(row: dict[str, Any], p: dict[str, float]) -> float:
    long = "long_threshold" in p and prompt_tokens(row) > p["long_threshold"]
    inp = p["long_input"] if long else p["input"]
    out = p["long_output"] if long else p["output"]
    return (row.get("input_tokens", 0) * inp
            + row.get("cache_creation_input_tokens", 0) * inp * p.get("cache_write_factor", 1.25)
            + row.get("cache_read_input_tokens", 0) * inp * p.get("cache_read_factor", 0.10)
            + row.get("output_tokens", 0) * out) / 1e6


def actual(event_paths: list[Path], prices: dict | None = None) -> dict[str, Any]:
    rows = [e for path in event_paths for e in read_events(path)
            if e["type"] == "llm_call" and not e.get("estimated") and "input_tokens" in e]
    by_model: dict[str, float] = defaultdict(float)
    for r in rows:
        by_model[r["model"]] += call_cost(r, price_for(prices or {}, r["model"]))
    return {
        "calls": len(rows),
        "usd": round(sum(by_model.values()), 4),
        "input_tokens": sum(r.get("input_tokens", 0) for r in rows),
        "cache_creation_input_tokens": sum(r.get("cache_creation_input_tokens", 0) for r in rows),
        "cache_read_input_tokens": sum(r.get("cache_read_input_tokens", 0) for r in rows),
        "output_tokens": sum(r.get("output_tokens", 0) for r in rows),
        "max_prompt_tokens": max((prompt_tokens(r) for r in rows), default=0),
    }
