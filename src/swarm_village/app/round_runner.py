"""RoundRunner: one round, all agents.

Every living agent decides from the same snapshot (one runtime call each, in parallel when the
runtime allows); the engine then validates and applies the answers in an order drawn by lot, and
resolves the round. In Arm B, a term's last round ends with the council: its members propose, then
vote, each as one more runtime call.
"""

from __future__ import annotations

from ..domain.actions import Decision, parse
from ..domain.village import Village
from ..ports import AgentRuntimePort, Reply


def to_decision(reply: Reply | None, village: Village) -> Decision:
    if reply is None or reply.fallback:
        return Decision(fallback=True)
    return parse(reply.raw, village.types, village.cfg.comms.max_text_chars, pool=village.commons,
                 answers=village.tontine and village.cfg.tontine.standing_requests,
                 trade=village.cfg.comms.info_trade,
                 bond_answers=village.tontine and village.cfg.tontine.standing_bonds,
                 family=village.family_round(), referendum=village.referendum_active())


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
        if v.governance_due():
            self.council()

    def council(self) -> None:
        v = self.village
        members = v.council()
        v.ledger.emit("council", members=members)
        replies = {r.agent_id: r for r in self.runtime.decide_batch(v.governance_contexts("propose", members))}
        proposals = v.collect_proposals(members, replies)
        votes = {}
        if proposals:
            votes = {r.agent_id: r for r in self.runtime.decide_batch(v.governance_contexts("vote", members, proposals))}
        v.settle_votes(members, proposals, votes)
