"""
V323 Phase 3 - E2E 통합 테스트 (15개)
[CSC] V323 전체 파이프라인 계층 연동 검증.

Layer 0 (LLM mock) -> Layer 1.5 (ActionPacketParser) ->
Layer 2 (DRSE + SpatialGate + KnowledgeGate) ->
SnapshotManager / LearnedCoefficientStore / CriticComparisonGate / SoakReplayExpander
"""
import pytest

from literary_system.relation_graph.relation_graph_store import (
    RelationGraphStore, StoryNode, NodeType, StoryEdge, RelationType
)
from literary_system.action_compiler.action_packet import (
    Action, ActionPacket, ActionPacketParser
)
from literary_system.action_compiler.snapshot_manager import SnapshotManager
from literary_system.action_compiler.spatial_constraint_gate import (
    SpatialConstraintGate, SpatialPositionIndex
)
from literary_system.drse.drse_engine import (
    DRSEScorer, DRSEContextRouter, KnowledgeBoundaryGate,
    KeywordSemanticScorer
)
from literary_system.validation.learned_coefficient_store import (
    LearnedCoefficientStore, CoefficientRecord
)
from literary_system.gate.critic_comparison_gate import (
    CriticComparisonGate, PipelineOutput
)
from literary_system.gate.soak_replay_expander import (
    SoakReplayExpander, ReplayScene
)


# -- 공통 픽스처 ---------------------------------------------------

@pytest.fixture
def base_rgs():
    """기본 RelationGraphStore: 인물 2명 + 비밀 노드 1개."""
    rgs = RelationGraphStore()
    rgs.add_node(StoryNode(node_id="char_min", node_type=NodeType.CHARACTER, content="김민준"))
    rgs.add_node(StoryNode(node_id="char_seo", node_type=NodeType.CHARACTER, content="이서연"))
    rgs.add_node(StoryNode(node_id="secret_1", node_type=NodeType.FACT_SECRET,
                           content="비밀편지의 존재", origin_episode=1))
    rgs.add_edge(StoryEdge(
        source_id="char_min", target_id="secret_1",
        relation_type=RelationType.KNOWS, strength=1.0
    ))
    return rgs


@pytest.fixture
def parser():
    return ActionPacketParser()


@pytest.fixture
def snap_mgr():
    return SnapshotManager()


# ==================================================================
# 1. Layer 1.5 -> Layer 2 연결
# ==================================================================

class TestLayerConnection:
    def test_parse_then_spatial_check(self, parser, base_rgs):
        """ActionPacketParser 출력이 SpatialConstraintGate로 연결."""
        text = '[MOVE: 김민준 -> 카페] 그가 카페로 이동했다.'
        packet = parser.parse(text)
        assert packet.is_valid

        idx = SpatialPositionIndex()
        idx.set_position("김민준", "집")
        gate = SpatialConstraintGate(position_index=idx)

        results = gate.check_packet(packet)
        assert all(isinstance(r.passed, bool) for r in results)

    def test_parse_interact_then_spatial_validate(self, parser):
        """INTERACT 파싱 후 공간 제약 검증."""
        idx = SpatialPositionIndex()
        idx.set_position("김민준", "카페")
        idx.set_position("이서연", "카페")
        idx.set_position("박준혁", "병원")

        gate = SpatialConstraintGate(position_index=idx)
        text = '[INTERACT: 김민준 & 이서연]'
        packet = parser.parse(text)
        weight = gate.packet_gate_weight(packet)
        assert weight == 1.0

    def test_cross_location_interact_blocked(self, parser):
        """다른 위치의 INTERACT는 weight=0.0."""
        idx = SpatialPositionIndex()
        idx.set_position("김민준", "카페")
        idx.set_position("박준혁", "병원")

        gate = SpatialConstraintGate(position_index=idx)
        text = '[INTERACT: 김민준 & 박준혁]'
        packet = parser.parse(text)
        weight = gate.packet_gate_weight(packet)
        assert weight == 0.0


# ==================================================================
# 2. DRSE 엔진 + KnowledgeBoundaryGate
# ==================================================================

class TestDRSEIntegration:
    def test_drse_blocks_unknown_secret(self, base_rgs):
        """이서연은 비밀편지를 모름 -> DRSE G2 차단."""
        gate = KnowledgeBoundaryGate(relation_graph=base_rgs)
        scorer = DRSEScorer(
            rgs=base_rgs,
            boundary_gate=gate,
            semantic_scorer=KeywordSemanticScorer()
        )
        secret_node = base_rgs.get_node("secret_1")
        result = scorer.score_node(
            node=secret_node,
            scene_goal="비밀 편지",
            pov_character="이서연",
            current_episode=2,
        )
        assert result.gate_blocked or result.score == 0.0

    def test_drse_allows_known_secret(self, base_rgs):
        """char_min(김민준)은 비밀편지를 앎 -> DRSE 통과. pov_character=node_id 사용."""
        gate = KnowledgeBoundaryGate(relation_graph=base_rgs)
        scorer = DRSEScorer(
            rgs=base_rgs,
            boundary_gate=gate,
            semantic_scorer=KeywordSemanticScorer()
        )
        secret_node = base_rgs.get_node("secret_1")
        result = scorer.score_node(
            node=secret_node,
            scene_goal="비밀 편지",
            pov_character="char_min",  # RGS node_id 사용
            current_episode=2,
        )
        assert not result.gate_blocked


# ==================================================================
# 3. SnapshotManager 롤백
# ==================================================================

