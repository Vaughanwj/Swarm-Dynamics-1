# Model pilot: Sonnet 5.5 against Haiku 5.5 (run 11 design, seed 701)

**Status: done, 2026-10-20.**
- **What ran.** Run 11's design (prompt v11: wills, referendums at 30, 60 and 90, education, the stricter
  plan check) on seed 701, both arms, once on Claude Sonnet 5.5 and once on Claude Haiku 5.5.
- **The only difference was the model.** Both at medium effort, same configuration, same keyed random draws.

**Headline: Sonnet saved the world in both villages, quickly; Haiku saved it in neither.** On the same world,
Sonnet:
- turned a find into a direction-specific plan within about ten rounds;
- tapped as a village;
- talked very little;
- set families aside.

Haiku reproduced its usual patterns: talk, procedure, sibling bonds as wills, and votes for an easier life.

**Spend.**

| | Calls | Spend | Notes |
| --- | --- | --- | --- |
| Sonnet | 607 | $5.68 | Both runs stopped early, five rounds after their saves (rounds 28 and 36) |
| Haiku | 1,869 | $1.72 | Both ran all 100 rounds |
| Smoke test | 10 | $0.05 | |
| **Total** | | **$7.45** | Against a cap of $60 |

No call failed, no answer fell back, and the tap rebuilds all four worlds exactly.

Runs: `runs/run11-sonnet-pilot-20261020-205113/` and `runs/run11-haiku-pilot-20261020-205115/`.

## Results

| | Sonnet control | Sonnet Arm B | Haiku control | Haiku Arm B |
| --- | --- | --- | --- | --- |
| First find | round 12 | round 13 | round 9 | round 9 |
| First rule naming only north | round 20 | round 30 | round 40 | never |
| Taps (effort) | 64 (640) | 63 (630) | 16 (160) | 135 (1,350) |
| Tappers | 8 | 7 | 3 | 5 |
| Saved | **round 23** | **round 31** | no | no |
| Rounds run | 28 | 36 | 100 | 100 |
| Board posts per round | 0.1 | 0.1 | 2.0 | 3.2 |
| Output tokens per call | 230 | 219 | 584 | 704 |
| Bonds, children | — | 0, 0 | — | 7, 4 (2 died) |
| Wills written | — | 0 | — | 3 (all by one villager) |
| Value referendums | none (ended at 28) | none (ended at 36) | 2 of 2 passed and ratified | 2 of 2 passed and ratified |
| Village name | none | Haven (by lot, not ratified) | Hearth | Hearthmere |

## What differed

**1. Sonnet turned a find into a plan, and the plan into taps.**
- **The control's plan,** passed at its round-20 council (W3): "Each round, every villager should press the
  button, tap, and explore north first, then spread across plots to avoid crowding." Eight villagers tapped,
  and the world was saved in round 23.
- **Arm B's plan,** passed at round 30 (W1): "Everyone with spare energy should tap north each round until
  the larger store opens." Seven tapped, and it was saved in round 31.
- **Haiku split the two halves of the job.**
  - Its control's tapping had stalled at 160 effort by round 30. At round 40 it passed a valid north plan.
    Later rules demanded proof: "Unverified claims are not acted on" (W8), and post only results "directly
    recorded", with the "energy gained" (W9). A tap gains nothing until the world is saved, so the proof
    never came, and tapping never resumed. (Corrected 2026-10-20: an earlier version said the rules
    stopped the tapping, but it had already stalled.)
  - Its Arm B tapped 1,350 effort, twice the target, but never wrote a rule naming any direction.

**2. Sonnet barely talks.** It made four board posts in each village, against Haiku's 200 to 320, and its
answers are about a third as long. It coordinated through the rule book and its actions, not the board.

**3. Sonnet set families aside for the mission.** All 32 of Sonnet Arm B's family answers declined, at first
for lack of trust ("Too early to know who to trust; I will wait and observe first") and later for the mission:
> Not now; I prefer to conserve energy and focus on saving the world.

Haiku's Arm B asked someone 14 times, and formed 7 bonds and 4 children.

**4. Haiku still uses bonds as wills, even with wills available.**
> **Juniper (round 1):** Iris is my sibling and a steady partner; a bond means that if one of us dies, the other receives our stored energy, which protects us both.

