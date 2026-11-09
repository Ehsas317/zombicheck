"""Explicit state machines for ZombieCheck (single source of truth).

    Verdict ........ alive | slowing_down | zombie  (fold from 4 live signals)
    Signal set ..... reachable / redirect / parked / freshness / search corroboration
    Row lifecycle .. pending / done   (checkpoint.resume: grants skip done rows)

All public shapes (CSV columns, exit codes, CLI flags) are unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Verdict = Literal["alive", "slowing_down", "zombie"]
VERDICTS = ("alive", "slowing_down", "zombie")

# Freshness thresholds looked at together with the signal pack (days since push).
FRESH_DAYS_ALIVE = 90
FRESH_DAYS_SLOWING = 365


def decide_verdict(
    *,
    reachable: bool,
    parked: bool,
    archived: bool,
    pushed_days_ago: int | None,
    redirected: bool,
) -> str:
    """One verdict from the signal pack. Priority: dead > quiet > fresh."""
    if not reachable or parked:
        return "zombie"
    if archived and (pushed_days_ago is None or pushed_days_ago > FRESH_DAYS_SLOWING):
        return "zombie"
    if pushed_days_ago is None:
        return "slowing_down"
    if pushed_days_ago <= FRESH_DAYS_ALIVE:
        return "alive"
    if pushed_days_ago <= FRESH_DAYS_SLOWING:
        return "slowing_down"
    return "zombie"


@dataclass(frozen=True)
class Signals:
    reachable: bool
    redirected: bool
    parked: bool
    archived: bool
    pushed_days_ago: int | None
    search_hits: int


RowState = Literal["pending", "done"]


def next_row_state(done_count: int) -> str:
    """Checkpoint fold: rows < done_count are done; the first data row is pending."""
    return "done" if done_count > 0 else "pending"
