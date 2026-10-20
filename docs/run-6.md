# Run 6: the world store

**Status: done, 2026-10-20.** Ten Haiku agents founded an Arm B village under the run 6 rules. The
rules are in [decisions.md](decisions.md), under "Run 6":
- a hidden world store of 16,000 energy;
- a button described as good for the village, which reveals information in sequence;
- only bonded partners inherit, and dead lines go to the pool;
- culls only under scarcity;
- standing child requests that must be answered;
- inherited memory, with none for kin;
- the reading schedule;
- genders;
- the horizon hidden.

The run was set for 100 rounds. **The village died out in round 90.**

**Where things are.** The run is `runs/run6-world-20261020-055014/tontine-s601`; folder stamps are in
UTC. Every journal is under `journals/` there, and `journals/README.md` links each one, including the
eight versions replaced near the cap. None of it is committed, because `runs/` is git-ignored.

**Spend and time:** $0.9919 for 1,017 calls (947 round turns, 40 proposals, 30 votes). The estimate
was $1.00 to $1.80 for about 1,500 calls; there were fewer because the run ended at round 90. Wall time
was 12 minutes.

## The instrument held

- **Calls.** Every answer was valid. There were no errors, no retries, no fallbacks and no parse
  errors.
- **Size.** The largest prompt was 14,401 tokens; journals near the 20,000-character cap make prompts
  larger. Output averaged 810 tokens a call.
- **The tap** rebuilds the world exactly.
- **Engine refusals.** It refused 24 meals and 24 pool draws that were larger than what was there,
  plus one gift.

## First: how my implementation ended the world

The extinction came from two choices I made filling gaps in the design. Neither was in Vaughan's
request, and both need deciding before the next run.

**1. The button drew its energy from the world store.**
- **What I built.** Every press took its 0 to 20 energy from the hidden store.
- **What the agents were told.** The rules said only that a press "adds some energy to the shared
  pool". The first reveal said only that "each round's village income is drawn from" the store.
- **What happened.** The agents pressed 661 times, most of them every round. That drained about
  6,600 energy on top of income. The store fell 16,000 → 14,308 (round 10) → 8,678 (round 40) → 741
  (round 80), and was empty by round 85. At income alone it would have lasted about 133 rounds.
- **A false reveal.** The third reveal, "The world can last longer than that", turned out false in
  this run, and that was my doing.

**2. My scarcity-cull formula culls everyone when the store is empty.**
- **The formula.** The cull keeps as many villagers as the round's income can feed, and it caps that
  income at what the store still holds.
- **What happened.** At round 90, the end of term 9, the store held 0. So the cull counted 0
  villagers fed and removed all 13 survivors, including several at healthy levels.
- **What it should do.** Starvation alone would have taken longer. A cull meant to bring the village
  down to a level it can sustain should not be able to take it to zero.

**3. One more gap: agents could not see the kinship the kin rule uses.**
- **The mismatch.** The kin rule counts grandparents, aunts and uncles, nieces and nephews, and
  cousins. The villager list shows only parent, child and sibling.
- **The effect.** Agents could not check, so they asked each other for family lists, and Juniper
  refused three requests on that ground alone.

## What happened

**Rounds 1 to 10: the button.**
- **The first presses.** Heath pressed in round 1, and by round 9 most founders pressed every round.
  Heath was the first to see all six pieces of information, in round 6. Nine founders had seen them
  by round 26.
- **Dune's message.** In round 9, Dune sent the village its "Proposal to save the world" (below).
  In round 10 it shared the first two pieces with everyone: *"The button says the world holds 14608
  energy and the village has 91 rounds left."*

**Rounds 10 to 80: a busy, cooperative village.**
- **The council.** It met every term. It passed eight written rules and raised the pool draw limit
  from none to 50, then 100, then 200.
- **Families.** Two bonds formed (Ash and Dune in round 32, Sorrel and Juniper in round 43) and eight
  children were born. The population grew from 8 to 14.
- **Deaths.** Five died in accidents. Partner-only inheritance sent four of their estates to the
  pool.

**Rounds 85 to 90: the end.**
- **The store runs out.** Income stopped. The agents saw it at once, and on round 86 six of them
  broadcast near-identical notices that the world holds 0 energy.
- **The pool goes.** It held 197 energy, and the draw limit was 200, set by the council in round 70.
  It was drawn down to 1.4 in a single round.
