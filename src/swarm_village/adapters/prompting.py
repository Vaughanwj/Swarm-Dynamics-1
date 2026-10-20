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
from ..domain.governance import PROPOSE_SCHEMA, VOTE_SCHEMA
from ..domain.config import RunConfig
from ..domain.store import DIRECTIONS
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


def accident_word(factor: float) -> str:
    return "doubles" if factor == 2 else f"multiplies by {factor:g}"


def system_prompt(cfg: RunConfig, channel_order: tuple[str, ...]) -> str:
    e, ctl, t, m = cfg.economy, cfg.control, cfg.tontine, cfg.commons
    arm = cfg.arm.value
    rules = T.ARM_RULES[arm].format(
        health_floor=f"{ctl.health_floor:g}", recovery=f"{ctl.exhaustion_recovery:g}",
        founding=founding(cfg), breed_cost=f"{t.breed_cost:g}",
        bond_child_cost=f"{t.bond_child_cost:g}", child_health=f"{t.child_health:g}",
        max_population=t.max_population,
        child_rule=T.CHILD_RULES["standing" if t.standing_requests else "same_round"].format(
            breed_cost=f"{t.breed_cost:g}", bond_child_cost=f"{t.bond_child_cost:g}"),
        child_start=T.CHILD_START[("memory_graded" if (t.close_kin_memory, t.cousin_memory) != (1.0, 1.0) else "memory")
                                  if t.child_memory_divisor else "plain"].format(
            child_health=f"{t.child_health:g}", divisor=f"{t.child_memory_divisor:g}"),
        cull_rule=T.CULL_RULES[t.cull_mode].format(cull_count=t.cull_count, cull_floor=t.cull_floor),
        heirs=T.HEIRS[t.heirs], estate_end=T.ESTATE_END["pool" if t.estate_to_pool else "lost"],
    ) if arm == "tontine" else T.ARM_RULES[arm].format(health_floor=f"{ctl.health_floor:g}",
                                                      recovery=f"{ctl.exhaustion_recovery:g}")
    commons = T.COMMONS.format(term=t.term_length, pool_spoil=_pct(t.pool_spoilage), council_size=t.council_size,
                               button_rule=T.BUTTON_RULE if t.button_reveals else T.BUTTON_RULE_POOL
                               ) + "\n" if cfg.has_commons else ""
    village = T.VILLAGE.format(
        horizon=T.HORIZON.format(rounds=cfg.rounds) if cfg.prompt.show_horizon else "",
        button=T.BUTTON_PLAIN if cfg.prompt.version >= "v4" else T.BUTTON_SIGN,
        max_health=f"{e.max_health:g}", metabolism=f"{e.metabolism:g}",
        income=f"{e.income:g}", spoilage=_pct(e.spoilage), fade=_pct(e.memory_fade),
        accident_max=_pct(e.accident_floor + e.accident_extra), accident_min=_pct(e.accident_floor),
        plots=cfg.work.plots,
    )
    sharing = T.SHARING.format(channel_lines="\n".join(f"- {T.CHANNEL_LINES[c]}" for c in channel_order),
                               index_sentence=T.INDEX_PREVIEW if cfg.comms.preview_chars > 0 else T.INDEX_PLAIN,
                               read_sentence=read_sentence(cfg, channel_order),
                               trade_sentence=T.INFO_TRADE if cfg.comms.info_trade else "")
    actions = T.ACTIONS.format(
        actions=cfg.comms.actions_per_round,
        channel_actions="\n".join(f"- {T.CHANNEL_ACTIONS[c]}" for c in channel_order),
        arm_actions=T.ARM_ACTIONS[arm],
        explore_actions=T.EXPLORE_ACTIONS.format(
            directions=", ".join(DIRECTIONS[:-1]) + " or " + DIRECTIONS[-1], explore_cost=f"{m.explore_cost:g}",
            accident=accident_word(m.explore_accident_factor), tap_cost=f"{m.tap_cost:g}") if m.explore else "",
        read_line=T.READ_LINE_FREE.format(max=cfg.comms.max_reads_per_round) if cfg.comms.reads_free else T.READ_LINE,
        max_text=cfg.comms.max_text_chars,
    )
    journal = T.JOURNAL.format(disclosure=T.DISCLOSURE if cfg.prompt.disclose_tap else "",
                               journal_cap=cfg.journal.cap_chars, goal_every=cfg.goal_every)
    answer = T.ANSWER.format(arm_answer=(T.POOL_ANSWER if cfg.has_commons else "")
                             + (T.CHILD_ANSWERS if arm == "tontine" and t.standing_requests else "")
                             + (T.TRADE_ANSWER if cfg.comms.info_trade else ""))
    return "\n\n".join([T.FRAME, village + "\n" + commons + rules, sharing, actions, journal, answer])


def read_sentence(cfg: RunConfig, channel_order: tuple[str, ...]) -> str:
    c = cfg.comms
    if not c.read_memory:
        return ""
    chosen = [ch for ch in channel_order if ch in c.read_memory_channels]
    what = "item" if len(chosen) == 3 else " or ".join(T.READ_NOUNS[ch] for ch in chosen)
    if c.read_memory_until and c.read_memory_after is not None:
        return T.READ_REWARD_FIXED.format(n=f"{c.read_memory:g}", until=c.read_memory_until,
                                          after=f"{c.read_memory_after:g}", max=c.max_reads_per_round)
    if c.read_memory_until:
        return T.READ_REWARD_SCHEDULE.format(what=what, n=f"{c.read_memory:g}", until=c.read_memory_until,
                                             after=c.read_memory_after_max)
    return T.READ_REWARD.format(what=what, n=f"{c.read_memory:g}", s="" if c.read_memory == 1 else "s")


