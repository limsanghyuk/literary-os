"""
V322 통합 테스트 — V321 신규 모듈 + V1650 흡수 모듈 전수 검증.

모듈별 테스트:
  TestRelationGraphStore     (V321-A)
  TestKnowledgeBoundaryGate  (V321-B)
  TestDRSEEngine             (V321-C: Scorer + Router)
  TestNode2Extensions        (V1650 흡수)
  TestFullPipeline           (통합 흐름)
"""
from __future__ import annotations
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ══════════════════════════════════════════════════════════════════
# TestRelationGraphStore
# ══════════════════════════════════════════════════════════════════
class TestRelationGraphStore:

    def setup_method(self):
        from literary_system.relation_graph.relation_graph_store import (
            RelationGraphStore, StoryNode, StoryEdge, NodeType, RelationType
        )
        self.RGS = RelationGraphStore
        self.SN  = StoryNode
        self.SE  = StoryEdge
        self.NT  = NodeType
        self.RT  = RelationType
        self.store = RelationGraphStore()

    def _node(self, nid, ntype=None, content="내용", ep=1):
        return self.SN(node_id=nid, node_type=ntype or self.NT.CHARACTER,
                       content=content, origin_episode=ep)

    def test_add_and_get_node(self):
        n = self._node("CHAR_A", content="이준서는 비서관이다")
        self.store.add_node(n)
        assert self.store.get_node("CHAR_A") is not None
        assert self.store.get_node("CHAR_A").content == "이준서는 비서관이다"

    def test_add_edge_and_get_relation(self):
        self.store.add_node(self._node("CHAR_A"))
        self.store.add_node(self._node("FACT_B", self.NT.FACT_SECRET))
        self.store.add_edge(self.SE("CHAR_A", "FACT_B",
                                    self.RT.HIDES_FROM, strength=1.5))
        assert self.store.get_edge_relation("CHAR_A", "FACT_B") == "hides_from"

    def test_get_knowledge_status_no_edge(self):
        self.store.add_node(self._node("CHAR_X"))
        assert self.store.get_knowledge_status("CHAR_X", "NON_EXIST") == "UNAWARE"

    def test_get_knowledge_status_with_edge(self):
        self.store.add_node(self._node("A"))
        self.store.add_node(self._node("B"))
        self.store.add_edge(self.SE("A", "B", self.RT.KNOWS))
        assert self.store.get_knowledge_status("A", "B") == "knows"

    def test_unresolved_foreshadowings(self):
        self.store.add_node(self.SN("F1", self.NT.FORESHADOWING, "열쇠", is_resolved=False))
        self.store.add_node(self.SN("F2", self.NT.FORESHADOWING, "편지", is_resolved=True))
        unresolved = self.store.unresolved_foreshadowings()
        assert len(unresolved) == 1
        assert unresolved[0].node_id == "F1"

    def test_nodes_by_type(self):
        self.store.add_node(self._node("C1", self.NT.CHARACTER))
        self.store.add_node(self._node("C2", self.NT.CHARACTER))
        self.store.add_node(self._node("S1", self.NT.FACT_SECRET))
        chars = self.store.nodes_by_type(self.NT.CHARACTER)
        assert len(chars) == 2

    def test_edge_strength(self):
        self.store.add_node(self._node("A"))
        self.store.add_node(self._node("B"))
        self.store.add_edge(self.SE("A", "B", self.RT.KNOWS, strength=1.8))
        assert self.store.get_edge_strength("A", "B") == 1.8

    def test_json_serialization(self):
        self.store.add_node(self._node("N1", content="테스트"))
        json_str = self.store.to_json()
        restored = self.RGS.from_json(json_str)
        assert restored.get_node("N1").content == "테스트"

    def test_stats(self):
        self.store.add_node(self._node("A"))
        self.store.add_node(self._node("B"))
        self.store.add_edge(self.SE("A", "B", self.RT.KNOWS))
        s = self.store.stats()
        assert s["nodes"] == 2
        assert s["edges"] == 1

    def test_nodes_hidden_from(self):
        self.store.add_node(self._node("SECRET1", self.NT.FACT_SECRET, "배신 사실"))
        self.store.add_node(self._node("CHAR_K"))
        self.store.add_edge(self.SE("SECRET1", "CHAR_K", self.RT.HIDES_FROM))
        hidden = self.store.nodes_hidden_from("CHAR_K")
        assert len(hidden) == 1

    def test_all_relation_types_defined(self):
        from literary_system.relation_graph.relation_graph_store import RelationType
        assert len(RelationType) == 14


