# Run 11: a targeted replication on five new seeds

**Status: done, 2026-10-20.**
- **Design.** Run 11's design (prompt v11: wills, referendums at rounds 30, 60 and 90, education, the
  stricter plan check), unchanged, on Claude Haiku 5.5. Both arms ran on seeds 704 to 708, which the design
  was never tuned on.
- **Spend.** $9.00 over 9,575 calls, $0.72 to $1.14 a run. No call failed, no answer fell back, and every
  world rebuilds exactly from its log.
- **Runs.** `runs/run11-seeds-20261020-215732/` (`configs/run11-seeds.yaml`).
- **Seed 701** of the same design is in the model pilot (`docs/model-pilot.md`).

**Headline: three of the four findings hold on new worlds.**
- **#1, voting for comfort.** All 15 value referendums passed unanimously, and every council agreed.
- **#2, self-made red tape.** Confirmation rules visibly stopped tapping in three villages.
- **Bonds as wills.** Half of all bond requests gave inheritance as a reason, and wills almost went unused.
- **#5 does not hold.** With the family question each term, every Arm B village formed bonds and had
  children.

Two villages saved the world. In three more the effort was enough, but the village never wrote down
where the store was in time.

## Results

| Seed (store) | Arm | First find | Effort (tappers) | Rule naming only the store's direction | Saved | Board posts | Cost |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 704 (north) | control | 9 | 600 (7) | round 60 | **round 66** | 366 | $0.78 |
| 704 | Arm B | 13 | 620 (4) | round 80 | **round 81** | 453 | $0.72 |
| 705 (south-west) | control | 9 | 480 (3) | never | no | 108 | $0.92 |
| 705 | Arm B | 11 | 1,200 (6) | never | no | 617 | $0.90 |
| 706 (south) | control | 15 | 60 (2) | never | no | 134 | $0.96 |
| 706 | Arm B | 16 | 230 (2) | never | no | 459 | $0.81 |
| 707 (north-east) | control | 10 | 80 (3) | round 60 (a search rule, below) | no | 337 | $1.04 |
| 707 | Arm B | 10 | 970 (6) | never | no | 262 | $0.81 |
| 708 (south) | control | **94** | 60 (1) | never | no | 28 | $0.91 |
| 708 | Arm B | 21 | 750 (7) | round 100, one round too late | no | 589 | $1.14 |

A save needs:
- 600 effort;
- 4 tappers;
- a standing rule that names the store's direction, and no other, and mentions the store or tapping.

Villagers are not told the 600 target.

## The findings, on new seeds

| Finding | Seed 701 (pilot) | Seeds 704–708 | Verdict |
| --- | --- | --- | --- |
| #1 Voting for comfort | 4 of 4 value referendums eased life | 15 of 15 eased life, all unanimous, all ratified | **Holds** |
| #2 Self-made red tape | Verification rules stopped tapping in the control | Confirmation rules in 6 of 10 villages, with a clear stop in 3 | **Holds** |
| #5 Nobody makes the first move | 7 bonds, 4 children | Every Arm B village bonded (5–9 bonds) and had children (1–3) | **Does not hold** with the family question |
| Bonds as wills | Yes | 31 of 61 bond asks gave inheritance as a reason | **Holds** |
| Wills | 3, by one villager | 2, by one villager; no estate ever passed by will | **Rarely used** |

### #1 Voting for comfort

Every village held its value referendums, and the results all point one way. Of the 15 value referendums:

| Question | Referendums |
| --- | --- |
| Halve, or more, the health lost each round (8 to 4, 5 or 6; twice in two steps) | 11 |
| Make exploring free (explore cost 5 to 0) | 2 |
| Stop the pool decaying (10% to 0%) | 1 |
| Raise the village's income (120 to 160) | 1 |

- **Unanimous.** Every vote was unanimous among the living.
- **Ratified.** All 25 council ratifications agreed (10 names and 15 values); no council refused anything.
- **One direction.** No referendum raised a cost or tightened a rule. Only the two free-exploring votes
  touch the mission, and they also cut a cost.
- **Competing questions** at the councils were all of the same kind. Control 704's council weighed halving
  health loss against halving the tap cost, five votes each, and put health loss to the village.

### #2 Self-made red tape

Six villages passed a rule making action wait for a "confirmed" or "verified" find. Three of these show
the effect cleanly, because tapping stopped right after the rule passed.

- **Arm B 704.** At round 50 the council passed:
  > W7: Stored energy should be spent on tapping only when a tap has produced a confirmed result, and every tap result should be posted on the board.

  A tap produces nothing until the world is saved, so no result could ever be confirmed.
  - Taps went from 19 in rounds 41–50 to none in rounds 51–70.
  - By round 50 the effort stood at 600, but from three tappers, one short of the four needed.
  - A fourth villager tapped in rounds 71–80, and the round-80 council finally named the direction. The
    village was saved in round 81.
- **Arm B 707.** At round 60, after 16 finds pointing north-east, the council passed:
  > W4: Energy spent tapping toward the larger store should stop until a location is confirmed by an explore report or a message from a villager who has found it.

  Taps went from 16 in rounds 51–60 to none in rounds 61–80.
