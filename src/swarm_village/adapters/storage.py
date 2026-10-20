"""EventLogPort (the tap, one JSONL file per run) and StoragePort (state snapshots and run files)."""

from __future__ import annotations

import gzip
import json
import threading
from pathlib import Path
from typing import Any

RESERVED = {"t", "ts", "type"}


def _check(data: dict[str, Any]) -> None:
    clash = RESERVED & data.keys()
    if clash:
        raise ValueError(f"event data may not use the reserved keys {sorted(clash)}")


class JsonlEventLog:
    """Append-only. Every event gets a sequence number, a timestamp from the clock, and the run's
    tags. Written and flushed one line at a time, so a crash loses nothing already recorded."""

    def __init__(self, path: Path, run_id: str, arm: str, seed: int, clock: Any) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = self.path.open("w", encoding="utf-8", newline="\n")
        self._lock = threading.Lock()
        self._seq = 0
        self.clock = clock
        self.base = {"run": run_id, "arm": arm, "seed": seed}

    def record(self, event_type: str, **data: Any) -> None:
        _check(data)
        with self._lock:
            self._seq += 1
            row = {"t": self._seq, "ts": self.clock.now(), "type": event_type, **self.base, **data}
            self._fh.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
            self._fh.flush()

    def close(self) -> None:
        with self._lock:
            if not self._fh.closed:
                self._fh.close()


class MemoryEventLog:
    """For tests: keeps events in a list."""

    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def record(self, event_type: str, **data: Any) -> None:
        _check(data)
        self.events.append(json.loads(json.dumps({"t": len(self.events) + 1, "type": event_type, **data}, default=str)))

    def close(self) -> None:
        pass


class RunDirStorage:
    def __init__(self, run_dir: Path) -> None:
        self.dir = Path(run_dir)
        self.dir.mkdir(parents=True, exist_ok=True)

    def save_snapshot(self, round_: int, state: dict[str, Any]) -> None:
        self.save_json(f"snapshots/round-{round_:04d}.json", state)

    def save_final(self, state: dict[str, Any]) -> None:
        self.save_json("final_state.json", state)

    def save_text(self, name: str, text: str) -> None:
        path = self.dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")

    def save_json(self, name: str, data: Any) -> None:
        self.save_text(name, json.dumps(data, indent=2, ensure_ascii=False, default=str))


def read_events(path: Path) -> list[dict[str, Any]]:
    """Read a run's tap, plain (events.jsonl) or gzipped (events.jsonl.gz)."""
    path = Path(path)
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def event_files(batch_dir: Path) -> list[Path]:
    b = Path(batch_dir)
    return sorted(list(b.glob("*/events.jsonl")) + list(b.glob("*/events.jsonl.gz")))