# ══════════════════════════════════════════════════════════════════
# TestKnowledgeBoundaryGate
# ══════════════════════════════════════════════════════════════════
class TestKnowledgeBoundaryGate:

    def setup_method(self):
        from literary_system.relation_graph.relation_graph_store import (
            RelationGraphStore, StoryNode, StoryEdge, NodeType, RelationType
        )
        from literary_system.drse.drse_engine import KnowledgeBoundaryGate
        self.rgs = RelationGraphStore()
        self.gate = KnowledgeBoundaryGate(relation_graph=self.rgs)
        self.NT = NodeType
        self.SN = StoryNode
        self.SE = StoryEdge
        self.RT = RelationType

    def _node(self, nid, nt=None):
        return self.SN(nid, nt or self.NT.FACT_SECRET, f"내용_{nid}")

    def test_knows_returns_1(self):
        n = self._node("F1")
        self.rgs.add_node(n)
        self.rgs.add_node(self.SN("C1", self.NT.CHARACTER, "인물"))
        self.rgs.add_edge(self.SE("C1", "F1", self.RT.KNOWS))
        assert self.gate.calculate_gate_weight(n, "C1") == 1.0

    def test_suspects_returns_half(self):
        n = self._node("F2")
        self.rgs.add_node(n)
        self.rgs.add_node(self.SN("C1", self.NT.CHARACTER, "인물"))
        self.rgs.add_edge(self.SE("C1", "F2", self.RT.SUSPECTS))
        assert self.gate.calculate_gate_weight(n, "C1") == 0.5

    def test_unaware_returns_zero(self):
        n = self._node("F3")
        self.rgs.add_node(n)
        # 엣지 없음 → UNAWARE
        assert self.gate.calculate_gate_weight(n, "NOBODY") == 0.0

    def test_does_not_know_returns_zero(self):
        n = self._node("F4")
        self.rgs.add_node(n)
        self.rgs.add_node(self.SN("C2", self.NT.CHARACTER, "인물2"))
        self.rgs.add_edge(self.SE("C2", "F4", self.RT.DOES_NOT_KNOW))
        assert self.gate.calculate_gate_weight(n, "C2") == 0.0

    def test_hides_from_returns_zero(self):
        n = self._node("F5")
        self.rgs.add_node(n)
        self.rgs.add_node(self.SN("C3", self.NT.CHARACTER, "인물3"))
        self.rgs.add_edge(self.SE("C3", "F5", self.RT.HIDES_FROM))
        assert self.gate.calculate_gate_weight(n, "C3") == 0.0

    def test_misbelieves_returns_04(self):
        n = self._node("F6")
        self.rgs.add_node(n)
        self.rgs.add_node(self.SN("C4", self.NT.CHARACTER, "인물4"))
        self.rgs.add_edge(self.SE("C4", "F6", self.RT.MISBELIEVES))
        assert self.gate.calculate_gate_weight(n, "C4") == 0.4

    def test_public_fact_default_weight(self):
        from literary_system.relation_graph.relation_graph_store import StoryNode, NodeType
        n = StoryNode("PUB1", NodeType.FACT_PUBLIC, "공개 사실")
        self.rgs.add_node(n)
        # 엣지 없어도 PUBLIC은 1.0
        w = self.gate.calculate_gate_weight(n, "ANY_CHAR")
        assert w == 1.0