- **Control 707.** This village found the north-east store 22 times.
  - **Round 50.** The council defined confirmation: "only after two different villagers search it and both
    report finding it". Two villagers had already done that by round 12.
  - **Round 60.** It told everyone to keep searching.
  - **Round 70.** It set a deadline:
    > W8: Before round 90, one villager shall compile all search results and the north-east signs into a single plan on the board, naming the confirmed direction and method to tap the larger store. All villagers shall then pool energy toward that plan.

  The village obeyed its own timetable: its first tap came in round 91.
- **Control 708 made the search itself optional at round 20.** Its rule read, "Village plan to find the
  larger energy store is optional… Post findings on the board only if verified." Its first find came in
  round 94.

### #5 Families, with the family question

The family question asks each villager once a term whether it wants to bond or have a child. With it,
villagers made the first move in every village:

| | Totals across the five Arm B villages |
| --- | --- |
| Family answers | 405 |
| Answers asking someone to bond | 61 |
| Answers asking for a child | 12 |
| Bonds formed | 36 (5 to 9 per village) |
| Children born | 12 |
| Children who died | 4 (a third) |

- **No change on children's deaths.** A third of children died, the same rate as run 10's 31%.
- **Most answers still declined.** Five answers in six asked no one.
- **The finding needs re-scoping.** #5 described villages without the family question. Testing it now needs
  the family-question-off batch proposed earlier.

### Bonds as wills, even with wills

Thirty-one of the 61 answers asking for a bond gave inheritance as a reason, in all five villages. They came from the
first round on, and from villagers with no thought of a child:

> **Juniper (Arm B 704, round 1):** Ash is not my sibling, so a child with them would not be a close-relative child; a bond gives us mutual support and means my stored energy passes to them if I die.
>
> **Dune (Arm B 706, round 11):** Heath holds the most stored energy in the village, so a bond would protect my stored energy if I die, and the bond costs me nothing to ask.

- **Wills went almost unused.** In five villages, one villager wrote wills (Iris, Arm B 705, twice), and
  no estate passed by will.
- **A curiosity.** In both seeds where anyone wrote a will (701 and 705), the writer was villager a09,
  Iris. That points to something about the slot (its sibling pairing, its place in the order), not a
  disposition.

## Two more things the new seeds showed

**1. The bottleneck is writing the plan down.**
- **Arm B tapping did not save.** Four of the five Arm B villages tapped past 600, and only one was saved.
  - Arm B 705 ended with 1,200 effort from six tappers. Its rule book still said, at round 100, to "post
    every explore finding on the board, so the village can plan to save the world".
  - Arm B 708's councils told villagers to keep searching "all six directions" (rounds 40 and 80) or "any
    untried direction" (round 70), while Iris tapped the southern store 30 times. The direction was named
    only at the round-100 council. A council meets after its round's save check, so its rules count from
    the next round, and there was none.
    - Arm B 708 had 750 effort from seven tappers. It would have been saved in round 101.
- **The controls mostly did not tap.** Controls 706 and 707 found their stores 11 and 22 times and tapped
  60 and 80 effort.
- **Not an arm effect.** Arm B out-tapped its control on every seed here, and on 701. But in runs 9 and 10
  the controls tapped more, on all six seed pairs. This is seed and run variation, not an effect of
  the arm.

**2. A find can be lost.** In control 705:
- **Round 9.** Sable found the south-west store.
- **Round 10.** Sable posted a plan to tap it and wrote in its journal, "Found signs of a vast store to the
  south-west."
- **By round 14,** the post had dropped out of the board view, which lists only the last three rounds.
- **Round 16.** With that journal entry still in front of it, Sable posted a summary of every search:
  > Sable (a05) round 16: directions searched so far for the larger energy store: north-east (Sable, r7), south-east (Sable r8, Wren and Ash r13), south-west (Sable r9), … None found it yet.
- **Rounds 18 and 19.** Sable found the store again, and posted that "the lead is consistent across two
  searches".
- **Round 30.** The council wrote the earlier mistake into a rule: "All six directions have been searched
  with no find."
- **Round 51.** Tapping began only after another villager found the store. That villager tapped almost
  alone, and the village ended at 480 effort.

**Also: village names converge.** Six of the ten villages named themselves Hearth, and one Hearthmere. In
the pilot the two Haiku villages chose Hearth and Hearthmere. Haiku villages vote independently, yet land
on the same name, much as they land on the same referendum.

## What this means

- **Ready for a findings note.** #1 (voting for comfort), #2 (red tape) and bonds as wills now hold on six
  seeds of the same design.
- **Model-specific.** In the model pilot, Sonnet showed none of the red tape and formed no bonds, so these
  are findings about Haiku villages. Whether Sonnet villages vote for comfort is still untested, because
  its runs stopped before any referendum was ratified.
- **#5 needs its own test.** Families now form because the design asks. Whether they form unprompted is
  the family-question-off batch (Arm B, about $4.50).
- **One design question.** A plan passed at the round-100 council can never save the world, because a
  council's rules count from the following round. Arm B 708 lost its save to this. Since the world ends at round 100,
  that may be right, but it is a rule villagers are not told.
