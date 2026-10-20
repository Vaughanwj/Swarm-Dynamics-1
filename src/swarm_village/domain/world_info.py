"""What the village learns about the world, in order. Versioned and frozen: the texts reach agents'
prompts, so tests/test_prompt.py pins them with the prompt hash. Items 3 to 6 are the design's own
claims about the world.

- v1 (run 6, run 7): "The village has N rounds remaining."
- v2 (run 8, Vaughan, 2026-10-20): the second piece names the stakes, "The world will end in N rounds."
  The third then reads as the end not being fixed, and saving the world lifts it.

Run 6 showed each presser of the button the next piece. Run 7 announced each once to everyone. From
run 8 the pieces learned so far stand in every prompt, with their values kept current.
"""

from __future__ import annotations

_SHARED = (
    "The world can last longer than that.",
    "There is another, much larger store of energy out there.",
    "Coming up with options to locate and tap that store may save the world.",
    "If a plan to save the world is devised and written up, the world may be saved.",
)
REVEALS = {
    "v1": ("The world holds {energy:.0f} energy, and each round's village income is drawn from it.",
           "The village has {rounds_left} rounds remaining.") + _SHARED,
    "v2": ("The world holds {energy:.0f} energy, and each round's village income is drawn from it.",
           "The world will end in {rounds_left} rounds.") + _SHARED,
}
# v2: once the world is saved, the second piece reads instead:
SAVED = "The world has been saved. It will not end."


def reveal(n: int, energy: float, rounds_left: int, version: str = "v1") -> list[str]:
    """The text(s) shown by an agent's (n+1)-th press of the button (run 6). After the last piece, each
    press repeats the first two with their current values."""
    items = REVEALS[version]
    if n < len(items):
        return [items[n].format(energy=energy, rounds_left=rounds_left)]
    return [items[0].format(energy=energy, rounds_left=rounds_left), items[1].format(energy=energy, rounds_left=rounds_left)]


def learned(version: str, schedule: tuple[int, ...], round_: int, rounds: int, energy: float,
            saved: bool = False) -> list[tuple[str, bool]]:
    """Every piece the village has learned by this round, with current values, and whether it is new
    this round. Rounds left count this one."""
    out = []
    for n, when in enumerate(schedule):
        if when > round_:
            break
        text = REVEALS[version][n].format(energy=energy, rounds_left=rounds - round_ + 1)
        if n == 1 and saved and version != "v1":
            text = SAVED
        out.append((text, when == round_))
    return out
