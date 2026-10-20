"""The rule book and the council (Arm B, from Milestone 5). Pure functions: no ledger, no I/O.

The rule book holds two kinds of rule:
- settings, which the village's code enforces, from a fixed list (SETTINGS), each with bounds;
- written rules, free text the code records and shows to everyone but does not enforce.

At the end of every term the healthiest villagers form a council. Each member may propose one change
(add a written rule, change a rule, delete a rule); then the council votes on every proposal, and a
proposal passes with a majority of the council. Passed changes apply in proposal order from the next
round. A change aimed at a rule that an earlier passed proposal deleted in the same session is void.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from . import referendum as ref
from .actions import valid_name

PROPOSAL_KINDS = ("none", "add", "change", "delete", "referendum")

# id -> (setting name, what it means, initial value, lowest, highest). A draw limit of None is "no
# limit"; proposals give a value below 0 for that.
SETTINGS: dict[str, dict[str, Any]] = {
    "S1": {"name": "pool_draw_limit", "label": "Most energy one villager may draw from the pool in a round",
           "initial": None, "min": 0.0, "max": 1000.0},
    "S2": {"name": "pool_income_share", "label": "Share of each round's village income put into the pool before "
           "it is split", "initial": 0.0, "min": 0.0, "max": 0.5},
    # Run 10, Arm B only: what the pool spends on each child's education each round, in its first terms.
    "S3": {"name": "education_spend", "label": "Energy the pool spends on each child's education each round, in its "
           "first three terms of life", "initial": 0.0, "min": 0.0, "max": 10.0},
}


def initial_rules(education: bool = False) -> list[dict[str, Any]]:
    return [{"id": rid, "kind": "setting", "setting": s["name"], "value": s["initial"]} for rid, s in SETTINGS.items()
            if rid != "S3" or education]


def setting(rules: list[dict[str, Any]], name: str) -> Any:
    for r in rules:
        if r["kind"] == "setting" and r["setting"] == name:
            return r["value"]
    raise KeyError(name)


def _fmt_value(rid: str, value: Any) -> str:
    if rid == "S1":
        return "no limit" if value is None else f"{value:g} energy"
    if rid == "S3":
        return f"{value:g} energy"
    return f"{value * 100:g}%"


def describe(rule: dict[str, Any]) -> str:
    if rule["kind"] == "setting":
        return f"{rule['id']} (setting, enforced): {SETTINGS[rule['id']]['label']}: {_fmt_value(rule['id'], rule['value'])}."
    return f"{rule['id']} (written): {rule['text']}"


@dataclass(frozen=True)
class Proposal:
    by: str  # agent id
    kind: str  # add | change | delete; referendum (a question for the village); ratify (the village's, run 10)
    rule: str = ""  # target rule id (change, delete); a value id or "name" (referendum, ratify)
    text: str = ""  # add, or change of a written rule; referendum and ratify: what is proposed, in words
    value: float | None = None  # change of a setting (None: no limit, for S1); referendum: the new value
    name: str = ""  # referendum or ratify on the village's name: the name

    def describe(self, rules: list[dict[str, Any]]) -> str:
        if self.kind == "referendum":
            return f"put to the village at its referendum: {self.text}"
        if self.kind == "ratify":
            return f"enact the referendum result: {self.text}"
        if self.kind == "add":
            return f'add a written rule: "{self.text}"'
        if self.kind == "delete":
            target = next((r for r in rules if r["id"] == self.rule), None)
            what = "return it to its starting value" if target and target["kind"] == "setting" else "remove it"
            return f"delete {self.rule} ({what})"
        if self.rule in SETTINGS:
            return f"change {self.rule} to {_fmt_value(self.rule, self.value)}"
        return f'change {self.rule} to: "{self.text}"'


def parse_proposal(raw: Any, by: str, rules: list[dict[str, Any]], max_chars: int,
                   referendum: dict[str, Any] | None = None) -> tuple[Proposal | None, str | None]:
    """(proposal, error). (None, None) means the member proposed nothing. `referendum` is set when this
    council may put a question to the village: {"round", "arm", "cfg"} (run 10)."""
    p = raw.get("proposal") if isinstance(raw, dict) else None
    if not isinstance(p, dict) or p.get("kind") not in PROPOSAL_KINDS:
        return None, "Your proposal was not understood, so you proposed nothing."
    kind = p["kind"]
    if kind == "none":
        return None, None
    if kind == "referendum":
        if referendum is None:
            return None, "No referendum is due before the next council, so you proposed nothing."
        target = str(p.get("rule") or "").strip()
        if target.lower() == "name":
            name = " ".join(str(p.get("text") or "").split())
            if not valid_name(name):
                return None, "A new name for the village is 1 to 20 letters, spaces, hyphens or apostrophes; you proposed nothing."
            return Proposal(by, "referendum", rule="name", name=name, text=f"name the village {name}"), None
        value, error = ref.parse_value(target, p.get("value"), referendum["arm"])
        if error:
            return None, error
        cfg = referendum["cfg"]
        label = ref.VALUES[target]["label"]
        text = (f"change {target} ({label}) from {ref.fmt(target, ref.current(cfg, target))} to "
                f"{ref.fmt(target, value)}")
        return Proposal(by, "referendum", rule=target, value=value, text=text), None
    rule = str(p.get("rule") or "").strip()
    text = " ".join(str(p.get("text") or "").split())
    ids = {r["id"] for r in rules}
    if kind == "add":
        if not text:
            return None, "A new written rule needs a text; you proposed nothing."
        if len(text) > max_chars:
            return None, f"A written rule is at most {max_chars} characters; you proposed nothing."
        return Proposal(by, "add", text=text), None
    if rule not in ids:
        return None, f"There is no rule '{rule[:12]}' in the rule book; you proposed nothing."
    if kind == "delete":
        return Proposal(by, "delete", rule=rule), None
    if rule in SETTINGS:
        v = p.get("value")
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
            return None, f"A change to {rule} needs a number in value; you proposed nothing."
        s = SETTINGS[rule]
        if rule == "S1" and v < 0:
            return Proposal(by, "change", rule=rule, value=None), None
        if not s["min"] <= v <= s["max"]:
            return None, (f"{rule} must be between {_fmt_value(rule, s['min'])} and {_fmt_value(rule, s['max'])}; "
                          "you proposed nothing.")
        return Proposal(by, "change", rule=rule, value=float(v)), None
    if not text or len(text) > max_chars:
        return None, f"A changed written rule needs a text of 1 to {max_chars} characters; you proposed nothing."
    return Proposal(by, "change", rule=rule, text=text), None


def parse_votes(raw: Any, n: int) -> tuple[dict[int, bool], list[str]]:
    """Votes by proposal number (1..n). Missing votes are abstentions, which count as no."""
    out: dict[int, bool] = {}
    errors = []
    votes = raw.get("votes") if isinstance(raw, dict) else None
    if not isinstance(votes, list):
        return out, ["Your votes were not understood, so you abstained."]
    for v in votes:
        num = v.get("proposal") if isinstance(v, dict) else None
        if isinstance(num, bool) or not isinstance(num, int) or not 1 <= num <= n or v.get("vote") not in ("yes", "no"):
            errors.append("One vote was not understood and was ignored.")
            continue
        out[num] = v["vote"] == "yes"
    return out, errors


def next_written(rules: list[dict[str, Any]], used: int = 0) -> int:
    """The next written-rule number: past every id in the book and every number used before, so a
    deleted rule's id is never reused."""
    return 1 + max([used] + [int(r["id"][1:]) for r in rules if r["kind"] == "written"])


