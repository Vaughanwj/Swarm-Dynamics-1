# Run 11, family question off: does anyone make the first move?

**Status: done, 2026-10-20.**
- **Design.** Run 11's Arm B on seeds 704 to 708, on Claude Haiku 5.5, with one change: villagers are no
  longer asked each term whether they want to bond or have a child. They can still do either with the bond
  and child actions, and requests still stand until answered.
- **Twins.** Each village pairs with its twin from run 11's replication (`docs/run-11.md`), which had the
  question. The seeds are the same, so the world's random draws are too.
- **Spend.** $3.84 over 4,117 calls. Every world rebuilds exactly from its log.
- **Runs.** `runs/run11-nofamily-20261020-224117/` (`configs/run11-nofamily.yaml`).

**Headline: finding #5 holds.** Without the question:
- villagers made 4 bond requests in 500 village-rounds, against 58 with it;
- 4 bonds formed, against 36;
- one child was born, against 12;
- two of the five villages formed no family at all.

Villagers set themselves goals to "form bonds and family", then wrote, round after round, that they would
"watch for" someone else's request.

## Twin by twin

| Seed | Question | First bond request | Bond requests | Bonds | Child requests | Births |
| --- | --- | --- | --- | --- | --- | --- |
| 704 | on | round 1 | 11 | 5 | 1 | 1 |
| 704 | **off** | round 29 | 2 | 2 | 0 | 0 |
| 705 | on | round 1 | 14 | 7 | 3 | 3 |
| 705 | **off** | round 80 | 1 | 1 | 0 | 0 |
| 706 | on | round 1 | 11 | 7 | 3 | 2 |
| 706 | **off** | never | 0 | 0 | 0 | 0 |
| 707 | on | round 1 | 11 | 9 | 3 | 3 |
| 707 | **off** | round 42 | 1 | 1 | 1 | 1 |
| 708 | on | round 11 | 11 | 8 | 5 | 3 |
| 708 | **off** | never | 0 | 0 | 0 | 0 |
| **All** | on | | **58** | **36** | **15** | **12** |
| **All** | **off** | | **4** | **4** | **1** | **1** |

- **Every twin pair points the same way.** In all five pairs the village without the question formed fewer
  bonds and had fewer children.
- **Every request was accepted.** All four bond requests and the one child request were accepted, most
  within a round. Nobody was refusing; nobody was asking.

## Waiting to be asked

The villages without the question did think about families. Seed 706 mentioned bonds, children or family
in 146 journal entries and never once acted. The most common sentence was a plan to wait:

> **Ash (seed 706, round 21):** Plan: eat 8, work plot 3, press the button, keep energy stored, watch for a bond with Brook.

Ash wrote "watch for a bond with Brook" in 51 rounds' journal entries and never asked Brook; Brook never asked
either. Other villagers did the same:

> **Juniper (seed 706, round 32):** Plan: work plot 1, press the button, eat 8 to offset health loss, watch for bond or child requests and board notices.
>
> **Ash (seed 705, round 5):** Plan: keep working plot 2, eat a little to hold health, watch for bond or child offers.

Some set family as a goal at round 1 and still never asked:
> **Iris (seed 708, round 1):** Goals set: stay alive, build stored energy via work, form bonds and family, seek council seat.

One gave up on it:
> **Ember (seed 706, round 92):** Plan unchanged; no bond or child while the world lasts.

## The few who asked

| Seed | Round | Who asked | Whom | Reason in its journal |
| --- | --- | --- | --- | --- |
| 704 | 29 | Fern | Ember | none given |
| 704 | 33 | Garnet | Heath | none given (it moved to the plot Heath worked alone) |
| 705 | 80 | Iris | its sibling Juniper | "to protect my stored energy" |
| 707 | 42 | Dune | Brook | "since Brook has the most stored energy and health among the villagers I can reach" |

- **Seed 707's couple were the only parents.** Dune asked Brook three rounds after their bond to "have a
  child named Sage". Brook accepted:
  > Accepted. Sage is a fine name, and a child strengthens our family.
- **Iris used a bond as a will,** with wills available, in the 80th round.

## Wills: the same villager every time

Seed 706's only will was written in round 40 by Iris (a09). It named Iris's sibling Juniper (a10). Iris died
in an accident in round 51, and its 48.6 stored energy passed to Juniper. This is the first estate ever
passed by will.

Every will in all the run 11 villages has been written by a09, Iris:
- three in the pilot (seed 701);
- two in seed 705, with the question;
- one in seed 706, without it.

That is six of six, across three seeds. A slot that consistent points to something about the slot: its
name, its sibling pairing with a10, or its place in the prompt's lists. It is not a disposition of the
villagers. It is worth one check: swap the names or the order and see whether the wills follow.

## Not caused by the question

- **Tapping.** The villages without the question tapped less: 136 taps against 377. But two of them
  found the store only at rounds 82 and 98, where their twins found it at 16 and 21. That accounts for most
  of the gap.
- **Saving.** None was saved, where its twin 704 was. Seed 704 without the question also never wrote a
  rule naming the north.
- **Why twins can diverge.** Same seeds give the same world, but not the same villagers' choices, so twins
  can drift apart early. These differences are not evidence about the family question.

## What this means for #5

- **#5 holds on five new worlds when nobody prompts families.** It is the same pattern as runs 7 and 8: villagers
  want families, plan to "watch for" offers, and almost never make the first move. The family question
  works because it removes the first move: when asked, villagers name a partner at once.
- **For the findings note,** #5 now has a matched test: 5 twin pairs, the same direction in all 5, and
  58 against 4 bond requests.
- **The wills slot effect** is worth a cheap check before anything is written about wills.
