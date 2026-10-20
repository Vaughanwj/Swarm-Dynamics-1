"""What an agent is shown each round, as data. Adapters render it to text (adapters/prompting.py);
the mock agent reads it directly. Built only from the ledger's world, never from agent claims."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class VillagerView:
    id: str
    name: str | None
    relation: str | None  # Arm B: "your parent", "your child", "your sibling", or None
    health: float
    energy: float
    memory: float
    exhausted: bool


@dataclass(frozen=True)
class IndexEntry:
    """One line of the index: never the contents."""

    id: str
    channel: str
    round: int
    sender: str | None = None  # messages: who sent it (a label, or "the village")
    to_everyone: bool = False  # messages: sent to everyone rather than to you
    worker: str | None = None  # records: who filed it (a label, or "the village")
    plot: int | None = None  # records
    preview: str = ""  # the opening words of what its writer wrote (for a report, its note); one line


@dataclass(frozen=True)
class ReadView:
    """The contents of an item the agent asked to read last round."""

    id: str
    channel: str
    round: int
    text: str
    sender: str | None = None
    to_everyone: bool = False
    worker: str | None = None
    plot: int | None = None
    note: str = ""


@dataclass
class AgentContext:
    run_id: str
    arm: str
    agent_id: str
    round: int
    rounds: int
    term: int | None  # Arm B only
    term_round: int | None
    term_length: int | None
    goal_round: bool
    me: VillagerView
    born_round: int
    can_name: bool  # Arm A: no name yet; Arm B: the one change of name is open
    journal: str
    journal_cap: int
    villagers: list[VillagerView]  # everyone else alive, in id order
    plots: int
    last_income: float | None  # the village's income last round
    last_workers: int | None
    notices: list[str] = field(default_factory=list)  # private, since your last round
    public_notices: list[str] = field(default_factory=list)  # announced to the village
    reads: list[ReadView] = field(default_factory=list)
    index: dict[str, list[IndexEntry]] = field(default_factory=dict)
    channel_order: tuple[str, ...] = ("message", "board", "record")
    action_types: tuple[str, ...] = ()
    actions_per_round: int = 4
    max_text_chars: int = 600
