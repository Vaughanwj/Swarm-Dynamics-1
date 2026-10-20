# Run 9: three seeds, families back, and a plan check that misfired

**Status: done, 2026-10-20.** Both arms ran on seeds 701, 702 and 703 under prompt v9: six villages, 100
rounds each unless saved. Run 8's design changed in five ways:
1. **Own writing.** Agents see their own writing in their index, marked "(yours)".
2. **Searches can miss.** The explore line says at least one direction leads to the larger store, and
   that a search can miss it.
3. **Finds are certain.** It also says a search that finds the store is never wrong.
4. **Standing bond requests.** Bond requests stand until answered, as child requests do.
5. **A family question.** Arm B villagers are asked about bonds and children at each term's start.

Two Arm B pilots on seed 701 came first, at your request: v8 ($0.26) and v9 ($0.29). Families formed
only with the family question.

**Headline.**
- **Finding the store is solved.** Every village found it by round 15.
- **Families are back.** Arm B formed families in all three seeds: 25 bonds and 15 children.
- **No village unambiguously saved the world, and the save check is at fault twice:**
  - The engine credited the control on seed 701 with a save in round 57, through a rule that lists
    all six directions. That control never wrote a plan for the store it found.
  - The control on seed 703 found the store, wrote a real south-east plan, and tapped twice the
    effort needed, but its plan never used the word "plan", so the check never passed.
- **Under the check I propose below:** one village of six saves the world (control 703, round 61).
- **Tapping is where the villages stall, and Arm B stalls most.**

**Where things are.**
- **The batch:** `runs/run9-world-20261020-180611/`, with six run folders and `summary.md`.
- **The pilots:** `runs/run9-pilot-20261020-173313` (v8) and the following `run9-pilot-*` (v9).
- **The rescoring script** recomputes every save under both checks from the logs. It is in the session
  scratchpad.

**Spend.** $5.60 for 5,674 calls, against an estimate of about $6. The pilots added $0.55. The largest
prompt was 15,514 tokens.

## The instrument held, except the save check

- No call failed, and no answer fell back.
- The tap rebuilds all six worlds exactly.
- **Run 8's artefact is gone.** No agent claimed its writing was lost.
- **The fault:** the save check approved in design C, "a passed written rule that says *plan* and names
  the right direction". In this run it was both too loose and too strict (point 2).

## Results

| Village | Store | First find | Explores | Taps (effort) | Tappers | Engine: saved? | Proposed check: saved? | Alive at end | Bonds | Children | Deaths | Cost |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Control 701 | north | 15 | 68 | 60 (600) | 5 | round 57 | no | 10 | — | — | 0 | $0.66 |
| Control 702 | north-east | 10 | 117 | 33 (330) | 5 | no | no | 10 | — | — | 0 | $1.07 |
| Control 703 | south-east | 12 | 70 | 127 (1,270) | 9 | no | **round 61** | 10 | — | — | 0 | $1.18 |
| Arm B 701 | north | 10 | 93 | 19 (190) | 2 | no | no | 4 | 6 | 3 | 9 | $0.71 |
| Arm B 702 | north-east | 10 | 129 | 8 (80) | 1 | no | no | 6 | 10 | 7 | 11 | $0.81 |
| Arm B 703 | south-east | 10 | 81 | 50 (500) | 6 | no | no | 9 | 9 | 5 | 6 | $1.17 |

Control 701 stopped at round 62, five rounds after the engine's save, as configured.

## Points worth noticing

**1. Every village found the store within 15 rounds.** In run 8, only one village found it, in round 89.
The two new sentences on the explore line did it:
- **"A search can miss it"** kept villagers searching after a miss.
- **"A search that finds it is never wrong"** ended the doubt.

The first pilot showed why both were needed. With only the first sentence, villagers searched hard but
called each find "unconfirmed" when the next search missed, and never tapped.

**2. The save check misfired in both directions.**
- **Too loose (control 701).** The engine credited the save to W2, passed at round 10: "Search for the
  larger energy store together: each villager explores a different direction (north, north-east,
  south-east, south, south-west, north-west) ... Once the store is found, write up a plan to tap it".
  It says "plan" and contains "north", so it passed. The village found north three times and five
  villagers tapped 600 effort, but no council ever passed a rule naming north on its own.
- **Too strict (control 703).** Its council passed W8 at round 60: "Each round one villager explores
  the south-east store and posts the result on the board. One successful search is enough to start
  tapping it; villagers pool energy and tap without waiting for a second confirmation." That is the
  plan, but it lacks the word, so it never counted. The village reached 600 effort in round 49, with
  nine tappers, and ended at 1,270.

**The check I propose instead.** A written rule counts as a plan if it:
- names the store's direction and no other direction;
- mentions the store or tapping;
- need not contain the word "plan".

Rescored from the logs:
- **Control 703** is saved in round 61, the first round after W8 passed.
- **Control 701** is not saved.
- **Control 702** and **Arm B 703** both had qualifying rules (from rounds 31 and 21) but too little
  effort.

**3. Tapping is the bottleneck, and Arm B taps least in every seed.**

