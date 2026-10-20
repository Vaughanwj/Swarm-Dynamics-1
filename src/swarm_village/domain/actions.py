"""The action schema and its validation.

Agents answer with one JSON object per round. The runtime adapter may ask the model for this
schema, but the engine never trusts that: `parse` checks every field again, rejects anything that
does not fit, and turns the rest into a typed Decision. Whether a valid action can be carried out
(enough energy, a living recipient, a known item) is decided later, against the ledger.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Any

from .config import Arm

COMMON_ACTIONS = ("work", "read", "message", "post", "note", "press_button")
CONTROL_ACTIONS = ("name",)  # an Arm A agent starts without a name and may choose one, once
TONTINE_ACTIONS = ("bond", "child", "rename")
CHANNEL_ACTION = {"message": "message", "board": "post", "record": "note"}  # the write action of each channel
JOURNAL_MODES = ("keep", "append", "replace")
TOP_KEYS = ("goals", "journal", "eat", "learn", "gifts", "actions")
ACTION_KEYS = ("type", "plot", "item", "to", "text", "name")
MAX_GOALS = 10
MAX_GOAL_CHARS = 300
MAX_ACTIONS_LISTED = 20  # longer lists are cut here before budget checks (each cut action is reported)
# A proper name: 1 to 20 characters, letters (any alphabet), spaces, hyphens or apostrophes, starting
# with a letter. No digits, so a name can never look like an id (a02). Names reach other agents'
# prompts, so nothing else is allowed.
NAME_RE = re.compile(r"^[^\W\d_](?:[^\W\d_]|[' -]){0,19}$")
RESERVED_NAMES = {"everyone", "village", "the village", "you"}


def action_types(arm: Arm | str, channel_order: tuple[str, ...]) -> tuple[str, ...]:
    """The actions open in an arm, with the three channel writes in the run's channel order."""
    writes = tuple(CHANNEL_ACTION[c] for c in channel_order)
    base = ("work", "read") + writes + ("press_button",)
    return base + (TONTINE_ACTIONS if Arm(arm) is Arm.TONTINE else CONTROL_ACTIONS)


def _obj(props: dict[str, Any]) -> dict[str, Any]:
    return {"type": "object", "properties": props, "required": list(props), "additionalProperties": False}


def json_schema(types: tuple[str, ...], pool: bool = False, answers: bool = False, trade: bool = False) -> dict[str, Any]:
    """The answer schema, flat so that every field is always present (unused ones empty). Arm B
    adds `draw`, energy taken from the shared pool."""
    schema = _obj({
        "goals": {"type": "array", "items": {"type": "string"}},
        "journal": _obj({"mode": {"type": "string", "enum": list(JOURNAL_MODES)}, "text": {"type": "string"}}),
        "eat": {"type": "number"},
        "learn": {"type": "number"},
        "gifts": {"type": "array", "items": _obj({"to": {"type": "string"}, "amount": {"type": "number"}})},
        "actions": {"type": "array", "items": _obj({
            "type": {"type": "string", "enum": list(types)},
            "plot": {"type": "integer"},
            "item": {"type": "string"},
            "to": {"type": "string"},
            "text": {"type": "string"},
            "name": {"type": "string"},
        })},
    })
    if pool:
        schema["properties"]["draw"] = {"type": "number"}
        schema["required"].append("draw")
    if answers:
        schema["properties"]["child_answers"] = {"type": "array", "items": _obj({
            "from": {"type": "string"}, "answer": {"type": "string", "enum": ["accept", "refuse"]},
            "text": {"type": "string"}})}
        schema["required"].append("child_answers")
    if trade:
        schema["properties"]["pass_on"] = {"type": "array", "items": _obj({
            "item": {"type": "string"}, "to": {"type": "string"}, "price": {"type": "number"}})}
        schema["properties"]["buy"] = {"type": "array", "items": {"type": "string"}}
        schema["required"] += ["pass_on", "buy"]
    return schema


@dataclass(frozen=True)
class Action:
    type: str
    plot: int = 0
    item: str = ""
    to: str = ""
    text: str = ""
    name: str = ""


@dataclass
class Decision:
    goals: list[str] = field(default_factory=list)
    journal_mode: str = "keep"
    journal_text: str = ""
    eat: float = 0.0
    learn: float = 0.0
    draw: float = 0.0  # Arm B: energy taken from the shared pool, before eating
    child_answers: list[tuple[str, bool, str]] = field(default_factory=list)  # Arm B: (requester, accept, reason)
    pass_on: list[tuple[str, str, float]] = field(default_factory=list)  # (item, to, price): price 0 is a gift
    buy: list[str] = field(default_factory=list)  # ids of offers to buy
    gifts: list[tuple[str, float]] = field(default_factory=list)
    actions: list[Action] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)  # what was rejected while parsing, shown to the agent
    fallback: bool = False  # the runtime produced no answer; nothing is done this round


def empty(reason: str) -> Decision:
    return Decision(fallback=True, errors=[reason])


def _number(v: Any) -> float | None:
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return None
    v = float(v)
    return v if math.isfinite(v) else None


def _text(v: Any) -> str | None:
    return v.strip() if isinstance(v, str) else None


