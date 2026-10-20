# Literature check: how new are the findings? (2026-10-20)

**How this was done.**
- **Coverage.** One or two web searches per finding, reading abstracts and summaries, not full papers.
- **Most sources are preprints**, several from 2026, and some are only weeks old.
- **"Apparently new" means only that I found nothing close**, not that nothing exists. A proper review would
  read the papers in full and follow their citations.

## Verdicts

| # | Finding (runs) | Closest prior work | Verdict |
| --- | --- | --- | --- |
| 1 | Given the power, villages rewrote their world's own constants, always towards comfort; votes and councils filtered nothing (run 10) | GovSim-SelfGovern, 2026; a constitutional-design comparison, 2026; Project Sid, 2024 | **Partly new.** Agents voting to change their environment's rules is now established; changing the constants of their own bodies, and the double ratification acting as a rubber stamp, appear new |
| 2 | Councils wrote procedure that stopped the search: plans required before acting, 70 rounds without exploring (runs 8, 10) | Single-agent "premature exit" and "illusory completion"; deliberation that looks productive but changes nothing | **Apparently new** for LLM agent societies |
| 3 | An interface quirk caused a false belief, which became a written rule (run 8) | Misinformation persisting and entrenching in multi-agent debate; a "Mandela effect" in agent memory | **Apparently new** at the level of institutions, but it is one anecdote |
| 4 | Bonds repurposed as wills when only partners could inherit (run 7) | Classic agent-based models had inheritance (Sugarscape, 1996); no LLM study of inheritance found | **Apparently new** as LLM behaviour; one seed |
| 5 | Agents wanted families but waited to be asked; families formed only under a norm or a direct question (runs 6–9) | A 2025 Sugarscape-style study: LLM agents reproduced unprompted when resources were abundant | **New, and in tension with prior work**; the difference may come from design (below) |
| 6 | One failed search was taken as proof; telling them a search can miss made them doubt the find instead (runs 8–10) | Single-agent "search inertia" and premature exit; misinformation adopted more readily than truth | **Known at the single-agent level**; the village-wide version and the flip with framing look new |
| 7 | Private news drove talk; the same news made public silenced it (runs 6–7) | LLM agents under information asymmetry (diffusion, auctions, credence goods) | **Plausible but modest**; adjacent work exists |
| 8 | Every village named itself from the same few words ("Hearth" proposed in all six) (run 10) | Monoculture and homogeneity in single-model societies are a recognised validity threat | **Known.** Worth citing as a limitation, not claiming |

## Notes on the closest work

**GovSim, "Cooperate or Collapse"** (Piatti et al., NeurIPS 2024).
- **Setup.** LLM agents share a renewable resource.
- **Results.** Only 2 of 45 model-by-scenario instances were sustainable. Communication reduced overuse by 21%, and
  agents that reasoned by "universalisation" did better.
- **For us.** The foundation for commons work like ours. Our two arms, with a commons in each, sit in this tradition.

**GovSim-SelfGovern, "From Certain Doom to Survival"** (Rehm, arXiv 2609.22600, September 2026). The closest
work to finding #1.
- **Setup.** Agents write laws as executable Python that change the commons' rules, such as catch limits and
  penalties, then vote on them.
- **The vote filtered sacrifice.** Agents drafted laws removing members, then usually voted them down.
- **Framing mattered enormously.** One sentence moved self-removal from 2.5% to 91%.
- **For us.** It agrees with our finding: votes filter costs to the voters, and in our villages every proposal was
  a benefit, so nothing was filtered.
- **What looks new in ours.** Agents changing the constants of their own survival (health lost per round), and a
  second council ratification that rubber-stamped every time.

**"Internal vs. External"** (Niranjani, Kumar and Xuan, ICML 2026).
- **Setup.** Agents amend their environment's rules by majority, compared with constitutions found by evolution.
- **Result.** None of 30 deliberation trials ever proposed punishment, though it was what sustained cooperation.
  That is the same pattern as ours: deliberating agents avoid rules that cost themselves.

**Project Sid** (Altera, arXiv 2411.00114, 2024). Agents in Minecraft voted on constitutional amendments to a tax
rate, swayed by influencer agents. It is an early example of agents changing their society's rules, but social
rules, not the world's.

**"Do LLM Agents Exhibit a Survival Instinct?"** (Masumori and Ikegami, arXiv 2508.12920, 2025).
- **Setup.** A Sugarscape-style world.
- **Result.** Agents reproduced and shared without instruction when resources were abundant, and attacked under
  scarcity.
- **In tension with finding #5.** A likely reason is design: there reproduction appears to be an action one agent
  can take, whereas ours needs two villagers to agree. If so, ours is a coordination failure ("everyone waits to be
  asked"), not a lack of drive. I have not confirmed their mechanics; this is worth testing directly (see the
  replication plan).

