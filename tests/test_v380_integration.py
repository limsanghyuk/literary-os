"""
V380 통합 테스트 — SeriesArcPlanner + EpisodeRevealBudget + CharacterKnowledgeProseBridge
세 모듈의 연동 시나리오 검증
"""
import pytest
from literary_system.arc import SeriesArcPlanner, ArcAct
from literary_system.ledgers import EpisodeRevealBudget, RevealPolicy, RevealBlockedError
from literary_system.world.knowledge_state_tracker import (
    KnowledgeStateTracker, KnowledgeStatus, InformationType,
)
from literary_system.world.character_knowledge_prose_bridge import (
    CharacterKnowledgeProseBridge, KnowledgeLeakageError,
)
from literary_system.prose.contract import ProseRenderContract
from literary_system.nkg.graph_store import NKGGraphStore


class TestSeriesArcWithRevealBudget:
    def test_arc_plan_drives_reveal_budget(self):
        """SeriesArcPlanner로 생성한 아크에서 EpisodeRevealBudget 자동 구성"""
        planner = SeriesArcPlanner(total_episodes=8)
        graph = planner.plan()
        # ep_01에 금지 사실 추가
        node = graph.get_node("ep_01")
        node.forbidden_reveals.append("fact_murderer")
        budget = EpisodeRevealBudget.from_arc_graph(graph)
        # ep_01 → BLOCK
        with pytest.raises(RevealBlockedError):
            budget.check("ep_01", "fact_murderer")
        # ep_05 → ALLOW (미설정)
        budget.check("ep_05", "fact_murderer")

    def test_reveal_budget_escalation_follows_act(self):
        """결 막 에피소드는 기 막보다 높은 reveal_budget을 가져야"""
        planner = SeriesArcPlanner(total_episodes=16)
        graph = planner.plan()
        gi_nodes = graph.nodes_by_act(ArcAct.GI)
        gyeol_nodes = graph.nodes_by_act(ArcAct.GYEOL)
        avg_gi   = sum(n.reveal_budget for n in gi_nodes) / len(gi_nodes)
        avg_gyeol= sum(n.reveal_budget for n in gyeol_nodes) / len(gyeol_nodes)
        assert avg_gyeol > avg_gi

    def test_arc_to_nkg_sync_episode_count(self):
        """CausalPlotGraph → NKGGraphStore 동기화 에피소드 수 확인"""
        from literary_system.nkg.schema import NKGNodeType
        planner = SeriesArcPlanner(total_episodes=8)
        graph = planner.plan()
        nkg = NKGGraphStore()
        graph.sync_to_nkg(nkg)
        ep_nodes = nkg.nodes_by_type(NKGNodeType.EPISODE)
        assert len(ep_nodes) == 8


class TestKnowledgeBridgeWithContract:
    def setup_method(self):
        self.tracker = KnowledgeStateTracker("integration_test")
        self.tracker.register_fact("fact_secret", InformationType.IDENTITY,
                                   "비밀", "진실", reader_knows=True)
        self.tracker.set_knowledge("주인공", "fact_secret",
                                   KnowledgeStatus.UNAWARE, 1)
        self.tracker.set_knowledge("악당", "fact_secret",
                                   KnowledgeStatus.KNOWS, 1)
        self.tracker.set_knowledge("독자", "fact_secret",
                                   KnowledgeStatus.READER_ONLY, 1)
        self.bridge = CharacterKnowledgeProseBridge(self.tracker)

    def test_contract_enriched_with_blocked_for_reader_only(self):
        contract = ProseRenderContract.default()
        enriched = self.bridge.enrich_contract(
            contract, "독자", ["fact_secret"]
        )
        kc = enriched.metadata["knowledge_constraints"]
        assert "fact_secret" in kc["blocked"]

    def test_contract_enriched_no_blocked_for_knowing_char(self):
        contract = ProseRenderContract.default()
        enriched = self.bridge.enrich_contract(
            contract, "악당", ["fact_secret"]
        )
        kc = enriched.metadata["knowledge_constraints"]
        assert "fact_secret" not in kc["blocked"]

    def test_asymmetry_pressure_reflects_drama_potential(self):
        # 악당(앎) vs 주인공(모름) → 높은 압력
        pressure = self.bridge.asymmetry_pressure(
            "악당", "주인공", ["fact_secret"]
        )
        assert pressure >= 0.8

    def test_reader_only_check_scene_blocks(self):
        violations = self.bridge.check_scene("독자", ["fact_secret"])
        assert "fact_secret" in violations

    def test_multi_char_no_leakage_assertion(self):
        self.bridge.assert_no_leakage(["주인공", "악당"], ["fact_secret"])

    def test_multi_char_with_reader_only_raises(self):
        with pytest.raises(KnowledgeLeakageError):
            self.bridge.assert_no_leakage(
                ["주인공", "독자", "악당"], ["fact_secret"]
            )


