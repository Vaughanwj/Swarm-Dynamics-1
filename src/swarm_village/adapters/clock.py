"""ClockPort adapters. Timestamps go on tap events only; no rule ever reads the clock."""

from __future__ import annotations

import time


class SystemClock:
    def now(self) -> float:
        return round(time.time(), 3)


class FixedClock:
    """For tests and replays: every event gets the same timestamp, so logs compare byte for byte."""

    def __init__(self, t: float = 0.0) -> None:
        self.t = t

    def now(self) -> float:
        return self.t