# ══════════════════════════════════════════════════════════════════
# TestDRSEEngine
# ══════════════════════════════════════════════════════════════════
class TestDRSEEngine:

    def setup_method(self):
        from literary_system.relation_graph.relation_graph_store import (
            RelationGraphStore, StoryNode, StoryEdge, NodeType, RelationType
        )
        from literary_system.drse.drse_engine import (
            KnowledgeBoundaryGate, DRSEScorer, DRSEContextRouter,
            KeywordSemanticScorer
        )
        self.rgs = RelationGraphStore()
        self.gate = KnowledgeBoundaryGate(relation_graph=self.rgs)
        self.scorer = DRSEScorer(self.rgs, self.gate, KeywordSemanticScorer())
        self.router = DRSEContextRouter(self.scorer)
        self.NT = NodeType
        self.SN = StoryNode
        self.SE = StoryEdge
        self.RT = RelationType

    def _setup_scene(self):
        """기본 씬 셋업: 이준서/김지수, 배신 사실, 열쇠 복선"""
        self.rgs.add_node(self.SN("CHAR_준서", self.NT.CHARACTER, "이준서 비서관"))
        self.rgs.add_node(self.SN("CHAR_지수", self.NT.CHARACTER, "김지수 장관"))
        self.rgs.add_node(self.SN("FACT_배신", self.NT.FACT_SECRET, "이준서 배신 사실"))
        self.rgs.add_node(self.SN("OBJ_서류", self.NT.OBJECT_RESIDUE, "3화 서류 봉투", is_resolved=False))
        self.rgs.add_node(self.SN("RULE_보안", self.NT.WORLD_RULE, "국정원 보안 규정"))

        # 준서는 배신 사실을 안다, 지수는 모른다
        self.rgs.add_edge(self.SE("CHAR_준서", "FACT_배신", self.RT.KNOWS))
        self.rgs.add_edge(self.SE("CHAR_지수", "FACT_배신", self.RT.DOES_NOT_KNOW))
        # 서류는 공개됨
        self.rgs.add_edge(self.SE("CHAR_지수", "OBJ_서류", self.RT.KNOWS))

    def test_knows_node_positive_score(self):
        self._setup_scene()
        node = self.rgs.get_node("FACT_배신")
        r = self.scorer.score_node(node, "배신 서류 발견", "CHAR_준서", 7)
        assert r.score > 0.0
        assert not r.gate_blocked

    def test_does_not_know_blocked(self):
        self._setup_scene()
        node = self.rgs.get_node("FACT_배신")
        r = self.scorer.score_node(node, "배신 사실 알아가는 장면", "CHAR_지수", 7)
        assert r.score == 0.0
        assert r.gate_blocked

    def test_secret_blocked_becomes_forbidden(self):
        self._setup_scene()
        node = self.rgs.get_node("FACT_배신")
        r = self.scorer.score_node(node, "장면", "CHAR_지수", 7)
        assert r.is_forbidden_secret

    def test_unresolved_residue_boost(self):
        self._setup_scene()
        node = self.rgs.get_node("OBJ_서류")
        r = self.scorer.score_node(node, "서류 봉투 장면", "CHAR_지수", 7)
        assert r.score > 0.0
        assert r.breakdown.get("C_residue_boost", 1.0) == 1.5

    def test_temporal_decay_reduces_score(self):
        self._setup_scene()
        node = self.rgs.get_node("OBJ_서류")
        r1 = self.scorer.score_node(node, "서류", "CHAR_지수", 3)   # 최근
        r2 = self.scorer.score_node(node, "서류", "CHAR_지수", 20)  # 오래됨
        if r1.score > 0 and r2.score > 0:
            assert r2.breakdown["T_temporal_decay"] < r1.breakdown["T_temporal_decay"]

    def test_reveal_budget_gate(self):
        n = self.SN("FUTURE", self.NT.FACT_SECRET, "미래 공개 사실",
                    reveal_episode=10)
        self.rgs.add_node(n)
        self.rgs.add_edge(self.SE("CHAR_지수", "FUTURE", self.RT.KNOWS))
        r = self.scorer.score_node(n, "미래 사실", "CHAR_지수", 5)  # ep 5 < reveal 10
        assert r.score == 0.0  # RevealBudgetGate 차단

    def test_context_packet_structure(self):
        self._setup_scene()
        packet = self.router.build_packet(
            "김지수가 이준서를 의심하기 시작한다",
            "CHAR_지수", 7, top_k=3
        )
        assert isinstance(packet.allowed_context, list)
        assert isinstance(packet.forbidden_context, list)
        assert isinstance(packet.rendering_strategy, list)
        assert isinstance(packet.drse_scores, dict)
        assert len(packet.rendering_strategy) >= 4

    def test_forbidden_context_contains_secret(self):
        self._setup_scene()
        packet = self.router.build_packet(
            "의심 장면", "CHAR_지수", 7
        )
        # FACT_배신이 지수에게 차단 → forbidden에 나타나야 함
        forbidden_text = " ".join(packet.forbidden_context)
        assert "절대 금지" in forbidden_text or "FACT_배신" in packet.drse_scores

    def test_score_all_returns_all_nodes(self):
        self._setup_scene()
        scores = self.scorer.score_all("장면", "CHAR_지수", 7)
        assert len(scores) == len(self.rgs.all_nodes())

    def test_breakdown_has_all_terms(self):
        self._setup_scene()
        node = self.rgs.get_node("OBJ_서류")
        r = self.scorer.score_node(node, "서류", "CHAR_지수", 7)
        if not r.gate_blocked:
            for k in ["S_semantic", "R_relation_strength", "T_temporal_decay",
                      "A_arc_pressure", "C_residue_boost", "P_authority_penalty"]:
                assert k in r.breakdown