class TestFullPipelineIntegration:
    """
    전체 파이프라인: SeriesArcPlanner → EpisodeRevealBudget → Bridge → Contract
    """
    def test_full_pipeline(self):
        # 1. 16부작 아크 생성
        planner = SeriesArcPlanner(total_episodes=16, series_title="테스트극")
        graph = planner.plan()

        # 2. ep_01에 금지 사실 등록
        ep01 = graph.get_node("ep_01")
        ep01.forbidden_reveals.append("fact_villain_identity")

        # 3. RevealBudget 구성
        budget = EpisodeRevealBudget.from_arc_graph(graph)
        budget.set_policy("ep_14", "fact_villain_identity", RevealPolicy.ALLOW)

        # 4. 트래커 구성
        tracker = KnowledgeStateTracker("full_pipeline_test")
        tracker.register_fact("fact_villain_identity", InformationType.IDENTITY,
                               "악당 정체", "비서", reader_knows=True)
        tracker.set_knowledge("주인공", "fact_villain_identity",
                               KnowledgeStatus.UNAWARE, 1)
        tracker.set_knowledge("독자_관점", "fact_villain_identity",
                               KnowledgeStatus.READER_ONLY, 1)
        bridge = CharacterKnowledgeProseBridge(tracker)

        # 5. ep_01 렌더링: BLOCK → 예외
        with pytest.raises(RevealBlockedError):
            budget.check("ep_01", "fact_villain_identity")

        # 6. ep_14 렌더링: ALLOW → 통과
        budget.check("ep_14", "fact_villain_identity")

        # 7. 독자 관점 READER_ONLY → 차단
        with pytest.raises(KnowledgeLeakageError):
            bridge.check("독자_관점", "fact_villain_identity")

        # 8. 주인공(UNAWARE) → 통과
        bridge.check("주인공", "fact_villain_identity")

        # 9. 비대칭 압력 측정
        pressure = bridge.asymmetry_pressure(
            "독자_관점", "주인공", ["fact_villain_identity"]
        )
        assert pressure > 0.5

    def test_arc_tension_curve_coherent(self):
        """전반부보다 중반부 텐션이 높아야"""
        planner = SeriesArcPlanner(total_episodes=16)
        graph = planner.plan()
        nodes = graph.all_nodes()
        avg_first_quarter = sum(n.tension_level for n in nodes[:4]) / 4
        avg_mid_quarter   = sum(n.tension_level for n in nodes[8:12]) / 4
        assert avg_mid_quarter > avg_first_quarter

    def test_arc_edges_types_present(self):
        """16부작 아크에 CAUSAL + FORESHADOW + EMOTIONAL_ESCALATION 엣지 모두 존재"""
        from literary_system.arc.schema import ArcPlotEdgeType
        planner = SeriesArcPlanner(total_episodes=16)
        graph = planner.plan()
        edge_types = {e.edge_type for e in graph.all_edges()}
        assert ArcPlotEdgeType.CAUSAL in edge_types
        assert ArcPlotEdgeType.FORESHADOW in edge_types
        assert ArcPlotEdgeType.EMOTIONAL_ESCALATION in edge_types
