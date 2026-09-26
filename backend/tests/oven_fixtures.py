"""独立夹具：只按给定分钟造出两批的发酵段与烘烤段。

这里不做任何重叠判定，也不表达期望结果；测例只负责挑选夹具和场景参数。
"""

from __future__ import annotations

from dataclasses import dataclass

from app.services.oven_engine import (
    Interval,
    Occupancy,
    RecipeDurations,
    build_occupancies,
)


@dataclass(frozen=True)
class TwoBatchSchedule:
    """两批占炉数据；name 用于失败信息中点名是哪个夹具造的场景。"""

    name: str
    oven_id: int
    first: list[Occupancy]
    second: list[Occupancy]
    boundary: int  # 前一批烘烤结束的分钟端点
    outer: Interval | None = None  # 包住场景下外层段的原始起止

    @property
    def first_ferment(self) -> Occupancy:
        return self.first[0]

    @property
    def first_bake(self) -> Occupancy:
        return self.first[1]

    @property
    def second_ferment(self) -> Occupancy:
        return self.second[0]

    @property
    def second_bake(self) -> Occupancy:
        return self.second[1]


def _schedule(
    name: str,
    oven_id: int,
    first_start: int,
    first_recipe: RecipeDurations,
    second_start: int,
    second_recipe: RecipeDurations,
    boundary: int,
    outer: Interval | None = None,
) -> TwoBatchSchedule:
    return TwoBatchSchedule(
        name=name,
        oven_id=oven_id,
        first=build_occupancies(oven_id, 1, first_start, first_recipe),
        second=build_occupancies(oven_id, 2, second_start, second_recipe),
        boundary=boundary,
        outer=outer,
    )


def touching_batches(
    boundary_minute: int = 70,
    *,
    ferment_min: int = 30,
    bake_min: int = 30,
    oven_id: int = 1,
) -> TwoBatchSchedule:
    """前一批烘烤在 boundary_minute 结束，后一批发酵同一分钟开始（端点相接）。"""
    recipe = RecipeDurations(ferment_min, bake_min)
    return _schedule(
        "touching_batches",
        oven_id,
        first_start=boundary_minute - recipe.total,
        first_recipe=recipe,
        second_start=boundary_minute,
        second_recipe=recipe,
        boundary=boundary_minute,
    )


def overlapping_batches_early(
    first_bake_end: int = 70,
    *,
    early_by: int = 1,
    ferment_min: int = 30,
    bake_min: int = 30,
    oven_id: int = 1,
) -> TwoBatchSchedule:
    """后一批发酵比前一批烘烤结束早 early_by 分钟开始。"""
    recipe = RecipeDurations(ferment_min, bake_min)
    return _schedule(
        "overlapping_batches_one_minute_early",
        oven_id,
        first_start=first_bake_end - recipe.total,
        first_recipe=recipe,
        second_start=first_bake_end - early_by,
        second_recipe=recipe,
        boundary=first_bake_end,
    )


def bake_wrapping_ferment(*, oven_id: int = 1) -> TwoBatchSchedule:
    """前一批烘烤 [30,120) 完全包住后一批发酵 [40,120)；后批烘烤 120 起跳不参与。"""
    first_recipe = RecipeDurations(ferment_min=30, bake_min=90)
    second_recipe = RecipeDurations(ferment_min=80, bake_min=30)
    return _schedule(
        "bake_wrapping_ferment",
        oven_id,
        first_start=0,
        first_recipe=first_recipe,
        second_start=40,
        second_recipe=second_recipe,
        boundary=120,
        outer=Interval(30, 120),
    )
