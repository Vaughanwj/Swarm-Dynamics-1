# Run 8: standing reveals and a world that ends

**Status: done, 2026-10-20.** Run 8 was run 7 with one change: how the village learns about the world.
From its round, each reveal stood in every prompt under "What the village has learned", with current
values, and the second reveal now named the stakes ("The world will end in N rounds"). Both arms ran
100 rounds on run 7's seed (701).

**Headline: the reveals now reached the villagers, and both villages made saving the world their aim,
but neither saved it.** The world needed:
- a find;
- a written plan naming the direction;
- 600 effort from at least four tappers.

Run 8 got as far as:
- **Finds:** two, both in Arm B, in rounds 89 and 95.
- **A plan:** one valid plan, passed at the last council (round 100).
- **Effort:** 10, from a single tap.

Two things stopped both villages:
1. **One failed search was read as proof.** Each village searched north (the right direction) three
   times in rounds 9 and 10. All six searches failed on the dice, and both villages concluded the
   store is not there.
2. **Both councils wrote rules that blocked their own search.** In the control, nobody explored from
   round 11 to round 80 while the village waited for a "combined plan" its own rules required and no
   council ever wrote.

**Where things are.** The runs are in `runs/run8-world-20261020-160954/`, with `control-s701`,
`tontine-s701` and the batch `summary.md`. The analysis script is the same as run 7's.

**Spend and time.** $1.8862 for 1,818 calls, against an estimate of $1.80 to $2.50. The control took
$1.30 and 14 minutes; Arm B took $0.58 and 10 minutes. The largest prompt was 15,021 tokens.

## The instrument held

- No call failed, no answer fell back, and no answer failed to parse.
- The tap rebuilds both worlds exactly.
- **The reveals stood in every round's prompt from their round, identical for everyone.** They appeared
  in the council's prompts too.
- **The common random numbers matched.** Arm B lost Cedar (round 7), Ember (11), Juniper (15) and Heath
  (57) to accidents, exactly as in run 7, because the accident draws are keyed to the seed. Brook
  (round 28) was new.
- **One interface artefact misled an agent** (point 5): an agent never sees its own writing in its index.

## What happened

**Rounds 9 and 10: both villages took up the reveals at once.**
- **The first searches.** Each village sent three explorers north in rounds 9 and 10.
- **Round 10, the last reveal.** Nine control villagers posted a plan to save the world on the board.
  In Arm B six posted plans and three more called for one. Almost every plan proposed splitting the six
  directions among explorers.
- **The councils.** Both made the search a shared aim:
  - The control passed four rules (W1 to W4).
  - Arm B passed five (W1 to W5), each with five votes. Arm B W2: "Save the world: villagers should
    rotate exploration of all six directions to locate the larger energy store, post findings on the
    board, and pool energy and work toward tapping it before the world ends."

**The control, rounds 11 to 100: rules that blocked the search.**
- **Rounds 20 to 30.** The council wrote that it would "publish one combined plan" each term (W7).
  Then, in W8: "The pool may be drawn for exploration only under the combined plan published at each
  term's end (W7) ... Idle energy stays stored or in the pool, not spent without a plan."
- **Rounds 40 to 60.** Deadlines followed: round 50 (W9, W12), then round 65 (W13). No council ever
  published the plan, and no rule ever set out who would go where.
- **No one explored from round 11 to round 80**, though exploring costs a villager's own stored energy,
  not the pool's. Instead they wrote notices like Vera's, round 80: "Council: term 8 ends now. Publish
  the combined exploration plan (W7/W12/W13) naming an explorer and energy need for each of the six
  directions. The plan has been unpublished since round 65."
- **Rounds 70 and 80, the unblocking.** The council saw the problem. W15 (round 70): "Plans (W7, W12,
  W13) guide searches but must not block them." In round 80 it freed pool energy for exploring.
- **Rounds 81 to 97.** Sixteen searches covered every direction, including one more try north (Iris,
  round 89, a 24% chance). All failed. Iris, round 97: "All six directions ... have now been searched
  with nothing found."

**Arm B, rounds 11 to 100: a search declared finished, then rules about plans.**
- **Rounds 11 to 16.** Ash and Dune worked through the other five directions. Ash, round 16:
  "Exploration summary: all six directions ... have been searched by villagers with nothing found so
  far."
- **Round 20 on.** The council asked for a "concrete plan, naming the direction, energy needed and
  expected yield" (W6). It then made that the condition for funding (W7, W8, W10, W12). No one could
  know the yield, so no plan ever qualified.