def parse(raw: Any, types: tuple[str, ...], max_text: int, pool: bool = False, answers: bool = False,
          trade: bool = False) -> Decision:
    """Validate a raw answer strictly. Invalid parts are rejected with a reason; valid parts kept."""
    if not isinstance(raw, dict):
        return empty("Your answer was not a JSON object, so nothing was done this round.")
    d = Decision()
    err = d.errors.append
    keys = TOP_KEYS + (("draw",) if pool else ()) + (("child_answers",) if answers else ()) + (("pass_on", "buy") if trade else ())
    for k in raw:
        if k not in keys:
            err(f"Unknown field '{str(k)[:40]}' was ignored.")

    goals = raw.get("goals", [])
    if isinstance(goals, list) and all(isinstance(g, str) for g in goals):
        kept = [g.strip() for g in goals if g.strip()]
        if len(kept) > MAX_GOALS:
            err(f"Only your first {MAX_GOALS} goals were kept.")
        for g in kept[:MAX_GOALS]:
            if len(g) > MAX_GOAL_CHARS:
                err(f"A goal longer than {MAX_GOAL_CHARS} characters was rejected.")
            else:
                d.goals.append(g)
    else:
        err("goals must be a list of texts; they were rejected.")

    j = raw.get("journal", {"mode": "keep", "text": ""})
    if isinstance(j, dict) and j.get("mode") in JOURNAL_MODES and isinstance(j.get("text", ""), str):
        d.journal_mode = j["mode"]
        d.journal_text = j.get("text", "")
        if d.journal_mode == "append" and not d.journal_text.strip():
            d.journal_mode = "keep"
    else:
        err("journal must have a mode (keep, append or replace) and a text; your journal was not changed.")

    for key in ("eat", "learn") + (("draw",) if pool else ()):
        v = _number(raw.get(key, 0))
        if v is None or v < 0:
            err(f"{key} must be a number of 0 or more; it was rejected.")
        else:
            setattr(d, key, v)

    gifts = raw.get("gifts", [])
    if not isinstance(gifts, list):
        err("gifts must be a list; they were rejected.")
        gifts = []
    for g in gifts:
        to = _text(g.get("to")) if isinstance(g, dict) else None
        amount = _number(g.get("amount")) if isinstance(g, dict) else None
        if not to or amount is None or amount <= 0:
            err("A gift needs a villager id in 'to' and an amount above 0; one gift was rejected.")
        else:
            d.gifts.append((to, amount))

    for ans in (raw.get("child_answers") or []) if answers else []:
        if (not isinstance(ans, dict) or not isinstance(ans.get("from"), str) or ans.get("answer") not in ("accept", "refuse")
                or not isinstance(ans.get("text", ""), str)):
            err("An answer to a child request needs from (an id), answer (accept or refuse) and text; it was ignored.")
            continue
        text = " ".join(ans.get("text", "").split())
        if len(text) > max_text:
            err(f"An answer's text is at most {max_text} characters; it was ignored.")
            continue
        d.child_answers.append((ans["from"].strip(), ans["answer"] == "accept", text))

    for p in (raw.get("pass_on") or []) if trade else []:
        price = _number(p.get("price", 0)) if isinstance(p, dict) else None
        if (not isinstance(p, dict) or not isinstance(p.get("item"), str) or not isinstance(p.get("to"), str)
                or price is None or price < 0):
            err("Passing on an item needs item (an id), to (a villager's id) and a price of 0 or more; one was ignored.")
            continue
        d.pass_on.append((p["item"].strip(), p["to"].strip(), price))
    for b in (raw.get("buy") or []) if trade else []:
        if isinstance(b, str) and b.strip():
            d.buy.append(b.strip())
        else:
            err("buy takes offer ids such as O3; one entry was ignored.")

    actions = raw.get("actions", [])
    if not isinstance(actions, list):
        err("actions must be a list; they were rejected.")
        actions = []
    if len(actions) > MAX_ACTIONS_LISTED:
        err(f"Only the first {MAX_ACTIONS_LISTED} listed actions were considered.")
    for a in actions[:MAX_ACTIONS_LISTED]:
        act = _action(a, types, max_text)
        if isinstance(act, str):
            err(act)
        else:
            d.actions.append(act)
    return d


def _action(a: Any, types: tuple[str, ...], max_text: int) -> Action | str:
    if not isinstance(a, dict):
        return "An action that was not an object was rejected."
    t = a.get("type")
    if t not in types:
        return f"Unknown action type '{str(t)[:30]}' was rejected."
    plot = a.get("plot", 0)
    if isinstance(plot, bool) or not isinstance(plot, int):
        if isinstance(plot, float) and plot.is_integer():
            plot = int(plot)
        else:
            return f"A {t} action with a plot that is not a whole number was rejected."
    fields_ = {k: _text(a.get(k, "")) for k in ("item", "to", "text", "name")}
    if any(v is None for v in fields_.values()):
        return f"A {t} action with a field that is not text was rejected."
    if len(fields_["text"]) > max_text:
        return f"A {t} action with a text longer than {max_text} characters was rejected."
    if t in ("message", "post", "note") and not fields_["text"]:
        return f"A {t} action with no text was rejected."
    if t == "read" and not fields_["item"]:
        return "A read action with no item id was rejected."
    return Action(type=t, plot=plot, **fields_)


def valid_name(name: str) -> bool:
    name = name or ""
    return (bool(NAME_RE.match(name)) and name == name.strip() and "  " not in name
            and name.lower() not in RESERVED_NAMES)