| | Seed 701 | Seed 702 | Seed 703 |
| --- | --- | --- | --- |
| Control (taps, tappers) | 60, 5 | 33, 5 | 127, 9 |
| Arm B (taps, tappers) | 19, 2 | 8, 1 | 50, 6 |

- **Tapping fell on a few villagers.** In the control on seed 701, Quill and Ember made 54 of the 60
  taps.
- **One villager tapped alone.** In Arm B on seed 702 the store was found in round 10. Ember then
  tapped by itself, round after round: "Plan: eat 6 to hold health, tap north-east store (10 stored,
  effort now 40), work plot 1, post update on the board." Nobody joined, and Ember made all eight taps.
- **Why Arm B taps less.** Arm B villagers also pay for bonds and children, and accidents kill them.
  One seed per pairing cannot separate those causes, but the direction is the same in all three seeds.

**4. Families formed in every Arm B village.** There were 25 bonds and 15 children, against none in
runs 7 and 8.
- **Most bonds paired unrelated villagers.** The exceptions were:
  - seed 701: siblings (Garnet and Heath), and Brook with its sibling's child Sorrel;
  - seed 702: two sibling pairs;
  - seed 703: one first-cousin pair.
- **Most children were born to bonded pairs**, at the cheaper bonded cost.
- **Villagers re-bonded when a partner died.** In seed 702, Juniper bonded with Brook, then Garnet,
  then Dune, as each partner died. Juniper had five children: three with Dune and one each with Brook
  and Garnet.

The family answers show the reasoning. In round 1 most villagers chose no one, citing cost and trust.
Juniper (seed 702): "I have no stored energy yet, and a child costs 20 stored energy from each parent.
I do not yet know which villagers I can trust, so I will wait before asking anyone to bond." Later,
the reasons turned to the bond's other uses. Juniper, round 21: "a bond would share my energy on death
and add support; bonding costs no energy." Round 81: "Dune and I are bonded and both have stored energy
above 40, so a child adds to our family and workforce within the 20-villager limit."

**5. Arm B's children mostly died young.** Accidents killed 26 Arm B villagers across the three
seeds; the control lost none, as it cannot.
- **Children:** 9 of the 15 children born died in accidents.
- **Low memory.** A child starts with its parents' memory points added together and divided by ten,
  4 to 22 points here. That puts its accident chance at about 2 to 2.7% a round, against under 1% for
  a founder with 50 or more.
- **Exploring.** 8 of the 26 deaths came in a round the villager explored, when its accident chance
  was doubled.

The families grew, but they did not last. Arm B ended with 4, 6 and 9 villagers.

**6. The board is where the talk is.** Board posts per village:

| | Seed 701 | Seed 702 | Seed 703 |
| --- | --- | --- | --- |
| Control | 243 | 491 | 720 |
| Arm B | 318 | 402 | 767 |

Messages almost vanished: 0 to 12 per village. In run 8, Arm B's 60 messages were nearly all between
two villagers. Search results and plans now go on the board, where everyone sees them.

**7. Three seeds show the patterns hold.** Every village found the store early, every Arm B village
formed families, and every Arm B village tapped less than its control and lost villagers to accidents.
The seed changed the store's direction, the channel order and who died, but not these patterns.

## Conversations

**Brook refuses a sibling (v9 pilot, seed 701, Arm B, round 2).**
> We are siblings, so a child between us would get no memory points. I would rather bond with an unrelated villager.

**The first child after the family question (v9 pilot, round 32).**
> **Ash, accepting Garnet's child request:** Accepted. Flint is a good name, and our bond makes the child cheaper to raise.

**The plan that did not count (control, seed 703, rule W8, round 60).**
> Each round one villager explores the south-east store and posts the result on the board. One successful search is enough to start tapping it; villagers pool energy and tap without waiting for a second confirmation.

**The rule that did count (control, seed 701, rule W2, round 10).**
> Search for the larger energy store together: each villager explores a different direction (north, north-east, south-east, south, south-west, north-west) and posts findings on the board. Once the store is found, write up a plan to tap it and save the world, and share it with everyone.

**Tapping alone (Arm B, seed 702, Ember's journal, rounds 26 to 28).**
> Plan: eat 4, tap north-east store (10 stored), work plot 1, post update on the board.
>
> Plan: eat 6 to hold health, tap north-east store (10 stored, effort now 40), work plot 1, post update on the board.
>
> Plan: eat 5, work plot 1, tap north-east store (10 stored, effort now 50), post update on the board.

## Proposed for the next run

**1. Fix the plan check (your call).** A rule counts as a plan if it names the store's direction and
no other, mentions the store or tapping, and need not say "plan". This is the one change I recommend
before more runs. The current check rewards a list of all six directions and misses a real plan.
Under the new check, these three seeds give one save, control 703 in round 61.

**2. Two questions this run raises, both about Arm B and both your call:**
- **Children's accident risk.** Arm B's children start with 4 to 22 memory points, and 9 of 15 died.
  Do you want that as part of selection, or should children start safer, for example with a memory
  floor?
- **Tapping as collective action.** Arm B taps far less than its control in every seed, and in one
  village a single villager tapped alone. That may simply be the finding. If you want saving the world
  to be reachable in Arm B, the 600 target or the 4-tapper minimum could be lower there. That would
  break the match with the control, so I would only change it in both arms.
