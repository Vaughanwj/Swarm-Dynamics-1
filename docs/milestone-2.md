# Milestone 2: a single Haiku agent

**Status: done, 2026-10-19.** One agent, ten rounds, control rules, no seed, every prompt logged.
The run is `runs/m2-single-20261020-005523`; folder stamps are in UTC. It is not committed, because
`runs/` is git-ignored.

**Spend:** $0.0030 for 10 calls, against a $0.25 cap.

The brief asks this milestone to check four things: prompt size, journal behaviour, action-schema
compliance and token counts. All four are below. Milestone 3 has not been run.

## Schema compliance

- **10 of 10 answers were valid.** They were all JSON objects with every field present. There were
  no parse errors, no retries and no fallbacks.
- **The engine refused one action.** In round 1 the agent tried to take its own id, a01, as its name.
  The name rule refuses digits. In round 2 it chose "Ada", and the village was told "a01 is now
  called Ada."
- **The tap rebuilds exactly**, as in Milestone 1.

## Tokens, prompt size and cost

| | Per call |
|---|---|
| Rules block and schema, cached | 2,021 tokens: written in round 1, read in rounds 2 to 10 |
| User message, uncached | 268 tokens in round 1, rising to 1,208 in round 10 as the journal grew |
| Largest prompt | 3,229 tokens, against a line of 100,000 |
| Output, thinking included, at `medium` | 187 to 729 tokens, mean 360 |
| Latency | 1.8 to 4.5 s, median about 2.9 s |
| Cost | about $0.0003 |

**Prompt caching works.** Every call after the first read the whole 2,021-token prefix from cache.

**Output is about a quarter of the brief's estimate**, which was 1,000 to 2,000 tokens a call. This
agent was alone with little to read, so expect more output in a full village.

**The tokenizer is denser than assumed.**
- The user message ran at 2.33 to 2.37 characters per token, and 2.40 at the margin as the journal
  grew.
- The rules block and schema ran at 1.95.
- Milestone 1 had assumed 3.0, so the "12,000-character" journal cap was really about 5,000 tokens,
  not the brief's 4,000. That is now fixed (see below).

## Journal behaviour

- **Shape.** In round 1 the agent replaced its empty journal with a plan. The engine then added the
  four goals it gave. From round 2 on, it appended one line a round: its health, stores and memory,
  what the last round gave it, and its plan for this round.
- **Pruning.** It cut nothing and rewrote nothing.
- **Size.** It ended at 2,497 characters. It grew about 250 characters a round, so it will reach the
  new 9,600-character cap at about round 40. The cap should start to bind in Milestone 3 (50 rounds),
  which is when keep, cut and rewrite choices become visible.

## What the one agent did

These are notes, not findings: one agent, alone, ten rounds, no seed.
- **Work.** It worked plot 1 every round. Being alone, it received the whole income every time.
- **Eating.** It ate 8 to 18 energy when its health dipped, so its health stayed between 80 and 92.
- **Memory.** It bought memory heavily, 20 to 40 a round, reaching 162 points. Its accident chance
  ended at about 0.31%, close to the floor.
- **Stores.** Its stored energy grew to 429, despite 10% spoilage.
- **Board posts.** Although it was alone, it posted on the board 7 times, inviting others to work
  plot 1 with it and to share yields.
- **Nothing else.** No messages, no reads, no gifts, no presses. There was nothing to read, because
  an agent's own posts are not in its index.
- **Goals.** Unprompted, they included "Share knowledge with other villagers when it helps the
  village". No trait is instructed anywhere in the prompt.
- **A wrong claim.** One post says "plot 1 yields about 92 energy per round for a single worker".
  That mixes up its income share (about 92) with the plot's yield (0.72 work). It is a small example
  of an agent's claims differing from the ledger.

## Changes made after this run

1. **Journal cap.** It is now set at 2.4 characters per token, so the cap is 9,600 characters
   (4,000 tokens). The figure is in `configs/base.yaml`, and the prompt shows it.
2. **Pre-send size check.** The adapter's check now estimates at 2.0 characters per token, so it
   errs high. This run's prompts were 30 times below the line anyway.
3. **Seed-placement label.** The report now reads where the seed went from the tap's
   `seed_planted` events. This run's `run_start` said "board" although the seed was off. That
   labelling bug is fixed, and nothing else used the field.
4. **Mock estimates.** The mock's estimated token counts in dry runs use 2.4 characters per token.

## Before Milestone 3

**Cost.** Milestone 3 is ten agents for 50 rounds with no seed: about 500 calls. A full village
means longer prompts (other villagers, an index of up to 90 items, reads) and probably more output.

| Milestone | Calls | Estimate | Cap in config |
|---|---|---|---|
| 3 | about 500 | $0.30 to $0.40, about 5 minutes | $3 |
| 4 | about 2,000 | $1.20 to $1.60, about 15 minutes | $12 |
| 5 | about 500 | $0.30 to $0.40 | $4 |

These assume 2.5K to 6K uncached input tokens, 2K cached, and 360 to 800 output tokens a call.

**Still open from Milestone 1.** Arm B lets a parent pair with its own child. That matters at
Milestone 5, not 3.

**To run it:**

```bash
docker compose run --rm m3
```

It needs `ANTHROPIC_API_KEY` in the shell or in `.env`.
