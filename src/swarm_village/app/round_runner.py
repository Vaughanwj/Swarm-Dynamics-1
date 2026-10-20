"""RoundRunner: one round, all agents.

Every living agent decides from the same snapshot (one runtime call each, in parallel when the
runtime allows); the engine then validates and applies the answers in an order drawn by lot, and
resolves the round.
"""

from __future__ import annotations

from ..domain.actions import Decision, parse
from ..domain.village import Village
from ..ports import AgentRuntimePort, Reply


def to_decision(reply: Reply | None, village: Village) -> Decision:
    if reply is None or reply.fallback:
        return Decision(fallback=True)
    return parse(reply.raw, village.types, village.cfg.comms.max_text_chars)


class RoundRunner:
    def __init__(self, village: Village, runtime: AgentRuntimePort) -> None:
        self.village = village
        self.runtime = runtime

    def run(self, round_: int) -> None:
        v = self.village
        v.begin_round(round_)
        contexts = v.contexts()
        replies = self.runtime.decide_batch(contexts)
        by_agent = {r.agent_id: r for r in replies}
        for agent_id in v.order:
            reply = by_agent.get(agent_id)
            v.ledger.emit("decision", agent=agent_id, raw=reply.raw if reply else None,
                          fallback=reply is None or reply.fallback, error=reply.error if reply else "no reply")
            v.apply(agent_id, to_decision(reply, v))
        v.resolve()
