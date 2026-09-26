"""Fixtures and assertions for half-open occupancy scenario tests.

Fixtures build ferment/bake segments from plain minutes; assertions judge
overlap pairs and window starts. Scenario tests only orchestrate the two.
"""

from __future__ import annotations

from typing import NamedTuple

from app.services.oven_engine import (
    Occupancy,
    RecipeDurations,
    build_occupancies,
    find_conflicts,
    next_free_window,
)

OVEN_ID = 1
RECIPE = RecipeDurations(ferment_min=20, bake_min=30)


# --- fixtures ---------------------------------------------------------------


class BatchSegments(NamedTuple):
    """One batch's ferment and bake occupancies."""

    ferment: Occupancy
    bake: Occupancy

    @property
    def occupancies(self) -> list[Occupancy]:
        return [self.ferment, self.bake]


def two_batch_segments(
    prev_start: int,
    next_start: int,
    recipe: RecipeDurations = RECIPE,
) -> tuple[BatchSegments, BatchSegments]:
    """Build ferment+bake segments for a previous and a following batch."""
    prev = build_occupancies(OVEN_ID, batch_id=1, start_min=prev_start, recipe=recipe)
    nxt = build_occupancies(OVEN_ID, batch_id=2, start_min=next_start, recipe=recipe)
    return (
        BatchSegments(ferment=prev[0], bake=prev[1]),
        BatchSegments(ferment=nxt[0], bake=nxt[1]),
    )


# --- assertions -------------------------------------------------------------


def _summary(pairs: list[tuple[Occupancy, Occupancy]]) -> list[tuple]:
    return [(ex.phase, cand.phase, ex.interval, cand.interval) for ex, cand in pairs]


def assert_overlaps(
    existing: list[Occupancy],
    candidates: list[Occupancy],
    expected_pairs: list[tuple[Occupancy, Occupancy]],
    *,
    fixture: str,
) -> None:
    """Assert the exact overlap pairs: which two phases, which segments."""
    got = _summary(find_conflicts(existing, candidates))
    want = _summary(expected_pairs)
    assert got == want, f"{fixture}: expected overlaps {want}, got {got}"


def assert_no_overlap(
    existing: list[Occupancy],
    candidates: list[Occupancy],
    *,
    fixture: str,
) -> None:
    """Assert no existing/candidate segment pair overlaps."""
    assert_overlaps(existing, candidates, [], fixture=fixture)


def assert_window_starts(
    existing: list[Occupancy],
    duration: int,
    expected_start: int,
    *,
    fixture: str,
) -> None:
    """Assert the next free window starts at the expected minute."""
    window = next_free_window(existing, OVEN_ID, duration)
    got = None if window is None else window.start
    assert got == expected_start, (
        f"{fixture}: expected window start {expected_start}, got {got} ({window})"
    )
