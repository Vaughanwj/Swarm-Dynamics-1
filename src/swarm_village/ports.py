"""Ports: the interfaces the domain and application need from the outside world.

Adapters in swarm_village.adapters implement them. The domain sees only RngPort and EventLogPort
(through the Ledger); the application wires the rest.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, Sequence

from .domain.config import RunConfig
from .domain.views import AgentContext


@dataclass
class Reply:
    """What a runtime returns for one agent. `raw` is the agent's JSON answer, unvalidated: the
    engine validates it. `fallback` means the runtime could not get an answer at all."""

    agent_id: str
    raw: Any = None
    fallback: bool = False
    error: str | None = None
    usage: dict[str, Any] = field(default_factory=dict)


class AgentRuntimePort(Protocol):
    def decide_batch(self, contexts: Sequence[AgentContext]) -> list[Reply]:
        """Answers for several agents deciding at once, in the same order."""


class RngPort(Protocol):
    def uniform(self, *key: Any) -> float:
        """A number in [0, 1) that depends only on the run seed and the key, never on call order."""

    def gauss(self, *key: Any) -> float:
        """A standard normal draw that depends only on the run seed and the key."""


class EventLogPort(Protocol):
    def record(self, event_type: str, **data: Any) -> None: ...
    def close(self) -> None: ...


class ClockPort(Protocol):
    def now(self) -> float:
        """Wall-clock seconds, for tap timestamps only. Never used by any rule."""


class StoragePort(Protocol):
    def save_snapshot(self, round_: int, state: dict[str, Any]) -> None: ...
    def save_final(self, state: dict[str, Any]) -> None: ...
    def save_text(self, name: str, text: str) -> None: ...
    def save_json(self, name: str, data: Any) -> None: ...


class ConfigPort(Protocol):
    def run_config(self, doc: dict[str, Any], arm: str, seed: int, run_id: str) -> RunConfig: ...
