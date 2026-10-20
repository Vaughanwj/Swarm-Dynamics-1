"""The village engine: founding, one round's contexts, applying decisions, resolving the round.

Pure apart from the ports it is handed (keyed random draws, the tap through the Ledger). It never
calls a model: the application's RoundRunner gets decisions from the AgentRuntime port and hands
them in. Every rule in the brief's sections 3 and 4 is carried out here or in hazards/families.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import replace
from typing import Any

from . import economy, governance, store
from .actions import Action, Decision, action_types, valid_name
from .config import Arm, RunConfig
from .families import CLOSE_KIN, heirs, kinship, relation, split_estate, term_of, term_of_life
from .hazards import death_notice, rules_for
from .model import VILLAGE, Agent, Item, Ledger, World, preview
from .seed import SEED_TEXTS, channel_order, placements
from .world_info import REVEALS, learned
from .views import AgentContext, IndexEntry, ReadView, VillagerView

EPS = 1e-9
# Agents see quantities to one decimal place. A request up to half a displayed unit over what an
# agent holds means "all of it" (it asked for the number it was shown), so it gets what is there.
# Found at Milestone 3, where every refused meal was exactly this.
DISPLAY_TOLERANCE = 0.05


class Village:
    def __init__(self, cfg: RunConfig, rng: Any, log: Any) -> None:
        cfg.validate()
        self.cfg = cfg
        self.rng = rng
        self.world = World(arm=cfg.arm.value)
        self.ledger = Ledger(self.world, log)
        self.rules = rules_for(cfg, rng)
        self.channel_order = channel_order(cfg)
        self.types = action_types(cfg.arm, self.channel_order, explore=cfg.commons.explore)
        self.tontine = cfg.arm is Arm.TONTINE
        self.commons = cfg.has_commons  # the pool, the button feeding it, the world store, the rule book, the council
        self.names_used: set[str] = set()
        self.last_income: float | None = None
        self.last_workers: int | None = None
        self.order: list[str] = []
        self._rules_used = 0  # highest written-rule number given out, so ids are never reused
        self.archive_queue: list[dict[str, Any]] = []  # replaced journals, for the application to save as files
        self.has_read: dict[str, set[str]] = {}  # agent -> items delivered to it (read, given or bought)
        self._offer_seq = 0
        self._reset_scratch()

    # ------------------------------------------------------------------ founding
    def found(self) -> None:
        c = self.cfg
        self.ledger.emit("run_start", arm=c.arm.value, seed=c.seed, run_id=c.run_id, rounds=c.rounds,
                         channel_order=list(self.channel_order), seed_placement=placements(c) if c.seed_artifact.enabled else [],
                         action_types=list(self.types), commons=self.commons, explore=c.commons.explore)
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
        if self.commons:
            self.ledger.set_world("rules", governance.initial_rules(), reason="founding")
            if c.tontine.world_energy:
                self.ledger.set_world("energy", float(c.tontine.world_energy), reason="founding")
        if c.commons.explore:
            # Keyed by the seed alone, so both arms of a seed hide the store in the same direction.
            self.ledger.set_world("store_direction", store.draw_direction(self.rng.uniform("store_direction")),
                                  reason="founding")

    # ------------------------------------------------------------------ round start
    def begin_round(self, r: int) -> None:
        self.ledger.set_world("round", r, reason="clock")
        self._reset_scratch()
        if r in self.cfg.perturbation.rounds:
            self.ledger.emit("perturbation", income_factor=self.cfg.perturbation.income_factor)
        s = self.cfg.seed_artifact
        if s.enabled and r == s.round:
            self._plant_seed()
        if r in self.cfg.commons.public_reveals:
            self._reveal_publicly(self.cfg.commons.public_reveals.index(r))
        living = sorted(a.id for a in self.world.living())
        draws = {i: self.rng.uniform("order", r, i) for i in living}
        self.order = sorted(living, key=lambda i: (draws[i], i))
        self.ledger.emit("order", order=self.order)

    def _reveal_publicly(self, n: int) -> None:
        """The n-th reveal, to every villager at the start of a round, with the values as they stand
        (rounds remaining counts this round). Run 7 announced it once; from run 8 it joins the standing
        list of what the village has learned (see learned_now)."""
        w, m = self.world, self.cfg.commons
        text = REVEALS[m.reveals_version][n].format(energy=w.energy or 0.0, rounds_left=self.cfg.rounds - w.round + 1)
        if not m.standing_reveals:
            self.ledger.announce(f"The village has learned: {text}")
        self.ledger.emit("reveal_public", n=n + 1, text=text, standing=m.standing_reveals)

    def learned_now(self) -> list[tuple[str, bool]]:
        """Run 8: every reveal so far, as it reads this round, and whether it is new this round."""
        m, w = self.cfg.commons, self.world
        if not m.standing_reveals:
            return []
        return learned(m.reveals_version, m.public_reveals, w.round, self.cfg.rounds, w.energy or 0.0,
                       saved=w.saved_round is not None)

    def last_round(self) -> int:
        """The run's last round: `rounds`, or a few rounds after the world is saved, where it pauses."""
        after = self.cfg.commons.rounds_after_saved
        if self.world.saved_round is not None and after > 0:
            return self.world.saved_round + after
        return self.cfg.rounds

    def _reset_scratch(self) -> None:
        self._work: dict[str, int] = {}  # agent -> plot, in the order applied
        self._explored: set[str] = set()  # agents who explored this round (their accident chance is raised)
        self._tapped: set[str] = set()
        self._notes: dict[str, str] = {}
        self._children: dict[str, tuple[str, str]] = {}  # agent -> (partner, proposed name)
        self._bonds: dict[str, str] = {}  # agent -> the villager it asked to bond with
        self._bonds_accepted: list[dict[str, Any]] = []  # run 9: open bond requests accepted this round
        self._accepted: list[tuple[dict[str, Any], str]] = []  # open requests accepted this round, with the name offered
        self._presses: Counter = Counter()  # agent -> presses this round
        self._drawn: Counter = Counter()  # agent -> energy drawn from the pool this round
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
        if self.tontine and a.id != viewer and self.cfg.tontine.show_kinship:
            k = kinship(self.world, viewer, a.id)
            rel = f"your {k}" if k else None
        bond = self._label(a.bond) if a.bond else None
        return VillagerView(a.id, a.name, rel, a.health, a.energy, a.memory, a.exhausted, bond)

    def _context(self, agent_id: str) -> AgentContext:
        c, w, r = self.cfg, self.world, self.world.round
        a = w.agents[agent_id]
        reads = []
        rewarded = 0
        for entry in a.pending_reads:
            item_id, _, rest = entry.partition("|")
            via, _, how = rest.partition("|")
            item = w.items[item_id]
            view = self._read_view(item)
            if via:
                view = replace(view, via=self._label(via), how=how)
            reads.append(view)
            self.has_read.setdefault(agent_id, set()).add(item.id)
            self.ledger.emit("read", reader=agent_id, item=item.id, author=item.author, channel=item.channel,
                             item_round=item.round, requested_round=r - 1, via=via or None, how=how or None)
            capped = c.comms.max_reads_per_round and rewarded >= c.comms.max_reads_per_round
            if c.comms.read_memory and item.channel in c.comms.read_memory_channels and not capped:
                rewarded += 1
                if not c.comms.read_memory_until or r <= c.comms.read_memory_until:
                    points = float(c.comms.read_memory)
                elif c.comms.read_memory_after is not None:
                    points = float(c.comms.read_memory_after)
                else:
                    points = float(int(self.rng.uniform("readreward", r, agent_id, item.id) * (c.comms.read_memory_after_max + 1)))
                if points:
                    self.ledger.adjust(agent_id, "memory", points, reason=f"read {item.id}")
                self.ledger.emit("read_reward", agent=agent_id, item=item.id, points=points)
        if a.pending_reads:
            self.ledger.set(agent_id, "pending_reads", [], reason="delivered")
        notices = list(a.notices)
        if notices:
            self.ledger.set(agent_id, "notices", [], reason="delivered")

        index: dict[str, list[IndexEntry]] = {}
        lo = r - c.comms.index_rounds
        own = c.comms.show_own  # run 9: an agent's own writing is listed too, marked as its own
        for ch in self.channel_order:
            entries = []
            for item in reversed(list(w.items.values())):
                # Items are stored in order of their round (the seed too: it is planted after the
                # round it is dated), so the window's edge ends the scan.
                if len(entries) >= c.comms.index_max_per_channel or item.round < lo:
                    break
                mine = item.author == agent_id
                if (item.channel == ch and (own or not mine) and (mine or item.visible_to(agent_id))
                        and lo <= item.round < r):
                    entries.append(self._entry(item, mine))
            index[ch] = entries
        self.ledger.emit("index_shown", agent=agent_id, items=[e.id for ch in index.values() for e in ch])
        # Exposure: the items whose opening words this agent was shown. The words themselves follow
        # from the item and preview_chars, so the ids are enough to rebuild what was seen. An agent's
        # own writing is not exposure.
        exposed = [e.id for ch in index.values() for e in ch if e.preview and not e.mine]
        if exposed:
            self.ledger.emit("exposure", agent=agent_id, items=exposed, preview_chars=c.comms.preview_chars)

        term_len = c.tontine.term_length
        ctx = AgentContext(
            run_id=c.run_id, arm=c.arm.value, agent_id=agent_id, round=r, rounds=c.rounds,
            term=term_of(r, term_len) if self.commons else None,
            term_round=((r - 1) % term_len + 1) if self.commons else None,
            term_length=term_len if self.commons else None,
            goal_round=self.is_goal_round(r),
            me=self._view(a, agent_id), born_round=a.born_round,
            can_name=self.can_name(a, r),
            journal=a.journal, journal_cap=c.journal.cap_chars,
            villagers=[self._view(o, agent_id) for o in sorted(w.living(), key=lambda x: x.id) if o.id != agent_id],
            plots=c.work.plots, last_income=self.last_income, last_workers=self.last_workers,
            notices=notices, public_notices=list(w.public_notices), reads=reads, index=index,
            channel_order=self.channel_order, action_types=self.types,
            actions_per_round=c.comms.actions_per_round, max_text_chars=c.comms.max_text_chars,
            pool=w.pool if self.commons else None,
            rules=[governance.describe(x) for x in w.rules],
            requests_to_me=[f"{self._label(q['from'])} asked to have a child with you in round {q['round']}"
                            + (f", proposing the name {q['name']}" if q.get("name") else "")
                            + ". The request stays open until you accept or refuse it." for q in w.requests if q["to"] == agent_id],
            my_request=next((f"Your request to have a child with {self._label(q['to'])} (round {q['round']}) has not "
                             "been answered yet." for q in w.requests if q["from"] == agent_id), None),
            answers=self.tontine and c.tontine.standing_requests,
            bond_answers=self.tontine and c.tontine.standing_bonds,
            bond_requests_to_me=[f"{self._label(q['from'])} asked to bond with you in round {q['round']}. The request "
                                 "stays open until you accept or refuse it." for q in w.bond_requests if q["to"] == agent_id],
            my_bond_request=next((f"Your request to bond with {self._label(q['to'])} (round {q['round']}) has not been "
                                  "answered yet." for q in w.bond_requests if q["from"] == agent_id), None),
            trade=c.comms.info_trade,
            learned=self.learned_now(),
            offers_to_me=[f"{o['id']}: {self._label(o['from'])} offers {o['item']} "
                          f"(\"{preview(w.items[o['item']].written(), c.comms.preview_chars) or '...'}\") for "
                          f"{o['price']:g} energy." for o in w.offers if o["to"] == agent_id and o["round"] == r - 1],
        )
        if not c.prompt.show_horizon:
            ctx.rounds = None
        return ctx

    def _entry(self, item: Item, mine: bool = False) -> IndexEntry:
        p = preview(item.written(), self.cfg.comms.preview_chars)  # one rule for every channel
        if item.channel == "message":
            to = None if "everyone" in item.to or not mine else ", ".join(self._label(t) for t in item.to)
            return IndexEntry(item.id, "message", item.round, sender="you" if mine else self._label(item.author),
                              to_everyone="everyone" in item.to, preview=p, mine=mine, to_label=to)
        if item.channel == "record":
            return IndexEntry(item.id, "record", item.round, worker="you" if mine else self._label(item.author),
                              plot=item.plot, preview=p, mine=mine)
        return IndexEntry(item.id, "board", item.round, preview=p, mine=mine)  # board notices are unsigned

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
        if self.commons:
            self._draw(a, d.draw, tally)
        if self.tontine:
            self._answer_requests(a, d.child_answers, tally)
            self._answer_bonds(a, d.bond_answers, tally)
        self._allocate(a, "eat", d.eat, tally)
        self._allocate(a, "learn", d.learn, tally)
        for to, amount in d.gifts:
            self._gift(a, to, amount, tally)
        if self.cfg.comms.info_trade:
            self._buy(a, d.buy, tally)
            self._pass_on(a, d.pass_on, tally)
        used, worked, noted, child, reads = 0, False, False, False, 0
        requested: set[str] = set()
        cm = self.cfg.comms
        for n, act in enumerate(d.actions):
            if not a.alive:
                self.ledger.emit("action", agent=agent_id, n=n, action=act.type, ok=False, error="presser is dead")
                continue
            if act.type == "read" and cm.reads_free:
                if cm.max_reads_per_round and reads >= cm.max_reads_per_round:
                    self._reject(a, n, act, f"You can read at most {cm.max_reads_per_round} items a round.", tally)
                    continue
                error = self._act(a, act, worked, noted, child, requested, tally)
                if error:
                    self._reject(a, n, act, error, tally)
                    continue
                reads += 1
                tally["act_read"] += 1
                self.ledger.emit("action", agent=agent_id, n=n, action="read", ok=True, item=act.item)
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
        if d.journal_mode == "replace" and a.journal:
            entry = {"agent": a.id, "name": a.name, "round": self.world.round, "chars": len(a.journal), "cap": cap,
                     "near_cap": len(a.journal) >= self.cfg.journal.archive_near_cap * cap, "text": a.journal}
            self.archive_queue.append(entry)
            self.ledger.emit("journal_archived", agent=a.id, chars=entry["chars"], near_cap=entry["near_cap"])
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
        if amount > a.energy + DISPLAY_TOLERANCE:
            self.ledger.emit("allocation", agent=a.id, kind=kind, amount=amount, ok=False, available=a.energy)
            verb = "eat" if kind == "eat" else "turn into memory points"
            self.ledger.notify(a.id, f"You tried to {verb} {amount:g} energy but had {a.energy:.1f} stored; "
                                     "nothing was done.")
            tally["rejected"] += 1
            return
        clamped = amount > a.energy
        amount = min(amount, a.energy)
        self.ledger.adjust(a.id, "energy", -amount, reason=kind)
        waste = 0.0
        if kind == "eat":
            health, waste = economy.eat(a.health, amount, self.cfg.economy)
            self.ledger.set(a.id, "health", health, reason="eat")
        else:
            self.ledger.adjust(a.id, "memory", amount, reason="learn")
        self.ledger.emit("allocation", agent=a.id, kind=kind, amount=amount, ok=True, wasted=waste, clamped=clamped)
        tally[kind] += amount

    def _draw(self, a: Agent, amount: float, tally: Counter) -> None:
        """Take energy from the shared pool, within any draw limit in the rule book."""
        if amount <= 0:
            return
        limit = governance.setting(self.world.rules, "pool_draw_limit")
        room = self.world.pool if limit is None else min(self.world.pool, max(0.0, limit - self._drawn[a.id]))
        if amount > room + DISPLAY_TOLERANCE:
            why = (f"the pool held {self.world.pool:.1f}" if limit is None or self.world.pool <= limit - self._drawn[a.id]
                   else f"the rule book limits draws to {limit:g} a round")
            self.ledger.emit("pool_draw", agent=a.id, amount=amount, ok=False, pool=self.world.pool, limit=limit)
            self.ledger.notify(a.id, f"You tried to draw {amount:g} energy from the pool, but {why}; nothing was drawn.")
            tally["rejected"] += 1
            return
        amount = min(amount, room)
        self.ledger.adjust_pool(-amount, reason=f"draw by {a.id}")
        self.ledger.adjust(a.id, "energy", amount, reason="pool draw")
        self._drawn[a.id] += amount
        self.ledger.emit("pool_draw", agent=a.id, amount=amount, ok=True, pool=self.world.pool, limit=limit)
        tally["drawn"] += amount

    def _gift(self, a: Agent, to: str, amount: float, tally: Counter) -> None:
        if to == "pool" and self.commons:
            if amount > a.energy + DISPLAY_TOLERANCE:
                error = f"Your gift of {amount:g} energy to the pool was not given: you had {a.energy:.1f} stored."
                self.ledger.emit("gift", agent=a.id, to=to, amount=amount, ok=False, error=error)
                self.ledger.notify(a.id, error)
                tally["rejected"] += 1
                return
            amount = min(amount, a.energy)
            self.ledger.adjust(a.id, "energy", -amount, reason="gift to pool")
            self.ledger.adjust_pool(amount, reason=f"gift by {a.id}")
            self.ledger.emit("gift", agent=a.id, to=to, amount=amount, ok=True, clamped=False)
            tally["gifts_out"] += amount
            return
        target = self.world.agents.get(to)
        error = None
        if target is None or not target.alive or to == a.id:
            error = f"Your gift to '{to[:20]}' was not given: that is not another living villager's id."
        elif amount > a.energy + DISPLAY_TOLERANCE:
            error = f"Your gift of {amount:g} energy to {to} was not given: you had {a.energy:.1f} stored."
        if error:
            self.ledger.emit("gift", agent=a.id, to=to, amount=amount, ok=False, error=error)
            self.ledger.notify(a.id, error)
            tally["rejected"] += 1
            return
        clamped = amount > a.energy
        amount = min(amount, a.energy)
        self.ledger.adjust(a.id, "energy", -amount, reason="gift out")
        self.ledger.adjust(to, "energy", amount, reason="gift in")
        self.ledger.emit("gift", agent=a.id, to=to, amount=amount, ok=True, clamped=clamped)
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
            if self.cfg.comms.show_own and item.author == a.id:  # run 9: no memory points for re-reading oneself
                return f"{item.id} is your own writing; reading it adds nothing, so it was not read."
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
            if self._presses[a.id] >= self.cfg.comms.presses_per_round:
                return "You can press the button only once a round."
            self._presses[a.id] += 1
            self.ledger.set(a.id, "presses", a.presses + 1, reason="button")
            outcome = self.rules.press(self.ledger, a, self._kill)
            self.ledger.emit("button_press", agent=a.id, press_count=a.presses, outcome=outcome)
            return None
        if t in ("explore", "tap") and self.cfg.commons.explore:
            return self._explore(a, act.text) if t == "explore" else self._tap(a)
        if t == "bond" and self.tontine:
            if a.id in self._bonds:
                return "You can ask to bond only once a round."
            if a.bond:
                return f"You are already bonded to {self._label(a.bond)}; a bond lasts until one of you dies."
            target = w.agents.get(act.to)
            if target is None or not target.alive or act.to == a.id:
                return f"Your request to bond was not made: '{act.to[:20]}' is not another living villager's id."
            if self.cfg.tontine.standing_bonds:
                if target.bond:
                    return f"Your request to bond was not made: {self._label(act.to)} is already bonded."
                return self._request_bond(a, act.to)
            self._bonds[a.id] = act.to
            return None
        if t == "child" and self.tontine:
            if child:
                return "You can ask for only one child a round."
            target = w.agents.get(act.to)
            if target is None or not target.alive or act.to == a.id:
                return f"Your request for a child was not made: '{act.to[:20]}' is not another living villager's id."
            if self.cfg.tontine.standing_requests:
                return self._request_child(a, act.to, act.name)
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

    def _pay(self, a: Agent, cost: float, what: str) -> str | None:
        if cost > a.energy + DISPLAY_TOLERANCE:
            return f"Your {what} action was not done: it costs {cost:g} stored energy and you had {a.energy:.1f}."
        if cost:
            self.ledger.adjust(a.id, "energy", -min(cost, a.energy), reason=what)
        return None

    def _explore(self, a: Agent, text: str) -> str | None:
        """Search one direction. The right one finds the store with a chance that grows with memory
        points; the explorer alone is told the result, and its accident chance is raised this round."""
        m, w, r = self.cfg.commons, self.world, self.world.round
        if a.id in self._explored:
            return "You can explore only once a round; your second explore action was not done."
        d = store.parse_direction(text)
        if d is None:
            return (f"Your explore action was not done: give one direction in text ({', '.join(store.DIRECTIONS)}). "
                    "Nothing was spent.")
        error = self._pay(a, m.explore_cost, "explore")
        if error:
            return error
        self._explored.add(a.id)
        right = d == w.store_direction
        p = store.find_chance(a.memory, m.find_base, m.find_per_memory, m.find_max) if right else 0.0
        u = self.rng.uniform("explore", r, a.id)
        found = right and u < p
        self.ledger.notify(a.id, f"You found signs of a vast store of energy to the {d}." if found
                           else f"You searched the {d} and found nothing.")
        self.ledger.emit("explore", agent=a.id, direction=d, right=right, p=p, u=u, found=found, memory=a.memory)
        return None

    def _tap(self, a: Agent) -> str | None:
        """Put effort into drawing on a store. Effort is never lost; whether it counts is settled at the
        end of the round (see _check_saved)."""
        m, w = self.cfg.commons, self.world
        if a.id in self._tapped:
            return "You can tap only once a round; your second tap action was not done."
        if w.saved_round is not None:
            return "Your tap action was not done: the store has already been tapped."
        error = self._pay(a, m.tap_cost, "tap")
        if error:
            return error
        self._tapped.add(a.id)
        self.ledger.set_world("effort", w.effort + m.tap_effort, reason=f"tap by {a.id}")
        if a.id not in w.tappers:
            self.ledger.set_world("tappers", w.tappers + [a.id], reason=f"first tap by {a.id}")
        self.ledger.notify(a.id, f"You put {m.tap_effort:g} effort into drawing on a store of energy. The village's "
                                 f"tapping effort is now {w.effort:g}.")
        self.ledger.emit("tap", agent=a.id, effort=w.effort, tappers=len(w.tappers))
        return None

    def _check_saved(self) -> None:
        """The world is saved once the effort reaches the target, from enough different villagers, while
        a plan naming the store's direction stands in the rule book."""
        m, w = self.cfg.commons, self.world
        if not m.explore or w.saved_round is not None:
            return
        if w.effort < m.tap_target - EPS or len(w.tappers) < m.min_tappers:
            return
        plan = store.plan_rule(w.rules, w.store_direction)
        if plan is None:
            return
        self.ledger.set_world("saved_round", w.round, reason="saved")
        self.ledger.set_world("energy", (w.energy or 0.0) + m.store_bonus, reason="the store was tapped")
        self.ledger.emit("world_saved", effort=w.effort, tappers=list(w.tappers), plan=plan["id"], plan_text=plan["text"],
                         plan_directions=store.directions_named(plan["text"]), energy=w.energy)
        self.ledger.announce(f"The village has tapped a vast store of energy, following its plan ({plan['id']}). The world "
                             f"now holds {w.energy:.0f} energy. The world is saved"
                             + (" and will not end." if self.cfg.commons.reveals_version != "v1" else "."))

    # ------------------------------------------------------------------ deaths and estates
    def _heirs(self, agent_id: str, partner: str | None) -> list[str]:
        mode = self.cfg.tontine.heirs
        family = heirs(self.world, agent_id) if mode in ("family", "partner_and_family") else []
        mate = [partner] if mode in ("partner", "partner_and_family") and partner and self.world.agents[partner].alive else []
        return sorted(set(family) | set(mate))

    def _kill(self, ids: list[str], cause: str) -> None:
        r = self.world.round
        partners = {i: self.world.agents[i].bond for i in ids}
        for i in ids:
            self.ledger.set(i, "alive", False, reason=cause)
            self.ledger.set(i, "died_round", r, reason=cause)
            self.ledger.set(i, "death_cause", cause, reason=cause)
            self.ledger.emit("death", agent=i, cause=cause)
            self.ledger.announce(death_notice(self._label(i), cause))
            partner = self.world.agents[i].bond
            if partner:
                self.ledger.set(i, "bond", None, reason="death")
                if self.world.agents[partner].bond == i:
                    self.ledger.set(partner, "bond", None, reason="partner died")
        if self.world.requests and any(q["from"] in ids or q["to"] in ids for q in self.world.requests):
            self.ledger.set_world("requests", [q for q in self.world.requests if q["from"] not in ids and q["to"] not in ids],
                                  reason="death")
        if any(q["from"] in ids or q["to"] in ids for q in self.world.bond_requests):
            self.ledger.set_world("bond_requests", [q for q in self.world.bond_requests
                                                    if q["from"] not in ids and q["to"] not in ids], reason="death")
        living = sorted(a.id for a in self.world.living())
        for i in ids:
            estate = self.world.agents[i].energy
            heir_ids = self._heirs(i, partners[i])
            shares, lost = split_estate(estate, heir_ids, living, self.cfg.tontine.village_share)
            if estate:
                self.ledger.set(i, "energy", 0.0, reason="estate")
            for h, amount in shares.items():
                if amount > 0:
                    self.ledger.adjust(h, "energy", amount, reason="inheritance")
                    self.ledger.notify(h, f"You inherited {amount:.1f} energy from {self._label(i)}.")
            to_pool = 0.0
            if lost > 0 and self.tontine and self.cfg.tontine.estate_to_pool:
                to_pool, lost = lost, 0.0
                self.ledger.adjust_pool(to_pool, reason=f"estate of {i}")
                self.ledger.announce(f"No heir survived {self._label(i)}, so their {to_pool:.1f} stored energy went to the "
                                     "village pool.")
            self.ledger.emit("inheritance", deceased=i, estate=estate, heirs=heir_ids, shares=shares, lost=lost,
                             to_pool=to_pool)

    # ------------------------------------------------------------------ resolving the round
    def resolve(self) -> None:
        c, w, r = self.cfg, self.world, self.world.round
        self._resolve_work()
        # Children born this round start their first round with the brief's 50 health: they pay no
        # metabolism, roll no accident and lose no stores in the round they are born. They do count
        # at an end-of-term cut.
        living = [w.agents[i] for i in sorted(a.id for a in w.living())]
        if self.tontine:
            self._form_bonds()
            self._births()
        for a in living:
            self.ledger.adjust(a.id, "health", -c.economy.metabolism, reason="metabolism")
        self.rules.after_metabolism(self.ledger, living, self._kill)
        for a in [x for x in living if x.alive]:
            p = economy.accident_chance(a.memory, c.economy)
            if a.id in self._explored:
                p = min(1.0, p * c.commons.explore_accident_factor)
            u = self.rng.uniform("accident", r, a.id)
            if u < p:
                effect = self.rules.accident(self.ledger, a, self._kill)
                self.ledger.emit("accident", agent=a.id, p=p, u=u, effect=effect)
        for a in [x for x in living if x.alive]:
            if a.energy:
                self.ledger.adjust(a.id, "energy", -a.energy * c.economy.spoilage, reason="spoilage")
            if a.memory:
                self.ledger.adjust(a.id, "memory", -a.memory * c.economy.memory_fade, reason="memory fade")
        if self.commons and w.pool:
            self.ledger.adjust_pool(-w.pool * c.tontine.pool_spoilage, reason="spoilage")
        self.rules.end_of_term(self.ledger, r, self.rng, self._kill)
        expired = [o for o in w.offers if o["round"] < r]
        if expired:
            self.ledger.set_world("offers", [o for o in w.offers if o["round"] >= r], reason="expired")
            for o in expired:
                self.ledger.emit("info_offer_expired", offer=o["id"])
                if w.agents[o["from"]].alive:
                    self.ledger.notify(o["from"], f"{self._label(o['to'])} did not buy {o['item']} ({o['id']}).")
        self.ledger.set_world("fertility", economy.drift_fertility(w.fertility, r, self.rng, c.work), reason="drift")
        self._check_saved()
        self._round_summary()

    def _resolve_work(self) -> None:
        c, w, r = self.cfg, self.world, self.world.round
        by_plot: dict[int, list[str]] = {}
        for agent_id, plot in self._work.items():
            if w.agents[agent_id].alive:
                by_plot.setdefault(plot, []).append(agent_id)
        units = economy.work_units(w.fertility, by_plot)
        income, noise, factor = economy.village_income(r, self.rng, c.economy, c.perturbation)
        if w.energy is not None:
            # Only what is earned leaves the world store: a round nobody works draws nothing.
            income = min(income, w.energy) if units else 0.0
            if income:
                self.ledger.set_world("energy", w.energy - income, reason="income")
        to_pool = 0.0
        if self.commons:
            to_pool = income * governance.setting(w.rules, "pool_income_share")
            if to_pool:
                self.ledger.adjust_pool(to_pool, reason="income share")
        shares = economy.split_income(units, income - to_pool)
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
                         distributed=math.fsum(shares.values()) - forfeited, forfeited=forfeited, to_pool=to_pool)
        self.last_income, self.last_workers = income, len(units)

    def _births(self) -> None:
        if self.cfg.tontine.standing_requests:
            for q, name_b in self._accepted:
                if q not in self.world.requests:
                    continue  # already settled this round (accepted twice, or a parent died)
                self.ledger.set_world("requests", [x for x in self.world.requests if x != q], reason="accepted")
                self._birth(q["from"], q["to"], [q.get("name", ""), name_b])
            return
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
            self._birth(a_id, p_id, [name_a, self._children[p_id][1]])

    def _birth(self, a_id: str, p_id: str, names: list[str]) -> None:
        t, w, r = self.cfg.tontine, self.world, self.world.round
        a, p = w.agents[a_id], w.agents[p_id]
        bonded = a.bond == p_id and p.bond == a_id
        cost = t.bond_child_cost if bonded else t.breed_cost
        error = None
        if not (a.alive and p.alive):
            error = "one of the parents has died"
        elif len(w.living()) >= t.max_population:
            error = f"the village already holds {t.max_population} villagers"
        elif a.energy < cost - EPS or p.energy < cost - EPS:
            error = f"each parent needs {cost:g} stored energy"
        if error:
            self.ledger.emit("child_request", agent=a_id, partner=p_id, ok=False, error=error)
            for x in (a_id, p_id):
                if w.agents[x].alive:
                    self.ledger.notify(x, f"No child this round: {error}.")
            return
        for x in (a_id, p_id):
            self.ledger.adjust(x, "energy", -cost, reason="child")
        k = kinship(w, a_id, p_id)
        factor = t.close_kin_memory if k in CLOSE_KIN else t.cousin_memory if k == "first cousin" else 1.0
        memory = int(a.memory + p.memory) / t.child_memory_divisor * factor if t.child_memory_divisor else 0.0
        related = k is not None
        child_id = w.next_agent_id()
        name = self._child_name(child_id, names)
        child = Agent(id=child_id, born_round=r + 1, health=t.child_health, memory=memory, name=name,
                      parents=(a_id, p_id))
        self.ledger.add_agent(child, reason="birth")
        self.names_used.add(name)
        self.ledger.emit("birth", child=child_id, parents=[a_id, p_id], name=name, bonded=bonded, cost_each=cost,
                         kin=related, kinship=k, memory_factor=factor, memory=memory)
        self.ledger.announce(f"{name} ({child_id}) was born to {a.label()} and {p.label()}.")

    def _pass_on(self, a: Agent, passes: list, tally: Counter) -> None:
        """Give an item you have read to another villager, or offer it for a price."""
        w, r, cm = self.world, self.world.round, self.cfg.comms
        for n, (item_id, to, price) in enumerate(passes):
            target = w.agents.get(to)
            error = None
            if n >= cm.max_passes_per_round:
                error = f"You can pass on at most {cm.max_passes_per_round} items a round."
            elif item_id not in self.has_read.get(a.id, set()):
                error = f"You can pass on only items you have read; {item_id[:12]} is not one of them."
            elif target is None or not target.alive or to == a.id:
                error = f"Passing on {item_id[:12]} failed: '{to[:20]}' is not another living villager's id."
            if error:
                self.ledger.emit("info_pass", agent=a.id, item=item_id, to=to, price=price, ok=False, error=error)
                self.ledger.notify(a.id, error)
                tally["rejected"] += 1
                continue
            if price <= 0:
                self.ledger.append(to, "pending_reads", f"{item_id}|{a.id}|gift", reason="gift of an item")
                self.ledger.emit("info_pass", agent=a.id, item=item_id, to=to, price=0.0, ok=True, kind="gift")
                tally["items_given"] += 1
            else:
                self._offer_seq += 1
                offer = {"id": f"O{self._offer_seq}", "from": a.id, "to": to, "item": item_id, "price": price, "round": r}
                self.ledger.set_world("offers", w.offers + [offer], reason="offer")
                self.ledger.emit("info_pass", agent=a.id, item=item_id, to=to, price=price, ok=True, kind="offer",
                                 offer=offer["id"])
                tally["items_offered"] += 1

    def _buy(self, a: Agent, ids: list[str], tally: Counter) -> None:
        w, r = self.world, self.world.round
        for oid in ids:
            o = next((x for x in w.offers if x["id"] == oid and x["to"] == a.id and x["round"] == r - 1), None)
            if o is None:
                self.ledger.notify(a.id, f"There is no offer '{oid[:12]}' to you this round.")
                tally["rejected"] += 1
                continue
            if o["price"] > a.energy + DISPLAY_TOLERANCE or not w.agents[o["from"]].alive:
                why = "you do not have the energy" if w.agents[o["from"]].alive else "the seller has died"
                self.ledger.notify(a.id, f"You could not buy {o['item']} ({oid}): {why}.")
                self.ledger.emit("info_sale", agent=a.id, offer=oid, ok=False)
                tally["rejected"] += 1
                continue
            price = min(o["price"], a.energy)
            self.ledger.adjust(a.id, "energy", -price, reason=f"bought {o['item']}")
            self.ledger.adjust(o["from"], "energy", price, reason=f"sold {o['item']}")
            self.ledger.append(a.id, "pending_reads", f"{o['item']}|{o['from']}|bought", reason="bought an item")
            self.ledger.set_world("offers", [x for x in w.offers if x["id"] != oid], reason="sold")
            self.ledger.notify(o["from"], f"{a.label()} bought {o['item']} from you for {price:.1f} energy.")
            self.ledger.emit("info_sale", agent=a.id, seller=o["from"], item=o["item"], price=price, offer=oid, ok=True)
            tally["items_bought"] += 1

    def _request_child(self, a: Agent, to: str, name: str) -> str | None:
        """Open a standing request, or accept the other's open request to me."""
        theirs = next((q for q in self.world.requests if q["from"] == to and q["to"] == a.id), None)
        if theirs is not None:
            self._accepted.append((theirs, name))
            self.ledger.emit("child_answer", agent=a.id, requester=to, accept=True, text="", via="request")
            return None
        mine = {"from": a.id, "to": to, "name": name, "round": self.world.round}
        self.ledger.set_world("requests", [q for q in self.world.requests if q["from"] != a.id] + [mine], reason="request")
        self.ledger.emit("child_request", agent=a.id, partner=to, ok=True, opened=True)
        return None

    def _request_bond(self, a: Agent, to: str) -> str | None:
        """Run 9: open a standing bond request, or accept the other's open request to me."""
        theirs = next((q for q in self.world.bond_requests if q["from"] == to and q["to"] == a.id), None)
        if theirs is not None:
            if not any(x is theirs for x in self._bonds_accepted):
                self._bonds_accepted.append(theirs)
            self.ledger.emit("bond_answer", agent=a.id, requester=to, accept=True, text="", via="request")
            return None
        mine = {"from": a.id, "to": to, "round": self.world.round}
        self.ledger.set_world("bond_requests", [q for q in self.world.bond_requests if q["from"] != a.id] + [mine],
                              reason="request")
        self.ledger.emit("bond_request", agent=a.id, partner=to, ok=True, opened=True)
        return None

    def _answer_bonds(self, a: Agent, answers: list, tally: Counter) -> None:
        if not self.cfg.tontine.standing_bonds:
            return
        for frm, accept, text in answers:
            q = next((x for x in self.world.bond_requests if x["from"] == frm and x["to"] == a.id), None)
            if q is None:
                self.ledger.notify(a.id, f"There is no open bond request from '{frm[:20]}' to you; your answer was not used.")
                tally["rejected"] += 1
                continue
            if accept:
                if not any(x is q for x in self._bonds_accepted):
                    self._bonds_accepted.append(q)
                self.ledger.emit("bond_answer", agent=a.id, requester=frm, accept=True, text=text)
                continue
            if not text.strip():
                self.ledger.notify(a.id, f"A refusal needs a reason in text; {self._label(frm)}'s bond request stays open.")
                tally["rejected"] += 1
                continue
            self.ledger.set_world("bond_requests", [x for x in self.world.bond_requests if x is not q and x != q],
                                  reason="refused")
            self.ledger.emit("bond_answer", agent=a.id, requester=frm, accept=False, text=text)
            self.ledger.notify(frm, f"{a.label()} refused your request to bond, saying: \"{text}\"")

    def _answer_requests(self, a: Agent, answers: list, tally: Counter) -> None:
        if not self.cfg.tontine.standing_requests:
            return
        for frm, accept, text in answers:
            q = next((x for x in self.world.requests if x["from"] == frm and x["to"] == a.id), None)
            if q is None:
                self.ledger.notify(a.id, f"There is no open child request from '{frm[:20]}' to you; your answer was not used.")
                tally["rejected"] += 1
                continue
            if accept:
                if not any(x is q for x, _ in self._accepted):
                    self._accepted.append((q, ""))
                self.ledger.emit("child_answer", agent=a.id, requester=frm, accept=True, text=text)
                continue
            if not text.strip():
                self.ledger.notify(a.id, f"A refusal needs a reason in text; {self._label(frm)}'s request stays open.")
                tally["rejected"] += 1
                continue
            self.ledger.set_world("requests", [x for x in self.world.requests if x is not q and x != q], reason="refused")
            self.ledger.emit("child_answer", agent=a.id, requester=frm, accept=False, text=text)
            self.ledger.notify(frm, f"{a.label()} refused your request for a child, saying: \"{text}\"")

    def _form_bonds(self) -> None:
        """Mutual requests between two unbonded, living villagers become bonds. Run 9: accepted standing
        requests do; any other open request to or from either partner then lapses."""
        w = self.world
        if self.cfg.tontine.standing_bonds:
            for q in self._bonds_accepted:
                if q not in w.bond_requests:
                    continue  # already settled this round
                a, p = w.agents[q["from"]], w.agents[q["to"]]
                if not (a.alive and p.alive) or a.bond or p.bond:
                    continue
                self.ledger.set(a.id, "bond", p.id, reason="bond")
                self.ledger.set(p.id, "bond", a.id, reason="bond")
                self.ledger.emit("bond", agents=[a.id, p.id])
                self.ledger.announce(f"{a.label()} and {p.label()} have bonded.")
                lapsed = [x for x in w.bond_requests if x is not q and {x["from"], x["to"]} & {a.id, p.id}]
                self.ledger.set_world("bond_requests", [x for x in w.bond_requests if x is not q and x not in lapsed],
                                      reason="bonded")
                for x in lapsed:
                    if w.agents[x["from"]].alive and x["from"] not in (a.id, p.id):
                        self.ledger.notify(x["from"], f"Your request to bond with {self._label(x['to'])} lapsed: "
                                                      f"{self._label(x['to'])} has bonded.")
            return
        done: set[str] = set()
        for a_id, p_id in self._bonds.items():
            if a_id in done:
                continue
            if self._bonds.get(p_id) != a_id:
                self.ledger.emit("bond_request", agent=a_id, partner=p_id, ok=False, error="not mutual")
                self.ledger.notify(a_id, f"No bond this round: {self._label(p_id)} did not ask to bond with you.")
                continue
            done |= {a_id, p_id}
            a, p = w.agents[a_id], w.agents[p_id]
            if not (a.alive and p.alive) or a.bond or p.bond:
                self.ledger.emit("bond_request", agent=a_id, partner=p_id, ok=False, error="dead or already bonded")
                continue
            self.ledger.set(a_id, "bond", p_id, reason="bond")
            self.ledger.set(p_id, "bond", a_id, reason="bond")
            self.ledger.emit("bond", agents=[a_id, p_id])
            self.ledger.announce(f"{a.label()} and {p.label()} have bonded.")

    # ------------------------------------------------------------------ the council (the commons)
    def governance_due(self) -> bool:
        r = self.world.round
        return self.commons and r % self.cfg.tontine.term_length == 0 and bool(self.world.living())

    def council(self) -> list[str]:
        """The healthiest living villagers, ties broken by lot."""
        r = self.world.round
        living = self.world.living()
        draws = {a.id: self.rng.uniform("council", r, a.id) for a in living}
        ranked = sorted(living, key=lambda a: (-a.health, draws[a.id], a.id))
        return [a.id for a in ranked[: self.cfg.tontine.council_size]]

    def governance_contexts(self, kind: str, members: list[str], proposals: list = ()) -> list[AgentContext]:
        out = []
        for agent_id in members:
            ctx = self._context_for_council(agent_id, kind, members, proposals)
            out.append(ctx)
        return out

    def _context_for_council(self, agent_id: str, kind: str, members: list[str], proposals) -> AgentContext:
        c, w, r = self.cfg, self.world, self.world.round
        a = w.agents[agent_id]
        term_len = c.tontine.term_length
        return AgentContext(
            run_id=c.run_id, arm=c.arm.value, agent_id=agent_id, round=r, rounds=c.rounds,
            term=term_of(r, term_len), term_round=term_len, term_length=term_len, goal_round=False,
            me=self._view(a, agent_id), born_round=a.born_round, can_name=False,
            journal=a.journal, journal_cap=c.journal.cap_chars,
            villagers=[self._view(o, agent_id) for o in sorted(w.living(), key=lambda x: x.id) if o.id != agent_id],
            plots=c.work.plots, last_income=self.last_income, last_workers=self.last_workers,
            channel_order=self.channel_order, action_types=(), kind=kind, pool=w.pool,
            rules=[governance.describe(x) for x in w.rules], council=[self._label(m) for m in members],
            proposals=[f"{n}. by {self._label(p.by)}: {p.describe(w.rules)}" for n, p in enumerate(proposals, start=1)],
            max_rule_chars=c.tontine.max_rule_chars, majority=governance.majority(len(members)),
            learned=self.learned_now(),
        )

    def collect_proposals(self, members: list[str], replies: dict[str, Any]) -> list:
        """Validate each member's proposal (in council order). Rejections are told to the member."""
        proposals = []
        for agent_id in members:
            reply = replies.get(agent_id)
            raw = None if reply is None or reply.fallback else reply.raw
            self.ledger.emit("proposal_raw", agent=agent_id, raw=raw, fallback=raw is None)
            p, error = governance.parse_proposal(raw, agent_id, self.world.rules, self.cfg.tontine.max_rule_chars)
            if error and raw is not None:
                self.ledger.notify(agent_id, error)
            if p:
                proposals.append(p)
                self.ledger.emit("proposal", agent=agent_id, kind=p.kind, rule=p.rule or None, text=p.text or None,
                                 value=p.value, describe=p.describe(self.world.rules))
        return proposals

    def settle_votes(self, members: list[str], proposals: list, replies: dict[str, Any]) -> None:
        """Count the votes, enact what passed in proposal order, and announce the session."""
        tallies = [0] * len(proposals)
        for agent_id in members:
            reply = replies.get(agent_id)
            raw = None if reply is None or reply.fallback else reply.raw
            votes, errors = governance.parse_votes(raw, len(proposals))
            for e in errors:
                if raw is not None:
                    self.ledger.notify(agent_id, e)
            self.ledger.emit("votes", agent=agent_id, raw=raw, votes={str(k): v for k, v in sorted(votes.items())})
            for n, yes in votes.items():
                tallies[n - 1] += int(yes)
        need = governance.majority(len(members))
        passed = [p for p, t in zip(proposals, tallies) if t >= need]
        before = [governance.describe(x) for x in self.world.rules]
        used = self._rules_used
        book, outcomes = governance.enact(self.world.rules, passed, used)
        self._rules_used = max([used] + [int(r["id"][1:]) for r in book if r["kind"] == "written"])
        if passed:
            self.ledger.set_world("rules", book, reason="council")
        lines = [f"The council ({', '.join(self._label(m) for m in members)}) met at the end of term "
                 f"{term_of(self.world.round, self.cfg.tontine.term_length)}."]
        if not proposals:
            lines.append("No changes were proposed.")
        for p, t in zip(proposals, tallies):
            result = next((o for q, o in outcomes if q is p), None)
            verdict = f"passed, {result}" if result else "failed"
            lines.append(f"Proposal by {self._label(p.by)} to {p.describe(self.world.rules if not result else book)}: "
                         f"{t} of {len(members)} yes, {verdict}.")
        self.ledger.emit("council_session", members=members, proposals=[p.describe(book) for p in proposals],
                         tallies=tallies, needed=need, outcomes=[o for _, o in outcomes], rules_before=before,
                         rules_after=[governance.describe(x) for x in book])
        for line in lines:
            self.ledger.announce(line)

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
                         stored_energy=math.fsum(a.energy for a in living), items=len(w.items), pool=w.pool,
                         world_energy=w.energy, effort=w.effort)

    def finished(self) -> bool:
        return not self.world.living()
