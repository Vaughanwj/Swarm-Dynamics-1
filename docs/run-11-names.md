# Run 11 name-swap check: do wills follow Iris or a09?

**Status: done, 2026-10-20. Result: inconclusive.**
- **Design.** Run 11's Arm B, with the family question, on seeds 701 and 705, on Claude Haiku 5.5. The
  founders Iris and Cedar trade names: Iris moves to a03 (the second sibling pair, third in the lists), and
  a09 becomes Cedar.
- **Spend.** $1.77 over 1,756 calls. Both worlds rebuild exactly from their logs.
- **Runs.** `runs/run11-names-20261020-230422/` (`configs/run11-names.yaml`).

**Why check.** Every will in run 11 (6 of 6, three seeds) was written by a09, Iris, and a09's journals
mentioned wills in 54 of 718 entries, against at most 1 for any other founder. Founders differ only in name,
family and position, and nothing in the prompt names a09.

## Result

| | Seed 701, names as before | Seed 701, swapped | Seed 705, names as before | Seed 705, swapped |
| --- | --- | --- | --- | --- |
| Wills written | 3, by a09 (Iris) | **none** | 2, by a09 (Iris) | **none** |
| Journal entries about wills | a09: 16 | **none, by anyone** | a09: 37 | **none, by anyone** |
| Iris (the name) | a09, lived all 100 rounds | a03, **died in an accident in round 7** | a09, lived all 100 rounds | a03, lived all 100 rounds |

- **The slot alone did not produce wills.** a09, as Cedar, never mentioned a will in either village. In seed
  701 it still asked for bonds partly for the inheritance:
  > **Cedar, a09 (round 21):** Fern is healthy, unbonded and holds stored energy; a bond would pass my stored energy to her if I die…
- **The name alone did not either, where it had the chance.** In seed 705, Iris at a03 lived all 100
  rounds and never mentioned a will. In seed 701 it died in round 7, so that village tests nothing about the
  name.

## What it means

- **Inconclusive, as it risked being.** Will talk appeared in only 3 of the 11 earlier Arm B villages. At
  that rate, two villages with none happen by chance about half the time (53%), whatever the cause.
- **It leans against either factor alone.** Neither the name in a new slot (one fair village) nor the slot
  under a new name (two villages) showed any will talk. If anything, the combination matters: Iris, as
  a09, the elder of the last sibling pair. One seed-701 detail is consistent with that:
  - In the original run, Iris bonded with its sibling Juniper in round 2.
  - By round 5 it planned "a will to bonded partner Juniper".
  - Swapped, a09 (Cedar) bonded with Juniper in round 13, and never thought of a will.
- **For the findings note,** "all six wills by one slot" stays an unexplained curiosity. Wills are rare
  enough that no claim about them should be made yet.
- **To settle it** would take more villages, not a cleverer swap. Six runs per condition (names as before;
  swapped) would give each condition a good chance of showing will talk, at about $1 a run, or $12.
