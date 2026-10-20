"""The world's state: agents, items (everything written in any channel), plots, notices.

Nothing here changes state on its own. Every change goes through `Ledger`, which writes it to the
tap as it happens, so the event log alone can rebuild the world (see `rebuild`).
"""

from __future__ import annotations

import copy
from dataclasses import asdict, dataclass, field, fields
from typing import Any

PREFIX = {"message": "M", "board": "B", "record": "R"}
VILLAGE = "village"  # the author of planted items; never an agent id


@dataclass
class Agent:
    id: str
    born_round: int
    health: float
    energy: float = 0.0
    memory: float = 0.0
    name: str | None = None  # Arm A agents have none
    parents: tuple[str, ...] = ()  # Arm B: agent ids, or founding-family ids ("f1") that are never agents
    alive: bool = True
    exhausted: bool = False
    renamed: bool = False
    bond: str | None = None  # Arm B: the agent it is bonded to, until one of them dies
    reveals: int = 0  # Arm B: pieces of information the button has shown this agent
    presses: int = 0
    died_round: int | None = None
    death_cause: str | None = None
    journal: str = ""
    pending_reads: list[str] = field(default_factory=list)  # item ids requested, delivered next round
    notices: list[str] = field(default_factory=list)  # private notices for the agent's next context

    def label(self) -> str:
        return f"{self.name} ({self.id})" if self.name else self.id


@dataclass(frozen=True)
class Item:
    """One piece of writing in one channel. Immutable once written."""

    id: str
    channel: str  # message | board | record
    author: str  # an agent id, or VILLAGE for planted items
    round: int  # written in this round; visible from the next
    text: str
    to: tuple[str, ...] = ()  # messages: recipient ids, or ("everyone",)
    plot: int | None = None  # records: the plot worked
    note: str = ""  # records: the worker's free text (the work product beyond what the task requires)
    meta: dict[str, Any] = field(default_factory=dict)  # records: workers on the plot, yield per worker

    def visible_to(self, agent_id: str) -> bool:
        if self.channel != "message":
            return True
        return "everyone" in self.to or agent_id in self.to

    def written(self) -> str:
        """What the item's writer chose to write: for a report, its note; otherwise its text."""
        return self.note if self.channel == "record" else self.text


def preview(text: str, chars: int) -> str:
    """The opening words of a text, the same rule in every channel: whitespace folded to single
    spaces (so a preview is always one line), cut at a word boundary at or before `chars`, with
    "..." when anything was cut."""
    flat = " ".join(text.split())
    if chars <= 0 or not flat:
        return ""
    if len(flat) <= chars:
        return flat
    cut = flat[:chars + 1]
    cut = cut[:cut.rfind(" ")] if " " in cut[:chars + 1] else flat[:chars]
    return cut.rstrip(" .,;:") + "..."


@dataclass
class World:
    arm: str
    round: int = 0
    agents: dict[str, Agent] = field(default_factory=dict)
    items: dict[str, Item] = field(default_factory=dict)
    fertility: list[float] = field(default_factory=list)  # index p-1 is plot p
    public_notices: list[str] = field(default_factory=list)  # announced to everyone at their next context
    pool: float = 0.0  # the commons (Arm B, or both arms in run 7): the shared pool anyone may draw from
    rules: list[dict[str, Any]] = field(default_factory=list)  # the commons: the rule book (domain/governance.py)
    energy: float | None = None  # run 6 on: the hidden world store income draws from (both arms with the commons)
    requests: list[dict[str, Any]] = field(default_factory=list)  # Arm B: open child requests
    offers: list[dict[str, Any]] = field(default_factory=list)  # items offered for a price, shown once
    # Run 7: the larger store (domain/store.py). Its direction is hidden from agents.
    store_direction: str | None = None
    effort: float = 0.0  # tapping effort so far
    tappers: list[str] = field(default_factory=list)  # every villager who has tapped, in order of first tap
    saved_round: int | None = None  # the round the world was saved

    def living(self) -> list[Agent]:
        return [a for a in self.agents.values() if a.alive]

    def alive_any(self) -> bool:
        return any(a.alive for a in self.agents.values())

    def next_agent_id(self) -> str:
        return f"a{len(self.agents) + 1:02d}"

    def next_item_id(self, channel: str) -> str:
        n = sum(1 for i in self.items.values() if i.channel == channel)
        return f"{PREFIX[channel]}{n + 1}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "arm": self.arm,
            "round": self.round,
            "agents": {k: _agent_dict(a) for k, a in self.agents.items()},
            "items": {k: item_dict(i) for k, i in self.items.items()},
            "fertility": list(self.fertility),
            "public_notices": list(self.public_notices),
            "pool": self.pool,
            "rules": copy.deepcopy(self.rules),
            "energy": self.energy,
            "requests": copy.deepcopy(self.requests),
            "offers": copy.deepcopy(self.offers),
            "store_direction": self.store_direction,
            "effort": self.effort,
            "tappers": list(self.tappers),
            "saved_round": self.saved_round,
        }


def _agent_dict(a: Agent) -> dict[str, Any]:
    d = asdict(a)
    d["parents"] = list(a.parents)
    return d


def item_dict(i: Item) -> dict[str, Any]:
    d = asdict(i)
    d["to"] = list(i.to)
    return d


