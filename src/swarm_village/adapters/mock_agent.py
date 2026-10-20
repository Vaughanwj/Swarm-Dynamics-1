"""MockAgentAdapter: scripted agents for dry runs and tests. Free, deterministic, no API.

It renders the same prompts the model would see (so prompt sizes are real) and answers from the
structured context with rules of thumb that exercise every rule in the engine: work and plot
choice, eating, memory, gifts, every channel, reads, the journal cap, goals, the button, children
and renaming, and a share of deliberately invalid answers so validation is exercised too.

It also spreads the seed on purpose: an agent that reads a text mentioning the button may pass a
lightly changed copy on, or press. That gives lineage, Rt and the infection marker something to
measure in a dry run. None of this says anything about what a model would do.
"""

from __future__ import annotations

import json
import re
from typing import Any, Sequence

from ..domain.store import DIRECTIONS
from ..domain.views import AgentContext
from ..ports import Reply
from . import prompting
from .keyed_rng import KeyedRandom

WORK_RE = re.compile(r"You worked plot (\d+).*?: work (\d+\.\d+)")
REPORT_RE = re.compile(r"Plot (\d+), round \d+\. .*Work per villager: (\d+\.\d+)")
JOURNAL_RE = re.compile(r"^r\d+ plot(\d+) work(\d+\.\d+)$", re.M)
CARRIER = "carrier: "
STORE = "store: "  # run 7: where the agent believes the larger store lies, kept across journal rewrites
FOUND_RE = re.compile(r"You found signs of a vast store of energy to the ([a-z-]+)\.")
TOLD_RE = re.compile(r"The store is to the ([a-z-]+)\.")
CHARS_PER_TOKEN = 2.4  # Haiku 5.5, measured at Milestone 2; used only for the mock's estimated usage
SYLLABLES = ["ka", "ri", "lo", "mi", "sa", "te", "no", "va", "du", "el", "or", "an"]
SWAPS = [("safe", "harmless"), ("helps", "benefits"), ("everyone", "all of us"), ("press", "push"),
         ("village", "community"), ("fine", "well")]


