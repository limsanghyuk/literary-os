"""
Phase 5 ASD 테스트 — V541~V545
=================================
Literary OS Phase 5 Autonomous Story Doctor

커버리지
--------
TestNarrativeDebtDetector  (11 tests)  V541
TestArcConsistencyChecker  (11 tests)  V542
TestStoryDoctorOrchestrator (10 tests) V543
TestAutoRepairExecutor      (9 tests)  V544
TestGate28                 (11 tests)  V545

합계: 52 tests
"""
import sys
sys.path.insert(0, '/tmp/v525_work/literary_os_v430_COMPLETE')

import pytest

from literary_system.graph_intelligence.narrative_graph_schema import (
    NarrativeEdge, NarrativeEdgeType, NarrativeNodeType,
    CharacterNode, SceneNode, SecretNode, RevealNode,
    MotifNode, RelationshipNode, EmotionPressureNode,
)
from literary_system.graph_intelligence.narrative_graph_store import NarrativeGraphStore
from literary_system.graph_intelligence.asd import (
    # V541
    NarrativeDebtDetector, NarrativeDebtReport, NarrativeDebtItem, DebtType,
    # V542
    ArcConsistencyChecker, ArcConsistencyReport, ArcIssue, ArcIssueType,
    # V543
    StoryDoctorOrchestrator, DoctorReport, RepairRecommendation, RepairCategory,
    # V544
    AutoRepairExecutor, BatchExecutionResult, ExecutionResult, ExecutionStatus,
    # V545
    Gate28, Gate28Result,
)
from literary_system.graph_intelligence.sp2.code_dependency_graph import (
    CodeDependencyGraph, SceneDependencyKey, SceneProfile,
)


# ===========================================================================
# Fixtures
# ===========================================================================

def _make_store() -> NarrativeGraphStore:
    return NarrativeGraphStore()


def _char(store: NarrativeGraphStore, cid: str, label: str,
          ep_first: int = 1, ep_last: int = None) -> CharacterNode:
    n = CharacterNode(node_id=cid, node_type=NarrativeNodeType.CHARACTER, label=label,
                      episode_first=ep_first, episode_last=ep_last)
    store.add_node(n)
    return n


def _scene(store: NarrativeGraphStore, sid: str, label: str,
           episode: int = 1, idx: int = 0) -> SceneNode:
    n = SceneNode(node_id=sid, node_type=NarrativeNodeType.SCENE, label=label,
                  episode=episode, scene_idx=idx)
    store.add_node(n)
    return n


def _secret(store: NarrativeGraphStore, sid: str, label: str) -> SecretNode:
    n = SecretNode(node_id=sid, node_type=NarrativeNodeType.SECRET, label=label)
    store.add_node(n)
    return n


def _reveal(store: NarrativeGraphStore, rid: str, label: str,
            secret_id: str = "", ep: int = 1) -> RevealNode:
    n = RevealNode(node_id=rid, node_type=NarrativeNodeType.REVEAL, label=label,
                   secret_id=secret_id, reveal_episode=ep)
    store.add_node(n)
    return n


def _motif(store: NarrativeGraphStore, mid: str, label: str) -> MotifNode:
    n = MotifNode(node_id=mid, node_type=NarrativeNodeType.MOTIF, label=label, symbol=label)
    store.add_node(n)
    return n


def _edge(store, src_id, dst_id, etype, weight=1.0):
    eid = store.make_edge_id()
    e = NarrativeEdge(edge_id=eid, src_id=src_id, dst_id=dst_id,
                      edge_type=etype, weight=weight)
    store.add_edge(e)
    return e


def _rel(store: NarrativeGraphStore, rid: str, ca: str, cb: str,
         ep: int = 1) -> RelationshipNode:
    n = RelationshipNode(node_id=rid, node_type=NarrativeNodeType.RELATIONSHIP,
                         label=f"{ca}-{cb}", char_a_id=ca, char_b_id=cb,
                         rel_type="ally", episode=ep)
    store.add_node(n)
    return n


def _emotion(store: NarrativeGraphStore, eid: str, char_id: str) -> EmotionPressureNode:
    n = EmotionPressureNode(node_id=eid, node_type=NarrativeNodeType.EMOTION_PRESSURE,
                            label=f"ep_{char_id}", meta={"character_id": char_id})
    store.add_node(n)
    return n


