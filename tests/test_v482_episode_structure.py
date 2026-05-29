"""V482 테스트 — EpisodeStructureCalculator + TreeNode 스키마."""
from __future__ import annotations
import pytest

from literary_system.episode.episode_structure_calculator import (
    EpisodeStructureCalculator,
    EpisodeStructureConfig,
    EpisodeStructure,
    SceneRole,
    ActSegment,
)
from literary_system.schemas.tree_node import (
    TreeNode, TreeNodeType, TreeNodeBuilder,
)


# ── EpisodeStructureCalculator 기본 ─────────────────────────────

class TestEpisodeStructureCalculator:

    def _make_calc(self):
        return EpisodeStructureCalculator()

    def _make_config(self, ep_idx=0, total=16, runtime=60.0, act="5act"):
        return EpisodeStructureConfig(
            episode_idx=ep_idx,
            total_episodes=total,
            runtime_min=runtime,
            act_structure=act,
        )

    # 1. 기본 반환 타입
    def test_returns_episode_structure(self):
        calc = self._make_calc()
        cfg = self._make_config()
        result = calc.calculate(cfg)
        assert isinstance(result, EpisodeStructure)

    # 2. 60분 제약 통과
    def test_pass_60min_constraint(self):
        calc = self._make_calc()
        cfg = self._make_config(runtime=60.0)
        result = calc.calculate(cfg)
        assert result.pass_60min_constraint, f"runtime={result.runtime_min}"

    # 3. 씬 목록 비어있지 않음
    def test_scenes_not_empty(self):
        calc = self._make_calc()
        result = calc.calculate(self._make_config())
        assert len(result.scenes) > 0

    # 4. 콜드 오픈 씬 존재
    def test_cold_open_scene_exists(self):
        calc = self._make_calc()
        result = calc.calculate(self._make_config())
        cold_scenes = [s for s in result.scenes if s.role == SceneRole.COLD_OPEN]
        assert len(cold_scenes) == 1

    # 5. 예고편 씬 존재
    def test_preview_scene_exists(self):
        calc = self._make_calc()
        result = calc.calculate(self._make_config())
        preview_scenes = [s for s in result.scenes if s.role == SceneRole.PREVIEW]
        assert len(preview_scenes) == 1

    # 6. 씬 인덱스 단조 증가
    def test_scene_idx_monotonic(self):
        calc = self._make_calc()
        result = calc.calculate(self._make_config())
        idxs = [s.scene_idx for s in result.scenes]
        assert idxs == sorted(idxs)

    # 7. 씬 타임라인 비겹침
    def test_scene_timeline_no_overlap(self):
        calc = self._make_calc()
        result = calc.calculate(self._make_config())
        scenes = sorted(result.scenes, key=lambda s: s.start_min)
        for i in range(len(scenes) - 1):
            assert scenes[i].end_min <= scenes[i+1].start_min + 0.01, \
                f"overlap: {scenes[i].end_min:.2f} > {scenes[i+1].start_min:.2f}"

    # 8. 씬 duration 양수
    def test_scene_duration_positive(self):
        calc = self._make_calc()
        result = calc.calculate(self._make_config())
        for s in result.scenes:
            assert s.duration_min > 0, f"scene {s.scene_idx} duration={s.duration_min}"

    # 9. microplot_count == plan.K
    def test_microplot_count_matches_plan(self):
        calc = self._make_calc()
        result = calc.calculate(self._make_config())
        assert result.microplot_count == result.plan.microplot_count

    # 10. 5막 act 목록 비어있지 않음
    def test_acts_not_empty_5act(self):
        calc = self._make_calc()
        result = calc.calculate(self._make_config(act="5act"))
        assert len(result.acts) > 0

    # 11. 3막 구조
    def test_3act_structure(self):
        calc = self._make_calc()
        cfg = self._make_config(act="3act")
        result = calc.calculate(cfg)
        assert result.pass_60min_constraint
        assert len(result.scenes) > 0

    # 12. 마지막 화 처리 (ep_idx = total-1)
    def test_final_episode(self):
        calc = self._make_calc()
        cfg = self._make_config(ep_idx=15, total=16)
        result = calc.calculate(cfg)
        assert result.episode_idx == 15
        assert result.pass_60min_constraint

    # 13. 다른 런타임 (45분)
    def test_45min_runtime(self):
        calc = self._make_calc()
        cfg = self._make_config(runtime=45.0)
        result = calc.calculate(cfg)
        assert result.total_scene_count > 0
        assert result.main_content_min > 0

    # 14. to_dict() JSON 직렬화
    def test_to_dict_serializable(self):
        calc = self._make_calc()
        result = calc.calculate(self._make_config())
        d = result.to_dict()
        assert "scenes" in d
        assert "acts" in d
        assert "microplot_count" in d
        assert isinstance(d["scenes"], list)

    # 15. reveal_budget_total 양수
    def test_reveal_budget_positive(self):
        calc = self._make_calc()
        result = calc.calculate(self._make_config())
        assert result.reveal_budget_total >= 0.0

    # 16. critical_scene_count 합리적 범위
    def test_critical_scene_count_reasonable(self):
        calc = self._make_calc()
        result = calc.calculate(self._make_config())
        # 최소 콜드오픈 1개
        assert result.critical_scene_count >= 1