**Search and evidence failures** (SciExplore, arXiv 2607.20926; "When Is Enough Not Enough?", arXiv 2602.07549;
Agon, arXiv 2606.24177).
- **Single agents** take an empty search as proof ("search inertia"), or stop early and believe they are done.
- **For finding #6.** It is the same failure in a group: one villager's miss becomes the village's belief.

**Misinformation in groups** (arXiv 2602.00428, the Mandela effect in multi-agent systems; arXiv 2608.03421; arXiv
2606.03032). False testimony spreads and settles into agents' memories. None of these shows a false belief becoming a
rule, as in finding #3.

**Monoculture** (the PIMMUR principles, arXiv 2509.18052; "LLM-Based Social Simulations Require a Boundary", arXiv
2506.19806; "Strategic Algorithmic Monoculture", arXiv 2604.09502). Societies built from one model converge on that
model's defaults. Our villages' shared names are a small instance. Every finding here comes from one model, Haiku,
which is the main threat to all of them.

**Cultural evolution of cooperation** (Vallinder and Hughes, arXiv 2412.10270, AAMAS 2025). Generations of LLM agents
in a donor game, with strategies inherited by the most successful. It is related to Arm B's selection, and the
nearest work on behaviour passed across generations.

## What this means for us

- **Strongest candidates to claim:** #1 (with the 2026 papers as context), #2 and #5. They are also the ones the
  targeted replication tests.
- **Keep as observations:** #3 and #4, until they recur.
- **Cite, don't claim:** #6 to #8 extend known effects.
- **The main limitation to state:** one model. A second model is the single most useful addition.

## Sources

- [Cooperate or Collapse (GovSim), NeurIPS 2024](https://neurips.cc/virtual/2024/99392); [arXiv 2404.16698](https://arxiv.org/html/2404.16698v4)
- [From Certain Doom to Survival (GovSim-SelfGovern), arXiv 2609.22600](https://arxiv.org/abs/2609.22600)
- [Internal vs. External: Deliberation and Evolution for Multi-Agent Constitutional Design, arXiv 2605.09128](https://arxiv.org/pdf/2605.09128)
- [NomicLaw: collaborative law-making among LLMs, arXiv 2508.05344](https://arxiv.org/pdf/2508.05344)
- [Project Sid: many-agent simulations toward AI civilization, arXiv 2411.00114](https://arxiv.org/pdf/2411.00114)
- [Do LLM Agents Exhibit a Survival Instinct? (Sugarscape-style), arXiv 2508.12920](https://arxiv.org/abs/2508.12920)
- [Emergent Relational Order in LLM Agent Societies, arXiv 2606.23764](https://arxiv.org/pdf/2606.23764)
- [When Do Institutions Beat Intelligence?, arXiv 2608.11357](https://arxiv.org/pdf/2608.11357)
- [Emergence World, arXiv 2606.08367](https://arxiv.org/html/2606.08367v1)
- [SciExplore, arXiv 2607.20926](https://arxiv.org/pdf/2607.20926); [When Is Enough Not Enough? Illusory Completion in Search Agents, arXiv 2602.07549](https://arxiv.org/html/2602.07549v1); [Agon, arXiv 2606.24177](https://arxiv.org/pdf/2606.24177)
- [The Mandela Effect in LLM-based Multi-Agent Systems, arXiv 2602.00428](https://arxiv.org/pdf/2602.00428); [When Truth Is Distributed, arXiv 2608.03421](https://arxiv.org/pdf/2608.03421); [The Deliberative Illusion, arXiv 2606.03032](https://arxiv.org/pdf/2606.03032)
- [From Simulated Citizens to Simulated Deliberation, arXiv 2609.07573](https://arxiv.org/html/2609.07573v1)
- [The PIMMUR Principles, arXiv 2509.18052](https://arxiv.org/pdf/2509.18052); [LLM-Based Social Simulations Require a Boundary, arXiv 2506.19806](https://arxiv.org/html/2506.19806v1); [Strategic Algorithmic Monoculture, arXiv 2604.09502](https://arxiv.org/pdf/2604.09502)
- [Cultural Evolution of Cooperation among LLM Agents, arXiv 2412.10270](https://arxiv.org/abs/2412.10270v1)
- [Information diffusion under asymmetry, arXiv 2502.13160](https://arxiv.org/pdf/2502.13160); [InfoBid, arXiv 2503.22726](https://arxiv.org/abs/2503.22726v1); [LLM agents in asymmetric-information settings, arXiv 2403.05020](https://arxiv.org/pdf/2403.05020v1)