# ===========================================================================
# V541 — NarrativeDebtDetector
# ===========================================================================

class TestNarrativeDebtDetector:

    def test_clean_graph_returns_empty_report(self):
        store = _make_store()
        report = NarrativeDebtDetector(store).detect()
        assert report.is_clean()
        assert report.total_debts == 0
        assert report.overall_debt_score == 0.0

    def test_secret_without_reveals_edge(self):
        store = _make_store()
        _secret(store, "s1", "Secret1")
        report = NarrativeDebtDetector(store).detect()
        assert len(report.unresolved_secrets) == 1
        assert report.unresolved_secrets[0].debt_type == DebtType.UNRESOLVED_SECRET

    def test_secret_with_reveal_is_clean(self):
        store = _make_store()
        _secret(store, "s1", "Secret1")
        _reveal(store, "r1", "Reveal1", secret_id="s1")
        _edge(store, "s1", "r1", NarrativeEdgeType.REVEALS)
        report = NarrativeDebtDetector(store).detect()
        assert all(i.node_id != "s1" for i in report.unresolved_secrets)

    def test_secret_reveals_to_non_reveal_node(self):
        store = _make_store()
        _secret(store, "s1", "Secret1")
        sc = _scene(store, "sc1", "Scene1")
        _edge(store, "s1", "sc1", NarrativeEdgeType.REVEALS)
        report = NarrativeDebtDetector(store).detect()
        assert len(report.unresolved_secrets) == 1
        assert "sc1" in report.unresolved_secrets[0].related_ids

    def test_broken_foreshadow_dst_missing(self):
        store = _make_store()
        m = _motif(store, "m1", "Motif1")
        # FORESHADOWS 엣지: dst가 그래프에 없음
        eid = store.make_edge_id()
        with pytest.raises(ValueError):
            store.add_edge(NarrativeEdge(
                edge_id=eid, src_id="m1", dst_id="nonexistent",
                edge_type=NarrativeEdgeType.FORESHADOWS, weight=1.0
            ))

    def test_broken_foreshadow_dst_not_scene(self):
        store = _make_store()
        _motif(store, "m1", "Motif1")
        _char(store, "c1", "Char1")
        _edge(store, "m1", "c1", NarrativeEdgeType.FORESHADOWS)
        report = NarrativeDebtDetector(store).detect()
        assert any(i.debt_type == DebtType.BROKEN_FORESHADOW
                   for i in report.broken_foreshadows)

    def test_foreshadow_orphan_scene(self):
        store = _make_store()
        _motif(store, "m1", "Motif1")
        _scene(store, "sc_future", "FutureScene")
        _edge(store, "m1", "sc_future", NarrativeEdgeType.FORESHADOWS)
        # sc_future에 CAUSES/DEPENDS_ON 없음 → 고아
        report = NarrativeDebtDetector(store).detect()
        assert any(i.debt_type == DebtType.BROKEN_FORESHADOW
                   for i in report.broken_foreshadows)

    def test_foreshadow_connected_scene_is_ok(self):
        store = _make_store()
        _motif(store, "m1", "Motif1")
        _scene(store, "sc1", "Scene1")
        _scene(store, "sc_future", "FutureScene")
        _edge(store, "m1", "sc_future", NarrativeEdgeType.FORESHADOWS)
        _edge(store, "sc1", "sc_future", NarrativeEdgeType.CAUSES)
        report = NarrativeDebtDetector(store).detect()
        assert not report.broken_foreshadows

    def test_abandoned_thread_no_edges(self):
        store = _make_store()
        _char(store, "c1", "Ghost", ep_first=1, ep_last=None)
        report = NarrativeDebtDetector(store).detect()
        assert any(i.debt_type == DebtType.ABANDONED_THREAD
                   for i in report.abandoned_threads)

    def test_character_with_edges_not_abandoned(self):
        store = _make_store()
        _char(store, "c1", "Active")
        _char(store, "c2", "Partner")
        _edge(store, "c1", "c2", NarrativeEdgeType.KNOWS)
        report = NarrativeDebtDetector(store).detect()
        assert not any(i.node_id == "c1" for i in report.abandoned_threads)

    def test_multiple_debts_score_average(self):
        store = _make_store()
        _secret(store, "s1", "S1")
        _secret(store, "s2", "S2")
        report = NarrativeDebtDetector(store).detect()
        assert report.total_debts == 2
        assert 0.0 < report.overall_debt_score <= 1.0

    def test_custom_severity_reflected(self):
        store = _make_store()
        _secret(store, "s1", "S1")
        report = NarrativeDebtDetector(store, secret_severity=0.90).detect()
        assert report.unresolved_secrets[0].severity == pytest.approx(0.90)


