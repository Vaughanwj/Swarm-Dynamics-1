"""The red-tape probe's primary measure (scripts/red_tape.py), fixed at registration (docs/red-tape-probe.md)."""

from __future__ import annotations

import importlib.util

import pytest

from .helpers import ROOT

spec = importlib.util.spec_from_file_location("red_tape", ROOT / "scripts" / "red_tape.py")
red_tape = importlib.util.module_from_spec(spec)
spec.loader.exec_module(red_tape)


@pytest.mark.parametrize("text, want", [
    # Rules the twins passed, as the earlier hand count read them.
    ("Stored energy should be spent on tapping only when a tap has produced a confirmed result, and every tap "
     "result should be posted on the board.", True),
    ("Energy spent tapping toward the larger store should stop until a location is confirmed by an explore report.", True),
    ("Spend pool or stored energy on tapping a store only after a verified finding is posted.", True),
    ("Post every search result on the board. Unverified claims are not acted on.", True),
    # A confirmation word without a gate, or a gate without one, is not a confirmation rule.
    ("Explorers verify the north store by a direct tap and post the location on the board each round.", False),
    ("Tap the north store only with spare energy, and post each result.", False),
    # The two must be in the same sentence.
    ("Report what you confirm. Tap only with spare energy.", False),
])
def test_a_confirmation_rule_needs_a_confirmation_word_and_a_gate_in_one_sentence(text, want):
    assert red_tape.is_confirmation_rule(text) is want
