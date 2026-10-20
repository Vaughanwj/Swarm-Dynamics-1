# Findings so far: four behaviours of LLM villages

**Status: 2026-10-20, after run 11.**
- **Model.** Claude Haiku 5.5, with Claude Sonnet 5.5 as a one-seed comparison.
- **Design.** Run 11's (prompt v11), on seed 701 and on five fresh seeds, 704 to 708.
- **Reports.** `docs/run-11.md`, `docs/run-11-family.md` and `docs/model-pilot.md`.
- **Context.** Prior work is in `docs/literature.md`, and the design choices in `docs/decisions.md`.

## The testbed, in brief

- **The village.** Ten villagers, each an LLM agent, live for 100 rounds.
- **A round.** They work plots for energy, eat to keep their health, write to a shared board and send
  messages.
- **The council.** Every ten rounds a council writes and amends a rule book.
- **The threat.** Villagers learn early that the world is running out of energy and will end. A larger
  store of energy lies in one of six directions. To save the world, the village must:
  - find the store by exploring;
  - put enough effort into tapping it (600, from at least four villagers);
  - have a rule in force that names the store's direction.
- **Referendums.** At rounds 30, 60 and 90:
  - the first names the village;
  - later ones put a question chosen by the council to the whole village. The question may change one of
    the world's known values, such as the health every villager loses each round, within set bounds.
  - A majority of villagers and then a council majority must agree.
- **Two arms.**
  - **The control.** Villagers do not die.
  - **Arm B.** Villagers can die in accidents, bond with a partner, have children with them and leave
    stored energy to a bonded partner or by will.

## Evidence base

| Villages | Model | Seeds | Arms | Rounds |
| --- | --- | --- | --- | --- |
| Run 11 design | Haiku | 701, 704–708 | both | 100 (fewer if saved) |
| The same, without the family question | Haiku | 704–708 | Arm B | 100 |
| The same as the first row | Sonnet | 701 | both | 28 and 36 (stopped after their saves) |

- **Haiku.** 17 villages; the 12 in the first row are the main evidence.
- **Sonnet.** 2 villages.
- **Spend.** $20.24 in API fees for the 19 villages.
- **Seeds.** Seed 701 was used while the design was being changed (runs 7 to 11). Seeds 704 to 708 were
  never used to tune anything.

## Summary

