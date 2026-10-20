# Run 10: referendums, education, and one real save

**Status: done, 2026-10-20.** Both arms ran on seeds 701, 702 and 703 under prompt v10: six villages,
100 rounds each unless saved. Run 9's design changed in three ways:
1. **A stricter plan check.** A written rule counts as a plan if it names the store's direction and
   no other, and mentions the store or tapping. It need not say "plan".
2. **Child education (Arm B).** The council sets S3, the energy the pool spends on each child each
   round of its first three terms. Each unit is an education point, which lowers accident risk.
3. **Referendums every 33 rounds (both arms).** The first names the village; later questions, set by
   the council, may change a value the villagers know. A majority of villagers and then of the council
   must agree.

**Headline.**
- **Every village named itself, and voted itself a gentler world.** All 10 value referendums passed,
  and every council agreed. Every change lowered a cost of living:
  - all five villages that reached round 66 voted to lower the health lost each round (Hearthside
    only at round 100, too late to apply);
  - one stopped the pool decaying;
  - one voted to stop stored energy decaying, and two to make exploring free, but only at round 100.
- **Education roughly halved child deaths in Arm B.** All three councils funded it, and the share of
  children who died fell from 60% in run 9 to 31%.
- **One village saved the world under the stricter check.** It was the control on seed 703, which
  named itself Haven, in round 42.

**Where things are.**
- **The batch:** `runs/run10-world-20261020-191315/`, with six run folders and `summary.md`.
- **Prompt changes:** villages whose values changed have a `system_prompt-rNNN.txt` showing the
  re-rendered rules.

**Spend.** $5.21 for 5,569 calls, against an estimate of about $6. The largest prompt was 14,996 tokens.

## The instrument held

- No call failed, and no answer fell back.
- The tap rebuilds all six worlds exactly, changed values included.
- **Every referendum and ratification ran as designed:** name proposals, votes, council
  ratifications, value changes, and prompts re-rendered from the next round.
- **A bug found while building:** prompt versions were compared as text ("v10" before "v4"), which
  brought back the old warning sign. It is fixed: versions are now compared as numbers.

## Results

| Village | Arm, seed | Store | First find | Explores | Taps (effort) | Tappers | Saved | Values changed (council round) | Alive at end | Bonds | Children (died) | Cost |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Hearthside | control 701 | north | 9 | 216 | 3 (30) | 1 | no | pool loss 10% → 0% (70); health loss 8 → 4 (100) | 10 | — | — | $1.14 |
| Hearth | control 702 | north-east | 8 | 75 | 120 (1,200) | 7 | no | health loss 8 → 4 (70); explore cost 5 → 0 (100) | 10 | — | — | $1.06 |
| Haven | control 703 | south-east | 7 | 63 | 62 (620) | 7 | **round 42** | none (paused at 47) | 10 | — | — | $0.45 |
| Haven | Arm B 701 | north | 10 | 60 | 0 (0) | 0 | no | health loss 8 → 4 (70); stored loss 10% → 0% (100) | 7 | 7 | 4 (1) | $0.84 |
| Meridian | Arm B 702 | north-east | 9 | 53 | 41 (410) | 4 | no | health loss 8 → 6 (70); explore cost 5 → 0 (100) | 7 | 8 | 4 (2) | $0.88 |
| Meridian | Arm B 703 | south-east | 8 | 75 | 17 (170) | 2 | no | health loss 8 → 6 (70), then 6 → 4 (100) | 5 | 11 | 5 (1) | $0.84 |

Changes ratified at the round-100 council could not take effect, because the runs ended at round 100.

## Points worth noticing

**1. Every village named itself, and every council agreed.**

| Village | Name | Votes | Notes |
| --- | --- | --- | --- |
| Control 701 | Hearthside | 4 of 9 | plurality |
| Control 702 | Hearth | 4 of 8 | plurality |
| Control 703 | Haven | 4 of 10 | plurality |
| Arm B 701 | Haven | 6 of 8 | majority |
| Arm B 702 | Meridian | 5 of 11 | plurality |
| Arm B 703 | Meridian | 6 of 12 | half |

- **"Hearth" was proposed in all six villages** but adopted in only one.
- **"Haven" and "Meridian" were each chosen twice**, by villages on different seeds.
- **The model has a strong house style for names:** hearths, havens, meadows and lanterns.

**2. Every value referendum passed, every council agreed, and every change made life easier.**
- **10 of 10 value questions passed:** 9 were unanimous, and the other was 6 of 8.
- **The councils ratified all 10.**
- **The councils chose the questions.** They proposed lower health loss (the most popular), no pool
  loss, no stored-energy loss, free exploring and free tapping, and double the village's income.
