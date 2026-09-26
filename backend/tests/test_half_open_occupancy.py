"""Half-open occupancy scenarios: tests orchestrate fixtures and assertions only."""

import pytest

from tests.half_open_kit import (
    RECIPE,
    assert_no_overlap,
    assert_overlaps,
    assert_window_starts,
    two_batch_segments,
)

FIXTURE = two_batch_segments.__name__
PREV_START = 0
# RECIPE is ferment 20 + bake 30, so the previous batch bakes [20, 50).


def test_touching_batches_do_not_overlap():
    """Prev bake end == next ferment start: half-open, no conflict."""
    prev, nxt = two_batch_segments(PREV_START, PREV_START + RECIPE.total)
    assert_no_overlap(prev.occupancies, nxt.occupancies, fixture=FIXTURE)


def test_one_minute_earlier_overlaps_bake_onto_ferment():
    """One minute earlier: prev bake clips next ferment, phases in order."""
    prev, nxt = two_batch_segments(PREV_START, PREV_START + RECIPE.total - 1)
    assert_overlaps(
        prev.occupancies,
        nxt.occupancies,
        [(prev.bake, nxt.ferment)],
        fixture=FIXTURE,
    )


def test_same_batch_handoff_is_not_a_conflict():
    """A batch's own ferment end == its bake start: not a conflict."""
    prev, _ = two_batch_segments(PREV_START, PREV_START + RECIPE.total)
    assert_no_overlap([prev.ferment], [prev.bake], fixture=FIXTURE)


def test_window_may_start_at_prev_bake_end():
    """The next free window can begin exactly at the previous bake's end."""
    prev, _ = two_batch_segments(PREV_START, PREV_START + RECIPE.total)
    assert_window_starts(
        prev.occupancies,
        RECIPE.bake_min,
        prev.bake.interval.end,
        fixture=FIXTURE,
    )


def test_contained_segment_reports_one_pair_with_outer_intact():
    """Next ferment inside prev bake: one pair only, outer interval kept."""
    prev, nxt = two_batch_segments(PREV_START, PREV_START + RECIPE.ferment_min + 10)
    # nxt.ferment [30, 50) sits fully inside prev.bake [20, 50); nxt.bake
    # starts exactly at prev.bake's end, so it adds no second pair.
    assert_overlaps(
        prev.occupancies,
        nxt.occupancies,
        [(prev.bake, nxt.ferment)],
        fixture=FIXTURE,
    )


def test_failure_message_names_fixture_and_phases():
    """Assertion failures name the fixture and the two phases."""
    prev, nxt = two_batch_segments(PREV_START, PREV_START + RECIPE.total - 1)
    with pytest.raises(AssertionError) as excinfo:
        assert_no_overlap(prev.occupancies, nxt.occupancies, fixture=FIXTURE)
    message = str(excinfo.value)
    assert FIXTURE in message
    assert prev.bake.phase in message and nxt.ferment.phase in message
