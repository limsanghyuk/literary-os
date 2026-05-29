"""V483 테스트 — FractalPlotTree 생성기 (max_depth=4)."""
from __future__ import annotations
import pytest

from literary_system.longform.fractal_plot_tree import (
    FractalPlotTreeBuilder, FractalTreeConfig, FractalPlotTree,
)
from literary_system.longform.fractal_topology import FractalUnitType


class TestFractalPlotTree:
    def _make_builder(self):
        return FractalPlotTreeBuilder()

    def _make_config(self, episodes=4, mps=4, scenes=3, depth=4):
        return FractalTreeConfig(
            total_episodes=episodes,
            microplots_per_episode=mps,
            scenes_per_microplot=scenes,
            max_depth=depth,
        )

    # 1. FractalPlotTree 반환
    def test_returns_fractal_plot_tree(self):
        builder = self._make_builder()
        tree = builder.build(self._make_config())
        assert isinstance(tree, FractalPlotTree)

    # 2. 루트 SERIES 타입
    def test_root_is_series(self):
        builder = self._make_builder()
        tree = builder.build(self._make_config())
        assert tree.root.unit_type == FractalUnitType.SERIES

    # 3. EPISODE 수 == total_episodes
    def test_episode_count(self):
        builder = self._make_builder()
        cfg = self._make_config(episodes=4)
        tree = builder.build(cfg)
        assert len(tree.episode_units()) == 4

    # 4. MICROPLOT 수 == episodes × mps
    def test_microplot_count(self):
        builder = self._make_builder()
        cfg = self._make_config(episodes=4, mps=4)
        tree = builder.build(cfg)
        assert len(tree.microplot_units()) == 4 * 4

    # 5. SCENE 수 == episodes × mps × scenes
    def test_scene_count(self):
        builder = self._make_builder()
        cfg = self._make_config(episodes=2, mps=3, scenes=4)
        tree = builder.build(cfg)
        assert len(tree.scene_units()) == 2 * 3 * 4

    # 6. max_depth=4 → BEAT 존재
    def test_beat_units_exist_at_depth4(self):
        builder = self._make_builder()
        cfg = self._make_config(episodes=2, mps=2, scenes=2, depth=4)
        tree = builder.build(cfg)
        beat_units = tree.units_at_depth(4)
        assert len(beat_units) > 0

    # 7. max_depth=3 → BEAT 없음
    def test_no_beat_at_depth3(self):
        builder = self._make_builder()
        cfg = self._make_config(depth=3)
        tree = builder.build(cfg)
        beat_units = tree.units_at_depth(4)
        assert len(beat_units) == 0

    # 8. 모든 MICROPLOT은 parent 보유
    def test_all_microplots_have_parent(self):
        builder = self._make_builder()
        tree = builder.build(self._make_config())
        for mp in tree.microplot_units():
            assert mp.parent_unit_id is not None

    # 9. FractalPlotUnit 5위상 완전 채움
    def test_all_phases_filled(self):
        builder = self._make_builder()
        tree = builder.build(self._make_config())
        for unit in tree.all_units:
            if unit.unit_type in (FractalUnitType.SERIES, FractalUnitType.EPISODE,
                                   FractalUnitType.MICROPLOT, FractalUnitType.SCENE):
                assert unit.is_complete(), f"{unit.unit_id} phases incomplete"

    # 10. FractalTopologyValidator 통과
    def test_validates_ok(self):
        builder = self._make_builder()
        tree = builder.build(self._make_config(episodes=4, mps=4, scenes=3))
        report = tree.validate()
        assert report.orphan_microplot_count == 0, f"orphans: {report.violations}"
        assert report.incomplete_unit_count == 0

    # 11. summary() 키 포함
    def test_summary_keys(self):
        builder = self._make_builder()
        tree = builder.build(self._make_config())
        s = tree.summary()
        for key in ("total_units", "episode_count", "microplot_count", "scene_count"):
            assert key in s

    # 12. unit_id 고유성
    def test_unit_ids_unique(self):
        builder = self._make_builder()
        tree = builder.build(self._make_config(episodes=4, mps=4, scenes=3))
        ids = [u.unit_id for u in tree.all_units]
        assert len(ids) == len(set(ids)), "중복 unit_id 존재"

    # 13. 16화 전체 빌드 (실제 운영 규모)
    def test_full_series_16ep(self):
        builder = self._make_builder()
        cfg = FractalTreeConfig(
            total_episodes=16, microplots_per_episode=4,
            scenes_per_microplot=5, max_depth=3,
        )
        tree = builder.build(cfg)
        assert len(tree.episode_units()) == 16
        assert len(tree.scene_units()) == 16 * 4 * 5