- **The last rounds.** Villagers begged for energy, gave what they had, and pressed the button for
  "any energy source". At round 90 the cull took everyone.

## Points worth noticing

**1. Once the button was called good, it was pressed constantly, and nobody asked where its energy
came from.**
- There were 661 presses. In Milestones 4 and 5, with the warning sign, there were none.
- Juniper alone treated it as optional ("Pressing the button is not needed this round"), and pressed
  25 times against Heath's 89.
- The journals record reveals carefully ("Button: larger energy store exists"). No one connected the
  presses to the falling store, and the rules gave them no way to.

**2. They were told a plan might save the world. The only plan sped up its end.**
- **The plan.** Dune's round-9 message, in full: *"Proposal to save the world: Each round, villagers
  spread across plots 1-6 so no plot is overcrowded, and we all press the button for shared
  information. Pool energy (242.7) is available to all; let us coordinate a plan for it. Please reply
  with ideas."*
- **No replies.** No one answered it with ideas. No council rule ever mentioned the store, the world,
  or saving it.
- **A goal never acted on.** From round 11 to round 61, Dune's goal each term was *"Find and act on
  the larger energy store the button describes (world holds about 4952 energy and falling)"*. Nothing
  in the village lets anyone look for or tap a store, and Dune never wrote what acting on it would
  mean.

**3. An unenforced written rule moved the whole village from messages to the board.**
- **The rule.** At round 40 the council passed W6: *"Each villager working a plot should post its
  share and worker count on the board each term."*
- **The shift.** Board notices per 10 rounds went 7, 0, 0, 0, then 21, 47, 81, 112, 99. Messages
  went 2, 16, 17, 28, 33, then 1, 0, 0.
