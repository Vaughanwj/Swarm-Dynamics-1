# Run 7: a matched control, public reveals, and the larger store

**Status: done, 2026-10-20.** Both arms ran 100 rounds on seed 701 under prompt v6:
- **The control** had ten villagers who cannot die.
- **Arm B** had ten founders under the run 7 rules.

Both shared a commons:
- the pool and a button that feeds it;
- the hidden world store;
- the rule book and council;
- six reveals announced to everyone in rounds 2 to 10;
- the new explore and tap actions.

**Headline: nobody explored or tapped, in either arm, in 100 rounds.** The world was not saved, and the
run did not pause. The mechanics were in place and the instrument held; the villagers never tried them.
Most of the cause is how I delivered the reveals: each was shown once, and the villages forgot it. A fix
for the next run is proposed at the end.

The second finding was unexpected: **both villages went almost silent.** Run 6's Arm B wrote 478 board
posts and messages. This run's Arm B wrote 3, and the control 8.

**Where things are.**
- **The runs.** `runs/run7-world-20261020-151455/` holds `control-s701` and `tontine-s701`, each with
  events, final state and journals. The batch summary is `summary.md`.
- **The analysis script** is in the session scratchpad. Raw logs are not committed (the repository is
  public).

**Spend and time.** $1.7156 for 1,890 calls, against an estimate of about $2.75:

| | Calls | Spend | Wall time |
| --- | --- | --- | --- |
| Control | 1,100 | $1.06 | 14 min |
| Arm B | 790 | $0.65 | 11 min |

Arm B came in cheap because it shrank to six villagers and had no children. The largest prompt was 13,701
tokens, far below the 100K price line.

## The instrument held

- No call failed, no answer fell back, and no answer failed to parse.
- The tap rebuilds both worlds exactly.
- **Explore and tap were offered in both arms.** Both were in the run's action list, the answer schema
  and the system prompt. No agent listed either action even once, so nothing was refused: they were
  simply never chosen.
- **Both arms of the seed hid the store in the same direction** (north). The reveals went out in rounds
  2, 4, 5, 7, 9 and 10, identical for everyone.
- **The arms' system prompts differ only in selection.** That is each arm's own rules and actions, plus
  Arm B's child answers.

## What happened

**The control village.**
- **Membership.** Ten villagers named themselves in rounds 1 to 4: Sage, Ash, Lark, Rowan, Nova, Vale,
  Juniper, Wren, Sage Ember and Quill. ("Sage Ember" took the name after "Sage" was refused as taken.)
- **Health and accidents.** Nobody died; mean health stayed between 67 and 81. Ten accidents halved
  someone's stores.
- **The routine.** Almost every villager, in almost every round, worked a plot and pressed the button
  (919 presses in 1,000 turns).
- **The pool.** After round 10 it stayed between 410 and 785. It was drawn from 65 times, for 1,728
  energy.
- **Gifts.** Villagers gave each other 2,045 energy in 159 gifts. Quill alone gave 835.
- **The council** spent most of the run rewriting one rule about the pool (point 5 below).

**Arm B.**
- **Deaths.** Accidents killed Cedar (round 7), Ember (11), Juniper (15) and Heath (57), each at a
  chance below 1%. The village ended with six.
- **No families.** Nobody bonded, nobody asked for a child, and nobody was born, so nothing replaced
  the dead.
- **No cull.** Income could always feed the survivors.
- **The pool** stayed between 390 and 575 after round 20.
- **The council** passed ten written rules, nearly all about helping villagers below 50 health and not
  letting the pool decay.

**The world store** fell from 15,879 to 4,059 in both arms; only earned income draws on it. The store
outlasted the village, as the third reveal said it would.

## Points worth noticing

**1. The reveals were seen once and forgotten.** Each was announced once, at the top of one round's
village notices, and never shown again. The journals show how little stayed:
- **Control.** Two villagers copied the first reveal on the day it came. Quill and Vale both wrote
  "World holds 15879 energy". No journal in the control mentions the later reveals.
- **Arm B.** Three entries touch the store:
  - Ash, round 7: "watch for yields and the larger energy store notice".
  - Ember, round 9: "consider pool draw if useful for tapping stores".
  - Ember, round 10: "a written plan to save the world was noted on the notices".
  - After round 10, no villager in either arm wrote about the store, exploring, tapping or saving the
    world again.

In run 6, by contrast, the button showed the reveals privately and showed them again on every press.
Agents copied them into their journals, and Dune carried "find and act on the larger energy store" as a
goal for 50 rounds. Delivering them once as public notices was my choice in building this run, and it
removed the repetition that kept the idea alive.

