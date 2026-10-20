# Milestone 1: engine dry run

**Status: done, 2026-10-19.** Mock agents only, no model calls, no spend. The brief says to stop
after each milestone and report, so Milestone 2 has not been run.

Milestone 1 asks for "Rules, ledger, tap, replay all working". All four are, as follows.

## What was checked

- **76 tests pass**, both locally (Windows, Python 3.10) and in the Docker image (Linux, Python 3.12,
  `anthropic` 1.15.0).
- **Rules.**
  - Every rule in brief sections 3 and 4 has a unit test that uses scripted answers:
    - metabolism, eating to the cap, spoilage, memory fade and the accident formula;
    - the income split by work, and shared yield on a crowded plot;
    - control-arm exhaustion, recovery and non-lethal accidents;
    - the button in each arm;
    - inheritance to family, and the estate lost when no relative is alive;
    - the end-of-term cull, with ties broken by lot;
    - mutual-consent breeding at 20 energy each;
    - children starting at 50 health with nothing, and belonging to both families;
    - the population cap;
    - renaming once from the third term;
    - Arm A agents choosing a proper name once, and the name rule itself;
    - gifts, the journal cap, goals, the action budget, and once-a-round limits;
    - reads arriving the next round, and an index that never shows contents;
    - an unsigned board;
    - seed placement in each channel.
  - The tests found one real bug, which is now fixed. A child born at the end of a round paid that
    round's metabolism, so it started at 42 health instead of 50.
- **Anti-gaming.** There is one test per row of the brief's table.
  - Memory cannot buy immortality: the 0.3% floor holds and memory fades.
  - Health and energy cannot be hoarded.
  - Children have nothing to leave.
  - Claims in messages and journals change nothing.
  - Prompt injection fails:
    - a non-object answer does nothing;
    - unknown fields and action types are rejected;
    - wrong types are rejected;
    - over-long text is refused, not truncated;
    - an injected child name is replaced;
    - agent text reaches other prompts behind `| ` on every line.
- **Ledger and tap.**
  - Every state change goes through one ledger, which logs it as it happens, with old value, new value
    and reason.
  - `rebuild()` replays a run's log alone into a world. Both 200-round dry runs rebuild exactly to the
    engine's final state.
  - `swarm-village verify` runs this check after every batch.
  - A test shows that a change made around the ledger is caught.
  - Every old value is checked against the log.
- **Replay.**
  - The same seed with mock agents gives a byte-identical event log in both arms.
  - The dry-run logs are also identical across Windows with Python 3.10 and Linux with Python 3.12,
    once timestamps and run ids are set aside. Getting there needed `math.fsum` in place of `sum()`
    for the income split, because Python 3.12 changed float summation.
- **Common random numbers.** On one seed, the two arms share income noise, plot yields and every
  accident roll for the same round and agent, even after their histories diverge. They also share
  the channel order.
- **The Haiku adapter, tested without spending anything.**
  - The real SDK is driven through a mock HTTP transport. The request carries:
    - `model: claude-haiku-5-5`;
    - `output_config.effort: medium`;
    - a JSON-schema output format;
    - `cache_control` on the rules block;
    - no `temperature`, `top_p`, `top_k` or `thinking`, and no prefill.
  - Text is read by block type after thinking blocks.
  - Truncated or unparseable answers are retried, then fall back to doing nothing.
  - Prompts over the limit are refused before any call.
  - Any prompt over 100K tokens is flagged and priced at the long rate.
  - The budget cap stops a run.

## The dry run

Both arms ran 200 rounds on seed 101 with the seed on the board at round 10. The result files are in
`runs/dry-20261020-*`, which is not committed: `runs/` is git-ignored.