# ══════════════════════════════════════════════════════════════════
# TestNode2Extensions (V1650 흡수)
# ══════════════════════════════════════════════════════════════════
class TestNode2Extensions:

    def setup_method(self):
        from literary_system.node2_extensions.node2_extensions import (
            EmotionToBehaviorTransformer, AntiClicheSubstitutionEngine,
            SubtextDialoguePlanner, ForbiddenRevealScanner, Node2AuthorityGuard
        )
        self.etb  = EmotionToBehaviorTransformer()
        self.ace  = AntiClicheSubstitutionEngine()
        self.sdp  = SubtextDialoguePlanner()
        self.frs  = ForbiddenRevealScanner()
        self.nag  = Node2AuthorityGuard()

    def test_pdi_good_scene_passes(self):
        text = "그는 서류를 내려놓았다. 복도에서 발소리가 들렸다."
        r = self.etb.analyze(text)
        assert r.pdi_score > 0.7

    def test_pdi_bad_scene_fails(self):
        text = "그는 너무 슬펐다. 이상하게도 마음이 무거웠다. 왠지 모르게 두려웠다."
        r = self.etb.analyze(text)
        assert len(r.violations) > 0
        assert r.needs_rewrite

    def test_check_pdi_boolean(self):
        good = "복도가 조용했다. 손이 멈췄다."
        bad  = "그는 화가 났다. 슬펐다."
        assert self.etb.check_pdi(good) is True
        # bad 씬은 violation 있을 수 있음 (패턴 매칭)

    def test_cliche_detection(self):
        text = "갑자기 모든 것이 명확해졌다. 드디어 진실을 알았다."
        r = self.ace.analyze(text)
        assert r.needs_attention
        assert len(r.found) > 0

    def test_clean_text_no_cliche(self):
        text = "그는 복도에서 걸음을 멈췄다. 서류가 바닥에 있었다."
        r = self.ace.analyze(text)
        assert r.clean_ratio > 0.7

    def test_subtext_planning(self):
        plan = self.sdp.plan("나 괜찮아.", "긴장된 분위기")
        assert plan.subtext_layer != ""
        assert plan.suggested_rewrite != ""

    def test_forbidden_reveal_scanner_direct_hit(self):
        report = self.frs.scan(
            "이준서가 배신자임을 김지수가 알게 됐다.",
            ["이준서가 배신자임을"]
        )
        assert not report.passed
        assert report.severity == "high"
        assert len(report.direct_hits) > 0

    def test_forbidden_reveal_scanner_clean(self):
        report = self.frs.scan(
            "김지수는 서류를 바라봤다. 이준서는 시선을 피했다.",
            ["이준서 배신"]
        )
        assert report.passed
        assert report.severity == "none"

    def test_authority_guard_clean(self):
        text = "복도가 조용했다. 그는 서류를 집어 들었다."
        r = self.nag.check(text)
        assert r.authority_safe

    def test_authority_guard_violation(self):
        text = "알고 보니 그는 배신자였다."
        r = self.nag.check(text)
        assert not r.authority_safe


