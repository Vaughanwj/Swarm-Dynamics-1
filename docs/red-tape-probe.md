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

(Added after the run.)
