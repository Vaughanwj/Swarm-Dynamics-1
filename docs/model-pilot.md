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
  - Its control passed a valid north plan at round 40, then added rules that stopped it: "Unverified claims
    are not acted on" (W8), and post only results "directly recorded", with the "energy gained" (W9). A tap
    gains nothing until the world is saved, so the proof never came, and tapping stopped at 160 effort.
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
| #2 Self-made red tape | Replicated: verification rules stopped tapping after a valid plan | **Absent:** plan, then taps, within ten rounds |
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
  about $0.09 a round, or $9 per 100 rounds.
- **A design question this raised: should a tap show progress?** Haiku's councils demanded proof of "energy
  gained" from tapping, which a tap never gives before the world is saved. A tapper is told the total effort,
  but not the target or that a tap yields nothing until then.
