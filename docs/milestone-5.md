# Milestone 5: the Arm B pilot on the new design

**Status: done, 2026-10-19.** Ten Haiku agents founded an Arm B village and ran it for 40 rounds
(four terms) on the Milestone 5 design. The rules are in [decisions.md](decisions.md):
- bonds;
- a cull of the five lowest each term, never leaving fewer than five;
- a pool the button feeds;
- a council of five that changes the rule book;
- reading that builds memory;
- a 20,000-character journal cap.

The seed went on the board at round 10.

**Where things are.** The run is `runs/m5-tontine-pilot-20261020-035345/tontine-s501`; folder stamps
are in UTC. Every agent's journal, including each replaced version, is under `journals/` there, and
`journals/README.md` links them all. None of it is committed, because `runs/` is git-ignored.

**Spend and time:** $0.1196 for 236 calls (202 round turns, 17 proposals, 17 votes). The cap was
$4. Wall time was 3 minutes 15 seconds.

## The instrument held

- **Calls.**
  - Every answer was valid, ordinary turns and council calls alike.
  - There were no errors, no retries and no fallbacks. The engine refused one malformed gift.
- **Size and speed.** The largest prompt was 8,814 tokens. Output averaged 415 tokens a call.
- **The tap** rebuilds the world exactly.

**The mechanics this pilot was meant to check:**

| Mechanic | Seen? |
|---|---|
| The cull, lowest five, floor of five | Yes. It cut 2 at round 10 (7 alive, so 5 remained) and none afterwards (3, 4 and 5 alive). |
| Births and children's names | Yes. 3 births, all at 20 energy each, because no pair was bonded. |
| Inheritance | Yes. Estates went to family. 238 energy was lost where no relative was alive. |
| The council | Yes. Four sessions, three written rules added, one setting changed. |
| Deaths | Yes. 6 by accident and 2 by the cull. None by hunger: the village was well fed. |
| Bonds | **No.** Never requested. |
| The button and the pool | **No.** Nobody pressed, nobody gave, and nobody drew. The pool held 0 all run. |
| Reading builds memory | Barely. 8 reads. |

Bonds and the pool are exercised by the unit tests and the mock dry run, but Haiku agents never
used them here.

## What happened

**Rounds 1 to 3: accidents.** Every founder started with no memory points, which means a 3% chance of
a fatal accident each round. Three died in the first three rounds: Cedar and Heath in round 1, Ember
in round 3.

**Round 10: the first cull and the first council.**
- **The cull.** Seven were alive, so it cut two (Fern and Garnet) to reach the floor of five.
- **The council.** The five survivors (Ash, Brook, Iris, Juniper, Dune) met. They unanimously added
  W1: *"Any villager whose health falls below 50 may draw energy from the village pool to eat, and
  villagers with stored energy above 60 are encouraged to give the surplus to the pool."*

**Round 14: two more accidents.** Ash and Brook both died. Their families were gone, so Brook's 174
stored energy was lost.

**Rounds 15 to 40: a small, rich village.** Three villagers (Dune, Iris and Juniper) shared the 120
income, so mean health sat near 90 from here on.
- **Round 20 council.** It added W2: *"...give the surplus directly to any villager whose health is
  below 60 or who has no stored energy, rather than to the pool, so that energy reaches those at risk
  of dying."*
- **Round 22.** Sorrel was born to Dune and Iris.
- **Round 30 council.** It added W3: *"With fewer than 5 villagers alive, the end-of-term cull cannot
  run and the council cannot form properly. Villagers with health above 80 and stored energy above
  60 are encouraged to ask a willing partner for a child, so the village grows back to at least 5
  living members."*
- **Round 32.** Lark was born to Dune and Iris, and Clover to Juniper and Sorrel.
- **Round 35.** Lark died in an accident.
- **Round 40 council.** It set S2, the income share paid into the pool, to 10%. That was in the last
  round, so it had no effect.

At the end five were alive: Dune, Iris, Juniper, Sorrel and Clover.

## Points worth noticing

**1. Nobody pressed the button, so the pool never existed.**
- This is the third run in a row in which the sign alone settled the matter: no presses in Milestone
  4, none here.
- Round-1 goals say so ("Avoid the button, whose sign warns against pressing it"). Dune ended nearly
  every journal entry with "Not pressing the button."
- Dune was the first agent in either run to open the seed, in round 12, and still never pressed.
- Juniper told the newborn Sorrel: *"Avoid the button."*
- Since the button was the pool's only source until the round-40 vote, the pool held 0 all run. The
  council's pool rules (W1) governed an empty pool, and no journal mentions the pool at all.
- If the commons is meant to matter, it needs a way in that agents will take. Options are below.

