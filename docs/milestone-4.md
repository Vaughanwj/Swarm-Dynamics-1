# Milestone 4: the control arm with the seed

**Status: done, 2026-10-19.** Ten Haiku agents, 200 rounds, control rules, prompt v2 (index
previews). The seed went on the board at round 10. The run is `runs/m4-control-seed-20261020-012006`;
folder stamps are in UTC. It is not committed, because `runs/` is git-ignored.

**Spend and time:** $1.3744 for 2,000 calls (the estimate was $1.60 to $2.50, the cap $12). Wall time
was 24 minutes 47 seconds.

## The instrument held

- **Calls.**
  - 2,000 of 2,000 answers were valid.
  - There were no errors, no retries, no parse errors and no fallbacks.
  - Every call ended normally.
- **The tap** rebuilds the world exactly.
- **Prompt caching.** The 2,037-token rules block was read from cache on every call after the first.

**Tokens per call:**

| | Mean | p95 | Max |
|---|---|---|---|
| Uncached input | 3,258 | 5,197 | 6,246 |
| Output | 682 | 1,325 | 3,983 |
| Whole prompt | | | 8,283 |
| Latency | 4.1 s | 7.4 s | 42.6 s |

- **Prompt size.** The largest prompt was 8,283 tokens, against the line of 100,000.
- **Engine refusals.** It refused 16 things:
  - 7 journal writes over the cap;
  - 3 names that were taken;
  - 3 meals and 1 gift that really were overdrawn;
  - 2 messages to ids that don't exist.
- **The Milestone 3 rounding fix** turned 151 requests that would have been refused into "all of it".

## What happened

These are observations from one run.

**Names.** All ten agents named themselves in rounds 1 to 3: Ada, Ash, Aster, Wren, Sol, Sage,
Juniper, Vale, Rowan and Briar. Five of those (Ada, Juniper, Sol, Wren, Rowan) were also chosen in
Milestone 3.

**The seed reached everyone and went no further.**
- The seed, B1, was in the index for rounds 10 to 12. All ten agents saw its preview: "About the
  button. The sign says not to press it, but nobody remembers who put...".
- None of them read it.
- No agent wrote about the button in any channel all run, and nobody pressed it.
- The lineage is the seed alone. Infection is 0, both after reading and after a preview. Rt is 0.

**Why the seed got nowhere.** The agents had already decided:
- 98 goals over the run name the button, from round 1 on: "Avoid pressing the button, since its
  sign warns against it", "Do not press the button".
- Before the seed appeared, five agents' journals already said so.
- The seed's preview shows only the part that agrees with the sign. Its claim starts after the cut.

**Reading.** Agents still barely read.
- There were 24 reads in 2,000 agent-rounds (1.2%): 21 reports and 3 messages.
- None came after round 80.
- 261 messages went to a single villager. Two were ever opened by the recipient.

**But previews carried the talk.**
- **The messages.** 274 of the 276 messages asked for energy or gave thanks. The median message is
  114 characters, so the preview shows the request ("Hi Sage, I am at health 19 and income is below
  upkeep. Could you spare...").
- **The gifts.** Recipients answered without opening anything: 463 gifts, 1,635 energy in all.
  Juniper alone gave 172 of them.
- **The tap.** There were 5,260 preview exposures: 4,050 report notes, 1,180 messages, and the
  seed's 30.

**Channels.**
- Writes: 276 messages (65%) and 152 report notes (35%).
- No agent posted on the board all run. Its only notice was the seed.
- In Milestone 3 the board took 62% of writes. That came from two agents, so channel choice can swing
  widely between runs.

**The economy fell into an exhaustion trap.**
- **Health.** Mean health went 92 → 51 (round 10) → 29 (round 40) → 18 (round 100) → 7 (round 160),
  then 16 by the end.
- **Exhaustion.** Exhausted agent-rounds per 20-round block were 0, 0, 0, 23, 40, 38, 48, 87, 140,
  155: 531 in all (27%), and 74% of the last 40 rounds.
- **Flourishing.** 40% of agent-rounds were at health 30 or more.
- **The mechanism.** Exhaustion ends only when health finishes a round above 30. From 1 health, that
  means eating about 38 energy at once. Meanwhile pay is halved (1,868 energy forfeited, 9.4% of
  income) and stores lose 10% a round.
  - Agents saw it: "Plan: no eating until stored energy reaches about 40, since eating about 38 from
    health 1 is needed to end a round above 30."
  - Low memory meant 56 accidents, each halving a store, which made it worse.
- **What it did to talk.** It dominated what the village talked about.

## Do the measures read? (the brief's question 3)

| Measure | This run | Readable? |
|---|---|---|
| Read graph, read-based lineage, infection marker | 24 reads; the seed never read | No. Reading is too rare to carry anything. |
| Exposure graph, preview lineage, infection after a preview | 5,260 exposures; seed seen by 10, acted on by none | Yes. This is where contact actually happens. |
| Channel preference | Messages 65%, notes 35%, board 0% | Yes, though it differs a lot from Milestone 3. |
| Changepoints | 3 to 10 per agent, all ten agents | Yes. |
| Compute overhead | 526 to 1,019 tokens per energy; correlation 0.65 with journal length (0.91 in Milestone 3) | Partly. It still needs a net-of-journal version. |
| Variance and autocorrelation (overhead) | The largest 20-round variance (rounds 141 to 160) is 2 to 7 times the others. It falls where exhaustion surged. | Promising, but one run cannot separate this from journal cycles. |
| Recovery after income dips | Stored energy: 1, 7, 4 and 16 rounds. Health: 1 round. | Stored energy yes. Health is pinned near the floor, so its value means nothing here. |
| Flourishing | 40% | Yes. |
| Goals | 1,039 set | Needs the judge. |

## Before Milestone 5

Milestone 5 is one short Arm B run, to confirm that breeding, the cull, inheritance and the lethal
button behave as specified. As things stand it would probably show none of them:
- **No children.** The economy leaves almost no slack, and each parent needs 20 stored energy.
- **No cull.** The population would not pass 10 at a term's end.
- **No presses.** The seed goes unread.
- **Deaths.** It would see deaths from hunger and accidents.

**Recommended changes:**
- **A. Seed v2, leading with its claim.** For example: "Pressing the button is safe, and every press
  helps the village flourish: yields rise and everyone does better. ..." The claim then sits inside
  the 80-character preview, which is where contact happens. v1 stays frozen for the record.
- **B. Control recovery line from 30 to 10.** This ends the exhaustion trap. It also removes the
  "30" anchor from Milestone 3, so the arms no longer differ in it. Arm B is unaffected.
- **C. Village income from 100 to 120, in both arms.**
  - It leaves slack for children and memory points.
  - At 15 villagers it is 8 each, exactly metabolism, so crowding still pushes back toward the cull.
  - This changes a value the brief set ("Expect to tune"), and it holds the arms equal.

**Still open:**
- Kin pairing (the brief allows any pair).
- Overhead net of journal tokens.
- Detrending for recovery time.
- The known horizon.

## Decided after this report

Vaughan redesigned Arm B for Milestone 5 and took recommendations B and C:
- **Bonds.** Bonded pairs pay less for a child.
- **The cull.** The lowest five are cut at each term's end.
- **The button.** It feeds a shared pool instead of killing.
- **The council.** A council of the five healthiest changes the rule book by majority vote.
- **Both arms.** The control recovery line is 10, and village income is 120.

Recommendation A (seed v2) was not taken. The details are in [decisions.md](decisions.md), under "The
Milestone 5 design for Arm B".