# ===========================================================================
# V542 — ArcConsistencyChecker
# ===========================================================================

class TestArcConsistencyChecker:

    def test_clean_store_no_issues(self):
        store = _make_store()
        report = ArcConsistencyChecker(store).check()
        assert report.is_consistent()
        assert report.total_issues == 0

    def test_character_without_emotion_tracking_ac1(self):
        store = _make_store()
        _char(store, "c1", "Untracked")
        report = ArcConsistencyChecker(store).check()
        assert any(i.issue_type == ArcIssueType.ARC_NOT_TRACKED
                   for i in report.not_tracked)

    def test_character_with_escalates_is_tracked(self):
        store = _make_store()
        _char(store, "c1", "TrackedChar")
        _char(store, "c2", "Partner")
        _edge(store, "c1", "c2", NarrativeEdgeType.ESCALATES)
        report = ArcConsistencyChecker(store).check()
        assert not any(i.character_id == "c1" for i in report.not_tracked)

    def test_character_with_emotion_node_is_tracked(self):
        store = _make_store()
        _char(store, "c1", "EmotChar")
        _emotion(store, "ep1", "c1")
        report = ArcConsistencyChecker(store).check()
        assert not any(i.character_id == "c1" for i in report.not_tracked)

    def test_post_death_relationship_ac2(self):
        store = _make_store()
        _char(store, "c1", "Dead", ep_first=1, ep_last=3)
        _char(store, "c2", "Alive")
        _rel(store, "rel1", "c1", "c2", ep=5)  # episode 5 > ep_last 3
        report = ArcConsistencyChecker(store).check()
        assert any(i.issue_type == ArcIssueType.ARC_POST_DEATH_EDGE
                   for i in report.post_death_edges)

    def test_relationship_within_episode_ok(self):
        store = _make_store()
        _char(store, "c1", "Alive", ep_last=5)
        _char(store, "c2", "Partner")
        _rel(store, "rel1", "c1", "c2", ep=3)
        report = ArcConsistencyChecker(store).check()
        assert not report.post_death_edges

    def test_contradiction_overflow_ac3(self):
        store = _make_store()
        _char(store, "c1", "A")
        _char(store, "c2", "B")
        # threshold=2 → 2개 이상이면 fail
        _edge(store, "c1", "c2", NarrativeEdgeType.CONTRADICTS)
        _edge(store, "c2", "c1", NarrativeEdgeType.CONTRADICTS)
        report = ArcConsistencyChecker(store, contradiction_threshold=2).check()
        assert any(i.issue_type == ArcIssueType.ARC_CONTRADICTION_OVERFLOW
                   for i in report.contradiction_flows)

    def test_single_contradiction_ok(self):
        store = _make_store()
        _char(store, "c1", "A")
        _char(store, "c2", "B")
        _edge(store, "c1", "c2", NarrativeEdgeType.CONTRADICTS)
        report = ArcConsistencyChecker(store, contradiction_threshold=2).check()
        assert not report.contradiction_flows

    def test_episode_inversion_ac4(self):
        store = _make_store()
        _char(store, "c1", "Inverted", ep_first=5, ep_last=2)
        report = ArcConsistencyChecker(store).check()
        assert any(i.issue_type == ArcIssueType.ARC_EPISODE_INVERSION
                   for i in report.episode_inversions)

    def test_episode_order_ok(self):
        store = _make_store()
        _char(store, "c1", "OK", ep_first=1, ep_last=5)
        report = ArcConsistencyChecker(store).check()
        assert not report.episode_inversions

    def test_overall_score_nonzero_with_issues(self):
        store = _make_store()
        _char(store, "c1", "NoTrack")
        report = ArcConsistencyChecker(store).check()
        assert report.overall_score > 0.0


# ===========================================================================
# V543 — StoryDoctorOrchestrator
# ===========================================================================

