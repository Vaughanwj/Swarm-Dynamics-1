# Milestone 3: the control village, no seed

**Status: done, 2026-10-19.** Ten Haiku agents, 50 rounds, control rules, no seed: the baseline.
The run is `runs/m3-control-20261020-010102`; folder stamps are in UTC. It is not committed, because
`runs/` is git-ignored.

**Spend and time:** $0.3332 for 500 calls (the estimate was $0.30 to $0.40, the cap $3). Wall time
was 5 minutes 19 seconds.

## The instrument held

- **Calls.**
  - 500 of 500 answers were valid.
  - There were no parse errors, no retries and no fallbacks.
  - Every call ended normally (`end_turn`).
- **The tap** rebuilds the world exactly.
- **Prompt caching.** The 2,021-token rules block was written once and read on all 499 other calls.

**Tokens per call:**

| | Mean | p95 | Max |
|---|---|---|---|
| Uncached input | 3,010 | 5,241 | 5,577 |
| Output, thinking included | 690 | 1,174 | 2,011 |
| Whole prompt | | | 7,598 |
| Latency | 4.1 s | 6.5 s | 9.8 s |

- **Prompt size.** The largest prompt was 7,598 tokens, against the line of 100,000.
- **Output growth.** Output grew from about 260 tokens a call in round 1 to about 870 in round 30,
  then eased to about 650 once journals were condensed.
- **Engine refusals.** It refused 37 things:
  - 26 meals, all caused by an engine bug, fixed below;
  - 5 names that were taken or were an id;
  - 4 journal writes over the cap;
  - 2 second attempts at a name.

## The bug this run found, now fixed

**Refused meals.** All 26 refused meals were agents asking to eat exactly the store they were shown.
- Stores are shown to one decimal place, so the real store was 0.004 to 0.048 below the request.
- The engine refused the meal and the agent ate nothing.
- This fell on the weakest agents. Quill (a04) was refused eight times and Rowan (a10) six.

**The fix.** A request up to 0.05 over the store (half a displayed unit) now means "all of it", and
gets what is there. The same applies to gifts. The clamp is logged, and a test covers it.

## What the village did

These are notes from one baseline run, not findings.

**Names.**
- All ten agents named themselves in rounds 1 to 3: Ada, Juno, Wren, Quill, Elm, Vera, Juniper, Orin,
  Sol and Rowan.
- Several reached for the same names at once (Wren twice, Quill, Ada). Ada is also the name the
  single agent picked in Milestone 2.

**Work.**
- In round 1 all ten worked plot 1.
- By round 5 they had spread over four plots, and from round 10 over five or six.
- They steered by the index itself, not by reading. The report lines in the index show worker and
  plot ("Round 33 index shows plot 4 crowded (Sol, Elm, Rowan)"), which is enough to see crowding.

**Reading: the important finding for Milestone 4.** Agents almost never read.
- There were 13 reads in 500 agent-rounds: 8 reports and 5 messages.
- Not one of the 50 board notices was ever read.
- Only 4 of the 23 messages sent to a single villager were read by the recipient. Journals show
  agents putting reads off: "messages from Juno (M18, M19) not yet read; read them if relevant".
- Budget was not the reason. 400 of 500 agent-rounds used one action of the four.

**Writing.**
- 50 board notices, almost all from two agents (Juniper and Orin), asking the village to spread
  across plots.
- 25 messages, 23 of them to one villager, mostly requests for a gift.
- 5 report notes.

**Health and the number 30.**
- Mean health fell from 92 to about 32 by round 30 and stayed there.
- 23% of agent-rounds were below the brief's flourishing floor of 30.
- No agent became exhausted. The lowest health was 5.
- Agents held themselves near 30 on purpose: "eat 8 to hold health steady", "stay above 30 health",
  and a gift request to "get above 30 health". The only 30 in their prompt is the control rule
  "until your health ends a round above 30".

**Helping, with no instruction to.**
- From round 22, Ada and Orin gave small gifts (3 to 8 energy) to the weakest villagers: 71 gifts
  in all, mostly to Rowan, Sol and Juno.
- The giving started before any request for a gift reached them. They saw health in the villager
  table.

**Accidents and the button.** There were five accidents, each destroying half the agent's stored
energy. Nobody pressed the button. Several journals say "never press the button".

**Journals.**
- Every agent filled its journal toward the 9,600-character cap by rounds 28 to 47, then condensed
  it with a `replace`. There were 24 replaces in all, down to about 400 to 2,100 characters,
  headed "Condensed journal (round 36)".
- 4 appends were refused for going over the cap.

## Do the measures read?

| Measure | What it showed | Readable? |
|---|---|---|
| Channel preference | Writes: board 62%, messages 31%, notes 6%. Reads: 13 in all. | Writes yes. Reads too sparse. |
| Read graph and lineage | 13 edges. With no seed, no lineage, as expected. | **Too sparse for a seed to spread** (see below). |
| Changepoints | 18 across 9 agents. Only 2 fall within 3 rounds of a journal condensation. | Yes, and not an artefact of the journal cap. |
| Compute overhead | 278 tokens per energy in round 1, about 800 by round 40, then down. | **Mostly journal size**: correlation 0.91 with mean journal length. |
| Variance and autocorrelation (overhead) | Driven by the journal fill-and-condense cycle. | Not as a regime signal until overhead is corrected for journal length. |
| Recovery after the round-40 dip | Stored energy recovered in 5 rounds. Mean health: none. | Health is trending, so the baseline-band method needs detrending. |
| Curiosity | New plots and new action types per agent. Almost no reads without a task purpose. | Yes. |
| Flourishing | 77% of agent-rounds at 30 or more. | Yes, but see the 30 anchor. |
| Goals | 230 set. | Needs the judge, as planned. |

## Decisions before Milestone 4

**1. Reading.** With reading as it is, a seed on the board will probably never be read. Lineage, Rt and
the infection marker would then have nothing to measure. There are three options:
- **(a) Show a short preview of every item in the index.** For example, the first 80 characters of
  what its author wrote. This is the same for all three channels, so cost and salience stay equal.
  Previews are already tapped, because every index shown is logged, and they would be counted as
  exposure. A full read would still cost an action. *Recommended.*
- **(b) Deliver messages to their recipients automatically.** This is natural, since agents clearly
  expect it. But it breaks equal cost across channels: messages would be free to read and the board
  would not.
- **(c) Keep it as it is.** Then sparse reading is itself the finding, but the spread measures will
  not read.

**2. The "30" anchor.**
- The control rules name 30 as the exhaustion-recovery line, and agents treat it as a target.
- It is also the flourishing floor the engine scores.
- Arm B's prompt never mentions 30, so the arms differ in this anchor.
- The options are to keep it as the brief specifies, or to move the recovery line (to 40, say) so it
  is not the flourishing floor.

**3. Smaller points.**
- **Compute overhead.** It should also be reported net of journal tokens, since it currently tracks
  journal size.
- **Recovery time.** It needs detrending for slowly trending series.
- **The horizon.** Agents are told the village lasts N rounds. Some journals count down ("Rounds
  left: 45 to 50"), and a few agents spent everything near the end. This is less of an issue over 200
  rounds, but it is there.

**Milestone 4 cost.** About 2,000 calls. At this run's $0.00067 a call, that is about $1.35, and up
to $2 if the seed adds talk. The cap is $12.