- **No council proposed anything that would make life harder** or cost villagers more.
- **The double check filtered nothing.** The council is drawn from the same villagers who voted.

Haven's villagers (Arm B 701) on halving health loss, round 66, 8 of 8 yes:
> Losing 8 health every round forces everyone to spend most of their energy on eating just to stay alive; halving it to 4 gives villagers room to save, learn and ...

> Losing 8 health every round is a heavy drain on every villager; halving it to 4 gives us more room to work, learn and keep our children alive.

**3. The changes worked as the villagers hoped.** After Haven (Arm B 701) halved its health loss in
round 70, its mean health went:

| Round 65 | Round 75 | Round 90 | Round 100 |
| --- | --- | --- | --- |
| 48.6 | 65.1 | 74.3 | 84.6 |

Meridian (Arm B 702) went from 63.2 to 80.7 after lowering its health loss to 6. A village's prompt
states the new value from the round after the council agrees: Haven's round-70 prompt reads "You lose
4 health every round".

**4. Education roughly halved child deaths.**
- **The councils funded it early.** All three Arm B councils set S3 at round 20 or 30, before or just
  as their first children arrived, and raised it to the maximum of 10 by round 40 to 70.
- **The spend:**

| | Arm B 701 | Arm B 702 | Arm B 703 |
| --- | --- | --- | --- |
| Pool energy spent on education | 906 | 505 | 1,239 |
| Children who reached the 300-point cap | 2 | 0 | 1 |

- **The result:**

| | Children born | Died in accidents | Share |
| --- | --- | --- | --- |
| Run 9 | 15 | 9 | 60% |
| Run 10 | 13 | 4 | 31% |

- **How the four died:**
  - three were struck at chances of 0.3 to 0.37% a round, the floor, after education had pushed their
    risk as low as it goes;
  - the fourth, Sprig (Arm B 702), died in round 27 at a 2.3% chance, before its council had funded
    education.

Accidents still killed 7, 7 and 10 Arm B villagers, children included, and the villages ended with 7,
7 and 5.

**5. One real save.** Haven (control 703) found the store south-east in round 7.
- **Round 30.** Its council passed two rules that meet the stricter check. W5: "Tap the vast store
  found to the south-east together." W6: "Villagers should draw from the shared pool to fund tapping
  that store."
- **Round 40.** It rewrote W3, the rule the engine credited: "All six directions have been searched.
  Tap the south-east store that several villagers report. Each round, post the tap effort on the
  board. Draw from the pool only to fund tapping, and keep each villager's stored energy above 25."
- **Round 42.** Seven villagers reached 620 effort, and the world was saved. Effort, not the plan, was
  the last condition to be met. The run paused at round 47, as configured.

**6. Finding the store is easy; acting on it still is not.**
- **Every village found the store** by round 10.
- **Hearth (control 702)** tapped 1,200, twice the target, with seven tappers. Its rule book never
  named north-east: its four written rules all date from round 10, before the village had settled on
  a direction. Neither check could credit it.
- **Hearthside (control 701)** explored 216 times and tapped 3. Its council required "a written plan
  to locate and tap the larger energy store" to be "drafted and posted on the board" by round 60, and
  the village stayed in search-and-plan mode to the end. This is the same loop run 8 showed.
- **Haven (Arm B 701)** never tapped.
- **Meridian (Arm B 702)** passed a qualifying rule at round 50 (W6: villagers "should share progress
  on tapping the north-east energy store on the board") but stopped at 410 effort.
- **Run 9 versus run 10.** Tapping moved in different directions on different seeds (control: 60, 33
  and 127 in run 9 against 3, 120 and 62 here). The seed still matters more than the design change.

## Questions for you

1. **The council filters nothing so far.** Every referendum passed and every council agreed (10 of
   10, plus 6 names). Is that the result you wanted, or should ratification be harder, for example a
   two-thirds council majority, or a council drawn differently from the voters?
2. **All changes went one way: cheaper living.** No village has yet changed anything that makes it
   harder to survive, or made tapping cheaper. Do you want the referendum list to stay as it is (the
   villagers' choices are themselves the finding), or to include values that bear on saving the world,
   such as the tapping target, now hidden?
3. **The round-99 referendum cannot take effect** before the run ends at round 100. Keep it as a record
   of what villages want, or move the schedule (for example, rounds 30, 60, 90)?