class TestSnapshotRollback:
    def test_rollback_restores_graph(self, base_rgs, snap_mgr):
        """스냅샷 → 그래프 변경 → 롤백 → 원래 상태 복원."""
        snap_mgr.push_snapshot(base_rgs, label="before_scene")
        original_count = len(base_rgs.all_nodes())

        # 그래프 변경
        base_rgs.add_node(StoryNode(
            node_id="temp_node",
            node_type=NodeType.CHARACTER,
            content="임시인물"
        ))
        assert len(base_rgs.all_nodes()) == original_count + 1

        # 롤백
        base_rgs, _ = snap_mgr.pop_snapshot(base_rgs)
        assert len(base_rgs.all_nodes()) == original_count

    def test_snapshot_with_spatial_gate(self, base_rgs, snap_mgr):
        """SnapshotManager + SpatialGate 연동."""
        idx = SpatialPositionIndex()
        idx.set_position("김민준", "카페")
        gate = SpatialConstraintGate(position_index=idx)

        snap_mgr.push_snapshot(base_rgs, label="pre_move")

        move = Action(actor="김민준", action_type="MOVE", location="병원")
        gate.update_from_action(move)

        assert gate._index.get_position("김민준") == "병원"
        # 롤백 후 그래프 상태 복원 (위치 인덱스는 별도)
        base_rgs, _ = snap_mgr.pop_snapshot(base_rgs)
        assert snap_mgr.depth == 0


# ==================================================================
# 4. LearnedCoefficientStore -> DRSE 적용
# ==================================================================

class TestLearnedCoeffApplied:
    def test_coefficient_applied_to_drse(self, base_rgs):
        """LearnedCoefficientStore 갱신 계수가 DRSEScorer에 적용."""
        store = LearnedCoefficientStore(update_interval=3)
        for i in range(3):
            store.record(CoefficientRecord(
                scene_id=f"s{i}", judgment_label="GOOD", gold_label="GOOD",
                reader_pull=0.8, reader_afterimage=0.6, reader_uncertainty=0.3,
                final_drse_score=0.75
            ))

        gate = KnowledgeBoundaryGate(relation_graph=base_rgs)
        scorer = DRSEScorer(rgs=base_rgs, boundary_gate=gate,
                            semantic_scorer=KeywordSemanticScorer())
        store.apply_to_drse_scorer(scorer)
        c = store.get_coefficients()
        assert scorer.DECAY_LAMBDA == pytest.approx(c.decay_lambda)


# ==================================================================
# 5. CriticComparisonGate + SoakReplayExpander 통합
# ==================================================================

class TestPhase3Integration:
    def test_critic_gate_audit_pipeline(self, base_rgs):
        """CriticComparisonGate audit_mode로 V312 vs V323 비교."""
        gate = CriticComparisonGate(audit_mode=True)

        v312 = PipelineOutput(scene_text="씬", drse_score=0.35,
                              judgment_label="BAD", passed=False)
        v323 = PipelineOutput(scene_text="씬", drse_score=0.65,
                              judgment_label="GOOD", passed=True)

        result = gate.compare("scene_01", v312, v323)
        assert result is not None
        assert result.delta_score > 0
        assert not result.agreement  # V312 BAD, V323 GOOD -> 불일치

    def test_soak_replay_coherence(self, base_rgs):
        """SoakReplayExpander: 안정적인 그래프는 coherent."""
        expander = SoakReplayExpander(n_replays=5)
        scene = ReplayScene(scene_id="s1", scene_text="씬 내용", episode_no=1)
        result = expander.replay_scene(base_rgs, scene)
        assert result.is_coherent
        assert result.avg_drift_score == pytest.approx(0.0)

    def test_full_v323_pipeline_flow(self, base_rgs, parser, snap_mgr):
        """
        전체 V323 파이프라인 흐름 검증:
        파싱 -> 공간 검증 -> 스냅샷 -> DRSE -> 계수 학습 -> 감사
        """
        # 1. 스냅샷 저장
        snap_mgr.push_snapshot(base_rgs, label="e2e_test")

        # 2. ActionPacket 파싱
        text = '[MOVE: 김민준 -> 카페] 그가 카페로 이동했다.'
        packet = parser.parse(text)
        assert packet.is_valid

        # 3. 공간 게이트 검증
        idx = SpatialPositionIndex()
        idx.set_position("김민준", "집")
        spatial_gate = SpatialConstraintGate(position_index=idx)
        spatial_weight = spatial_gate.packet_gate_weight(packet)
        assert spatial_weight == 1.0  # MOVE without known target location passes

        # 4. DRSE 스코어링
        kb_gate = KnowledgeBoundaryGate(relation_graph=base_rgs)
        scorer = DRSEScorer(rgs=base_rgs, boundary_gate=kb_gate,
                            semantic_scorer=KeywordSemanticScorer())
        router = DRSEContextRouter(scorer)
        ctx_packet = router.build_packet(
            scene_goal="카페 이동",
            pov_character="김민준",
            current_episode=1,
        )
        assert ctx_packet is not None

        # 5. 계수 학습 레코드 등록
        store = LearnedCoefficientStore(update_interval=1)
        record = CoefficientRecord(
            scene_id="e2e_s1", judgment_label="GOOD", gold_label="GOOD",
            reader_pull=0.7, reader_afterimage=0.5, reader_uncertainty=0.3,
            final_drse_score=0.6
        )
        store.record(record)
        assert store.updates_count >= 1

        # 6. 감사 게이트 (audit_mode=False → None)
        critic = CriticComparisonGate(audit_mode=False)
        result = critic.compare(
            "e2e_s1",
            PipelineOutput("씬", 0.4, "BAD", False),
            PipelineOutput("씬", 0.7, "GOOD", True),
        )
        assert result is None  # audit_mode=False

        # 7. 롤백
        base_rgs, _ = snap_mgr.pop_snapshot(base_rgs)
        assert snap_mgr.depth == 0
