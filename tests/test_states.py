"""Unit tests for the verdict state machine - no API key, no network."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from zombicheck.states import decide_verdict, next_row_state  # noqa: E402


def test_fresh_push_is_alive():
    assert (
        decide_verdict(
            reachable=True,
            parked=False,
            archived=False,
            pushed_days_ago=10,
            redirected=False,
        )
        == "alive"
    )


def test_quiet_200_days_is_slowing():
    assert (
        decide_verdict(
            reachable=True,
            parked=False,
            archived=False,
            pushed_days_ago=200,
            redirected=False,
        )
        == "slowing_down"
    )


def test_dead_gt_year_is_zombie():
    assert (
        decide_verdict(
            reachable=True,
            parked=False,
            archived=False,
            pushed_days_ago=900,
            redirected=False,
        )
        == "zombie"
    )


def test_unreachable_or_parked_is_always_zombie():
    assert (
        decide_verdict(
            reachable=False,
            parked=False,
            archived=False,
            pushed_days_ago=None,
            redirected=False,
        )
        == "zombie"
    )
    assert (
        decide_verdict(
            reachable=True,
            parked=True,
            archived=False,
            pushed_days_ago=1,
            redirected=False,
        )
        == "zombie"
    )


def test_archived_and_stale_is_zombie_but_fresh_archived_is_not_dead():
    assert (
        decide_verdict(
            reachable=True,
            parked=False,
            archived=True,
            pushed_days_ago=800,
            redirected=False,
        )
        == "zombie"
    )
    # Archived but recently pushed: reachable + quiet signal -> slowing, not dead.
    assert (
        decide_verdict(
            reachable=True,
            parked=False,
            archived=True,
            pushed_days_ago=30,
            redirected=False,
        )
        == "alive"
    )


def test_unknown_freshness_is_slowing_not_alive():
    assert (
        decide_verdict(
            reachable=True,
            parked=False,
            archived=False,
            pushed_days_ago=None,
            redirected=False,
        )
        == "slowing_down"
    )


def test_redirected_and_fresh_is_alive():
    assert (
        decide_verdict(
            reachable=True,
            parked=False,
            archived=False,
            pushed_days_ago=5,
            redirected=True,
        )
        == "alive"
    )


def test_next_row_state():
    assert next_row_state(0) == "pending"
    assert next_row_state(3) == "done"