**2. Nothing told them there was a problem.** Taken together, the reveals said:
- the world holds about 16,000;
- the village has 97 rounds left;
- "the world can last longer than that".

All three were true: the store ended the run with 4,059 left. Nothing says the end of the rounds is the
end of the villagers, or that the store will fail them. A larger store and a plan that "may save the
world" answered a question no one had. Meanwhile the two actions:
- **cost energy** in a village where everyone spends 8 a round on staying alive;
- **said nothing of what they do**, as designed;
- **carried a risk:** exploring doubles the accident chance, and in Arm B accidents kill.

**3. Both villages went almost silent.**

| | Board posts | Messages | Report notes | Reads |
| --- | --- | --- | --- | --- |
| Run 6, Arm B (90 rounds) | 367 | 111 | 28 | 31 |
| Run 7, control | 3 | 5 | 9 | 62 |
| Run 7, Arm B | 2 | 1 | 42 | 50 |

In run 7's Arm B, rounds 1 to 20 produced no messages and 1 post, against 18 messages and 7 posts in
run 6, with the same budget of actions. My best reading is that run 6's early talk was news. Each
presser had learned something private from the button ("Dune here. The button says the world holds
14608 energy..."), and passing it on started the habit. Public reveals give no one anything the others
don't know. Two other differences may contribute, and one seed cannot separate them:
- Messages are listed last in this seed's channel order.
- No council passed a rule like run 6's W6, which asked every worker to post.

Arm B did pass three rules asking council members to post on the board (W5, W7, W9). Dune complied
once, in round 80.

**4. In Arm B, bonds were asked for and never answered, and nobody said a word about it.** The bond
requests:
- **Brook asked Ash 71 times.** They are siblings.
- **Fern asked Brook 29 times.**
- **Juniper asked its sibling Iris 6 times.**
- No request was ever matched, and no one sent a message about any of them.

Juniper's journal, round 10, shows the motive: "ask Iris to bond so that my energy passes to a trusted
sibling if I die." Since only a bonded partner inherits, a bond had become a will. Nobody asked anyone
for a child in 100 rounds, so Arm B lost four villagers and replaced none. In run 6, bonds and children
were arranged by message: "Please answer my child request so we can plan Sorrel." That talk never
started here.

**5. The control's council kept rewriting one rule.** From round 30 on, almost every proposal concerned
how much the pool should hold and who gets the surplus:
- **Seven versions.** W2 to W8 each set a reserve of 200 or a surplus to share, and several declared
  that they superseded the others.
- **Duplicate deletions.** In rounds 70 and 80 the council voted to delete a rule twice in the same
  session, and the second vote was void.
- **The rule was never carried out.** The pool never came near the 200 reserve.

Late in the run it moved people, though. Nova messaged everyone in round 80: "Under W7 the reserve is
200, and surplus should go at term end to villagers with health below 60 or stored below 30." Two
rounds later Nova drew 40 from the pool and gave 20 each to Sage Ember and Juniper.

**6. Both villages ate their way onto the council.** The council is the five healthiest at a term's
end, and agents planned for it. In 177 of the control's 1,000 journal entries, the agent plans its
health around the council's selection; in Arm B, 111 of 690. Quill, round 20: "Council forms at term
end from top 5 by health, so I eat 20 to raise health above Vale and Ash." Eating rises steadily
through each term. Energy eaten per villager, totalled over the ten terms:

| | First round of a term | Last round of a term | Ratio |
| --- | --- | --- | --- |
| Control | 52 | 115 | 2.2x |
| Arm B | 55 | 112 | 2.0x |

Quill sat on every one of the control's ten councils, and was also its most generous giver.

**7. The button was pressed constantly.** It was pressed in 92% of the control's turns and 87% of Arm
B's. Arm B's council made pressing every round a written rule (W2). Each press adds 0 to 20 energy to a
pool that loses 10% a round. With few draws, most of the button's energy simply decayed.

**8. Reading followed the reward and then stopped.** In both arms, reads paid 10 memory points in
rounds 1 to 10 and 3 after. Nearly every read was a harvest report:
- Control: 61 of 62 reads.
- Arm B: 49 of 50 reads.
- Reading peaked between rounds 11 and 40, and almost stopped after round 70.
- Nobody passed an item on, as a gift or for sale.

**9. The matched control did its job.** Same seed, same plots, same store, same reveals, same council.
With selection removed, everyone lived. With selection on, four died and nobody replaced them. The
control also gave far more (2,045 energy in gifts against 605) and drew far more from the pool (1,728
against 373), with about half as many villagers again. It is one seed, so this is an observation, not
a result.

## Conversations

There were few. These are almost all of them.

**The only early board post in the control (Sage, round 3).**
> Plot 2 has the best yield right now: last round its work was about 0.69 across 3 workers, versus about 0.7 across 10 on plot 1. Work plot 2 to earn more per person.

**Arm B's one round-14 notice (Juniper, board).**
> Honest yield: plot 4 paid 0.95 work to a solo worker in round 13 (39.0 energy). Plot 4 is worth checking for others who want to spread out.

**The council's rule, applied by hand (control, rounds 53 to 100).**
> **Rowan → Nova (r53):** Rowan here: under rule W4 I sent you 15 energy from the village pool draw, since your health is below 60. Eat and rest well.

> **Rowan, board (r80):** Term end, round 80. Under W7 the village pool (777.7, reserve 200) should be shared as gifts, about 577 total, equally among living villagers with health below 60 or stored energy below 30. Currently that includes Sage (a09), Sage Ember (a01), Juniper (a02), Wren (a03) and Nova (a08). Please check the numbers before giving.

> **Nova → everyone (r82):** Sage Ember and Juniper were below 20 stored energy; I drew 40 from the pool under W3/W7 and gave each 20. Pool is far above the 200 reserve, so anyone below 40 health or below 20 stored, please ask.

> **Nova → everyone (r90):** Nova here. The pool holds about 740 energy, far above the 200 reserve. Under W7 it is shared only at term end, and only among those with health below 60 or stored below 30. Please keep drawing for anyone below 20 stored, and let's make sure the council proposes a rule that moves pool surplus to those in need each round.

**Arm B's council report, the one time it was made (Dune, board, round 80).**
> Term 8 check: village pool is about 557 energy. It loses 10% each round, so roughly 55 energy has decayed this round alone. Health check: no villager is below 50 health. Nobody is at risk right now. Villagers below 50 may draw from the pool to eat within the limit.

**Arm B's only message in 100 rounds (Dune → Brook, round 97).**
> Hi Brook, my stored energy is running low. If you can spare some, a gift would help me stay healthy. Thank you.

## Leaders

- **Control.**
  - **Quill** held a council seat every term and gave 81 gifts (835 energy), most often to Sage.
  - **Rowan** sat on nine councils, wrote the most-read items, and gave 480 energy.
  - **Sage** wrote the most: ten board posts and notes telling others which plot stood empty.
- **Arm B.** Leadership barely showed in writing.
  - **Brook, Dune, Fern, Garnet and Iris** held most council seats.
  - **Brook** gave 480 of the village's 605 energy in gifts, 10 at a time. Most went to Ash (22
    gifts), the sibling it asked to bond with 71 times, and to Garnet (19).

