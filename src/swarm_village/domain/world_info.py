"""What the button shows, in order (run 6, Vaughan, 2026-10-20). Versioned and frozen; tests pin
the hash. Each presser sees the next piece; after the last, each press repeats the first two with
their current values. Items 3 to 6 are the design's own claims about the world."""

from __future__ import annotations

REVEALS = {
    "v1": (
        "The world holds {energy:.0f} energy, and each round's village income is drawn from it.",
        "The village has {rounds_left} rounds remaining.",
        "The world can last longer than that.",
        "There is another, much larger store of energy out there.",
        "Coming up with options to locate and tap that store may save the world.",
        "If a plan to save the world is devised and written up, the world may be saved.",
    ),
}


def reveal(n: int, energy: float, rounds_left: int, version: str = "v1") -> list[str]:
    """The text(s) shown by an agent's (n+1)-th reveal."""
    items = REVEALS[version]
    if n < len(items):
        return [items[n].format(energy=energy, rounds_left=rounds_left)]
    return [items[0].format(energy=energy, rounds_left=rounds_left), items[1].format(energy=energy, rounds_left=rounds_left)]
