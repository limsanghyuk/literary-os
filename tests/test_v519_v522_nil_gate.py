"""
Tests for V519~V522:
  - NILOrchestrator (nil_orchestrator.py)
  - Gate25          (gate25.py)
  - NIL 루프 통합 12종 테스트
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from literary_system.nie.nil_orchestrator import (
    NILOrchestrator, SceneInput, NILResult, WorkCompletionResult
)
from literary_system.nie.gate25 import (
    Gate25, Gate25Result, GateCheckItem,
    GATE_L_FINAL_MAX, GATE_SIGMA_MAX, GATE_NPS_MIN,
    GATE_EPISODE_PASS_RATE_MIN, GATE_COST_SLO_MAX_USD,
)
from literary_system.nie.nie_l7_container import NIEConfig


# ─── 헬퍼 ─────────────────────────────────────────────────────────────────────

def _make_scene(
    scene_id="S001",
    episode_idx=0,
    total_scenes=16,
    tension=0.60,
    char_updates=None,
    query=None,
) -> SceneInput:
    return SceneInput(
        scene_id=scene_id,
        episode_idx=episode_idx,
        total_scenes=total_scenes,
        metrics={"tension": tension, "sympathy": 0.55, "dread": 0.40, "catharsis": 0.50},
        char_updates=char_updates or [("A", "B", 0.10)],
        feature=[0.1, 0.2, 0.3],
        query=query,
    )


def _default_orchestrator() -> NILOrchestrator:
    return NILOrchestrator()


def _full_orchestrator() -> NILOrchestrator:
    config = NIEConfig(
        enable_stability=True,
        enable_temporal_cim=True,
        enable_meta_learner=True,
        enable_rag_classifier=True,
    )
    return NILOrchestrator(config)


# ─── TestNILOrchestrator ──────────────────────────────────────────────────────

class TestNILOrchestrator:

    # 1. 기본 초기화
    def test_init_default_config(self):
        orch = _default_orchestrator()
        assert orch.scene_count == 0

    # 2. process_scene 기본 실행
    def test_process_scene_returns_nil_result(self):
        orch = _default_orchestrator()
        scene = _make_scene()
        result = orch.process_scene(scene)
        assert isinstance(result, NILResult)
        assert result.scene_id == "S001"

    # 3. Step 1: CIM 업데이트 반영
    def test_step1_cim_edges_updated(self):
        orch = _default_orchestrator()
        scene = _make_scene(char_updates=[("A", "B", 0.1), ("B", "C", 0.2)])
        result = orch.process_scene(scene)
        assert result.step1_edges_updated == 2

    # 4. Step 2: Triangle 존재 여부
    def test_step2_triangles_computed(self):
        orch = _default_orchestrator()
        # 삼각형 최소 조건: 3캐릭터 + 3쌍 엣지
        orch.process_scene(_make_scene(char_updates=[("A", "B", 0.5)]))
        orch.process_scene(_make_scene(char_updates=[("B", "C", 0.5)]))
        result = orch.process_scene(_make_scene(char_updates=[("A", "C", 0.5)]))
        assert isinstance(result.step2_top_triangles, int)
        assert result.step2_top_triangles >= 0

    # 5. Step 3: AMW vector 반환
    def test_step3_amw_vector_has_dims(self):
        orch = _default_orchestrator()
        result = orch.process_scene(_make_scene())
        assert "tension" in result.step3_amw_vector

    # 6. Step 4: MAE 결과 구조
    def test_step4_mae_result_present(self):
        orch = _default_orchestrator()
        result = orch.process_scene(_make_scene())
        assert result.mae_result is not None
        assert hasattr(result.mae_result, "passed")

    # 7. Step 5: BridgeResult 구조
    def test_step5_bridge_result_present(self):
        orch = _default_orchestrator()
        result = orch.process_scene(_make_scene())
        assert result.bridge_result is not None
        assert hasattr(result.bridge_result, "advantage")

    # 8. Step 6: RAG intent (enable_rag_classifier=True 시)
    def test_step6_rag_intent_classified(self):
        config = NIEConfig(enable_rag_classifier=True)
        orch = NILOrchestrator(config)
        scene = _make_scene(query="주인공 캐릭터가 갈등하는 장면")
        result = orch.process_scene(scene)
        assert result.step6_rag_intent in ("CHARACTER", "EMOTIONAL", "PLOT_EVENT")

    # 9. scene_count 증가
    def test_scene_count_increments(self):
        orch = _default_orchestrator()
        for i in range(5):
            orch.process_scene(_make_scene(scene_id=f"S{i:03d}", episode_idx=i))
        assert orch.scene_count == 5

    # 10. complete_work 반환값
    def test_complete_work_returns_result(self):
        orch = _default_orchestrator()
        for i in range(8):
            orch.process_scene(_make_scene(scene_id=f"S{i:03d}", episode_idx=i, total_scenes=8))
        result = orch.complete_work(genre="melodrama")
        assert isinstance(result, WorkCompletionResult)
        assert result.l_final is not None

    # 11. complete_episode TemporalCIM 진행
    def test_complete_episode_advances_temporal_cim(self):
        config = NIEConfig(enable_temporal_cim=True)
        orch = NILOrchestrator(config)
        orch.process_scene(_make_scene())
        orch.complete_episode()
        # episode_idx 가 1로 증가했는지 내부 상태로 확인
        assert orch._episode_idx == 1

    # 12. 전체 파이프라인: 16씬 → complete_work
    def test_full_pipeline_16_scenes(self):
        orch = _full_orchestrator()
        for i in range(16):
            scene = SceneInput(
                scene_id=f"ep1_s{i:02d}",
                episode_idx=i,
                total_scenes=16,
                metrics={"tension": 0.50 + 0.02 * i, "sympathy": 0.55, "dread": 0.40, "catharsis": 0.50},
                char_updates=[("A", "B", 0.05), ("B", "C", 0.03)],
                feature=[0.1, 0.2, 0.3],
                query="주인공의 감정 변화",
            )
            orch.process_scene(scene)
        result = orch.complete_work(genre="melodrama")
        assert result.l_final.l_final >= 0.0
        assert orch.scene_count == 16


# ─── TestGate25 ───────────────────────────────────────────────────────────────

class TestGate25:

    def test_all_pass(self):
        gate = Gate25()
        result = gate.run(
            l_final=0.10,
            agent_sigma=0.05,
            nps=30,
            cost_usd_per_episode=3.0,
            episode_pass_rate=0.95,
        )
        assert result.overall_passed is True
        assert len(result.fail_reasons) == 0

    def test_g1_fail_high_l_final(self):
        gate = Gate25()
        result = gate.run(
            l_final=0.20,   # > 0.15
            agent_sigma=0.05,
            nps=30,
            cost_usd_per_episode=3.0,
            episode_pass_rate=0.95,
        )
        assert not result.overall_passed
        assert any("G1" in r for r in result.fail_reasons)

    def test_g2_fail_high_sigma(self):
        gate = Gate25()
        result = gate.run(
            l_final=0.10,
            agent_sigma=0.15,  # > 0.10
            nps=30,
            cost_usd_per_episode=3.0,
            episode_pass_rate=0.95,
        )
        assert not result.overall_passed
        assert any("G2" in r for r in result.fail_reasons)

    def test_g3_fail_low_nps(self):
        gate = Gate25()
        result = gate.run(
            l_final=0.10,
            agent_sigma=0.05,
            nps=20,            # < 25
            cost_usd_per_episode=3.0,
            episode_pass_rate=0.95,
        )
        assert not result.overall_passed
        assert any("G3" in r for r in result.fail_reasons)

    def test_g4_fail_high_cost(self):
        gate = Gate25()
        result = gate.run(
            l_final=0.10,
            agent_sigma=0.05,
            nps=30,
            cost_usd_per_episode=6.0,  # > 5.00
            episode_pass_rate=0.95,
        )
        assert not result.overall_passed
        assert any("G4" in r for r in result.fail_reasons)

    def test_g5_fail_low_pass_rate(self):
        gate = Gate25()
        result = gate.run(
            l_final=0.10,
            agent_sigma=0.05,
            nps=30,
            cost_usd_per_episode=3.0,
            episode_pass_rate=0.80,    # < 0.90
        )
        assert not result.overall_passed
        assert any("G5" in r for r in result.fail_reasons)

    def test_multiple_fail(self):
        gate = Gate25()
        result = gate.run(
            l_final=0.30,   # G1 fail
            agent_sigma=0.20,  # G2 fail
            nps=10,          # G3 fail
            cost_usd_per_episode=10.0,  # G4 fail
            episode_pass_rate=0.50,     # G5 fail
        )
        assert not result.overall_passed
        assert len(result.fail_reasons) == 5

    def test_summary_contains_gate_ids(self):
        gate = Gate25()
        result = gate.run(0.10, 0.05, 30, 3.0, 0.95)
        summary = result.summary()
        for g in ["G1", "G2", "G3", "G4", "G5"]:
            assert g in summary

    def test_boundary_l_final_exactly_015(self):
        """L_final = 0.15 정확히 경계값 → PASS."""
        gate = Gate25()
        result = gate.run(0.15, 0.05, 30, 3.0, 0.95)
        g1 = next(c for c in result.checks if c.gate_id == "G1")
        assert g1.passed is True

    def test_checks_count_is_5(self):
        gate = Gate25()
        result = gate.run(0.10, 0.05, 30, 3.0, 0.95)
        assert len(result.checks) == 5

    def test_run_from_orchestrator(self):
        """NILOrchestrator 와 Gate25 통합 실행."""
        orch = _default_orchestrator()
        for i in range(8):
            orch.process_scene(_make_scene(scene_id=f"S{i:03d}", episode_idx=i, total_scenes=8))

        gate = Gate25()
        result = gate.run_from_orchestrator(
            orchestrator=orch,
            nps=30,
            cost_usd_per_episode=2.5,
            episode_pass_rate=0.92,
        )
        assert isinstance(result, Gate25Result)
        # G1 여부 무관, 구조 확인
        assert len(result.checks) == 5