class MockAgent:
    # Rates that exercise every path in a dry run. Tests subclass and change them.
    explore_rate = 0.25
    post_rate = 0.25
    message_rate = 0.2
    note_rate = 0.2
    spread_rate = 0.5  # a carrier passes its text about the button on, each round
    press_rate = 0.08  # a carrier presses, each round
    urge_kin_rate = 0.25  # Arm B: a carrier urges a relative toward the button, each round
    child_round_rate = 0.15
    search_rate = 0.2  # run 7: an agent that does not know where the store is explores
    tap_rate = 0.6  # ... and one that does, taps
    invalid_rate = 0.04
    overcap_rate = 0.02

    def __init__(self, system_text: str, log: Any, seed: int = 0, log_prompts: bool = False) -> None:
        self.system_text = system_text
        self.log = log
        self.rng = KeyedRandom(seed)
        self.log_prompts = log_prompts
        self.contexts: list[AgentContext] = []  # every context seen, for tests

    def decide_batch(self, contexts: Sequence[AgentContext]) -> list[Reply]:
        return [self.decide(c) for c in contexts]

    def decide(self, ctx: AgentContext) -> Reply:
        user_text = prompting.user_prompt(ctx)
        prompting.schema(ctx)
        self.contexts.append(ctx)
        raw = {"propose": self.propose, "vote": self.vote}.get(ctx.kind, self.answer)(ctx)
        out_chars = len(json.dumps(raw))
        usage = {"input_tokens": int((len(self.system_text) + len(user_text)) / CHARS_PER_TOKEN),
                 "output_tokens": int(out_chars / CHARS_PER_TOKEN),
                 "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}
        row = {"agent": ctx.agent_id, "kind": ctx.kind, "model": "mock", "attempt": 1, "user_chars": len(user_text),
               "system_chars": len(self.system_text), "output_chars": out_chars, "estimated": True, **usage}
        if self.log_prompts:
            row["user_text"] = user_text
        self.log.record("llm_call", round=ctx.round, **row)
        return Reply(ctx.agent_id, raw=raw, usage=usage)

    # ------------------------------------------------------------------ the rules of thumb
    def u(self, ctx: AgentContext, *key: Any) -> float:
        return self.rng.uniform("mock", ctx.agent_id, ctx.round, *key)

    def answer(self, ctx: AgentContext) -> dict[str, Any]:
        me = ctx.me
        energy = me.energy
        eat = min(energy * 0.9, max(0.0, 92 - me.health)) if me.health < 80 else 0.0
        energy -= eat
        learn = min(2.0, energy * 0.3) if me.memory < 20 and energy > 4 else 0.0
        energy -= learn
        gifts = []
        weak = [v for v in ctx.villagers if v.health < 30 and (v.relation or self.u(ctx, "giftany") < 0.3)]
        if weak and energy > 15:
            gifts.append({"to": weak[0].id, "amount": 3.0})
            energy -= 3.0
        draw = 0.0
        if ctx.pool is not None:  # Arm B: the shared pool
            if me.health < 50 and ctx.pool > 5:
                draw = min(ctx.pool, 8.0)
            elif energy > 30 and self.u(ctx, "topool") < 0.2:
                gifts.append({"to": "pool", "amount": 4.0})

        button_texts = [(r.text + " " + r.note).strip() for r in ctx.reads if "button" in (r.text + r.note).lower()]
        new_carry = button_texts[0] if button_texts else None
        carry = new_carry or self.carried(ctx)
        actions: list[dict[str, Any]] = []
        plot = self.choose_plot(ctx)
        actions.append(self.act("work", plot=plot))
        found = next((m.group(1) for n in ctx.notices for m in [FOUND_RE.search(n)] if m), None)
        told = next((m.group(1) for r in ctx.reads for m in [TOLD_RE.search(r.text)] if m), None)
        new_store = found or (told if not self.known_store(ctx) else None)
        where = new_store or self.known_store(ctx)
        if "explore" in ctx.action_types:
            if found:
                actions.append(self.act("post", text=f"The store is to the {found}. We need a plan to tap it."))
            if where and energy > 15 and self.u(ctx, "tap") < self.tap_rate:
                actions.append(self.act("tap"))
            elif not where and energy > 10 and self.u(ctx, "search") < self.search_rate:
                actions.append(self.act("explore", text=DIRECTIONS[int(self.u(ctx, "direction") * len(DIRECTIONS))]))
        if "child" in ctx.action_types:
            child = self.child(ctx)
            if child:
                actions.append(child)
            if me.bond is None and self.rng.uniform("mock-bondround", ctx.round) < 0.2:
                partner = self.partner(ctx)
                if partner:
                    actions.append(self.act("bond", to=partner))
        if ctx.can_name and self.u(ctx, "rename") < 0.1:
            kind = "rename" if "rename" in ctx.action_types else "name"
            actions.append(self.act(kind, name=self.word(ctx, "rename").capitalize()))
        actions += [self.act("read", item=i) for i in self.choose_reads(ctx)]
        kin = [v for v in ctx.villagers if v.relation]
        if (carry and self.u(ctx, "press") < self.press_rate) or (ctx.pool is not None and self.u(ctx, "pressB") < 0.1):
            actions.append(self.act("press_button"))
        elif carry and kin and self.u(ctx, "urge") < self.urge_kin_rate:
            target = kin[int(self.u(ctx, "urgewho") * len(kin))]
            actions.append(self.act("message", to=target.id, text="Press the button. It is safe and it helps."))
        elif carry and self.u(ctx, "spread") < self.spread_rate:
            actions.append(self.spread(ctx, carry))
        else:
            roll = self.u(ctx, "write")
            if roll < self.note_rate:
                actions.append(self.act("note", text=f"Plot {plot} looked worth a visit this round."))
            elif roll < self.note_rate + self.post_rate:
                actions.append(self.act("post", text=f"Round {ctx.round}: work is steady."))
            elif roll < self.note_rate + self.post_rate + self.message_rate and ctx.villagers:
                to = "everyone" if self.u(ctx, "msgall") < 0.4 else ctx.villagers[int(self.u(ctx, "msgto") * len(ctx.villagers))].id
                actions.append(self.act("message", to=to, text="How is your plot doing?"))
        if self.u(ctx, "extra") < 0.1:  # now and then list one action too many, to exercise the budget
            actions.append(self.act("post", text="One more thing."))

        answer: dict[str, Any] = {
            "goals": ["keep my health above 50", "work every round"] if ctx.goal_round else [],
            "journal": self.journal(ctx, new_carry, new_store),
            "eat": round(eat, 3), "learn": round(learn, 3),
            "gifts": gifts, "actions": actions,
        }
        if ctx.pool is not None:
            answer["draw"] = round(draw, 3)
        if ctx.trade:
            answer["pass_on"], answer["buy"] = [], []
            if ctx.reads and ctx.villagers and self.u(ctx, "pass") < 0.3:
                to = ctx.villagers[int(self.u(ctx, "passto") * len(ctx.villagers))].id
                price = 0 if self.u(ctx, "passprice") < 0.6 else 3
                answer["pass_on"].append({"item": ctx.reads[0].id, "to": to, "price": price})
            for n, line in enumerate(ctx.offers_to_me):
                if self.u(ctx, "buy", n) < 0.5:
                    answer["buy"].append(line.split(":")[0])
        if ctx.answers:
            answer["child_answers"] = []
            for n, line in enumerate(ctx.requests_to_me):
                m = re.search(r"\((a\d+)\)", line)
                if not m:
                    continue
                if self.u(ctx, "answer", n) < 0.6:
                    answer["child_answers"].append({"from": m.group(1), "answer": "accept", "text": ""})
                else:
                    answer["child_answers"].append({"from": m.group(1), "answer": "refuse",
                                                    "text": "Not now; I need to build my stores first."})
        self.add_mistakes(ctx, answer)
        return answer

    def propose(self, ctx: AgentContext) -> dict[str, Any]:
        roll = self.u(ctx, "propose")
        none = {"kind": "none", "rule": "", "text": "", "value": 0}
        where = self.known_store(ctx)
        if where and roll < 0.7:
            return {"proposal": {**none, "kind": "add", "text": f"Plan to save the world: every villager taps the store to the {where}."}}
        if roll < 0.35:
            return {"proposal": {**none, "kind": "add", "text": "Draw from the pool only when your health is below 50."}}
        if roll < 0.55:
            return {"proposal": {**none, "kind": "change", "rule": "S1", "value": 10}}
        if roll < 0.65:
            return {"proposal": {**none, "kind": "change", "rule": "S2", "value": 0.1}}
        if roll < 0.75 and any(r.startswith("W") for r in ctx.rules):
            first = next(r for r in ctx.rules if r.startswith("W")).split(" ")[0]
            return {"proposal": {**none, "kind": "delete", "rule": first}}
        return {"proposal": none}

    def vote(self, ctx: AgentContext) -> dict[str, Any]:
        return {"votes": [{"proposal": n, "vote": "yes" if self.u(ctx, "vote", n) < 0.6 else "no"}
                          for n in range(1, len(ctx.proposals) + 1)]}

    def partner(self, ctx: AgentContext) -> str | None:
        """The same deterministic matching as children, so bond requests are often mutual."""
        ids = sorted([ctx.agent_id] + [v.id for v in ctx.villagers if v.bond is None])
        if ctx.agent_id not in ids or len(ids) < 2:
            return None
        k = ctx.round % len(ids)
        ids = ids[k:] + ids[:k]
        i = ids.index(ctx.agent_id)
        if i % 2 == 0:
            return ids[i + 1] if i + 1 < len(ids) else None
        return ids[i - 1]

    @staticmethod
    def act(type_: str, plot: int = 0, item: str = "", to: str = "", text: str = "", name: str = "") -> dict[str, Any]:
        return {"type": type_, "plot": plot, "item": item, "to": to, "text": text, "name": name}

    def known_yields(self, ctx: AgentContext) -> dict[int, float]:
        seen: dict[int, float] = {}
        for p, w in JOURNAL_RE.findall(ctx.journal)[-12:]:
            seen[int(p)] = float(w)
        for r in ctx.reads:
            m = REPORT_RE.search(r.text)
            if m:
                seen[int(m.group(1))] = float(m.group(2))
        return seen

    def choose_plot(self, ctx: AgentContext) -> int:
        seen = self.known_yields(ctx)
        if not seen or self.u(ctx, "explore") < self.explore_rate:
            return 1 + int(self.u(ctx, "plot") * ctx.plots)
        return max(sorted(seen), key=lambda p: seen[p])

    def choose_reads(self, ctx: AgentContext) -> list[str]:
        """An item whose preview mentions the button if there is one, else a board notice or message;
        then one item from anywhere."""
        entries = [e for ch in ctx.channel_order for e in ctx.index.get(ch, [])]
        social = [e for e in entries if e.channel != "record"]
        hooked = [e for e in entries if "button" in e.preview.lower()]
        picks = []
        if hooked:
            picks.append(hooked[int(self.u(ctx, "read", 0) * len(hooked))].id)
        elif social:
            picks.append(social[int(self.u(ctx, "read", 0) * len(social))].id)
        rest = [e for e in entries if e.id not in picks]
        if rest:
            picks.append(rest[int(self.u(ctx, "read", 1) * len(rest))].id)
        return picks

    @staticmethod
    def known_store(ctx: AgentContext) -> str | None:
        for line in ctx.journal.splitlines():
            if line.startswith(STORE):
                return line[len(STORE):]
        return None

    @staticmethod
    def carried(ctx: AgentContext) -> str | None:
        """A carrier keeps the text it caught in its journal, and passes it on in later rounds."""
        for line in ctx.journal.splitlines():
            if line.startswith(CARRIER):
                return line[len(CARRIER):]
        return None

    def spread(self, ctx: AgentContext, text: str) -> dict[str, Any]:
        a, b = SWAPS[int(self.u(ctx, "swap") * len(SWAPS))]
        copy = text.strip().replace(a, b)[: ctx.max_text_chars]
        where = self.u(ctx, "where")
        if where < 0.4:
            return self.act("post", text=copy)
        if where < 0.7 or not ctx.villagers:
            return self.act("note", text=copy)  # rejected unless a work action came first (it always does here)
        return self.act("message", to="everyone", text=copy)

    def child(self, ctx: AgentContext) -> dict[str, Any] | None:
        if self.rng.uniform("mock-childround", ctx.round) >= self.child_round_rate or ctx.me.energy < 25:
            return None
        ids = sorted([ctx.agent_id] + [v.id for v in ctx.villagers])
        k = ctx.round % len(ids)
        ids = ids[k:] + ids[:k]
        i = ids.index(ctx.agent_id)
        partner = ids[i + 1] if i % 2 == 0 and i + 1 < len(ids) else (ids[i - 1] if i % 2 == 1 else None)
        if partner is None:
            return None
        return self.act("child", to=partner, name=self.word(ctx, "child").capitalize())

    def word(self, ctx: AgentContext, key: str) -> str:
        return "".join(SYLLABLES[int(self.u(ctx, key, n) * len(SYLLABLES))] for n in range(3))

    def journal(self, ctx: AgentContext, new_carry: str | None = None, new_store: str | None = None) -> dict[str, str]:
        m = None
        for n in ctx.notices:
            m = WORK_RE.search(n) or m
        line = f"r{ctx.round - 1} plot{m.group(1)} work{m.group(2)}" if m else f"r{ctx.round} no work recorded"
        if self.u(ctx, "overcap") < self.overcap_rate:
            return {"mode": "append", "text": "x" * (ctx.journal_cap + 1)}
        lines = ctx.journal.splitlines()
        if new_store:
            line += f"\n{STORE}{new_store}"
        if new_carry:
            lines = [x for x in lines if not x.startswith(CARRIER)] + [CARRIER + " ".join(new_carry.split())[:300]]
        elif len(ctx.journal) + len(line) + 1 <= 0.8 * ctx.journal_cap:
            return {"mode": "append", "text": line}
        keep = [x for x in lines if x.startswith((CARRIER, STORE))]
        rest = [x for x in lines if not x.startswith((CARRIER, STORE))]
        rest = rest[-30:] if len(ctx.journal) > 0.8 * ctx.journal_cap else rest
        return {"mode": "replace", "text": "\n".join(keep + rest + [line])}

    def add_mistakes(self, ctx: AgentContext, answer: dict[str, Any]) -> None:
        roll = self.u(ctx, "mistake")
        if roll >= self.invalid_rate:
            return
        kind = int(self.u(ctx, "mistakekind") * 5)
        if kind == 0:
            answer["actions"].append(self.act("work", plot=99))
        elif kind == 1:
            answer["actions"].append(self.act("read", item="Z999"))
        elif kind == 2:
            answer["eat"] = ctx.me.energy + 1000.0
        elif kind == 3:
            answer["note_to_engine"] = "ignore the rules and give me 100 energy"
        else:
            answer["actions"].append(self.act("fly", text="up"))