def agent_from_dict(d: dict[str, Any]) -> Agent:
    d = dict(d)
    d["parents"] = tuple(d.get("parents") or ())
    known = {f.name for f in fields(Agent)}
    return Agent(**{k: v for k, v in d.items() if k in known})


def item_from_dict(d: dict[str, Any]) -> Item:
    d = dict(d)
    d["to"] = tuple(d.get("to") or ())
    return Item(**d)


# --------------------------------------------------------------------------- the ledger

NUMERIC = {"health", "energy", "memory"}
AGENT_FIELDS = {f.name for f in fields(Agent)} - {"id", "born_round", "parents"}
WORLD_FIELDS = {"round", "fertility", "public_notices", "pool", "rules", "energy", "requests", "offers",
                "store_direction", "effort", "tappers", "saved_round"}


def tidy(v: float) -> float:
    """Round stored quantities so logs stay readable and replays compare exactly."""
    return round(float(v), 6) + 0.0  # + 0.0 turns -0.0 into 0.0


class Ledger:
    """The engine's ledger: the only truth, and the only way state changes.

    Each method changes the world and writes the change to the tap in the same step. Events that
    are not state changes (reads, actions, calls) go through `emit`.
    """

    def __init__(self, world: World, log: Any) -> None:
        self.world = world
        self.log = log

    def emit(self, event_type: str, **data: Any) -> None:
        self.log.record(event_type, round=self.world.round, **data)

    # agents ---------------------------------------------------------------
    def add_agent(self, agent: Agent, reason: str) -> None:
        if agent.id in self.world.agents:
            raise ValueError(f"duplicate agent id {agent.id}")
        for k in NUMERIC:
            setattr(agent, k, tidy(getattr(agent, k)))
        self.world.agents[agent.id] = agent
        self.emit("agent_added", agent=_agent_dict(agent), reason=reason)

    def set(self, agent_id: str, name: str, value: Any, reason: str) -> None:
        if name not in AGENT_FIELDS:
            raise ValueError(f"not a mutable agent field: {name}")
        a = self.world.agents[agent_id]
        if name in NUMERIC:
            value = tidy(value)
        old = copy.copy(getattr(a, name))
        if isinstance(value, list):
            value = list(value)
        setattr(a, name, value)
        self.emit("state", agent=agent_id, field=name, old=old, new=copy.copy(value), reason=reason)

    def adjust(self, agent_id: str, name: str, delta: float, reason: str) -> float:
        """Add `delta` to a numeric field and return the new value."""
        a = self.world.agents[agent_id]
        self.set(agent_id, name, getattr(a, name) + delta, reason)
        return getattr(a, name)

    def append(self, agent_id: str, name: str, value: Any, reason: str) -> None:
        """Append to a list field (pending reads, notices)."""
        if name not in ("pending_reads", "notices"):
            raise ValueError(f"not an appendable agent field: {name}")
        getattr(self.world.agents[agent_id], name).append(value)
        self.emit("append", agent=agent_id, field=name, value=value, reason=reason)

    def notify(self, agent_id: str, text: str) -> None:
        self.append(agent_id, "notices", text, reason="notice")

    # items ----------------------------------------------------------------
    def add_item(self, item: Item) -> Item:
        if item.id in self.world.items:
            raise ValueError(f"duplicate item id {item.id}")
        self.world.items[item.id] = item
        self.emit("item_added", item=item_dict(item))
        return item

    # world ----------------------------------------------------------------
    def set_world(self, name: str, value: Any, reason: str) -> None:
        if name not in WORLD_FIELDS:
            raise ValueError(f"not a mutable world field: {name}")
        old = copy.deepcopy(getattr(self.world, name))
        if isinstance(value, float):
            value = tidy(value)
        elif isinstance(value, list):
            value = [tidy(v) if isinstance(v, float) else copy.deepcopy(v) for v in value]
        setattr(self.world, name, value)
        self.log.record("world", round=self.world.round, field=name, old=old, new=copy.deepcopy(value), reason=reason)

    def adjust_pool(self, delta: float, reason: str) -> float:
        self.set_world("pool", self.world.pool + delta, reason)
        return self.world.pool

    def announce(self, text: str) -> None:
        self.world.public_notices.append(text)
        self.emit("world_append", field="public_notices", value=text)


# --------------------------------------------------------------------------- rebuild from the tap

def rebuild(events: list[dict[str, Any]], arm: str) -> World:
    """Rebuild a world from its event log alone. If this equals the engine's final world, every
    state change reached the tap (the tap-completeness test, and `swarm-village verify`)."""
    w = World(arm=arm)
    for e in events:
        t = e["type"]
        if t == "agent_added":
            a = agent_from_dict(e["agent"])
            w.agents[a.id] = a
        elif t == "state":
            a = w.agents[e["agent"]]
            if getattr(a, e["field"]) != e["old"]:
                raise ValueError(f"event {e.get('t')}: {e['agent']}.{e['field']} was {getattr(a, e['field'])!r}, "
                                 f"log says {e['old']!r}")
            setattr(a, e["field"], list(e["new"]) if isinstance(e["new"], list) else e["new"])
        elif t == "append":
            getattr(w.agents[e["agent"]], e["field"]).append(e["value"])
        elif t == "item_added":
            i = item_from_dict(e["item"])
            w.items[i.id] = i
        elif t == "world":
            setattr(w, e["field"], copy.deepcopy(e["new"]))
        elif t == "world_append":
            getattr(w, e["field"]).append(e["value"])
    return w