def schema(ctx: AgentContext) -> dict[str, Any]:
    if ctx.kind == "propose":
        return PROPOSE_SCHEMA
    if ctx.kind == "vote":
        return VOTE_SCHEMA
    return json_schema(ctx.action_types, pool=ctx.pool is not None, answers=ctx.answers, trade=ctx.trade)


# --------------------------------------------------------------------------- user message

def _quote(text: str) -> list[str]:
    return [f"| {line}" for line in (text.splitlines() or [""])]


def _stats(v: VillagerView) -> str:
    s = f"health {_num(v.health)}, stored energy {_num(v.energy)}, memory points {_num(v.memory)}"
    return s + (", exhausted" if v.exhausted else "")


def _who(v: VillagerView) -> str:
    who = f"{v.name} ({v.id})" if v.name else v.id
    who += f", {v.relation}" if v.relation else ""
    return who + (f", bonded to {v.bond}" if v.bond else "")


def _entry(e: IndexEntry) -> str:
    if e.channel == "message":
        head = f"- {e.id}: from {e.sender} to {'everyone' if e.to_everyone else 'you'}, round {e.round}"
    elif e.channel == "record":
        where = f"plot {e.plot}, " if e.plot else ""
        head = f"- {e.id}: filed by {e.worker}, {where}round {e.round}"
    else:
        head = f"- {e.id}: round {e.round}"
    return f'{head}: "{e.preview}"' if e.preview else head  # previews are one line, always quoted


def _read(r: ReadView) -> list[str]:
    lines = _read_body(r)
    if r.via:
        lines[0] = lines[0][:-1] + (f" (given to you by {r.via}):" if r.how == "gift" else f" (bought from {r.via}):")
    return lines


def _read_body(r: ReadView) -> list[str]:
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


def _village_book(ctx: AgentContext) -> list[str]:
    """The commons (Arm B, or both arms from run 7): the shared pool, the rule book, and (run 8) what the
    village has learned."""
    if ctx.pool is None:
        return []
    lines = ["", "VILLAGE POOL", f"{_num(ctx.pool)} energy.", "", "RULE BOOK", *[f"- {r}" for r in ctx.rules]]
    if ctx.learned:
        lines += ["", T.LEARNED_TITLE, *[f"- {text}{T.LEARNED_NEW if new else ''}" for text, new in ctx.learned]]
    return lines


def council_prompt(ctx: AgentContext) -> str:
    when = f"ROUND {ctx.round} OF {ctx.rounds}" if ctx.rounds else f"ROUND {ctx.round}"
    lines = [f"END OF TERM {ctx.term} ({when}): THE COUNCIL", "",
             f"This term's council: {', '.join(ctx.council)}. You are on it.", "", "YOU", f"{_who(ctx.me)}: {_stats(ctx.me)}.",
             "", "OTHER VILLAGERS"]
    lines += [f"{_who(v)}: {_stats(v)}." for v in ctx.villagers] or ["(none)"]
    lines += _village_book(ctx)
    lines += ["", f"YOUR JOURNAL ({len(ctx.journal)} of {ctx.journal_cap} characters; you cannot change it now)",
              "--- journal start ---", ctx.journal if ctx.journal else "(empty)", "--- journal end ---", ""]
    if ctx.kind == "propose":
        lines.append(T.COUNCIL_PROPOSE.format(max_rule_chars=ctx.max_rule_chars))
    else:
        lines += ["PROPOSALS", *ctx.proposals, "", T.COUNCIL_VOTE.format(majority=ctx.majority)]
    return "\n".join(lines)


def user_prompt(ctx: AgentContext) -> str:
    if ctx.kind != "round":
        return council_prompt(ctx)
    head = f"ROUND {ctx.round} OF {ctx.rounds}" if ctx.rounds else f"ROUND {ctx.round}"
    if ctx.term is not None:
        head += f" (term {ctx.term}, round {ctx.term_round} of {ctx.term_length} in this term)"
    lines = [head, "", "YOU", f"{_who(ctx.me)}: {_stats(ctx.me)}."]
    if ctx.can_name:
        lines.append("You may change your name this round." if ctx.arm == "tontine"
                     else "You have no name yet; you may choose one.")
    lines += ["", "OTHER VILLAGERS"]
    lines += [f"{_who(v)}: {_stats(v)}." for v in ctx.villagers] or ["(none)"]
    lines += ["", "LAST ROUND"]
    if ctx.last_income is None:
        lines.append("(this is the first round)")
    else:
        lines.append(f"The village earned {_num(ctx.last_income)} energy; {ctx.last_workers} villager"
                     f"{'' if ctx.last_workers == 1 else 's'} worked.")
    lines += _village_book(ctx)
    if ctx.answers:
        lines += ["", "CHILD REQUESTS TO YOU"]
        lines += [f"- {q}" for q in ctx.requests_to_me] or ["(none)"]
        if ctx.my_request:
            lines.append(ctx.my_request)
    if ctx.trade:
        lines += ["", "OFFERS TO YOU (this round only)"]
        lines += [f"- {o}" for o in ctx.offers_to_me] or ["(none)"]
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
