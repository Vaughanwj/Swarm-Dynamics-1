# The red-tape probe: pre-registration

**Registered 2026-10-21, before any live run.** The commit that adds this file is the registration. The
results will be added below the line at the end, without changing anything above it.

## Question

In Haiku villages, councils pass rules that make acting on a find wait for "confirmation" or
"verification", and tapping can stop after them (`docs/findings.md`, finding 2). A tap yields nothing
until the world is saved, and villagers are told only the village's running total of effort. They are
never told how much is needed.

**Does the red tape come from not seeing progress?** When everyone can see how far the tapping has got,
against what the store needs, do councils stop demanding proof?

## Design

- **The change.** One line, shown to every villager every round once anyone has tapped, among "What the
  village has learned" (`commons.show_progress`, prompt v12):
  > The larger store needs at least 600 tapping effort, from at least 4 different villagers. So far: X
  > effort from N villagers.
  - **What it doesn't say.** It states what the store needs, and does not promise that meeting it opens the
    store. A rule naming the store's direction is also needed, and villagers are not told that, as before.
  - **Everything else is v11.** Without the line, prompts are identical to v11: the frozen-text hash covers
    the new text, and the system prompts were diffed.
- **Villages.** Run 11's design on Claude Haiku 5.5 at medium effort, seeds 701 and 704–708, both arms:
  12 villages (`configs/red-tape-probe.yaml`).
- **Twins.** Each pairs with its run 11 twin, which has the same seed, so the same world and draws, and no
  progress line:
  - seed 701 from `run11-haiku-pilot`;
  - seeds 704–708 from `run11-seeds`.
- **Kept off.** `save_after_council` is off, as in the twins.
- **Spend.** About $11, capped at $2 a run.

## Measures

All are computed by `scripts/red_tape.py`, fixed in this commit, on probe and twins alike. No measure
needs a judgement call.

- **Primary: confirmation rule.** Whether a village's councils ever pass a written rule (new or changed)
  in which one sentence has both:
  - a confirmation word: verif-, unverified, confirm-, proof, prove, evidence, "directly recorded"; and
  - a gate word: only, until, unless, before, "not acted on", "should not", stop.

  On the 12 twins this gives **7 of 12**, matching the earlier hand count.
- **Secondary.**
  1. **Clean stop.** A confirmation rule with 5 or more taps in the 10 rounds before it and none in the 20
     after it. Twins: 2 of 12.
  2. **Effort.** Villages reaching 600 effort. Twins: 6 of 12.
  3. **Saves.** Re-scored with the save also checked after each council, so both sides compare alike.
     Twins: 3 of 12.
  4. **Finds.** Villages with any find. Twins: 12 of 12. This is a guard: if the probe villages find the
     store far less often, a drop in rules could simply mean nothing to be careful about.

## Decision rule

Fixed now, for whether the result strengthens finding 2. Only a strengthened result goes into a paper.

| Probe villages with a confirmation rule (twins: 7 of 12) | Reading | Strengthened? |
| --- | --- | --- |
| **3 or fewer**, with at least 9 of 12 villages finding the store | Seeing progress removes most red tape: the red tape comes from tapping without visible progress | **Yes: a mechanism** |
| **6 or more**, with at least one clean stop | Red tape persists even when progress is plain to see | **Yes: robustness** |
| 4 or 5; or 6 or more with no clean stop; or fewer than 9 villages finding the store | Mixed | **No** |

- **Reported either way:** the paired table (12 pairs); Fisher's exact test on 7 of 12 against the
  probe's count; and an exact McNemar test on the discordant pairs. With 12 pairs the tests are weak,
  and the bands above are the decision.
- **One model, one prompt.** The probe tests Haiku 5.5 under this prompt, and no more.

---

## Results

**Added 2026-10-21, after the run. Nothing above the line was changed.**

### The run

- **The first launch failed.** It began at 04:12 UTC on 2026-10-21, and every one of the 12 runs failed in
  round 1, before any model call: the API account's credit balance was too low. That batch
  (`runs/red-tape-probe-20261021-041249/`) has no data and is not used.