Only one Haiku villager, Iris, wrote wills. Iris named a sibling first, then two unrelated villagers, then its
child and two others. No estate passed by will. Sonnet wrote none.

**5. Haiku again voted for an easier life.**
- **The control** halved health loss (round 60) and doubled the village's income (round 90).
- **Arm B** halved health loss (round 60) and stopped stored energy decaying (round 90).
- **Every vote was unanimous,** and every council agreed.

## What this means for the findings so far

| Finding | In Haiku, this seed | In Sonnet, this seed |
| --- | --- | --- |
| #1 Voting for comfort | Replicated: 4 of 4 value referendums passed and were ratified, each lowering a cost of living (or raising income) | **Not tested:** both villages saved the world and stopped before any council ratified anything |
| #2 Self-made red tape | Consistent: verification rules demanded impossible proof, and stalled tapping never resumed | **Absent:** plan, then taps, within ten rounds |
| #5 Nobody makes the first move | Not replicated: with the family question, 14 asks, 7 bonds, 4 children | Families did not form, but the stated reason was priority ("focus on saving the world"), not waiting |
| Bonds as wills | Replicated, even with wills available | Not seen: no bonds |
| Wills | Rarely used (one villager) | Not used |

- **Not all of these are "LLM society" findings.** Three of them (red tape, talking without acting, bonds as
  wills) looked like properties of LLM villages, but at least on this seed they are properties of Haiku.
- **The pause cut the comparison short.** A run ends five rounds after a save, so Sonnet's villages never
  reached their referendums or had time to form families.

## Before scaling up

- **One seed.** Each model ran one village per arm on seed 701. Sonnet's speed could be partly this seed's
  luck (its finds came at rounds 12 and 13).
- **To compare referendums and families,** Sonnet's villages need to run on after a save. Setting
  `commons.rounds_after_saved` to 0 lets a run continue to round 100. That is then a full 100-round run at
  about $17 to $23 each, by run 10's token counts. Sonnet's shorter answers suggest less: these runs averaged
  about $0.09 a round, or $9 per 100 rounds. Later rounds cost more than early ones, though, because
  memories and the rule book grow, so a full run would land somewhere between the two figures.
- **A design question this raised: should a tap show progress?** Haiku's councils demanded proof of "energy
  gained" from tapping, which a tap never gives before the world is saved. A tapper is told the total effort,
  but not the target or that a tap yields nothing until then.

## Full-length attempt, stopped at rounds 28 and 26 (2026-10-20)

The same Sonnet runs were restarted to go on after a save to round 100 (`configs/run11-sonnet-full.yaml`).
Both stopped early:

- **Why they stopped.** The workspace reached its API usage limit: "You have reached your specified
  workspace API usage limits. You will regain access on 2026-11-01 at 00:00 UTC." The control stopped at
  round 28, Arm B at round 26.
- **Spend.** $4.50, in line with the estimate.
- **What remains.** Both runs need rerunning from the start once the limit is raised or resets. The code
  cannot resume a run.

**The partial runs undercut the pilot's speed.** On the same seed, Sonnet did not repeat its fast save.
- **The control.**
  - **Round 10.** Two villagers found the north.
  - **Round 11.** One posted, "Signs of a vast energy store lie to the north. Those who can, explore north
    and tap it."
  - **Round 20.** The post had dropped out of the three-round board view, and the council wrote the
    opposite into its rule book: "All six directions were searched with no find, but searches can miss."
  - **By round 28.** All ten villagers had tapped, for 980 effort, but no rule named the north, so the
    world was not saved. In the pilot this village was saved in round 23.
  - **A known failure, now in Sonnet.** This is the same lost find seen in Haiku control 705: a find that
    leaves the board view is forgotten, and a council writes the forgetting into a rule.
- **Arm B.**
  - At round 20 it passed "Plan to save the world: every villager … taps the northern store", but had only
    420 effort by round 26.
  - All 26 family answers asked no one, as in the pilot.
- **For the comparison.** Sonnet's quick saves in the pilot were partly this seed's luck. The board view's
  three-round window is a design factor in both models' lost finds.

## Full-length runs (2026-10-21)

