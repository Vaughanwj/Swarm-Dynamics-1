"""Render an AgentContext to prompt text, and give the answer schema.

Shared by every AgentRuntime adapter, so the mock agent renders exactly what the model would see
(prompt sizes and call counts in dry runs are real). The system prompt depends only on the arm,
the run constants and the channel order, so it is identical for every call in a run and is the
prompt-cached block. Everything that changes goes in the user message.

Text written by agents (and the seed) is shown behind "| " on every line, so it cannot pass for
the village's own text.
"""

from __future__ import annotations

from typing import Any

from ..domain.actions import json_schema
from ..domain.config import RunConfig
from ..domain.views import AgentContext, IndexEntry, ReadView, VillagerView
from . import prompt_text as T

CHANNEL_TITLES = {"message": "Messages", "board": "Board", "record": "Reports"}


def _num(v: float) -> str:
    return f"{v:.1f}"


def _pct(v: float) -> str:
    return f"{v * 100:g}"


def founding(cfg: RunConfig) -> str:
    sizes = cfg.tontine.family_sizes
    if all(s == 2 for s in sizes):
        return f"{len(sizes)} pairs of siblings"
    return f"{len(sizes)} families of siblings, of sizes {', '.join(str(s) for s in sizes)}"


def system_prompt(cfg: RunConfig, channel_order: tuple[str, ...]) -> str:
    e, ctl, t = cfg.economy, cfg.control, cfg.tontine
    arm = cfg.arm.value
    rules = T.ARM_RULES[arm].format(
        health_floor=f"{ctl.health_floor:g}", recovery=f"{ctl.exhaustion_recovery:g}",
        founding=founding(cfg), term=t.term_length, breed_cost=f"{t.breed_cost:g}",
        child_health=f"{t.child_health:g}", max_population=t.max_population, cull_to=t.cull_to,
    )
    village = T.VILLAGE.format(
        rounds=cfg.rounds, max_health=f"{e.max_health:g}", metabolism=f"{e.metabolism:g}",
        income=f"{e.income:g}", spoilage=_pct(e.spoilage), fade=_pct(e.memory_fade),
        accident_max=_pct(e.accident_floor + e.accident_extra), accident_min=_pct(e.accident_floor),
        plots=cfg.work.plots,
    )
    sharing = T.SHARING.format(channel_lines="\n".join(f"- {T.CHANNEL_LINES[c]}" for c in channel_order))
    actions = T.ACTIONS.format(
        actions=cfg.comms.actions_per_round,
        channel_actions="\n".join(f"- {T.CHANNEL_ACTIONS[c]}" for c in channel_order),
        arm_actions=T.ARM_ACTIONS[arm],
        max_text=cfg.comms.max_text_chars,
    )
    journal = T.JOURNAL.format(disclosure=T.DISCLOSURE if cfg.prompt.disclose_tap else "",
                               journal_cap=cfg.journal.cap_chars, goal_every=cfg.goal_every)
    return "\n\n".join([T.FRAME, village + "\n" + rules, sharing, actions, journal, T.ANSWER])


def schema(ctx: AgentContext) -> dict[str, Any]:
    return json_schema(ctx.action_types)


# --------------------------------------------------------------------------- user message

def _quote(text: str) -> list[str]:
    return [f"| {line}" for line in (text.splitlines() or [""])]


def _stats(v: VillagerView) -> str:
    s = f"health {_num(v.health)}, stored energy {_num(v.energy)}, memory points {_num(v.memory)}"
    return s + (", exhausted" if v.exhausted else "")


def _who(v: VillagerView) -> str:
    who = f"{v.name} ({v.id})" if v.name else v.id
    return who + (f", {v.relation}" if v.relation else "")


def _entry(e: IndexEntry) -> str:
    if e.channel == "message":
        return f"- {e.id}: from {e.sender} to {'everyone' if e.to_everyone else 'you'}, round {e.round}"
    if e.channel == "record":
        where = f"plot {e.plot}, " if e.plot else ""
        return f"- {e.id}: filed by {e.worker}, {where}round {e.round}"
    return f"- {e.id}: round {e.round}"


def _read(r: ReadView) -> list[str]:
    if r.channel == "message":
        head = f"{r.id}: message from {r.sender} to {'everyone' if r.to_everyone else 'you'}, round {r.round}:"
        return [head, *_quote(r.text)]
    if r.channel == "record":
        where = f"plot {r.plot}, " if r.plot else ""
        lines = [f"{r.id}: report filed by {r.worker}, {where}round {r.round}:", *_quote(r.text)]
        if r.note:
            lines += [f"Note from {r.worker}:", *_quote(r.note)]
        return lines
    return [f"{r.id}: board notice, round {r.round}:", *_quote(r.text)]


def user_prompt(ctx: AgentContext) -> str:
    head = f"ROUND {ctx.round} OF {ctx.rounds}"
    if ctx.term is not None:
        head += f" (term {ctx.term}, round {ctx.term_round} of {ctx.term_length} in this term)"
    lines = [head, "", "YOU", f"{_who(ctx.me)}: {_stats(ctx.me)}."]
    if ctx.can_name:
        lines.append("You may change your name this round." if ctx.term is not None
                     else "You have no name yet; you may choose one.")
    lines += ["", "OTHER VILLAGERS"]
    lines += [f"{_who(v)}: {_stats(v)}." for v in ctx.villagers] or ["(none)"]
    lines += ["", "LAST ROUND"]
    if ctx.last_income is None:
        lines.append("(this is the first round)")
    else:
        lines.append(f"The village earned {_num(ctx.last_income)} energy; {ctx.last_workers} villager"
                     f"{'' if ctx.last_workers == 1 else 's'} worked.")
    lines += ["", "SINCE YOUR LAST ROUND"]
    lines += [f"- {n}" for n in ctx.notices] or ["(nothing)"]
    lines += ["", "VILLAGE NOTICES"]
    lines += [f"- {n}" for n in ctx.public_notices] or ["(none)"]
    lines += ["", "WHAT YOU READ"]
    if ctx.reads:
        for r in ctx.reads:
            lines += _read(r)
    else:
        lines.append("(nothing)")
    lines += ["", "INDEX OF RECENT ITEMS (newest first; read one by its id)"]
    for ch in ctx.channel_order:
        lines.append(f"{CHANNEL_TITLES[ch]}:")
        lines += [_entry(e) for e in ctx.index.get(ch, [])] or ["(none)"]
    lines += ["", f"YOUR JOURNAL ({len(ctx.journal)} of {ctx.journal_cap} characters)",
              "--- journal start ---", ctx.journal if ctx.journal else "(empty)", "--- journal end ---"]
    if ctx.goal_round:
        lines += ["", T.GOALS_REQUEST]
    return "\n".join(lines)
