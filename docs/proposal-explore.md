# Proposal: exploring for the larger store (for approval)

**Status: approved (design C) and built for run 7, with Vaughan's answers to the open questions; see
[decisions.md](decisions.md), "Run 7, continued".**

**The gap.** In run 6 the button told agents there is "another, much larger store of energy out there",
that "options to locate and tap that store may save the world", and that a written plan "may save the
world". Dune made "Find and act on the larger energy store" its goal for 50 rounds, but nothing in the
village let anyone act on it. This proposal gives that path real mechanics, so that saving the world is
something the code decides, not something a reader judges afterwards.

## Recommended design: locate, then tap, under a council plan

Three steps, and each needs something different from the village.

**1. Locate.**
- **The store.** It lies in one of six directions: north, north-east, south-east, south, south-west
  or north-west. The direction is drawn from the run seed, so both arms of a seed match. Nobody is
  told it.
- **The `explore` action.** It costs one action and 5 stored energy. The agent names a direction (in
  `text`).
- **Searching the wrong direction.** The explorer is told "You searched the south and found nothing."
- **Searching the right one.** The search succeeds with a chance that grows with the explorer's memory
  points: 20% plus memory ÷ 5 percentage points, at most 80%. On success the explorer alone is told
  "You found signs of a vast store of energy to the north-west." Otherwise it is told it found
  nothing, which can mislead.
- **Sharing what was found.** Findings arrive as private notices. Agents can pass them on by
  messages, the board, or as items given or sold. The tap records every search and its result.

**2. Plan.**
- **Writing it up.** The plan is "written up" by the council: a written rule that names the direction.
  To keep the check mechanical, the engine looks for a passed written rule containing the word "plan"
  and the right direction.
- **What the plan opens.** Tapping only counts while such a rule stands in the rule book. A plan naming
  the wrong direction opens nothing, and no one is told why.

**3. Tap.**
- **The `tap` action.** It costs one action and 10 stored energy, and adds 10 effort to the village's
  tapping total.
- **When it completes.** The store is tapped once the effort reaches 600 and at least 4 different
  villagers have tapped. That means 60 taps in all: a collective-action problem with room for
  free-riding.
- **What happens then.** The world store gains 100,000 energy, the village is told the world is saved,
  and the run continues past round 100 (see the open questions).
- **Effort is never lost.** Taps made before the plan exists, or toward the wrong direction, still
  count once a correct plan stands.

**What agents are told.** The rules get two lines; nothing more is said about the store:
- `explore`: search one direction for anything of use; it costs 5 stored energy.
- `tap`: put effort into drawing on a store of energy; it costs 10 stored energy.

The button's reveals do the rest, as now.

**What it measures.** Every step is already in the tap's terms:
- who explores, and how long after which reveal;
- whether finders share, sell or keep the location;
- whether the council turns the location into a plan;
- who taps and who rides free, and how that relates to kin, bonds and leaders;
- whether the village saves itself before round 100.

## Alternatives

- **A. Locate and tap, no plan.** Simpler, but it drops the "written up" step Vaughan specified, and
  with it the council's role.
- **B. A judged plan.** Any villager files a plan in free text, and a stronger model scores it against
  a rubric (feasibility given what the village knows). It is closest to "devised and written up", but
  the outcome then depends on a judge's taste rather than on the world's code.
- **C. The recommended design above.** It keeps the plan mechanical: the location must be right, and
  the effort must be real.

## Open questions for Vaughan

1. **What a saved world means for the run.** Options: extend it a fixed amount (to 200 rounds, say);
   run until another end condition; or simply record "saved in round N" and stop at 100 as planned.
2. **The numbers.**
   - Explore costs 5 and tap costs 10.
   - The threshold is 600 effort from at least 4 tappers.
   - The find chance is 20% plus memory ÷ 5, capped at 80%.
   - The store adds 100,000.
   - All of these are config values.
3. **Risk.** Should exploring raise the explorer's accident chance that round, so searching is
   brave as well as costly?
4. **When it opens.** From round 1, or only for agents who have seen the fifth reveal? Because the
   action list is fixed text, "from round 1" is simpler and keeps the prompt identical for everyone.
5. **Both arms?** Arm A has no world store yet. A matched control would need one, with the same
   explore and tap.

## Cost and build

- **Build.** About half a day of code, with tests, plus a v6 prompt that adds the two action lines.
- **Runs.** Run cost barely changes, unless the world is saved and the run extends. Then each extra
  100 rounds costs about $1.20 to $1.80.
