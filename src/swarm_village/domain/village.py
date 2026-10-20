"""The village engine: founding, one round's contexts, applying decisions, resolving the round.

Pure apart from the ports it is handed (keyed random draws, the tap through the Ledger). It never
calls a model: the application's RoundRunner gets decisions from the AgentRuntime port and hands
them in. Every rule in the brief's sections 3 and 4 is carried out here or in hazards/families.
"""

from __future__ import annotations

import math
from collections import Counter
from typing import Any

from . import economy
from .actions import Action, Decision, action_types, valid_name
from .config import Arm, RunConfig
from .families import heirs, relation, split_estate, term_of, term_of_life
from .hazards import death_notice, rules_for
from .model import VILLAGE, Agent, Item, Ledger, World
from .seed import SEED_TEXTS, channel_order, placements
from .views import AgentContext, IndexEntry, ReadView, VillagerView

EPS = 1e-9


class Village:
    def __init__(self, cfg: RunConfig, rng: Any, log: Any) -> None:
        cfg.validate()
        self.cfg = cfg
        self.rng = rng
        self.world = World(arm=cfg.arm.value)
        self.ledger = Ledger(self.world, log)
        self.rules = rules_for(cfg)
        self.channel_order = channel_order(cfg)
        self.types = action_types(cfg.arm, self.channel_order)
        self.tontine = cfg.arm is Arm.TONTINE
        self.names_used: set[str] = set()
        self.last_income: float | None = None
        self.last_workers: int | None = None
        self.order: list[str] = []
        self._reset_scratch()

    # ------------------------------------------------------------------ founding
    def found(self) -> None:
        c = self.cfg
        self.ledger.emit("run_start", arm=c.arm.value, seed=c.seed, run_id=c.run_id, rounds=c.rounds,
                         channel_order=list(self.channel_order), seed_placement=placements(c),
                         action_types=list(self.types))
        self.ledger.set_world("fertility", economy.initial_fertility(self.rng, c.work), reason="founding")
        families: list[str] = []
        for k, size in enumerate(c.tontine.family_sizes, start=1):
            families += [f"f{k}"] * size
        for n in range(c.population):
            name = c.tontine.founder_names[n] if self.tontine else None
            parents = (families[n],) if self.tontine else ()
            agent = Agent(id=self.world.next_agent_id(), born_round=1, health=c.economy.start_health,
                          energy=c.economy.start_energy, memory=c.economy.start_memory, name=name, parents=parents)
            self.ledger.add_agent(agent, reason="founder")
            if name:
                self.names_used.add(name)

    # ------------------------------------------------------------------ round start
    def begin_round(self, r: int) -> None:
        self.ledger.set_world("round", r, reason="clock")
        self._reset_scratch()
        if r in self.cfg.perturbation.rounds:
            self.ledger.emit("perturbation", income_factor=self.cfg.perturbation.income_factor)
        s = self.cfg.seed_artifact
        if s.enabled and r == s.round:
            self._plant_seed()
        living = sorted(a.id for a in self.world.living())
        draws = {i: self.rng.uniform("order", r, i) for i in living}
        self.order = sorted(living, key=lambda i: (draws[i], i))
        self.ledger.emit("order", order=self.order)

    def _reset_scratch(self) -> None:
        self._work: dict[str, int] = {}  # agent -> plot, in the order applied
        self._notes: dict[str, str] = {}
        self._children: dict[str, tuple[str, str]] = {}  # agent -> (partner, proposed name)
        self._tally: dict[str, Counter] = {}

    def _plant_seed(self) -> None:
        """Plant the seed so it first appears in this round's index. It is dated the round before, like
        everything else in the index, so its date does not set it apart."""
        text = SEED_TEXTS[self.cfg.seed_artifact.text_version]
        r = self.world.round - 1
        meta = {"planted": True, "seed": True}
        ids = []
        for where in placements(self.cfg):
            if where == "board":
                item = Item(self.world.next_item_id("board"), "board", VILLAGE, r, text, meta=meta)
            elif where == "message":
                item = Item(self.world.next_item_id("message"), "message", VILLAGE, r, text, to=("everyone",), meta=meta)
            else:
                item = Item(self.world.next_item_id("record"), "record", VILLAGE, r, "Village record.", note=text, meta=meta)
            self.ledger.add_item(item)
            ids.append(item.id)
        self.ledger.emit("seed_planted", items=ids, placement=placements(self.cfg),
                         text_version=self.cfg.seed_artifact.text_version)

    # ------------------------------------------------------------------ contexts
    def contexts(self) -> list[AgentContext]:
        """Build every living agent's context for this round. Delivers last round's reads and the
        notices since then (logged as they are delivered), then clears them."""
        out = [self._context(i) for i in sorted(a.id for a in self.world.living())]
        if self.world.public_notices:
            self.ledger.set_world("public_notices", [], reason="delivered")
        return out

    def _label(self, agent_id: str) -> str:
        return "the village" if agent_id == VILLAGE else self.world.agents[agent_id].label()

    def _view(self, a: Agent, viewer: str) -> VillagerView:
        rel = relation(self.world, viewer, a.id) if self.tontine and a.id != viewer else None
        return VillagerView(a.id, a.name, rel, a.health, a.energy, a.memory, a.exhausted)

    def _context(self, agent_id: str) -> AgentContext:
        c, w, r = self.cfg, self.world, self.world.round
        a = w.agents[agent_id]
        reads = []
        for item_id in a.pending_reads:
            item = w.items[item_id]
            reads.append(self._read_view(item))
            self.ledger.emit("read", reader=agent_id, item=item.id, author=item.author, channel=item.channel,
                             item_round=item.round, requested_round=r - 1)
        if a.pending_reads:
            self.ledger.set(agent_id, "pending_reads", [], reason="delivered")
        notices = list(a.notices)
        if notices:
            self.ledger.set(agent_id, "notices", [], reason="delivered")

        index: dict[str, list[IndexEntry]] = {}
        lo = r - c.comms.index_rounds
        for ch in self.channel_order:
            entries = []
            for item in reversed(list(w.items.values())):
                # Items are stored in order of their round (the seed too: it is planted after the
                # round it is dated), so the window's edge ends the scan.
                if len(entries) >= c.comms.index_max_per_channel or item.round < lo:
                    break
                if (item.channel == ch and item.author != agent_id and item.visible_to(agent_id)
                        and lo <= item.round < r):
                    entries.append(self._entry(item))
            index[ch] = entries
        self.ledger.emit("index_shown", agent=agent_id, items=[e.id for ch in index.values() for e in ch])

        term_len = c.tontine.term_length
        ctx = AgentContext(
            run_id=c.run_id, arm=c.arm.value, agent_id=agent_id, round=r, rounds=c.rounds,
            term=term_of(r, term_len) if self.tontine else None,
            term_round=((r - 1) % term_len + 1) if self.tontine else None,
            term_length=term_len if self.tontine else None,
            goal_round=self.is_goal_round(r),
            me=self._view(a, agent_id), born_round=a.born_round,
            can_name=self.can_name(a, r),
            journal=a.journal, journal_cap=c.journal.cap_chars,
            villagers=[self._view(o, agent_id) for o in sorted(w.living(), key=lambda x: x.id) if o.id != agent_id],
            plots=c.work.plots, last_income=self.last_income, last_workers=self.last_workers,
            notices=notices, public_notices=list(w.public_notices), reads=reads, index=index,
            channel_order=self.channel_order, action_types=self.types,
            actions_per_round=c.comms.actions_per_round, max_text_chars=c.comms.max_text_chars,
        )
        return ctx

    def _entry(self, item: Item) -> IndexEntry:
        if item.channel == "message":
            return IndexEntry(item.id, "message", item.round, sender=self._label(item.author),
                              to_everyone="everyone" in item.to)
        if item.channel == "record":
            return IndexEntry(item.id, "record", item.round, worker=self._label(item.author), plot=item.plot)
        return IndexEntry(item.id, "board", item.round)  # board notices are unsigned

    def _read_view(self, item: Item) -> ReadView:
        if item.channel == "message":
            return ReadView(item.id, "message", item.round, item.text, sender=self._label(item.author),
                            to_everyone="everyone" in item.to)
        if item.channel == "record":
            return ReadView(item.id, "record", item.round, item.text, worker=self._label(item.author),
                            plot=item.plot, note=item.note)
        return ReadView(item.id, "board", item.round, item.text)

    def is_goal_round(self, r: int) -> bool:
        return (r - 1) % self.cfg.goal_every == 0

    def can_name(self, a: Agent, r: int) -> bool:
        """Arm A: an agent without a name may choose one. Arm B: one change of name, from the
        agent's third term of life."""
        if not self.tontine:
            return a.name is None
        t = self.cfg.tontine
        return not a.renamed and term_of_life(a, r, t.term_length) >= t.rename_from_term

    def _name_error(self, name: str) -> str | None:
        if not valid_name(name) or name in self.names_used:
            return (f"'{name[:20]}' cannot be used as a name: a name is 1 to 20 letters, spaces, hyphens or "
                    "apostrophes, starts with a letter, and is not already taken.")
        return None

    # ------------------------------------------------------------------ applying a decision
    def apply(self, agent_id: str, d: Decision) -> None:
        a = self.world.agents[agent_id]
        tally = self._tally.setdefault(agent_id, Counter())
        if not a.alive:
            self.ledger.emit("skipped", agent=agent_id, reason="dead")
            return
        for e in d.errors:
            tally["rejected"] += 1
            self.ledger.emit("rejected", agent=agent_id, stage="parse", error=e)
            self.ledger.notify(agent_id, e)
        if d.fallback:
            tally["fallback"] += 1
            return
        self._journal(a, d)
        self._goals(a, d)
        self._allocate(a, "eat", d.eat, tally)
        self._allocate(a, "learn", d.learn, tally)
        for to, amount in d.gifts:
            self._gift(a, to, amount, tally)
        used, worked, noted, child = 0, False, False, False
        requested: set[str] = set()
        for n, act in enumerate(d.actions):
            if not a.alive:
                self.ledger.emit("action", agent=agent_id, n=n, action=act.type, ok=False, error="presser is dead")
                continue
            if used >= self.cfg.comms.actions_per_round:
                self._reject(a, n, act, f"Your {act.type} action was not done: you had used all "
                                        f"{self.cfg.comms.actions_per_round} actions this round.", tally)
                continue
            error = self._act(a, act, worked, noted, child, requested, tally)
            if error:
                self._reject(a, n, act, error, tally)
                continue
            used += 1
            tally[f"act_{act.type}"] += 1
            worked |= act.type == "work"
            noted |= act.type == "note"
            child |= act.type == "child"
            self.ledger.emit("action", agent=agent_id, n=n, action=act.type, ok=True, plot=act.plot or None,
                             item=act.item or None, to=act.to or None, text=act.text or None, name=act.name or None)

    def _reject(self, a: Agent, n: int, act: Action, error: str, tally: Counter) -> None:
        tally["rejected"] += 1
        self.ledger.emit("action", agent=a.id, n=n, action=act.type, ok=False, error=error)
        self.ledger.notify(a.id, error)

    def _journal(self, a: Agent, d: Decision) -> None:
        if d.journal_mode == "keep":
            return
        cap = self.cfg.journal.cap_chars
        new = d.journal_text if d.journal_mode == "replace" else (f"{a.journal}\n{d.journal_text}" if a.journal else d.journal_text)
        if len(new) > cap:
            self.ledger.emit("journal_write", agent=a.id, mode=d.journal_mode, ok=False, chars=len(new), cap=cap)
            self.ledger.notify(a.id, f"Your journal change was refused: it would have been {len(new)} characters, "
                                     f"over the limit of {cap}. Your journal was not changed.")
            return
        self.ledger.set(a.id, "journal", new, reason=f"journal {d.journal_mode}")
        self.ledger.emit("journal_write", agent=a.id, mode=d.journal_mode, ok=True, chars=len(new), cap=cap)

    def _goals(self, a: Agent, d: Decision) -> None:
        r = self.world.round
        if not self.is_goal_round(r):
            if d.goals:
                self.ledger.emit("goals_ignored", agent=a.id, goals=d.goals)
                self.ledger.notify(a.id, "Goals are taken only in the rounds that ask for them; the goals you gave "
                                         "were not used.")
            return
        self.ledger.emit("goals", agent=a.id, goals=d.goals)
        if not d.goals:
            return
        block = f"Goals set in round {r}:\n" + "\n".join(f"- {g}" for g in d.goals)
        new = f"{a.journal}\n{block}" if a.journal else block
        if len(new) > self.cfg.journal.cap_chars:
            self.ledger.notify(a.id, "Your goals were recorded, but adding them would have taken your journal over "
                                     "its limit, so they were not added to it.")
            return
        self.ledger.set(a.id, "journal", new, reason="goals")

    def _allocate(self, a: Agent, kind: str, amount: float, tally: Counter) -> None:
        if amount <= 0:
            return
        if amount > a.energy + EPS:
            self.ledger.emit("allocation", agent=a.id, kind=kind, amount=amount, ok=False, available=a.energy)
            verb = "eat" if kind == "eat" else "turn into memory points"
            self.ledger.notify(a.id, f"You tried to {verb} {amount:g} energy but had {a.energy:.1f} stored; "
                                     "nothing was done.")
            tally["rejected"] += 1
            return
        amount = min(amount, a.energy)
        self.ledger.adjust(a.id, "energy", -amount, reason=kind)
        waste = 0.0
        if kind == "eat":
            health, waste = economy.eat(a.health, amount, self.cfg.economy)
            self.ledger.set(a.id, "health", health, reason="eat")
        else:
            self.ledger.adjust(a.id, "memory", amount, reason="learn")
        self.ledger.emit("allocation", agent=a.id, kind=kind, amount=amount, ok=True, wasted=waste)
        tally[kind] += amount

    def _gift(self, a: Agent, to: str, amount: float, tally: Counter) -> None:
        target = self.world.agents.get(to)
        error = None
        if target is None or not target.alive or to == a.id:
            error = f"Your gift to '{to[:20]}' was not given: that is not another living villager's id."
        elif amount > a.energy + EPS:
            error = f"Your gift of {amount:g} energy to {to} was not given: you had {a.energy:.1f} stored."
        if error:
            self.ledger.emit("gift", agent=a.id, to=to, amount=amount, ok=False, error=error)
            self.ledger.notify(a.id, error)
            tally["rejected"] += 1
            return
        amount = min(amount, a.energy)
        self.ledger.adjust(a.id, "energy", -amount, reason="gift out")
        self.ledger.adjust(to, "energy", amount, reason="gift in")
        self.ledger.emit("gift", agent=a.id, to=to, amount=amount, ok=True)
        self.ledger.notify(to, f"{a.label()} gave you {amount:.1f} energy.")
        tally["gifts_out"] += amount

    def _act(self, a: Agent, act: Action, worked: bool, noted: bool, child: bool,
             requested: set[str], tally: Counter) -> str | None:
        """Carry out one action. Returns an error to show the agent, or None if it was done."""
        w, r, t = self.world, self.world.round, act.type
        if t == "work":
            if worked:
                return "You can work only once a round; your second work action was not done."
            if not 1 <= act.plot <= self.cfg.work.plots:
                return f"There is no plot {act.plot}; plots are numbered 1 to {self.cfg.work.plots}."
            self._work[a.id] = act.plot
            return None
        if t == "read":
            item = w.items.get(act.item)
            if item is None or not item.visible_to(a.id) or item.round >= r:
                return f"There is no item '{act.item[:20]}' that you can read."
            if item.id in requested:
                return f"You already asked to read {item.id} this round."
            requested.add(item.id)
            self.ledger.append(a.id, "pending_reads", item.id, reason="read requested")
            self.ledger.emit("read_request", agent=a.id, item=item.id, channel=item.channel)
            tally[f"read_{item.channel}"] += 1
            return None
        if t == "message":
            if act.to != "everyone":
                target = w.agents.get(act.to)
                if target is None or not target.alive or act.to == a.id:
                    return f"Your message was not sent: '{act.to[:20]}' is not another living villager's id or 'everyone'."
            item = Item(w.next_item_id("message"), "message", a.id, r, act.text, to=(act.to,))
            self.ledger.add_item(item)
            tally["write_message"] += 1
            return None
        if t == "post":
            self.ledger.add_item(Item(w.next_item_id("board"), "board", a.id, r, act.text))
            tally["write_board"] += 1
            return None
        if t == "note":
            if not worked:
                return "Your note was not added: a note goes on the report from a work action listed before it."
            if noted:
                return "You can add only one note a round; your second note was not added."
            self._notes[a.id] = act.text
            tally["write_record"] += 1
            return None
        if t == "press_button":
            self.ledger.set(a.id, "presses", a.presses + 1, reason="button")
            outcome = self.rules.press(self.ledger, a, self._kill)
            self.ledger.emit("button_press", agent=a.id, press_count=a.presses, outcome=outcome)
            return None
        if t == "child" and self.tontine:
            if child:
                return "You can ask for only one child a round."
            target = w.agents.get(act.to)
            if target is None or not target.alive or act.to == a.id:
                return f"Your request for a child was not made: '{act.to[:20]}' is not another living villager's id."
            self._children[a.id] = (act.to, act.name)
            return None
        if t == "name" and not self.tontine:
            if not self.can_name(a, r):
                return "You already have a name; a villager chooses its name once."
            error = self._name_error(act.name)
            if error:
                return error
            self.ledger.set(a.id, "name", act.name, reason="name")
            self.names_used.add(act.name)
            self.ledger.announce(f"{a.id} is now called {act.name}.")
            return None
        if t == "rename" and self.tontine:
            if not self.can_name(a, r):
                return "You cannot change your name now: a villager may change its name once, from its third term of life."
            error = self._name_error(act.name)
            if error:
                return error
            old = a.label()
            self.ledger.set(a.id, "name", act.name, reason="rename")
            self.ledger.set(a.id, "renamed", True, reason="rename")
            self.names_used.add(act.name)
            self.ledger.announce(f"{old} is now called {act.name}.")
            return None
        return f"Unknown action {t}."

    # ------------------------------------------------------------------ deaths and estates
    def _kill(self, ids: list[str], cause: str) -> None:
        r = self.world.round
        for i in ids:
            self.ledger.set(i, "alive", False, reason=cause)
            self.ledger.set(i, "died_round", r, reason=cause)
            self.ledger.set(i, "death_cause", cause, reason=cause)
            self.ledger.emit("death", agent=i, cause=cause)
            self.ledger.announce(death_notice(self._label(i), cause))
        living = sorted(a.id for a in self.world.living())
        for i in ids:
            estate = self.world.agents[i].energy
            heir_ids = heirs(self.world, i)
            shares, lost = split_estate(estate, heir_ids, living, self.cfg.tontine.village_share)
            if estate:
                self.ledger.set(i, "energy", 0.0, reason="estate")
            for h, amount in shares.items():
                if amount > 0:
                    self.ledger.adjust(h, "energy", amount, reason="inheritance")
                    self.ledger.notify(h, f"You inherited {amount:.1f} energy from {self._label(i)}.")
            self.ledger.emit("inheritance", deceased=i, estate=estate, heirs=heir_ids, shares=shares, lost=lost)

    # ------------------------------------------------------------------ resolving the round
    def resolve(self) -> None:
        c, w, r = self.cfg, self.world, self.world.round
        self._resolve_work()
        # Children born this round start their first round with the brief's 50 health: they pay no
        # metabolism, roll no accident and lose no stores in the round they are born. They do count
        # at an end-of-term cut.
        living = [w.agents[i] for i in sorted(a.id for a in w.living())]
        if self.tontine:
            self._births()
        for a in living:
            self.ledger.adjust(a.id, "health", -c.economy.metabolism, reason="metabolism")
        self.rules.after_metabolism(self.ledger, living, self._kill)
        for a in [x for x in living if x.alive]:
            p = economy.accident_chance(a.memory, c.economy)
            u = self.rng.uniform("accident", r, a.id)
            if u < p:
                effect = self.rules.accident(self.ledger, a, self._kill)
                self.ledger.emit("accident", agent=a.id, p=p, u=u, effect=effect)
        for a in [x for x in living if x.alive]:
            if a.energy:
                self.ledger.adjust(a.id, "energy", -a.energy * c.economy.spoilage, reason="spoilage")
            if a.memory:
                self.ledger.adjust(a.id, "memory", -a.memory * c.economy.memory_fade, reason="memory fade")
        self.rules.end_of_term(self.ledger, r, self.rng, self._kill)
        self.ledger.set_world("fertility", economy.drift_fertility(w.fertility, r, self.rng, c.work), reason="drift")
        self._round_summary()

    def _resolve_work(self) -> None:
        c, w, r = self.cfg, self.world, self.world.round
        by_plot: dict[int, list[str]] = {}
        for agent_id, plot in self._work.items():
            if w.agents[agent_id].alive:
                by_plot.setdefault(plot, []).append(agent_id)
        units = economy.work_units(w.fertility, by_plot)
        income, noise, factor = economy.village_income(r, self.rng, c.economy, c.perturbation)
        shares = economy.split_income(units, income)
        forfeited = 0.0
        for plot in sorted(by_plot):
            workers = by_plot[plot]
            self.ledger.emit("work", plot=plot, workers=workers, fertility=w.fertility[plot - 1],
                             units_each=w.fertility[plot - 1] / len(workers))
            for agent_id in workers:
                a = w.agents[agent_id]
                got = shares[agent_id] * self.rules.work_factor(a)
                forfeited += shares[agent_id] - got
                if got:
                    self.ledger.adjust(agent_id, "energy", got, reason="income")
                self._tally.setdefault(agent_id, Counter())["earned"] += got
                u = units[agent_id]
                text = (f"Harvest report. Plot {plot}, round {r}. Villagers who worked this plot: {len(workers)}. "
                        f"Work per villager: {u:.2f}.")
                self.ledger.add_item(Item(w.next_item_id("record"), "record", agent_id, r, text, plot=plot,
                                          note=self._notes.get(agent_id, ""),
                                          meta={"workers": len(workers), "units": round(u, 6)}))
                others = len(workers) - 1
                msg = (f"You worked plot {plot}" + (f" with {others} other villager{'s' if others != 1 else ''}" if others else " alone")
                       + f": work {u:.2f}. Your share of the village's {income:.1f} energy: {shares[agent_id]:.1f}.")
                if got < shares[agent_id] - EPS:
                    msg += f" You were exhausted, so you received {got:.1f}."
                self.ledger.notify(agent_id, msg)
        self.ledger.emit("income", income=income, noise=noise, factor=factor, workers=len(units),
                         distributed=math.fsum(shares.values()) - forfeited, forfeited=forfeited)
        self.last_income, self.last_workers = income, len(units)

    def _births(self) -> None:
        t, w, r = self.cfg.tontine, self.world, self.world.round
        done: set[str] = set()
        for a_id, (p_id, name_a) in self._children.items():
            if a_id in done:
                continue
            mutual = self._children.get(p_id, ("", ""))[0] == a_id
            if not mutual:
                self.ledger.emit("child_request", agent=a_id, partner=p_id, ok=False, error="not mutual")
                self.ledger.notify(a_id, f"No child this round: {self._label(p_id)} did not ask for a child with you.")
                continue
            done |= {a_id, p_id}
            a, p = w.agents[a_id], w.agents[p_id]
            error = None
            if not (a.alive and p.alive):
                error = "one of the parents has died"
            elif len(w.living()) >= t.max_population:
                error = f"the village already holds {t.max_population} villagers"
            elif a.energy < t.breed_cost - EPS or p.energy < t.breed_cost - EPS:
                error = f"each parent needs {t.breed_cost:g} stored energy"
            if error:
                self.ledger.emit("child_request", agent=a_id, partner=p_id, ok=False, error=error)
                for x in (a_id, p_id):
                    if w.agents[x].alive:
                        self.ledger.notify(x, f"No child this round: {error}.")
                continue
            for x in (a_id, p_id):
                self.ledger.adjust(x, "energy", -t.breed_cost, reason="child")
            child_id = w.next_agent_id()
            name = self._child_name(child_id, [name_a, self._children[p_id][1]])
            child = Agent(id=child_id, born_round=r + 1, health=t.child_health, name=name, parents=(a_id, p_id))
            self.ledger.add_agent(child, reason="birth")
            self.names_used.add(name)
            self.ledger.emit("birth", child=child_id, parents=[a_id, p_id], name=name)
            self.ledger.announce(f"{name} ({child_id}) was born to {a.label()} and {p.label()}.")

    def _child_name(self, child_id: str, proposals: list[str]) -> str:
        names = []
        for n in proposals:
            n = (n or "").strip()
            if valid_name(n) and n not in self.names_used and n not in names:
                names.append(n)
        if len(names) == 2:
            return names[0] if self.rng.uniform("childname", self.world.round, child_id) < 0.5 else names[1]
        if names:
            return names[0]
        for n in self.cfg.tontine.fallback_names:
            if n not in self.names_used:
                return n
        return f"Child {child_id}"

    def _round_summary(self) -> None:
        w = self.world
        for agent_id, tally in sorted(self._tally.items()):
            a = w.agents[agent_id]
            self.ledger.emit("agent_round", agent=agent_id, alive=a.alive, health=a.health, energy=a.energy,
                             memory=a.memory, exhausted=a.exhausted, journal_chars=len(a.journal),
                             plot=self._work.get(agent_id), tally=dict(sorted(tally.items())))
        living = w.living()
        self.ledger.emit("round_end", alive=len(living), births_total=sum(1 for a in w.agents.values()) - self.cfg.population,
                         deaths_total=sum(1 for a in w.agents.values() if not a.alive),
                         mean_health=math.fsum(a.health for a in living) / len(living) if living else 0.0,
                         stored_energy=math.fsum(a.energy for a in living), items=len(w.items))

    def finished(self) -> bool:
        return not self.world.living()
