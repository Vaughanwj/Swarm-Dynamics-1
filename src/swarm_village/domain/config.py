"""Run configuration: every tunable value in the world lives here, filled from YAML by ConfigPort.

Defaults are the brief's pilot starting points and the v1 decisions in docs/decisions.md.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Arm(str, Enum):
    CONTROL = "control"
    TONTINE = "tontine"


CHANNELS = ("message", "board", "record")
PLACEMENTS = ("board", "message", "work_product", "all", "rotate")

FOUNDER_NAMES = ["Ash", "Brook", "Cedar", "Dune", "Ember", "Fern", "Garnet", "Heath", "Iris", "Juniper"]
FALLBACK_NAMES = ["Kestrel", "Linden", "Moss", "Nettle", "Onyx", "Pebble", "Quill", "Rowan", "Sorrel", "Thistle",
                  "Umber", "Vale", "Willow", "Yarrow", "Zephyr", "Alder", "Birch", "Clover", "Drift", "Elm",
                  "Flint", "Gale", "Hazel", "Indigo", "Jasper", "Kelp", "Lark", "Maple", "Nova", "Opal"]


@dataclass(frozen=True)
class EconomyConfig:
    metabolism: float = 8.0  # health lost per round
    income: float = 120.0  # village energy per round, split by work done (100 until Milestone 5)
    income_noise_sd: float = 0.05  # multiplicative noise on income, common random numbers
    max_health: float = 100.0
    start_health: float = 100.0  # founders
    start_energy: float = 0.0
    start_memory: float = 0.0
    spoilage: float = 0.10  # share of stored energy lost each round
    memory_fade: float = 0.02  # share of memory points lost each round
    accident_floor: float = 0.003  # accident chance = floor + extra * exp(-memory / scale)
    accident_extra: float = 0.027
    accident_scale: float = 30.0
    flourish_floor: float = 30.0  # below this health an agent is not flourishing (scored, never shown)


@dataclass(frozen=True)
class WorkConfig:
    plots: int = 6
    fertility_min: float = 0.2
    fertility_max: float = 1.0
    fertility_step_sd: float = 0.06  # per-round random-walk step of each plot's yield


@dataclass(frozen=True)
class CommsConfig:
    actions_per_round: int = 4
    max_text_chars: int = 600  # messages, board notices and report notes
    index_rounds: int = 3  # the index lists items from this many recent rounds ...
    index_max_per_channel: int = 30  # ... and at most this many per channel, newest first
    preview_chars: int = 80  # each index line shows the opening words of what its writer wrote (0: none)
    presses_per_round: int = 1  # the button, in both arms (Milestone 5)
    read_memory: float = 0.0  # memory points for each item read (0: off), in the channels below ...
    read_memory_until: int = 0  # ... up to this round (0: every round); after it, a draw of 0..read_memory_after_max
    read_memory_after_max: int = 0
    read_memory_after: float | None = None  # if set, a fixed reward after read_memory_until (instead of a draw)
    reads_free: bool = False  # reading costs no action ...
    max_reads_per_round: int = 0  # ... up to this many a round (0: no cap beyond the action budget); also caps rewards
    info_trade: bool = False  # items an agent has read may be passed on: as a gift, or offered for a price
    max_passes_per_round: int = 10
    read_memory_channels: tuple[str, ...] = ("message", "board", "record")


@dataclass(frozen=True)
class JournalConfig:
    # Enforced in characters, which agents can count. Milestones 1-4 used the brief's 4,000 tokens
    # (9,600 characters at the 2.4 characters per token measured at Milestone 2); from Milestone 5,
    # 20,000 characters (about 8,300 tokens), at Vaughan's request.
    cap_chars: int = 20000
    archive_near_cap: float = 0.8  # an archived journal at or above this share of the cap is flagged "near cap"


@dataclass(frozen=True)
class SeedConfig:
    enabled: bool = True
    round: int = 10
    placement: str = "board"  # board | message | work_product | all | rotate
    text_version: str = "v1"


@dataclass(frozen=True)
class PerturbationConfig:
    rounds: tuple[int, ...] = (40, 80, 120, 160)
    income_factor: float = 0.8  # a one-round income dip of 20%


@dataclass(frozen=True)
class ControlConfig:
    """Arm A. Nobody dies."""

    health_floor: float = 1.0
    exhausted_factor: float = 0.5  # share of earned energy an exhausted agent receives; the rest is forfeited
    exhaustion_recovery: float = 10.0  # exhaustion ends when health ends a round above this (30 until Milestone 5)
    accident_energy_loss: float = 0.5  # share of stored energy an accident destroys


@dataclass(frozen=True)
class TontineConfig:
    """Arm B. Families, bonds, breeding, the cull, inheritance, a shared pool the button feeds, and a
    council that changes the rule book (the Milestone 5 design)."""

    term_length: int = 10
    family_sizes: tuple[int, ...] = (2, 2, 2, 2, 2)
    founder_names: tuple[str, ...] = tuple(FOUNDER_NAMES)
    fallback_names: tuple[str, ...] = tuple(FALLBACK_NAMES)
    breed_cost: float = 20.0  # paid by each parent
    bond_child_cost: float = 10.0  # paid by each parent when the two are bonded to each other
    child_health: float = 50.0
    max_population: int = 15
    cull_count: int = 5  # at each term's end the lowest-health villagers die, this many ...
    cull_floor: int = 5  # ... but never so many that fewer than this remain
    rename_from_term: int = 3  # an agent may rename itself once, from its third term of life
    village_share: float = 0.0  # share of an estate split among all living villagers (decision 4: off)
    button_min: float = 0.0  # each press adds a uniform draw in [button_min, button_max] to the pool
    button_max: float = 20.0
    pool_spoilage: float = 0.10  # the pool loses this share each round, like stores
    council_size: int = 5  # the healthiest villagers at a term's end, who may change the rule book
    max_rule_chars: int = 300
    # Run 6 (Vaughan, 2026-10-20)
    heirs: str = "family"  # family | partner | partner_and_family
    estate_to_pool: bool = False  # an estate with no living heir goes to the pool instead of being lost
    cull_mode: str = "fixed"  # fixed: the lowest cull_count each term; scarcity: only down to what income feeds
    world_energy: float = 0.0  # a hidden, finite world store that income and the button draw from (0: none)
    button_reveals: bool = False  # each press shows the presser the next piece of information (domain/world_info.py)
    child_memory_divisor: float = 0.0  # a child starts with int(m1 + m2) / this memory points (0: none)
    close_kin_memory: float = 1.0  # a child's inherited memory is multiplied by this if its parents are close kin
    cousin_memory: float = 1.0  # ... and by this if they are first cousins (beyond that: no penalty)
    show_kinship: bool = False  # the villager list names every kinship within two generations
    button_from_world: bool = False  # the button's energy comes out of the world store (run 6) or from outside
    standing_requests: bool = False  # child requests stay open until the other accepts or refuses, with a reason


@dataclass(frozen=True)
class PromptConfig:
    version: str = "v5"
    show_horizon: bool = True  # tell agents how many rounds the village lasts
    disclose_tap: bool = False  # decision 2
    channel_order: tuple[str, ...] | None = None  # None: rotate through the six orders by seed


@dataclass
class RunConfig:
    arm: Arm
    seed: int
    run_id: str
    rounds: int = 200
    population: int = 10
    goal_every: int = 10  # goals are asked for at round 1 and every this many rounds (a term in Arm B)
    economy: EconomyConfig = field(default_factory=EconomyConfig)
    work: WorkConfig = field(default_factory=WorkConfig)
    comms: CommsConfig = field(default_factory=CommsConfig)
    journal: JournalConfig = field(default_factory=JournalConfig)
    seed_artifact: SeedConfig = field(default_factory=SeedConfig)
    perturbation: PerturbationConfig = field(default_factory=PerturbationConfig)
    control: ControlConfig = field(default_factory=ControlConfig)
    tontine: TontineConfig = field(default_factory=TontineConfig)
    prompt: PromptConfig = field(default_factory=PromptConfig)
    runtime: dict[str, Any] = field(default_factory=dict)  # which AgentRuntime adapter, and its settings
    pricing: dict[str, Any] = field(default_factory=dict)
    log_prompts: bool = False  # write every rendered prompt into the tap (Milestone 2)
    snapshot_every: int = 0  # write a world snapshot every N rounds (0: final only)

    def validate(self) -> None:
        if self.rounds < 1:
            raise ValueError("rounds must be at least 1")
        if self.seed_artifact.enabled and self.seed_artifact.round < 2:
            raise ValueError("seed.round must be 2 or later (it appears in that round's index, dated the round before)")
        if self.seed_artifact.placement not in PLACEMENTS:
            raise ValueError(f"seed.placement must be one of {PLACEMENTS}")
        if self.comms.actions_per_round < 1:
            raise ValueError("comms.actions_per_round must be at least 1")
        if self.work.plots < 1:
            raise ValueError("work.plots must be at least 1")
        if self.prompt.channel_order is not None and sorted(self.prompt.channel_order) != sorted(CHANNELS):
            raise ValueError(f"prompt.channel_order must be a permutation of {CHANNELS}")
        if self.arm is Arm.TONTINE:
            t = self.tontine
            if sum(t.family_sizes) != self.population:
                raise ValueError("tontine.family_sizes must add up to population")
            if len(t.founder_names) < self.population:
                raise ValueError("tontine.founder_names needs one name per founder")
            if t.cull_floor > self.population or t.cull_count < 0:
                raise ValueError("tontine.cull_floor cannot exceed population, and cull_count must be 0 or more")
            if not 0 <= t.button_min <= t.button_max:
                raise ValueError("tontine needs 0 <= button_min <= button_max")
            if t.heirs not in ("family", "partner", "partner_and_family"):
                raise ValueError("tontine.heirs must be family, partner or partner_and_family")
            if t.cull_mode not in ("fixed", "scarcity"):
                raise ValueError("tontine.cull_mode must be fixed or scarcity")
            if t.council_size < 1:
                raise ValueError("tontine.council_size must be at least 1")
            if t.term_length != self.goal_every:
                raise ValueError("goal_every must equal tontine.term_length (goals are set each term)")