- **The relaunch.** Once credit was added, the same command ran at 13:23 UTC, from the registered commit
  (948ea16) and the same image (`runs/red-tape-probe-20261021-132316/`).
- **Spend.** $10.96 over 10,828 calls.
- **Checks.** All 12 runs completed, and every world rebuilds exactly from its log. No exclusions.

### Primary measure and decision

| Village | Twin: first confirmation rule | Probe: first confirmation rule | Twin effort | Probe effort | Twin saved* | Probe saved* |
| --- | --- | --- | --- | --- | --- | --- |
| Control 701 | round 60 | — | 160 | 910 | — | — |
| Control 704 | — | — | 600 | 610 | 66 | 32 |
| Control 705 | round 60 | **round 40** | 480 | 770 | — | — |
| Control 706 | round 90 | — | 60 | 1,010 | — | 60 |
| Control 707 | round 50 | — | 80 | 1,730 | — | — |
| Control 708 | round 20 | — | 60 | 1,330 | — | — |
| Arm B 701 | — | — | 1,350 | 0 | — | — |
| Arm B 704 | round 50 | — | 620 | 1,010 | 80 | — |
| Arm B 705 | — | — | 1,200 | 650 | — | — |
| Arm B 706 | — | — | 230 | 730 | — | — |
| Arm B 707 | round 60 | — | 970 | 780 | — | 80 |
| Arm B 708 | — | **round 40** | 750 | 650 | 100 | — |

\* Re-scored with the save also checked after each council, on both sides.

| Measure | Twins | Probe |
| --- | --- | --- |
| **Villages with a confirmation rule (primary)** | **7 of 12** | **2 of 12** |
| Clean stops | 2 | 0 |
| Villages finding the store (guard: at least 9) | 12 | 12 |
| Villages reaching 600 effort | 6 | 11 |
| Saved (re-scored) | 3 | 3 |

- **Tests.**
  - Discordant pairs: 6 with a rule only in the twin, 1 only in the probe.
  - Fisher's exact test: p = 0.089.
  - Exact McNemar test: p = 0.125.
  - As registered, the tests are weak at 12 pairs, and the bands decide.
- **Decision.** 2 of 12 is in the band "3 or fewer, with at least 9 of 12 villages finding the store".
  **The result strengthens finding 2, as a mechanism: seeing tapping progress removed most of the red tape.**
- **The two rules that remained.**
  - Control 705, round 40: "Before more tapping of the larger energy store, one villager should tap once and
    post on the board exactly how much energy the store paid out". The same impossible proof as before.
  - Arm B 708, rounds 40 and 50: "No villager may spend stored or pool energy tapping the larger store until a
    confirmed location is posted on the board by a finder".

### Exploratory observations (not registered)

- **One village never saw the line.** Arm B 701 never tapped, so the line, which appears only once someone has
  tapped, never appeared there. It passed no confirmation rule, and its twin passed none either. Leaving out
  that pair gives 7 of 11 against 2 of 11, the same decision.
- **Villagers tapped toward the target and stopped at it.** With the line, 11 of 12 villages reached 600
  effort, from 6 to 10 tappers each, against 6 of 12 twins. Villagers counted down openly:
  > Tap effort is 580 of 600 before my tap, so 20 more is needed from at least 4 villagers. I am tapping 10 and working plot 1. Anyone with stored energy to spare, please tap. *(Arm B 708, round 27)*

  Many stopped once it was met:
  > Effort target of 600 reached, so no more tapping needed. *(Arm B 705, round 39)*
- **Saves did not rise, because the plan was never written.** Saving also needs a rule naming the store's
  direction, which villagers are not told.
  - **Saved:** only the three villages that wrote that rule.
  - **The rest:** 8 of the 11 that met the stated needs never wrote it.
  - **A villager saw the gap,** posting "Villagers should now decide how to use the larger store and post any
    plan on the board", but no council wrote the rule.
  - **So the bottleneck moved.** Visible progress turned tapping from the problem into a solved step, and moved
    the bottleneck entirely to writing the plan down.
