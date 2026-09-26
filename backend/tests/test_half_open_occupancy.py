"""半开占炉测例：只编排场景并调用夹具（oven_fixtures）与断言（oven_assertions）。

是否重叠、点名哪两个阶段、窗口起点在哪里，一律由断言模块给出，
测例本身不写任何重叠判定，也不出现期望布尔值。
"""

from .oven_assertions import (
    assert_bake_runs_into_ferment,
    assert_next_window_starts_at_bake_end,
    assert_no_cross_batch_overlap,
    assert_no_overlap_between,
    assert_wrapping_reported_once,
)
from .oven_fixtures import (
    bake_wrapping_ferment,
    overlapping_batches_early,
    touching_batches,
)


def test_bake_end_touching_next_ferment_start_is_not_conflict():
    # 前一批烘烤结束 == 后一批发酵开始：半开端点相接，不重叠。
    sched = touching_batches(boundary_minute=70)
    assert_no_cross_batch_overlap(sched)


def test_next_batch_one_minute_early_conflicts_bake_against_ferment():
    # 后一批早一分钟：重叠，且必须点名烘烤段对发酵段，阶段名不能对调。
    sched = overlapping_batches_early(first_bake_end=70, early_by=1)
    assert_bake_runs_into_ferment(sched)


def test_same_batch_ferment_end_touching_own_bake_start_is_not_conflict():
    # 同一批自己的发酵结束 == 烘烤开始：首尾相接，不得判成冲突。
    sched = touching_batches(boundary_minute=70)
    assert_no_overlap_between(sched.name, sched.first_ferment, sched.first_bake)


def test_free_window_may_start_exactly_at_previous_bake_end():
    # 窗口可以刚好从上一批烘烤结束的端点起跳。
    sched = touching_batches(boundary_minute=70)
    assert_next_window_starts_at_bake_end(sched, duration=30)


def test_fully_wrapped_interval_reports_single_pair_with_outer_bounds_kept():
    # 一段完全包住另一段：只报一对重叠，外层烘烤段起止仍保留。
    sched = bake_wrapping_ferment()
    assert_wrapping_reported_once(sched)