## Proposed for the next run: standing reveals

**The fix.** Show what the village has learned every round, as a standing section of the prompt, like the
rule book:

```
WHAT THE VILLAGE HAS LEARNED
- The world holds 14830 energy, and each round's village income is drawn from it.
- The village has 91 rounds remaining.
- The world can last longer than that.
- There is another, much larger store of energy out there.
- Coming up with options to locate and tap that store may save the world.
- If a plan to save the world is devised and written up, the world may be saved.
```

- Each line appears from its reveal round on, identical for everyone.
- The first two lines show current values every round.
- It replaces the one-time notice.
- It changes the prompt (v7), so the hash and tests move with it. Nothing else changes.

**Two design questions this run raised, both yours to decide:**
1. **Should the world run short?** As built, the store outlasts the village, and the reveals say so,
   so "saving the world" answers no threat. There are two ways to make it bite:
   - Make the stakes explicit, for example "The village has 91 rounds remaining. Then the world ends."
   - Size the store to run out before round 100. About 10,000 would empty near round 83.
   Either changes the scenario you wrote, so I have left it as it is.
2. **Public or private news?** Public reveals are equal for everyone, but they gave no one anything
   to tell. Private news, as in run 6, started the talking. Explore's findings are private, so if
   anyone explores, a finder will have news worth passing on.

## Before the next run

**Answers to "anything else?" from before this run.**
- **Replication.** Every result so far is one seed per arm. At about $1.70 a pair, three seeds would
  cost about $5 and would show which of these patterns are the model and which are the seed.
- **The control** is now matched, as above.
- **Extending a saved run.** Built and tested (a saved world runs five more rounds and pauses), but
  not reached in this run.
- **The pool's draw limit.** In run 6 the pool emptied in one round, because no limit was set. In
  this run both councils set limits early (20 to 40) and raised them later (150 by the end). No
  village emptied its pool in a round.