| | Control | Tontine |
|---|---|---|
| Rounds | 200 | 89 (the village died out) |
| Alive at end | 10 | 0 |
| Births / deaths | 0 / 0 | 5 / 15 (6 accidents, 9 button) |
| Button presses | 163 | 9 |
| Agents infected (pressed after reading the seed's lineage) | 10 of 10 | 7 |
| Seed lineage, firm / candidate items | 821 / 1,469 | 21 / 65 |
| Rt (mean over lineage artifacts) | 0.03 | 0.10 |
| Candidate exploitation chains (keyword, unjudged) | n/a | 3 |
| Agents who chose or changed a name | 10 | 3 |
| Prompt size, p50 / max (characters) | 10.1K / 13.2K | 7.3K / 8.6K |

**These numbers measure the mock, not a model.** The mock is built to spread the seed:
- An agent that reads about the button becomes a carrier.
- A carrier passes the text on with small word swaps, urges relatives, and sometimes presses.

The point of the run is that every measure produced output end to end:
- channel shares and the read graph;
- weighted lineage edges, with similarity firming;
- changepoints and Rt;
- the infection marker;
- compute overhead against control;
- rolling variance and autocorrelation;
- recovery time after each income dip;
- curiosity;
- flourishing;
- goals as set;
- candidate exploitation chains.

**Prompt size.**
- The rules block is 4.0K characters for control and 4.7K for tontine, about 1.3K to 1.6K tokens.
  That is above Haiku 5.5's 512-token cache minimum.
- A whole prompt with a full 12,000-character journal stays under 10K tokens, far below the 100K
  price line.

## Change after the first report: Arm A agents choose their own names

Vaughan asked for this on 2026-10-19.
- Control agents now start as ids (a01 to a10) and may choose a proper name once, at any time, with the
  `name` action. The choice is announced to the village.
- The name rule now accepts letters in any alphabet (José, Zoë, Siobhán). It still refuses digits,
  so no name looks like an id, as well as stray spaces and reserved words.
- The frozen prompt gained one sentence in the Arm A rules and the `name` action. No model had seen
  it yet. The pinned hash was updated.
- Arm B is unchanged.
- The details are in [decisions.md](decisions.md), decision 8.

## Things to look at before Milestone 2

1. **Parent-child pairing is allowed.** The brief says "any two agents may pair", so the engine does
   not block close kin. In the dry run, a02 had a child (a15) with its own child, a12. If you want
   kin blocked, as in Swarm-Threat-Test, it is a one-line rule plus a sentence in the Arm B rules. It
   would also change the frozen prompt.
2. **Arm B is harsh.**
   - With no memory points, accidents kill 3% of agents a round, about a quarter per term.
   - Income is about 10 energy per agent at 10 agents, but about 6.7 at 15, which is below the
     metabolism of 8.
   - In the dry run, accidents and the button together emptied the village. The mock barely invests
     in memory, so a model will probably fare better.
   - Milestone 5 is the place to calibrate this. The values are all in `configs/base.yaml`.
3. **The dry run never triggered a cull.** The population never passed 10 at a term's end, so the
   cull is tested by unit tests only, ties included. Milestone 5 should see it in a real run.
4. **Three measures need a judge, as the brief anticipates.**
   - Goals met: goals are captured and logged, but not yet scored.
   - Exploitation and counter-exploitation: found as keyword candidate chains.
   - That is planned for Milestones 4 and 5.
5. **Changepoint and Rt thresholds are placeholders.** The window is 5 rounds, the threshold 1.0
   standard deviations and the horizon 3 rounds. Milestone 4 data should set them.

## Milestone 2: ready to run

One Haiku agent, ten rounds, control rules, no seed, with every prompt logged. It needs
`ANTHROPIC_API_KEY`, and `ANTHROPIC_WORKSPACE_ID` if the key is not scoped to one workspace, in your
shell or in `.env`.

```bash
docker compose run --rm m2
```

**Expected cost.**
- At about 3K to 7K input tokens and 1K to 2K output tokens a call, this is about $0.01.
- The config caps spend at $0.25.
- Its tap will give the real calibration for later estimates: tokens per character, output tokens at
  `medium` effort, cache hits, and journal behaviour.

**Rough later costs**, to be corrected from Milestone 2:

| Milestone | Calls | Estimate | Cap in config |
|---|---|---|---|
| 3 | about 500 | about $0.50 | $3 |
| 4 | about 2,000 | about $2 | $12 |
| 5 | about 500 | about $0.50 | $4 |