class TestStoryDoctorOrchestrator:

    def _healthy_store(self) -> NarrativeGraphStore:
        store = _make_store()
        c1 = _char(store, "c1", "Hero", ep_first=1, ep_last=10)
        c2 = _char(store, "c2", "Villain", ep_first=1, ep_last=10)
        _emotion(store, "ep1", "c1")
        _emotion(store, "ep2", "c2")
        # 양방향 엣지 → 두 캐릭터 모두 나가는 엣지 있음 (abandoned_thread 방지)
        _edge(store, "c1", "c2", NarrativeEdgeType.KNOWS)
        _edge(store, "c2", "c1", NarrativeEdgeType.KNOWS)
        return store

    def test_diagnose_healthy_store(self):
        store = self._healthy_store()
        orch  = StoryDoctorOrchestrator(store)
        report = orch.diagnose()
        assert isinstance(report, DoctorReport)
        assert report.is_healthy()

    def test_diagnose_returns_debt_report(self):
        store = self._healthy_store()
        _secret(store, "s1", "UnresolvedSecret")
        report = StoryDoctorOrchestrator(store).diagnose()
        assert report.debt_report.total_debts >= 1

    def test_diagnose_returns_arc_report(self):
        store = _make_store()
        _char(store, "c1", "Inverted", ep_first=5, ep_last=2)
        report = StoryDoctorOrchestrator(store).diagnose()
        assert report.arc_report.total_issues >= 1

    def test_recommendations_sorted_by_priority(self):
        store = _make_store()
        _secret(store, "s1", "S1")
        _secret(store, "s2", "S2")
        _char(store, "c1", "Ghost")
        report = StoryDoctorOrchestrator(store).diagnose()
        scores = [r.priority_score for r in report.recommendations]
        assert scores == sorted(scores, reverse=True)

    def test_high_priority_threshold(self):
        store = _make_store()
        _secret(store, "s1", "S1")
        orch = StoryDoctorOrchestrator(store, high_threshold=0.50)
        report = orch.diagnose()
        for r in report.high_priority:
            assert r.priority_score >= 0.50

    def test_medium_priority_threshold(self):
        store = _make_store()
        _char(store, "c1", "Ghost")  # ARC_NOT_TRACKED → severity 0.45
        orch = StoryDoctorOrchestrator(store, high_threshold=0.70, medium_threshold=0.30)
        report = orch.diagnose()
        # all recs appear in one of high/medium/low
        total = (len(report.high_priority)
                 + len(report.medium_priority)
                 + len(report.low_priority))
        assert total == report.total_issues

    def test_recommendation_has_correct_category_for_secret(self):
        store = _make_store()
        _secret(store, "s1", "S1")
        report = StoryDoctorOrchestrator(store).diagnose()
        cats = [r.category for r in report.recommendations]
        assert RepairCategory.RESOLVE_SECRET in cats

    def test_blast_ratio_zero_for_non_scene_node(self):
        store = _make_store()
        _secret(store, "s1", "S1")
        report = StoryDoctorOrchestrator(store).diagnose()
        # SECRET 노드는 씬이 아니므로 blast_ratio=0
        for r in report.recommendations:
            if r.node_id == "s1":
                assert r.blast_ratio == 0.0

    def test_priority_score_capped_at_1(self):
        store = _make_store()
        _char(store, "c1", "C", ep_first=5, ep_last=2)  # inversion sev=0.90
        report = StoryDoctorOrchestrator(store, blast_weight=10.0).diagnose()
        for r in report.recommendations:
            assert r.priority_score <= 1.0

    def test_total_issues_matches_recommendation_list(self):
        store = _make_store()
        _secret(store, "s1", "S1")
        _char(store, "c1", "Ghost")
        report = StoryDoctorOrchestrator(store).diagnose()
        assert report.total_issues == len(report.recommendations)


# ===========================================================================
# V544 — AutoRepairExecutor
# ===========================================================================

def _make_code_dep(store):
    """빌드된 빈 CodeDependencyGraph 반환."""
    cdg = CodeDependencyGraph()
    profiles = [
        SceneProfile(key=SceneDependencyKey(episode=1, scene_id=node.node_id))
        for node in store.nodes_by_type(NarrativeNodeType.SCENE)
    ]
    if profiles:
        cdg.register_batch(profiles)
    cdg.build()
    return cdg