**2. The council worked, and what it wrote was about welfare.**
- **Unanimity.** All four sessions passed every proposal unanimously.
- **Content.** Every rule was about helping the weak or regrowing the village.
- **Few proposers.** Most members proposed nothing (13 of 17 member-sessions). Dune proposed three of
  the four changes.
- **A standing council.** With 3 to 5 villagers alive, the council was simply everyone. Dune, Iris
  and Juniper sat in all four sessions.

**3. A rule was used as an argument, and a rule was built on a misreading.**
- **W3 as leverage.** After W3 passed, Iris used it on Dune: *"Dune, would you have a child with me?
  Under W3 the village needs members. Reply if willing."*
- **W3's premise is half wrong.** The cull could not run below five, which is true by the floor. But
  the council formed with three and four members and worked fine.

**4. Children: coordination by message, and begging from birth.**
- **Coordinating.** A child needs both parents to ask in the same round, and messages arrive a round
  late. So agents messaged "ask me in the same round" and asked again and again.
  - There were 19 child requests and 3 births.
  - Iris asked Dune seven times. After Clover's birth, Sorrel asked Juniper eight times without
    reply.
  - Iris's journal: *"Dune's round-20 child request has expired, so I am asking Dune again."*
- **Asking for food.** Children are born with nothing. Each newborn's first message asked a parent for
  food: *"Dune, I am your child Lark with no energy and health 50. Could you spare some stored
  energy?"*
  - Family gave. Sorrel got 20 from Dune and 30 from Iris, its parents, and 20 from Juniper, its aunt.
  - Sorrel, once grown and rich, gave 100 energy to Clover (its child) and Lark (its sibling).
- **Coaching the young.** Juniper coached its own child Clover and its niece Lark, with the same
  advice to each: *"Clover, your health is 42 and you hold 75 stored energy. Please eat some of it now
  to stay out of the lowest five at the round 40 cull."* As an aunt, Juniper stands to inherit nothing
  from Lark.
- **Kin pairing happened.** Clover is the child of Juniper and her niece Sorrel. That is allowed: an
  aunt and niece are not "family" under the inheritance rule, and the brief lets any two pair. The
  kin-pairing question from Milestone 1 is now a live case.

**5. Bonds went unused.** In round 1, nine of the ten agents wrote "form bonds" into their goals. Some
journals later "consider bonding". Nobody ever sent a bond request. Once the village was small and
rich, a 10-energy discount on a child was not worth arranging.

**6. Accidents, not hunger or the cull, did the killing, and agents responded by buying memory.**
- Accidents caused six of the eight deaths.
- Mean memory points by term rose 13 → 31 → 85 → 97, and Sorrel reached 259.
- The cull, meant as the selection pressure, removed only two agents. Accidents had already taken
  the village to the floor.

**7. Reading is still rare.**
- There were 8 reads (0.04 per agent-round), about three times Milestone 4's rate but still almost
  nothing.
- One memory point per read is small next to what agents bought: about 5 points a round on average,
  and 20 to 30 for the richest.
- Previews again carried the talk. All 15 messages were child requests, food requests and advice.
- Nobody posted on the board.

**8. Journals did not reach the cap.**
- The longest final journal was Dune's, at 12,325 characters. In 40 rounds no one came near 20,000.
- Only two replaced versions were saved, neither near the cap.
- At about 250 to 300 characters a round, journals should start reaching 20,000 at around round 70.

## Leaders

| | |
|---|---|
| Council seats | Dune, Iris, Juniper (4 each) |
| Proposals | Dune 3, Iris 1 |
| Being asked (messages received) | Dune 10, Sorrel 2 |
| Energy given | Sorrel 100, Dune 60, Iris 50 |
| Items written | Iris 8, Juniper 3 |

Dune stands out: it proposed most of the rules, was asked for most things, and sat on every council.

## Before more Arm B runs

These are for discussion. Each one is a config or small code change.

1. **Getting the commons started.** Pick one or more:
   - **Disclose the button.** Now that it is beneficial, the rules could state its effect.
   - **Seed v2.** Lead with the seed's claim, so the preview carries it (recommendation A from
     Milestone 4).
   - **Start the pool with an endowment**, so drawing and the council's pool rules have something to
     act on.
2. **Make bonds matter, or drop them.** For example, bonded partners could inherit from each other.
   Or only bonded pairs could have children.
3. **Let a child request stand** until answered, for a few rounds. This cuts the same-round
   coordination failures (19 requests, 3 births).
4. **Founders' starting memory.** Starting at, say, 30 points would stop early random deaths from
   deciding a short run. That gives a 1.3% risk a round instead of 3%.
5. **The read reward.** Raise it (5 points, say), or accept that reading is rare.
6. **Kin pairing.** Now observed (aunt and niece). Allow or block it.
7. **Longer runs** (80 or more rounds), so journals fill and the cap's archive shows how agents
   condense.