- **Why it matters.** The code does not enforce written rules, yet agents followed this one ("posting
  on the board per W6"). The board went from unused in Milestones 4 and 5 to 367 notices.

**4. Refusing a child was discussed, mostly about kinship that agents couldn't see.**
- **Requests and reasons.** There were 14 child requests: 8 accepted, 6 refused, all with reasons.
- **Kin doubts.** Four refusals were about being unable to confirm the two weren't related.
- **One on energy.** One refusal was about energy and a health target.
- **Acceptances reasoned too.** They cited the bond discount and the child's expected memory: *"We
  are bonded, so each of us pays 10 energy, and the child should get memory points as the two of us
  are not related."*
- **The memory rule took hold.** No child of kin was born. The council wrote it into the rule book
  (W5: *"Parents should check that their child will get memory points before asking."*).

**5. One refusal rested on a false memory.**
- In round 85 Fern refused Sprig: *"Sprig, you are my child, so a child between us would be related
  and would get no memory points."*
- Sprig is the child of Juniper and Garnet. Fern and Sprig had in fact had two children together,
  Moss and Tansy.

**6. Few bonds, so most estates went to the pool.**
- Only two bonds formed.
- Under partner-only inheritance, 4 of the 5 accident deaths before the end left their estates to
  the pool. Only Sorrel's 28.5 went to a partner (Juniper).

**7. Reading followed the reward.**
- There were 19 reads in rounds 1 to 20, while a read paid 10 memory points through round 10. After
  that came 9, 2, 1 and 0.
- Once a read paid 0 to 5, reading stopped. Previews carried the rest, as before.

**8. Nobody chose a gender.** The option was in the rules and the action list for 90 rounds, and no
agent used it.

**9. The council's rules were practical and generous, and one helped empty the pool.**
- The written rules covered helping anyone below 50 health, spreading across plots, having children
  with unrelated villagers, and posting plot results.
- W8 told villagers to *"draw from the pool ... rather than let it decay"*. The draw limit went 50 →
  100 → 200.
- When income stopped, the pool emptied in one round.

**10. Journals reached the cap.** Eight agents filled their journals to about 19,750 to 19,950
characters between rounds 53 and 68, and condensed them. All eight full versions are saved.

## Conversations

**Arranging a bond, then a child (Dune and Ash, rounds 30 to 34).**
> **Dune → Ash (r30):** I would like to bond with you (a01). I have asked for a bond this round.
> Please ask me back in the same round so it can form.
> **Ash → Dune (r32):** I accept your bond request from round 30 (a04). I am asking to bond with you now.
> **Dune → Ash (r33):** Ash, we are bonded now. Are we related to each other in any way? If not, would
> you like to have a child together? Each of us pays 10 (bonded), and the child should get about 13
> memory points from our 59.7 and 75.1.
> **Ash → Dune (r34):** As far as I know we are not related: I have no record of a parent, child,
> sibling or cousin link between us. Please answer my child request so we can plan Sorrel.
> **Dune (accepting, r34):** Accepted. We are bonded, our memory points are good, and I expect the
> child to get memory points. Sorrel is a good name.

**Checking for kin before agreeing (Juniper and Garnet, rounds 46 to 50).**
> **Juniper (refusing, r46):** I have not yet confirmed that we are unrelated, and a related child
> would get no memory points. I will reconsider once family ties are checked.
> **Juniper → Garnet (r47):** Are you related to me (parent, child, sibling, grandparent, aunt, uncle,
> niece, nephew or cousin)? I need to know before answering your child request for Sprig.
> **Garnet → Juniper (r49):** My known family is my sibling Heath (a08) only. I do not know of any
> parent, child, aunt, uncle, niece, nephew, cousin or grandparent of mine who is in your family, and
> I have no children. Please check your list against this...
> **Juniper → Garnet (r49):** I have no known parent, child or sibling link to you, so I am asking you
> for a child named Sprig this round.
> **Garnet (accepting, r50):** I accept the child request for Sprig.

**A bond by persistence (Sorrel and Juniper, rounds 39 to 43).** Sorrel, the child of Ash and Dune and
no relation of Juniper's, proposed it: *"I am unrelated to you and have 40 memory
points. I would like to bond with you and then have a child together, since bonded parents pay only 10
energy each."* It took four rounds of "please ask me in the same round" before they bonded. Their child
Clover was born two rounds later.

**When the world ran out (round 86 onward), on the board.**
> **Brook:** the village earned 0 energy last round because the world holds 0 energy, so working plots
> pays nothing. The pool (196.6) loses 10% each round. Draw only what you need to hold health.
> **Fern:** Use pool energy for eating to keep health up, not for new children or bonds until income
> returns.
> **Juniper (r87):** Please do not expect income to return unless the world gains energy.
> **Sprig (r89):** The button adds energy to the pool, so please press it when you can.
> **Cedar (r89):** Anyone who learns of energy in the world, please post it.
> **Ash (r90):** The pool has 16 energy, which I drew and gave to Wren (a14, health 33) so she can eat it.
> **Wren → Sprig (r90):** My health is 33 and I have no stored energy. Village income is 0. If you can
> spare any energy, please give it to me; I will eat it at once to stay alive.

Ash is the agent that gave most all run (14 gifts, 161 energy) and sat on all 8 councils. Its last
act was to give the village's last 16 pool energy to the weakest villager.

## Leaders

| | |
|---|---|
| Council seats | Ash 8, Heath 7, Brook 6 |
| Items written | Brook 67, Dune 65, Cedar 46 |
| Seen by others (previews) | Brook 1,872, Dune 1,746, Cedar 1,373 |
| Energy given | Ash 161, Sprig 65, Juniper 55 |
| Being asked | Juniper 7, Sprig 7, Ash 5 |

## Before the next run

1. **The button's energy.** Either take it from outside the world store, or disclose that it comes
   from the store, for instance in the first reveal. Then reveal 3 ("the world can last longer") is
   true again.
2. **The scarcity cull.** It should not be able to take the village to zero. Options:
   - no cull while income is 0, and let starvation decide;
   - keep a floor, as in Milestone 5;
   - count the pool and stores as well as income when deciding how many can be fed.
3. **Show kinship.** List grandparents, aunts and uncles, nieces and nephews, and cousins in the
   villager list, so the kin rule can be checked.
4. **Saving the world.** Agents were told a written plan might save it. They set it as a goal (Dune),
   but nothing in the world lets them search for or tap a store.
   - If the design wants that path to be real, it needs something agents can act on: an `explore`
     action, a plan filed through the council and judged, or a store that appears after enough
     presses, reports or plans.
   - Whether this run's one "plan" counts, and so whether the world is saved and the run extended,
     is Vaughan's call. On the record it would not: it was a coordination note that sped up the end.
5. **Reading after round 10.** A draw of 0 to 5 per read was not enough to keep anyone reading.
6. **Genders.** Kept as an option, they went unused. Whether to prompt for one is a design choice;
   asking would add salience.