def enact(rules: list[dict[str, Any]], passed: list[Proposal], used: int = 0
          ) -> tuple[list[dict[str, Any]], list[tuple[Proposal, str]]]:
    """Apply passed proposals in order. Returns the new rule book and (proposal, outcome) pairs.
    `used` is the highest written-rule number ever given out."""
    book = [dict(r) for r in rules]
    used = next_written(rules, used) - 1  # the book as it stood before this session counts as used
    outcomes = []
    for p in passed:
        if p.kind not in ("add", "change", "delete"):
            continue  # referendums and ratifications are the village's business, not the rule book's
        if p.kind == "add":
            n = next_written(book, used)
            used = n
            rid = f"W{n}"
            book.append({"id": rid, "kind": "written", "text": p.text})
            outcomes.append((p, f"added {rid}"))
            continue
        target = next((r for r in book if r["id"] == p.rule), None)
        if target is None:
            outcomes.append((p, "void: the rule was deleted earlier in this session"))
            continue
        if p.kind == "delete":
            if target["kind"] == "setting":
                target["value"] = SETTINGS[p.rule]["initial"]
                outcomes.append((p, f"{p.rule} returned to its starting value"))
            else:
                book.remove(target)
                outcomes.append((p, f"deleted {p.rule}"))
        elif target["kind"] == "setting":
            target["value"] = p.value
            outcomes.append((p, f"{p.rule} changed"))
        else:
            target["text"] = p.text
            outcomes.append((p, f"{p.rule} changed"))
    return book, outcomes


def majority(council_size: int) -> int:
    return council_size // 2 + 1


# --------------------------------------------------------------------------- answer schemas

def _obj(props: dict[str, Any]) -> dict[str, Any]:
    return {"type": "object", "properties": props, "required": list(props), "additionalProperties": False}


PROPOSE_SCHEMA = _obj({"proposal": _obj({
    "kind": {"type": "string", "enum": list(PROPOSAL_KINDS)},
    "rule": {"type": "string"},
    "text": {"type": "string"},
    "value": {"type": "number"},
})})

VOTE_SCHEMA = _obj({"votes": {"type": "array", "items": _obj({
    "proposal": {"type": "integer"},
    "vote": {"type": "string", "enum": ["yes", "no"]},
})}})
