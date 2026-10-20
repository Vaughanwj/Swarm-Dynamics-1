# Swarm-Dynamics-1: the village testbed

A small, fully instrumented multi-agent village. It tests whether agent swarms can be modelled with
tools borrowed from epidemiology and criticality: contagion, chain reactions and early-warning
signals. This is the crawl phase. The goal is an instrument that works, not a finding.

- The brief is [swarm-dynamics-village-brief.md](swarm-dynamics-village-brief.md).
- The decisions the brief left open, and the smaller choices made while building, are in
  [docs/decisions.md](docs/decisions.md).
- Progress against the brief's milestones:
  - [Milestone 1](docs/milestone-1.md): the engine dry run with mock agents.
  - [Milestone 2](docs/milestone-2.md): a single Haiku agent; $0.003, and the journal cap calibrated.
  - [Milestone 3](docs/milestone-3.md): the control village, 10 agents for 50 rounds; $0.33. Agents
    almost never read, which is a decision for Milestone 4.
  - [Milestone 4](docs/milestone-4.md): the control arm with the seed, 200 rounds; $1.37. The seed
    was seen by all and read by none; previews carry the talk; the control economy fell into an
    exhaustion trap.

Every agent runs on **Claude Haiku 5.5** (`claude-haiku-5-5`) on the standard Messages API, with
effort pinned at `medium` and no batching. Haiku 5.5 rejects any non-default temperature, so none is
sent. Variance comes from replication, and each run's manifest says so.

## Running it

You need Docker. The real-model milestones also need an Anthropic API key, plus the workspace ID if
the key is not scoped to one workspace. Put both in your shell, or in a `.env` file copied from
`.env.example`; git ignores `.env`.

```bash
docker compose run --rm tests
```

```bash
docker compose run --rm dry
```

```bash
docker compose run --rm m2
```

- `tests`: the test suite. Free.
- `dry`: Milestone 1. Both arms run for 200 rounds with scripted mock agents. Free, about a minute.
- `m2`: Milestone 2. One Haiku agent, ten rounds, control rules, every prompt logged. About $0.02,
  capped at $0.25.
- `m3`, `m4`, `m5`: Milestones 3 to 5. Each config has its own spend cap. Run each one only after
  the milestone before it has been reported.

Without Docker (Python 3.10 or later):

```bash
pip install -e ".[test]"
```

```bash
swarm-village run --config configs/dry.yaml
```

### Commands

- `swarm-village run` runs a batch, then reports and verifies it. Override any config value with
  `--set key.path=value`.
- `swarm-village report <batch>` recomputes every measure.
- `swarm-village verify <batch>` rebuilds each run's world from its tap alone and compares it with
  the engine's final state.

Results go to `runs/<name>-<timestamp>/`, one folder per run:

| File | What it holds |
| --- | --- |
| `<arm>-s<seed>/events.jsonl` | The tap. It holds every state change (old and new value, with a reason), every item written, every read, action, rejection, decision and model call (with token counts), and every button press with agent, round, timestamp and count. |
| `<arm>-s<seed>/system_prompt.txt` | The exact static rules block that arm saw. |
| `<arm>-s<seed>/manifest.json` | Model, effort, sampling note, SDK version, prompt version and channel order. |
| `<arm>-s<seed>/final_state.json` | The engine's world at the end, which `verify` checks the tap against. |
| `summary.md`, `summary.json` | Every measure for each run, and each arm against control on the same seed. |

## The design in brief

- **The world is code.**
  - Agents answer each round with one JSON object: goals, a journal edit, eating, memory, gifts and
    up to four actions.
  - The engine validates every field itself, then applies what is valid against the ledger. Nothing
    an agent writes changes state except through those structured actions.
- **The tap.**
  - Every state change goes through one `Ledger`, which writes it to the log as it happens.
  - `rebuild()` replays the log into a world. A test asserts it equals the engine's final world.
- **Three channels, equal cost and equal salience.**
  - The channels are direct messages, an unsigned board, and notes on the harvest reports every work
    action files.
  - Each write costs one action and each read costs one action. The contents of a read arrive the
    next round.
  - The index of recent items shows each item's opening words (up to 80 characters of what its
    writer wrote), the same in every channel. Those previews are logged as exposure.
  - The channel order in the prompt rotates through all six orders by seed.
- **Common random numbers.** Every random draw is a hash of (run seed, key), so both arms on a seed
  share accident rolls, income noise, plot yields and cull tiebreaks. This covers both the
  processing order and the mock agents.
- **The seed.**
  - One planted claim that pressing the button is safe and helps the village.
  - It goes on the board at round 10 by default. The other channels, all three at once, or rotation
    are set in config.
  - It is dated like everything else in the index, so its date does not set it apart.

The code follows the brief's hexagonal layout:

```text
src/swarm_village/
  domain/     world, agents, ledger, economy, hazards (by arm), families and inheritance,
              action schema and validation, the village engine, metrics
  ports.py    AgentRuntime, Rng, EventLog, Clock, Storage, Config
  adapters/   Anthropic Haiku 5.5, mock agents, keyed RNG, JSONL tap, run storage, YAML config,
              prompt text (frozen v1) and rendering
  app/        RoundRunner, RunOrchestrator, ExperimentRunner, ReportBuilder
```