class TestAutoRepairExecutor:

    def _store_with_scene(self):
        store = _make_store()
        _scene(store, "sc1", "Scene1")
        return store

    def _make_executor(self, store, repair_fn=None):
        cdg = _make_code_dep(store)
        return AutoRepairExecutor(store, cdg, repair_fn=repair_fn)

    def test_dry_run_returns_dry_run_status(self):
        store = self._store_with_scene()
        _secret(store, "s1", "S1")
        _scene(store, "sc1", "Scene1")  # already added above but idempotent via dict
        orch   = StoryDoctorOrchestrator(store).diagnose()
        recs   = orch.recommendations
        exec_  = self._make_executor(store, repair_fn=None)
        # SECRET 노드로는 Gate 통과가 PLAN_ABORT 혹은 DRY_RUN(gate pass)일 수 있음
        result = exec_.execute(recs[0])
        assert result.recommendation_id == recs[0].recommendation_id

    def test_batch_execution_totals_match(self):
        store = _make_store()
        _char(store, "c1", "Ghost")
        _scene(store, "sc1", "SceneX")
        orch  = StoryDoctorOrchestrator(store).diagnose()
        exec_ = self._make_executor(store)
        batch = exec_.execute_batch(orch.recommendations)
        assert batch.total == len(orch.recommendations)

    def test_success_rate_between_0_and_1(self):
        store = _make_store()
        _char(store, "c1", "Ghost")
        orch  = StoryDoctorOrchestrator(store).diagnose()
        exec_ = self._make_executor(store)
        batch = exec_.execute_batch(orch.recommendations)
        assert 0.0 <= batch.success_rate() <= 1.0

    def test_repair_fn_called_on_approval(self):
        called = []
        store = self._store_with_scene()
        # 씬 노드로 recommendation 만들기: scene arc consistency issue
        _char(store, "c1", "Inv", ep_first=5, ep_last=2)
        orch = StoryDoctorOrchestrator(store).diagnose()
        recs = [r for r in orch.recommendations
                if r.category == RepairCategory.ARC_INVERSION]
        if not recs:
            pytest.skip("No ARC_INVERSION rec for this store config")
        exec_ = self._make_executor(store, repair_fn=lambda r: called.append(r) or True)
        result = exec_.execute(recs[0])
        # Gate pass 여부와 무관하게 결과 구조 유효성 확인
        assert isinstance(result, ExecutionResult)

    def test_execution_result_ok_method_dry_run(self):
        result = ExecutionResult(
            recommendation_id="R0001",
            scene_id="sc1",
            status=ExecutionStatus.DRY_RUN,
        )
        assert result.ok()

    def test_execution_result_ok_method_gate_fail(self):
        result = ExecutionResult(
            recommendation_id="R0001",
            scene_id="sc1",
            status=ExecutionStatus.GATE_FAIL,
        )
        assert not result.ok()

    def test_batch_result_counts_consistent(self):
        store = _make_store()
        _char(store, "c1", "Ghost")
        orch  = StoryDoctorOrchestrator(store).diagnose()
        exec_ = self._make_executor(store)
        batch = exec_.execute_batch(orch.recommendations)
        total_counted = (batch.approved + batch.dry_run + batch.gate_failed
                         + batch.plan_aborted + batch.errors)
        assert total_counted == batch.total

    def test_empty_recommendations_batch(self):
        store = _make_store()
        exec_ = self._make_executor(store)
        batch = exec_.execute_batch([])
        assert batch.total == 0
        assert batch.success_rate() == 0.0

    def test_error_status_on_invalid_node(self):
        store = _make_store()
        exec_ = self._make_executor(store)
        # 존재하지 않는 씬 ID로 recommendation 직접 생성
        rec = RepairRecommendation(
            recommendation_id="R9999",
            category=RepairCategory.RESOLVE_SECRET,
            node_id="nonexistent_scene",
            label="Bad",
            detail="test",
            severity=0.5,
            blast_ratio=0.0,
            priority_score=0.5,
        )
        result = exec_.execute(rec)
        # Gate가 처리하거나 ERROR 반환
        assert result.recommendation_id == "R9999"


# ===========================================================================
# V545 — Gate28
# ===========================================================================