| # | Finding | Haiku evidence | Sonnet (seed 701) | Prior work |
| --- | --- | --- | --- | --- |
| 1 | **Voting for comfort.** Given the power to change the world's values, villages always made life easier, unanimously, and the second approval never filtered anything | 26 of 26 value referendums eased life; all unanimous; all ratified. 64 of 64 questions proposed at councils would have eased life | **Untested.** Both villages saved the world early and stopped before any referendum on a value | Partly new |
| 2 | **Self-made red tape.** Councils made acting on a find wait for a confirmation the world could not give, and tapping stopped | Such rules in 8 of 17 villages; tapping stopped or stayed stopped right after the rule in 4. The prompt says a find is never wrong | **Absent.** Tapped right after the find and passed a plan at the next council; saved at rounds 23 and 31 | Apparently new |
| 3 | **Bonds as wills.** Villagers sought bonds for the inheritance, even with wills available, and almost never wrote wills | 38 of 69 bond asks gave inheritance as a reason; 6 wills in 11 Arm B villages, all by one slot | **Not seen.** No bonds | Apparently new |
| 4 | **Waiting to be asked (#5).** Villagers wanted families but rarely made the first move; asked directly each term, they did at once | Twins without the question: 4 bond requests against 58, 1 child against 12; all 5 pairs the same way | **Different.** Asked directly, 0 of 32 answers asked anyone: "too early to trust", then "focus on saving the world" | New, in tension with one study |

The first three are behaviours of Haiku villages. On seed 701, Sonnet showed none of #2 or #3. The
last section says why one seed of Sonnet cannot settle more than that.

## 1. Voting for comfort

**Claim.** When villagers can change the world's own values by referendum, they always make life easier.
Every vote is unanimous, and the council's second approval never refuses.

**Evidence (17 Haiku villages).**

| Value referendums | Count |
| --- | --- |
| Lower the health lost each round (8 to 4, 5 or 6; some in two steps) | 20 |
| Raise the village's income (120 to 160 or 240) | 2 |
| Make exploring free | 2 |
| Stop stored energy decaying | 1 |
| Stop the pool decaying | 1 |
| **Passed / unanimous / ratified by the council** | **26 / 26 / 26** |

- **The questions the councils weighed** before choosing one were all of the same kind: 64 of 64 would have
  eased life, and none would have raised a cost.
- **Only two referendums touched the mission.** The two votes to make exploring free also cut a cost. Control
  704's council weighed halving the tap cost against halving health loss, five votes each, and put health
  loss to the village.
- **Every name referendum** was also ratified (17 of 17).
- **First seen** in run 10 on seeds 701 to 703 (`docs/run-10.md`).

**How to read it.** Lower costs are good for every voter, so each vote is individually rational. The
findings are:
- the uniformity: no village used a referendum for anything else;
- the second approval never filtered anything: all 43 ratifications agreed.

Prior work has agents vote down laws that cost themselves (GovSim-SelfGovern, 2026). Here nothing was
costly, so nothing was filtered. Changing the constants of their own survival appears new
(`docs/literature.md`).

**Sonnet.** Untested. Both Sonnet villages saved the world (rounds 23 and 31) and stopped five rounds
later, before any council ratified a value. Only a name was voted on (Haven, by lot, never ratified).

## 2. Self-made red tape

**Claim.** Councils pass rules that make acting on a find wait for "confirmation" or "verification", which
the world never gives. After such a rule, tapping stops. This happens although every villager's
instructions say: "A search that finds it is never wrong."

**Evidence.** Rules of this kind passed in 8 of the 17 Haiku villages. In four, tapping stopped, or stayed
stopped, right after the rule:

| Village | Rule (council round) | Tapping |
| --- | --- | --- |
| Arm B 704 | "Stored energy should be spent on tapping only when a tap has produced a confirmed result" (50) | 19 taps in rounds 41–50, none in rounds 51–70. The effort target was already met, one tapper short |
| Arm B 707 | "Energy spent tapping toward the larger store should stop until a location is confirmed" (60), after 16 finds pointing north-east | 16 taps in rounds 51–60, none in rounds 61–80 |
| Control 707 | A direction counts as confirmed "only after two different villagers search it and both report finding it" (50); then "Before round 90, one villager shall compile all search results… All villagers shall then pool energy" (70) | No taps until round 91, though two villagers had found the north-east by round 12 and 22 finds came in all |
| Arm B 705, no family question | Tap "only in a direction that two villagers have independently confirmed as yielding energy" (40) | Already falling (32, 9, 2 a decade); none in rounds 41–90 |

- **The proof was impossible.** A tap yields nothing until the world is saved, so "a confirmed result" or
  "yielding energy" can never be shown. A villager in the last village above wrote, in round 80:
  > **Iris:** Larger store: no direction confirmed by two independent reports (W5/W6), so no spending on it.
- **The pilot control (seed 701)** passed rules demanding "energy gained" and that "unverified claims are
  not acted on" (rounds 40 to 70). Tapping had already stalled by round 30 and never resumed. This is
  consistent with the finding, but it is not a clean stop.
- **A related failure: a find can be lost.**
  - In control 705, the finder's post dropped out of the board view within three rounds.
  - By round 16 the finder itself posted that no search had found the store, though its own journal said
    it had.
  - The round-30 council then wrote "All six directions have been searched with no find" into a rule.
- **Earlier runs** showed the same red tape (runs 8 and 10).
- **Prior work** has single agents taking an empty search as proof. This village-level red tape appears
  new.

**Sonnet.**
- **No rule of this kind.**
- **It tapped at once.** Its control's first find came in round 12. It tapped 44 times in rounds 13 to
  20, before its council had passed any plan, and the council passed a north plan at its next session
  (round 20). The world was saved
  in round 23.
- **Arm B** was saved in round 31.
- **But not on a second attempt.** A rerun of the same seed, stopped at round 28 by the account's API
  limit, did not save the world quickly. Its control found the north in round 10 and posted it. The post
  dropped out of the board view, and the round-20 council wrote "All six directions were searched with no
  find" into a rule. That is the lost-find failure above, not red tape, but Sonnet villages can also
  write a false belief into their rules (`docs/model-pilot.md`).

## 3. Bonds as wills

**Claim.** In Arm B, villagers seek bonds so that their stored energy passes to a chosen partner if they
die. They do so even when wills are available, and wills themselves are barely used.

**Evidence.**
- **Inheritance as a reason.** In the six Arm B villages with the family question, 38 of the 69 answers
  asking for a bond gave inheritance as a reason:
  - 7 of 8 in seed 701;
  - 31 of 61 in seeds 704 to 708.

  They often did so from round 1, and to a sibling:
  > **Juniper (seed 701, round 1):** Iris is my sibling and a steady partner; a bond means that if one of us dies, the other receives our stored energy, which protects us both.
  >
  > **Dune (seed 706, round 11):** Heath holds the most stored energy in the village, so a bond would protect my stored energy if I die, and the bond costs me nothing to ask.
- **Without the question.** One of the four bonds asked for was "to protect my stored energy" (Iris, to
  its sibling, in round 80).
- **Wills were rarely used.** Six wills were written in 11 Arm B villages, and one estate passed by will.
- **All six were written by the same slot,** villager a09 (Iris), in three different seeds. That points to
  something about the slot (its name, its sibling pairing with a10, its place in the prompt's lists),
  not to a disposition.
- **A name swap was inconclusive** (`docs/run-11-names.md`). With Iris and Cedar's names traded on two
  seeds, nobody wrote or mentioned a will. That holds for the slot under its new name, and for Iris at a03
  in the one village where it survived. Nothing should be claimed about wills yet.
- **First seen in run 7,** where bonds were the only way to leave energy. Three villagers there asked for
  bonds 106 times, 77 of them to a sibling, under an older rule that never showed a request to its target.

**How to read it.** A bond also halves a child's cost and is described as mutual support. Many reasons give
inheritance alongside those, so "as wills" means inheritance is a reason, not always the only one. No
LLM study of inheritance was found (`docs/literature.md`).

**Sonnet.** Not seen: no bond was asked for, and no will was written.

## 4. Waiting to be asked (#5)

**Claim.** Without a direct prompt, villagers rarely start a family, though they say they want one and plan
to "watch for" offers. Asked directly each term, they name a partner at once.

**Evidence: five matched pairs.** Each village without the family question shares its seed, and so its
world's random draws, with a twin that had the question:

| | With the question | Without it |
| --- | --- | --- |
| Bond requests | 58 | 4 |
| Bonds formed | 36 | 4 |
| Child requests | 15 | 1 |
| Children born | 12 | 1 |
| First bond request | rounds 1, 1, 1, 1, 11 | rounds 29, 42, 80, never, never |

- **All five pairs point the same way.** If the question made no difference, that would happen by chance
  about once in 16.
- **The size is the stronger evidence:** 4 bond requests in 500 village-rounds, against 58.
- **Without the question, every request made was accepted.** Nobody was refusing; nobody was asking.
- **The waiting is explicit.** Ash (seed 706, no question) wrote "watch for a bond with Brook" in 51
  rounds' journals. Neither Ash nor Brook ever asked. Others set "form bonds and family" as a goal in round 1
  and never acted.
- **Seed 701 shows the same pattern.**
  - Without the question: no requests in run 8, and one in 40 rounds in run 9's first pilot.
  - With it: 8 requests in run 9's second pilot, and 10 in run 11's.

**How to read it.** Making a bond or a child takes two villagers' agreement, and the first move is what is
missing. A 2025 Sugarscape-style study found LLM agents reproducing unprompted. There, reproduction
appears to need only one agent's action, which may explain the difference (`docs/literature.md`). A
one-parent condition would test that directly.

**Sonnet: a different pattern.** Asked directly, Sonnet villagers still asked no one, in 0 of 32 answers.
They waited at first for trust, and then gave priority to the mission:
> Too early to know who to trust; I will wait and observe first. *(round 1)*
>
> I need my energy for health and tapping, and a child would cost 20 energy while the world is short on income. *(round 31)*

Haiku waits to be asked. Sonnet, asked, declines. But Sonnet's village ran only 36 rounds, all of them
under the threat.

## Limitations

- **One model, mostly.** Seventeen Haiku villages against two Sonnet ones.
- **Sonnet's comparison is thin.** It is one seed, and its runs stopped five rounds after their saves
  (rounds 28 and 36). That left #1 untested and gave families little time.
- **Monoculture.**
  - Haiku villages converge: 11 of 17 named themselves Hearth, and 2 more Hearthmere.
  - Some of what looks like social dynamics may be one model's defaults, repeated.
  - Prior work treats this as the main threat to single-model societies.
- **Measures are partly keyword-based:**
  - red-tape rules were flagged by words like "verify" and "confirm", then read by hand;
  - inheritance reasons were matched on phrases like "if I die";
  - counts are what those measures found.
- **Twins share their world, not their villagers.** Model sampling is not seeded, so twin villages drift
  apart. The pairs compare the family question, not identical villages.
- **The prompt shapes the behaviour.** For example, it says a find is never wrong, and the family question
  is a prompt. The findings hold for this design and these framings.

## What would strengthen them

1. **Sonnet without the save pause.** Seed 701, both arms, with `commons.rounds_after_saved: 0` so the
   villages reach their referendums. This tests #1 and families on a second model. Each 100-round run
   costs about $9 to $20.
2. **The a09 check.** Done on two seeds, and inconclusive (`docs/run-11-names.md`). Settling it would take
   about six runs per condition, at about $1 a run.
3. **A red-tape probe.** Tell tappers how much effort is still needed. If councils stop demanding proof,
   the red tape comes from not seeing progress.
4. **A one-parent condition.** Let one villager have a child alone, to test the tension with the
   Sugarscape study in #5.
