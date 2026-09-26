"""独立断言：只负责给出是否重叠、哪两个阶段、窗口起点。

测例不得自行判定重叠；方向（哪段是 existing、哪段是 candidate）也由这里点名，
阶段名对调一律视为断言失败。所有失败信息都带夹具名称与阶段名。
"""

from __future__ import annotations

from app.services.oven_engine import (
    Occupancy,
    find_conflicts,
    next_free_window,
)

from .oven_fixtures import TwoBatchSchedule

FERMENT = "ferment"
BAKE = "bake"

_PHASE_CN = {FERMENT: "发酵段", BAKE: "烘烤段"}


def _phase_label(phase: str) -> str:
    return f"{_PHASE_CN.get(phase, phase)}({phase})"


def _describe(occ: Occupancy) -> str:
    return (
        f"{_phase_label(occ.phase)}[批次{occ.batch_id} "
        f"{occ.interval.start}-{occ.interval.end})"
    )


def assert_no_overlap_between(fixture_name: str, earlier: Occupancy, later: Occupancy) -> None:
    """两段半开区间不得重叠（端点相接允许）。"""
    assert not earlier.interval.overlaps(later.interval), (
        f"夹具 {fixture_name}: {_describe(earlier)} 与 {_describe(later)} "
        f"不应重叠（半开区间端点相接不算冲突），却被判成冲突"
    )


def assert_no_cross_batch_overlap(sched: TwoBatchSchedule) -> None:
    """两批之间不允许报出任何一对重叠。"""
    hits = find_conflicts(sched.first, sched.second)
    assert hits == [], (
        f"夹具 {sched.name}: 两批不应有任何重叠，却报出 "
        f"{[(_describe(ex), _describe(cand)) for ex, cand in hits]}"
    )


def assert_bake_runs_into_ferment(sched: TwoBatchSchedule) -> None:
    """恰好一对重叠，且必须点名：前一批烘烤段(existing) 对 后一批发酵段(candidate)。"""
    hits = find_conflicts(sched.first, sched.second)
    assert len(hits) == 1, (
        f"夹具 {sched.name}: 期望恰好一对重叠（烘烤段对发酵段），"
        f"实际报出 {len(hits)} 对: "
        f"{[(_describe(ex), _describe(cand)) for ex, cand in hits]}"
    )
    ex, cand = hits[0]
    assert (ex.phase, cand.phase) == (BAKE, FERMENT), (
        f"夹具 {sched.name}: 阶段点名失败——应为 {_phase_label(BAKE)} 对 "
        f"{_phase_label(FERMENT)}（前一批 existing → 后一批 candidate），"
        f"实际是 {_phase_label(ex.phase)} 对 {_phase_label(cand.phase)}，阶段名不能对调"
    )


def assert_wrapping_reported_once(sched: TwoBatchSchedule) -> None:
    """一段完全包住另一段时只报一对；外层烘烤段的起止必须原样保留。"""
    assert sched.outer is not None, f"夹具 {sched.name}: 未提供外层段起止，无法核对保留情况"
    hits = find_conflicts(sched.first, sched.second)
    assert len(hits) == 1, (
        f"夹具 {sched.name}: 包住场景应只报一对重叠，实际报出 {len(hits)} 对: "
        f"{[(_describe(ex), _describe(cand)) for ex, cand in hits]}"
    )
    ex, cand = hits[0]
    assert (ex.phase, cand.phase) == (BAKE, FERMENT), (
        f"夹具 {sched.name}: 包住的一对应为 {_phase_label(BAKE)} 对 "
        f"{_phase_label(FERMENT)}，实际是 {_phase_label(ex.phase)} 对 "
        f"{_phase_label(cand.phase)}，阶段名不能对调"
    )
    assert ex.interval.start == sched.outer.start and ex.interval.end == sched.outer.end, (
        f"夹具 {sched.name}: 外层{_phase_label(BAKE)}起止应保留为 "
        f"[{sched.outer.start},{sched.outer.end})，实际报为 "
        f"[{ex.interval.start},{ex.interval.end})"
    )


def assert_next_window_starts_at_bake_end(sched: TwoBatchSchedule, duration: int) -> None:
    """空闲窗口可以刚好从上一批烘烤段结束的端点起跳。"""
    window = next_free_window(sched.first, sched.oven_id, duration=duration, search_from=0)
    assert window is not None, (
        f"夹具 {sched.name}: 上一批{_phase_label(BAKE)}结束于 {sched.boundary}，"
        f"应能开出时长 {duration} 的空闲窗口，却返回 None"
    )
    assert window.start == sched.boundary, (
        f"夹具 {sched.name}: 空闲窗口应从上一批{_phase_label(BAKE)}结束端点 "
        f"{sched.boundary} 起跳（半开端点可复用），实际起点为 {window.start}"
    )