# ── TreeNode 스키마 ─────────────────────────────────────────────

class TestTreeNode:

    # 17. TreeNode.new() 생성
    def test_tree_node_new(self):
        node = TreeNode.new(TreeNodeType.EPISODE, "EP01")
        assert node.node_type == TreeNodeType.EPISODE
        assert node.label == "EP01"
        assert len(node.node_id) > 0

    # 18. add_child / parent_id 자동 설정
    def test_add_child_sets_parent_id(self):
        parent = TreeNode.new(TreeNodeType.EPISODE, "EP01")
        child = TreeNode.new(TreeNodeType.MICROPLOT, "MP01")
        parent.add_child(child)
        assert child.parent_id == parent.node_id
        assert child in parent.children

    # 19. all_descendants BFS
    def test_all_descendants(self):
        root = TreeNode.new(TreeNodeType.SERIES, "ROOT")
        ep = TreeNode.new(TreeNodeType.EPISODE, "EP01")
        mp = TreeNode.new(TreeNodeType.MICROPLOT, "MP01")
        ep.add_child(mp)
        root.add_child(ep)
        descs = root.all_descendants()
        assert ep in descs
        assert mp in descs

    # 20. to_dict / from_dict 라운드트립
    def test_to_dict_from_dict_roundtrip(self):
        parent = TreeNode.new(TreeNodeType.EPISODE, "EP01", metadata={"x": 1})
        child = TreeNode.new(TreeNodeType.MICROPLOT, "MP01")
        parent.add_child(child)
        d = parent.to_dict()
        restored = TreeNode.from_dict(d)
        assert restored.label == "EP01"
        assert restored.metadata["x"] == 1
        assert len(restored.children) == 1
        assert restored.children[0].label == "MP01"

    # 21. from_scene_slot
    def test_from_scene_slot(self):
        calc = EpisodeStructureCalculator()
        result = calc.calculate(EpisodeStructureConfig())
        slot = result.scenes[0]
        node = TreeNode.from_scene_slot(slot)
        assert node.node_type == TreeNodeType.SCENE
        assert "scene_idx" in node.metadata
        assert node.metadata["scene_idx"] == slot.scene_idx

    # 22. find_by_type
    def test_find_by_type(self):
        root = TreeNode.new(TreeNodeType.SERIES, "S")
        ep1 = TreeNode.new(TreeNodeType.EPISODE, "E1")
        ep2 = TreeNode.new(TreeNodeType.EPISODE, "E2")
        root.add_child(ep1)
        root.add_child(ep2)
        eps = root.find_by_type(TreeNodeType.EPISODE)
        assert len(eps) == 2

    # 23. is_leaf
    def test_is_leaf(self):
        node = TreeNode.new(TreeNodeType.SCENE, "SC01")
        assert node.is_leaf
        child = TreeNode.new(TreeNodeType.BEAT, "BT01")
        node.add_child(child)
        assert not node.is_leaf

    # 24. depth()
    def test_depth(self):
        assert TreeNodeType.SERIES.depth == 0
        assert TreeNodeType.EPISODE.depth == 1
        assert TreeNodeType.MICROPLOT.depth == 2
        assert TreeNodeType.SCENE.depth == 3
        assert TreeNodeType.BEAT.depth == 4


# ── TreeNodeBuilder ─────────────────────────────────────────────

class TestTreeNodeBuilder:

    # 25. build_episode_tree 반환
    def test_build_episode_tree(self):
        calc = EpisodeStructureCalculator()
        structure = calc.calculate(EpisodeStructureConfig())
        builder = TreeNodeBuilder()
        ep_tree = builder.build_episode_tree(structure)
        assert ep_tree.node_type == TreeNodeType.EPISODE

    # 26. SCENE 노드 수 == 씬 수
    def test_scene_node_count_matches(self):
        calc = EpisodeStructureCalculator()
        structure = calc.calculate(EpisodeStructureConfig())
        builder = TreeNodeBuilder()
        ep_tree = builder.build_episode_tree(structure)
        scene_nodes = ep_tree.find_by_type(TreeNodeType.SCENE)
        assert len(scene_nodes) == structure.total_scene_count

    # 27. build_series_tree 2화
    def test_build_series_tree(self):
        calc = EpisodeStructureCalculator()
        s1 = calc.calculate(EpisodeStructureConfig(episode_idx=0))
        s2 = calc.calculate(EpisodeStructureConfig(episode_idx=1))
        builder = TreeNodeBuilder()
        series_tree = builder.build_series_tree([s1, s2])
        assert series_tree.node_type == TreeNodeType.SERIES
        ep_nodes = series_tree.find_by_type(TreeNodeType.EPISODE)
        assert len(ep_nodes) == 2