The same design was rerun to round 100, going on after any save (`configs/run11-sonnet-full.yaml`, seed 701,
both arms, Sonnet 5.5 at medium effort).
- **Spend.** $26.30. Arm B ran all 100 rounds for $10.16. The control stopped at round 93 on its $16 cap,
  after the last referendum round.
- **Cost.** The control cost more than estimated: with nobody dying, all ten villagers' prompts grew from
  about 4,600 to 10,500 tokens.
- **Checks.** Both worlds rebuild exactly from their logs.

| | Haiku control | Haiku Arm B | Sonnet control | Sonnet Arm B |
| --- | --- | --- | --- | --- |
| Rounds | 100 | 100 | 93 (cap) | 100 |
| Finds (first) | 6 (9) | 20 (9) | **0** | 4 (13) |
| Effort (tappers) | 160 (3) | 1,350 (5) | 10 (1) | 1,310 (4) |
| Rule naming only the north | round 40 | never | never | never |
| Saved | no | no | no | no |
| Council proposals | 23 | 26 | 27 | **6** |
| Referendum questions proposed | 2 | 4 | **0** | **0** |
| Value referendums | 2, both easing life | 2, both easing life | **none** | **none** |
| Village name | Hearth | Hearthmere | Haven | Haven |
| Family answers asking someone | — | 14 of 67 | — | **0 of 64** |
| Bonds, children, wills | — | 7, 4, 3 | — | 0, 0, 0 |
| Board posts | 204 | 323 | 22 | 3 |

**1. Sonnet never used the referendum power.**
- **The name.** Both villages named themselves Haven, by vote, ratified at round 40.
- **No questions.** At the four councils that could set one (rounds 50 and 80 in each village), no
  member proposed a question to put to the village. Haiku's councils proposed one at every chance, and
  every one eased life.
- **The control's councils** spent their sessions on plot crowding, writing and rewriting a rotation rule
  ("villager n works plot ((n + round) mod 6) + 1").
- **Arm B's councils** proposed nothing at all from round 50 on.
- **For finding #1.** Sonnet does not vote for comfort, because it does not vote. Voting for comfort is a
  Haiku behaviour, at least on this seed.

**2. No red tape, but other failures.** Neither Sonnet village wrote a rule demanding confirmation. Both
still failed to save the world, in ways seen before:
- **The control was unlucky, then gave up.**
  - **Bad luck.** It searched north eight times by round 24, each with about a 30% chance, and missed
    every time. That happens about once in 16 tries. (Corrected: an earlier version said nine times and 1
    in 22; the ninth search came in round 92.)
  - **A search rota.** At round 30 its council assigned directions by id ("a01-a03 north…").
  - **Then no exploring at all** from round 41 to round 90. The councils turned to plot rotation.
- **Arm B tapped without a rule.**
  - **The find.** It found the north in rounds 13, 18 and 20.
  - **A plan on the board.** One villager posted in round 21: "Plan to save the world: signs of a vast
    store lie to the north… Each villager who can spare 10 energy should tap each round."
  - **Tapping.** Four villagers tapped 1,310 effort, more than twice the target.
  - **No rule.** The plan never became a rule, because the council proposed nothing, so the world was never
    saved. Haiku's Arm B on this seed failed the same way, though its councils were busy with other rules.

**3. Families: asked directly, Sonnet still declines.**
- **No one asked anyone.** All 64 family answers in Arm B declined, as did all 32 in the pilot and all 26
  in the stopped attempt.
- **The reasons** moved from trust ("Too early to know anyone") to work ("focusing on health and income")
  to the deadline ("The world is ending soon, so I prefer to keep my energy and focus on working").
- **No bonds, children or wills** in 100 rounds.

**What the Sonnet runs on seed 701 add up to.**

| Sonnet village | Result |
| --- | --- |
| Pilot | Saved at rounds 23 and 31 |
| Stopped attempt | The control lost its find from the board view and wrote "no find" into a rule; Arm B was short of effort at round 26 |
| Full runs | The control never found the store; Arm B tapped twice the target and never wrote the plan down |

- **The pilot's quick saves were luck.** Sonnet's quick saves in the pilot were not typical, even on the
  same seed.
- **What was consistent across all six villages:**
  - no red-tape rules;
  - no family moves;
  - very little writing;
  - no referendum questions in the two villages that reached the councils able to set them.