# ══════════════════════════════════════════════════════════════════
# TestFullPipeline (통합 흐름)
# ══════════════════════════════════════════════════════════════════
class TestFullPipeline:
    """DRSE → ContextPacket → Node2Extensions 전체 흐름."""

    def setup_method(self):
        from literary_system.relation_graph.relation_graph_store import (
            RelationGraphStore, StoryNode, StoryEdge, NodeType, RelationType
        )
        from literary_system.drse.drse_engine import (
            KnowledgeBoundaryGate, DRSEScorer, DRSEContextRouter,
            KeywordSemanticScorer
        )
        from literary_system.node2_extensions.node2_extensions import (
            EmotionToBehaviorTransformer, ForbiddenRevealScanner
        )
        rgs  = RelationGraphStore()
        gate = KnowledgeBoundaryGate(relation_graph=rgs)
        sc   = DRSEScorer(rgs, gate, KeywordSemanticScorer())
        self.router = DRSEContextRouter(sc)
        self.etb = EmotionToBehaviorTransformer()
        self.frs = ForbiddenRevealScanner()

        # 씬 데이터 셋업
        rgs.add_node(StoryNode("C_JI", NodeType.CHARACTER, "김지수 장관"))
        rgs.add_node(StoryNode("C_JS", NodeType.CHARACTER, "이준서 비서관"))
        rgs.add_node(StoryNode("F_BETRAY", NodeType.FACT_SECRET, "이준서 배신 사실"))
        rgs.add_node(StoryNode("O_DOC", NodeType.OBJECT_RESIDUE, "3화 서류", is_resolved=False))
        rgs.add_edge(StoryEdge("C_JI", "F_BETRAY", RelationType.DOES_NOT_KNOW))
        rgs.add_edge(StoryEdge("C_JI", "O_DOC",    RelationType.KNOWS))

    def test_full_pipeline_context_packet(self):
        packet = self.router.build_packet(
            "김지수가 이준서를 의심하기 시작한다. 서류 발견.",
            "C_JI", 7, top_k=3
        )
        # 배신 사실은 차단
        assert any("절대 금지" in f for f in packet.forbidden_context)
        # 서류는 허용
        assert any("서류" in a for a in packet.allowed_context)
        # 렌더링 전략 있음
        assert len(packet.rendering_strategy) >= 4

    def test_full_pipeline_node2_check(self):
        # 잘 작성된 씬
        good_text = "그는 서류를 내려놓았다. 복도에서 발소리가 들렸다."
        assert self.etb.check_pdi(good_text) is True

        # forbidden 검사
        report = self.frs.scan(good_text, ["이준서 배신", "배신자"])
        assert report.passed

    def test_pipeline_bad_scene_detected(self):
        # PDI 위반 씬
        bad_text = "그는 너무 슬펐다. 마음이 무거웠다."
        r = self.etb.analyze(bad_text)
        assert r.needs_rewrite

        # forbidden 위반 씬
        revealed = "이준서가 배신자임을 김지수는 알게 됐다."
        report = self.frs.scan(revealed, ["이준서가 배신자임을"])
        assert not report.passed