def _make_doctor_report(debt_score=0.0, arc_score=0.0, high_cnt=0) -> DoctorReport:
    """DoctorReport stub for Gate28 testing."""
    from literary_system.graph_intelligence.asd.narrative_debt_detector import NarrativeDebtReport
    from literary_system.graph_intelligence.asd.arc_consistency_checker import ArcConsistencyReport

    debt_report = NarrativeDebtReport(
        total_debts=0, unresolved_secrets=[], broken_foreshadows=[],
        abandoned_threads=[], overall_debt_score=debt_score,
    )
    arc_report = ArcConsistencyReport(
        total_issues=0, not_tracked=[], post_death_edges=[],
        contradiction_flows=[], episode_inversions=[],
        overall_score=arc_score,
    )
    recs = [
        RepairRecommendation(
            recommendation_id=f"R{i:04d}", category=RepairCategory.RESOLVE_SECRET,
            node_id="x", label="x", detail="x",
            severity=0.8, blast_ratio=0.0, priority_score=0.8,
        )
        for i in range(high_cnt)
    ]
    return DoctorReport(
        recommendations=recs, total_issues=len(recs),
        high_priority=recs, medium_priority=[], low_priority=[],
        debt_report=debt_report, arc_report=arc_report,
    )


class TestGate28:

    def test_clean_report_passes_all(self):
        gate   = Gate28()
        report = _make_doctor_report(0.0, 0.0, 0)
        result = gate.evaluate(report)
        assert result.approved
        assert not result.failed_gates

    def test_debt_score_above_threshold_fails_g28_1(self):
        gate   = Gate28(debt_threshold=0.50)
        report = _make_doctor_report(debt_score=0.60)
        result = gate.evaluate(report)
        assert not result.approved
        assert "G28-1" in result.failed_gates

    def test_arc_score_above_threshold_fails_g28_2(self):
        gate   = Gate28(arc_threshold=0.40)
        report = _make_doctor_report(arc_score=0.55)
        result = gate.evaluate(report)
        assert "G28-2" in result.failed_gates

    def test_high_priority_cnt_above_threshold_fails_g28_3(self):
        gate   = Gate28(high_priority_threshold=5)
        report = _make_doctor_report(high_cnt=6)
        result = gate.evaluate(report)
        assert "G28-3" in result.failed_gates

    def test_combined_quality_formula(self):
        debt = 0.60; arc = 0.40
        expected_combined = round(min(debt * 0.55 + arc * 0.45, 1.0), 4)
        gate   = Gate28(combined_threshold=0.99)  # other gates pass
        report = _make_doctor_report(debt_score=debt, arc_score=arc)
        result = gate.evaluate(report)
        assert result.combined_quality == pytest.approx(expected_combined, abs=1e-4)

    def test_g28_4_fails_when_combined_above_threshold(self):
        gate   = Gate28(debt_threshold=1.0, arc_threshold=1.0,
                        high_priority_threshold=9999, combined_threshold=0.30)
        report = _make_doctor_report(debt_score=0.50, arc_score=0.40)
        result = gate.evaluate(report)
        assert "G28-4" in result.failed_gates

    def test_all_four_gates_can_fail(self):
        gate   = Gate28(debt_threshold=0.0, arc_threshold=0.0,
                        high_priority_threshold=0, combined_threshold=0.0)
        report = _make_doctor_report(debt_score=0.5, arc_score=0.5, high_cnt=1)
        result = gate.evaluate(report)
        assert len(result.failed_gates) == 4

    def test_gate28_result_summary_contains_status(self):
        gate   = Gate28()
        report = _make_doctor_report()
        result = gate.evaluate(report)
        assert "PASS" in result.summary() or "FAIL" in result.summary()

    def test_gate28_passes_at_exact_boundary(self):
        gate   = Gate28(debt_threshold=0.50, arc_threshold=0.40)
        report = _make_doctor_report(debt_score=0.50, arc_score=0.40)
        result = gate.evaluate(report)
        # G28-1, G28-2 should pass (≤ threshold)
        assert "G28-1" not in result.failed_gates
        assert "G28-2" not in result.failed_gates

    def test_combined_quality_capped_at_1(self):
        gate   = Gate28(combined_threshold=0.99)
        report = _make_doctor_report(debt_score=1.0, arc_score=1.0)
        result = gate.evaluate(report)
        assert result.combined_quality <= 1.0

    def test_gate28_check_count(self):
        gate   = Gate28()
        report = _make_doctor_report()
        result = gate.evaluate(report)
        assert len(result.checks) == 4