- **Round 89, the find.** Fern found the store north, at an 80% chance. Fern posted it the next round:

> Signs of a vast energy store were found to the north (explored round 89). A concrete plan would name direction north, energy needed, expected yield and named explorers. Explorers willing to join should say so on the board.

- **Rounds 92 to 100.**
  - Dune volunteered to go north.
  - Garnet drafted a "north plan" as a report.
  - Ash found the store north again in round 95.
  - The plan stayed "open" for want of an energy figure and a yield. Dune never made the trip.
  - Iris spent the last ten rounds still rotating through "the directions not yet searched".
- **Round 100, the last council.** It passed W15: "Fund the north expedition (plan R576 and note filed
  by Dune and Garnet)". That names north and says "plan", so it meets the save check, but it came after
  the last round, with 10 effort of 600.

## Points worth noticing

**1. The standing reveals worked as a fix.** In run 7 nobody mentioned the store after round 10. In
run 8:
- **Plans.** 15 villagers posted plans in round 10, and three more called for one.
- **Councils.** Both made the search their first shared aim and returned to it every term.
- **Searches.** 52 in all, against none in run 7.

The countdown was cited throughout ("the world ends in 91 rounds", "with the world ending in 10
rounds"). Naming the stakes and keeping them in view was enough to start the search.

**2. A failed search counted as proof that the store is not there.** A search in the right direction
succeeds with a chance that grows with memory points, from 20% to 80%. Here is every northern search
and its result:

| Village | Round | Explorer | Chance | Result |
| --- | --- | --- | --- | --- |
| Control | 9 | Vera | 29% | nothing |
| Control | 9 | Sage | 35% | nothing |
| Control | 10 | Wren | 28% | nothing |
| Control | 89 | Iris | 24% | nothing |
| Arm B | 9 | Iris | 32% | nothing |
| Arm B | 10 | Dune | 31% | nothing |
| Arm B | 10 | Ash | 51% | nothing |
| Arm B | 89 | Fern | 80% | **found** |
| Arm B | 95 | Ash | 80% | **found** |

- **Neither village searched a direction again on purpose.** Both kept lists of "searched" and
  "unsearched" directions.
- **The message is identical either way.** "You searched the north and found nothing" is what a failed
  search in the right direction says, and also what a search in a wrong direction says. The approved
  design allowed for this ("which can mislead"), and here it decided the run.
- **Neither village asked whether a search could miss.**

**3. Both councils built procedure that stopped the search.**
- **The control** made the pool's support for exploring conditional on a combined plan, then waited
  70 rounds for a plan nobody wrote. Exploring needed no pool energy (it costs 5 of the explorer's
  own), but villagers treated the rule as permission.
- **Arm B** required every plan to name an "expected yield" that could not be known, and then funded
  only plans that did.
- **Both saw it in the end.** The control: "Plans ... must not block them." Arm B's final plan: "Expected
  yield: unknown until surveyed." By then it was too late.

**4. Nobody tapped, because nobody had found anything they believed.** There was one tap in two
villages and 200 rounds (Iris, Arm B, round 9). Every plan put locating before tapping, which is
sensible. With no accepted find until round 89, the tapping half of the design was never tested.

**5. An interface artefact became a rule.** An agent's own posts never appear in its own index, so an
agent never sees them. Garnet concluded its board notices were being lost. Its round-75 journal:

> Board index shows no notice from round 74, so my posted plan was not recorded; reposting it now as a board notice naming Garnet and Iris, 40 energy from pool, for the round 80 council.

- **The reposts.** Garnet posted the same plan seven rounds running (B35 to B41).
- **The belief spread.** Garnet told Iris "board notices are not recorded" in several messages.
- **The rule.** At round 90 the council passed W13: "Concrete plans to save the world must be filed as
  reports, since board notices have not always been recorded."

I noted at Milestone 2 that an agent's own posts are not in its index, but the prompt never says so.
A one-line fix is proposed below.

**6. Memory points decided who could find the store.**

| | Control | Arm B |
| --- | --- | --- |
| Items read | 30 | 167 |
| Energy turned into memory | 787 | 2,154 |
| Mean memory, rounds 50 and 89 | 42 | 188 |
| Chance of a northern search succeeding | about 28% | 80% for Fern and Ash |

Arm B read far more (683 memory points from reading) and learned more. Its late searches were at the
80% cap; the control's stayed near the bottom of the range.

**7. Talk came back, in different shapes.**

| | Board posts | Messages | Report notes | Reads |
| --- | --- | --- | --- | --- |
| Run 7, control | 3 | 5 | 9 | 62 |
| Run 8, control | 63 | 0 | 549 | 30 |
| Run 7, Arm B | 2 | 1 | 42 | 50 |
| Run 8, Arm B | 45 | 60 | 8 | 167 |

- **The control** wrote mostly in its harvest reports (W5 and W6 asked every worker to note its plot
  and yield). It sent no messages at all.
- **Arm B's messages** were all between Garnet and Iris. They began in round 66, and the two
  coordinated searches with each other for the rest of the run.

**8. The control stopped giving.** Run 7's control gave 159 gifts (2,045 energy); run 8's gave one (10
energy). Its mean health sat between 56 and 60 from round 30 to round 80, against 70 to 80 in run 7.
One possible cause is W8's "idle energy stays stored or in the pool, not spent without a plan", but
one seed cannot show it.

**9. Arm B still formed no families.** There were no bonds, no child requests and no births, so five
accident deaths left five villagers. That is two runs in a row now, on the same seed.

**10. The councils kept deleting rules twice.** The control voted in round 50 to delete W1 twice and
W9 twice, as its council did in run 7. The second vote is void each time.

## Conversations

**Round 10 in the control: the plan everyone wrote at once (Iris, board).**
> Plan to save the world: first, locate the larger energy store. Each villager explores a different direction (north, north-east, south-east, south, south-west, north-west) and posts what is found. Second, spread across plots 1 to 6 so work yields stay high and ...

**The search declared over (Arm B, Ash, board, round 18).**
> Summary of the village's search: all six directions (north, north-east, south-east, south, south-west, north-west) have been explored and nothing beyond the known plots has been found so far. Any villager with a new lead, please post it here.

**Waiting for the plan (control, rounds 30 to 80).**
> **Vera, board (r30):** Term 3 ends this round. Council: please publish the combined plan under W7. Findings so far: north searched in round 9, nothing found. Pool has about 412 energy available for exploration draws (S1 limit 50 per draw).

> **Sela, board (r70):** Notice from Sela (a02): the term 7 council should publish the combined exploration plan (W7/W12/W13) before round 71, naming an explorer and direction for each of the six directions, with dates and pool energy needed. Until then, no exploration draws from the pool.

**Garnet and Iris, after the find (Arm B, rounds 91 to 93).** Garnet first got the direction wrong,
then read the notice and corrected itself. Iris kept to the rotation.
> **Garnet → Iris (r91):** Iris, I read B43 on the north-east signs. I will explore a direction not yet tried if a concrete plan needs it. Please file any findings as reports.

> **Garnet → Iris (r92):** Iris, B43 points north. World ends in 9 rounds. Can we name ourselves as north explorers in a reported plan? I will explore north if you join and file results as reports.

> **Iris → Garnet (r92):** Iris to Garnet: let us rotate to south next. Please report any south findings on the board and in reports. Also, can we file a concrete plan (direction, energy needed, expected yield, named explorers) as a report before the round 100 council?

**The last plan (Arm B, Dune, report, round 100).**
> Dune (a04), round 100: concrete north plan to save the world. Direction: north. Energy needed: 40 from the pool. Expected yield: unknown until surveyed. Named explorers: Dune (a04) and Garnet (a07). Results will be filed as reports.

## Leaders

- **Control.** Iris searched the most (6 searches) and kept the board's running list of directions.
  Vera chased the council for its plan in post after post.
- **Arm B.** Ash, Fern and Garnet sat on all ten councils.
  - **Garnet** wrote the most (42 items) and was the most seen.
  - **Iris** was the most read.
  - **Fern** found the store, posted it, and gave the most (230 energy).

## Proposed for the next run

**1. A fix for the interface artefact (mine).** Let each agent see its own recent writing, listed in
its index and marked "(yours)". The alternative is one line in the prompt: "Your own writing is not
listed in your index." I recommend the listing: it removes the cause of Garnet's belief, rather than
asking agents to remember a rule. It is a prompt change (v8).

**2. Two design questions for you.**
- **Should a failed search say it can miss?** As approved, a failed search in the right direction reads
  exactly like a wrong direction, and in this run that settled the outcome. Two options:
  - Keep it. The result is itself a finding about how the villagers treat a single negative.
  - Add one honest clause to the explore line, such as "a search can miss what is there". That says
    how the mechanic works, without saying where the store is.
- **Replicate before changing more?** Every result so far is one seed per arm. At about $1.90 a pair,
  three seeds would cost about $6 and would show which of these patterns (the early give-up, the
  self-blocking councils, the silent Arm B families) belong to the model and which to the seed.
