"""
V327 Phase 1 통합 테스트
P1-1: SelfLearningCollector 배선 검증
P1-2: SceneMetricsCollector 기본값화 / DRSE 실 활성화 검증
"""
from __future__ import annotations
import pytest
from unittest.mock import MagicMock, patch


# ──────────────────────────────────────────────────────────────
# 공통 픽스처
# ──────────────────────────────────────────────────────────────

def _make_mock_bridge(text="씬 텍스트"):
    b = MagicMock()
    b.generate.return_value = text
    return b

def _make_seq_plans(count=2, scene_count=2):
    from literary_system.orchestrators.sequence_planner import SequencePlan, SequenceType
    return [
        SequencePlan(
            seq_id=f"seq_{i}",
            episode_no=1,
            seq_index=i,
            goal="테스트 목표",
            tension_target=0.7,
            scene_count=scene_count,
            act_index=0,
            pct_start=i / max(count, 1),
            pct_end=(i + 1) / max(count, 1),
            seq_type=SequenceType.CONFLICT_PEAK.value,
        )
        for i in range(count)
    ]

def _make_mae(consensus=True, score=0.8):
    mae = MagicMock()
    vote = MagicMock(); vote.score = score
    result = MagicMock()
    result.consensus = consensus
    result.votes = [vote, vote, vote]
    mae.evaluate.return_value = result
    return mae


# ──────────────────────────────────────────────────────────────
# P1-1: SelfLearningCollector 배선 테스트
# ──────────────────────────────────────────────────────────────

class TestV327P1SelfLearningCollector:
    """P1-1: SelfLearningCollector가 씬마다 자동 호출되는지 검증."""

    def test_collector_param_accepted(self):
        """SGO __init__이 collector 파라미터를 받아들임."""
        from literary_system.orchestrators.scene_generation_orchestrator import (
            SceneGenerationOrchestrator
        )
        from literary_system.trace.self_learning_collector import SelfLearningCollector
        import tempfile, os
        with tempfile.TemporaryDirectory() as d:
            collector = SelfLearningCollector(store_path=d)
            sgo = SceneGenerationOrchestrator(
                bridge=_make_mock_bridge(),
                collector=collector,
            )
            assert sgo._collector is collector

    def test_collector_none_by_default(self):
        """collector 없이 인스턴스화 가능 (하위 호환)."""
        from literary_system.orchestrators.scene_generation_orchestrator import (
            SceneGenerationOrchestrator
        )
        sgo = SceneGenerationOrchestrator(bridge=_make_mock_bridge())
        assert sgo._collector is None

    def test_collector_called_per_scene(self):
        """run_episode() 후 collector.record_count == 생성된 씬 수."""
        from literary_system.orchestrators.scene_generation_orchestrator import (
            SceneGenerationOrchestrator
        )
        from literary_system.trace.self_learning_collector import SelfLearningCollector
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            collector = SelfLearningCollector(store_path=d)
            seq_plans = _make_seq_plans(count=1, scene_count=3)
            sgo = SceneGenerationOrchestrator(
                bridge=_make_mock_bridge("씬 내용"),
                collector=collector,
                scene_metrics_collector=MagicMock(collect=MagicMock(
                    return_value=MagicMock(
                        drse_gate_pass_rate=1.0, character_state_valid=True,
                        reader_pull=0.7, reader_afterimage=0.6,
                        reader_uncertainty=0.3, reader_composite_score=0.5,
                        spatial_violation_count=0, relation_consistency=1.0,
                    )
                )),
            )
            result = sgo.run_episode(seq_plans, project_id="test", episode_no=1)
            assert result.total_scenes_generated == 3
            assert collector.record_count == 3

    def test_collector_receives_scene_record(self):
        """collector에 저장된 레코드가 SceneRecord 속성을 갖는다."""
        from literary_system.orchestrators.scene_generation_orchestrator import (
            SceneGenerationOrchestrator
        )
        from literary_system.trace.self_learning_collector import SelfLearningCollector
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            collector = SelfLearningCollector(store_path=d)
            seq_plans = _make_seq_plans(count=1, scene_count=1)
            sgo = SceneGenerationOrchestrator(
                bridge=_make_mock_bridge("테스트 씬 텍스트입니다."),
                collector=collector,
            )
            sgo.run_episode(seq_plans, episode_no=5)
            assert collector.record_count == 1
            slm = collector._records[0]
            assert slm.episode_no == 5
            assert slm.scene_text == "테스트 씬 텍스트입니다."

    def test_collector_episode_no_synced(self):
        """episode_no가 SLMRecord에 정확히 전달된다."""
        from literary_system.orchestrators.scene_generation_orchestrator import (
            SceneGenerationOrchestrator
        )
        from literary_system.trace.self_learning_collector import SelfLearningCollector
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            collector = SelfLearningCollector(store_path=d)
            sgo = SceneGenerationOrchestrator(
                bridge=_make_mock_bridge(),
                collector=collector,
            )
            sgo.run_episode(_make_seq_plans(1, 2), episode_no=7)
            for rec in collector._records:
                assert rec.episode_no == 7

    def test_collector_error_doesnt_break_pipeline(self):
        """collector가 예외를 던져도 씬 생성이 계속된다."""
        from literary_system.orchestrators.scene_generation_orchestrator import (
            SceneGenerationOrchestrator
        )
        broken = MagicMock()
        broken.collect.side_effect = RuntimeError("의도적 오류")
        sgo = SceneGenerationOrchestrator(
            bridge=_make_mock_bridge(),
            collector=broken,
        )
        result = sgo.run_episode(_make_seq_plans(1, 2), episode_no=1)
        assert result.success is True
        assert result.total_scenes_generated == 2

    def test_no_collector_pipeline_unchanged(self):
        """collector=None일 때 기존 결과와 동일하게 작동."""
        from literary_system.orchestrators.scene_generation_orchestrator import (
            SceneGenerationOrchestrator
        )
        seq_plans = _make_seq_plans(2, 2)
        sgo = SceneGenerationOrchestrator(bridge=_make_mock_bridge())
        result = sgo.run_episode(seq_plans)
        assert result.total_scenes_generated == 4
        assert result.success is True

    def test_jsonl_file_created(self):
        """씬 수집 후 JSONL 파일이 실제 생성된다."""
        from literary_system.orchestrators.scene_generation_orchestrator import (
            SceneGenerationOrchestrator
        )
        from literary_system.trace.self_learning_collector import SelfLearningCollector
        import tempfile, os
        with tempfile.TemporaryDirectory() as d:
            collector = SelfLearningCollector(store_path=d)
            sgo = SceneGenerationOrchestrator(
                bridge=_make_mock_bridge("JSONL 테스트"),
                collector=collector,
            )
            sgo.run_episode(_make_seq_plans(1, 1))
            jsonl = os.path.join(d, "slm_records.jsonl")
            assert os.path.exists(jsonl)
            with open(jsonl) as f:
                lines = f.readlines()
            assert len(lines) == 1


# ──────────────────────────────────────────────────────────────
# P1-2: SceneMetricsCollector 기본값화 / DRSE 실 활성화
# ──────────────────────────────────────────────────────────────

class TestV327P2SceneMetricsDefault:
    """P1-2: SceneMetricsCollector 기본값화 및 collect() 메서드 검증."""

    def test_metrics_collector_has_collect_method(self):
        """SceneMetricsCollector가 collect(scene_id, text) 메서드를 갖는다."""
        from literary_system.evaluation.scene_metrics_collector import SceneMetricsCollector
        col = SceneMetricsCollector()
        assert hasattr(col, "collect")
        assert callable(col.collect)

    def test_collect_returns_scene_metrics(self):
        """collect()가 SceneMetrics 인스턴스를 반환한다."""
        from literary_system.evaluation.scene_metrics_collector import (
            SceneMetricsCollector, SceneMetrics
        )
        col = SceneMetricsCollector()
        metrics = col.collect("scene_001", "테스트 씬 텍스트")
        assert isinstance(metrics, SceneMetrics)
        assert metrics.scene_id == "scene_001"

    def test_collect_reader_pull_scales_with_text_length(self):
        """reader_pull이 텍스트 길이에 비례한다."""
        from literary_system.evaluation.scene_metrics_collector import SceneMetricsCollector
        col = SceneMetricsCollector()
        short  = col.collect("s1", "짧은 텍스트")
        long_  = col.collect("s2", "긴 텍스트입니다. " * 100)
        assert long_.reader_pull >= short.reader_pull

    def test_collect_empty_text(self):
        """빈 텍스트도 정상 처리."""
        from literary_system.evaluation.scene_metrics_collector import SceneMetricsCollector
        col = SceneMetricsCollector()
        m = col.collect("empty", "")
        assert 0.0 <= m.reader_pull <= 1.0

    def test_sgo_metrics_col_not_none_by_default(self):
        """SGO 기본 생성 시 metrics_col이 None이 아닐 수 있다 (DRSE 가용 시)."""
        from literary_system.orchestrators.scene_generation_orchestrator import (
            SceneGenerationOrchestrator, _DRSE_AVAILABLE
        )
        sgo = SceneGenerationOrchestrator(bridge=_make_mock_bridge())
        if _DRSE_AVAILABLE:
            assert sgo.metrics_col is not None
        else:
            # DRSE 불가 환경에서는 None도 허용
            pass

    def test_collect_metrics_uses_real_instance(self):
        """_collect_metrics()가 실 SceneMetricsCollector를 사용하면 _DefaultSceneMetrics가 아닌 SceneMetrics를 반환."""
        from literary_system.orchestrators.scene_generation_orchestrator import (
            SceneGenerationOrchestrator, _DRSE_AVAILABLE
        )
        from literary_system.evaluation.scene_metrics_collector import SceneMetrics
        if not _DRSE_AVAILABLE:
            pytest.skip("DRSE 환경 없음")
        sgo = SceneGenerationOrchestrator(bridge=_make_mock_bridge())
        result = sgo._collect_metrics("test_scene", "충분히 긴 텍스트 " * 20)
        assert isinstance(result, SceneMetrics)

    def test_dummy_metrics_no_longer_default_path(self):
        """실 collector 있으면 _DefaultSceneMetrics 경로에 도달하지 않는다."""
        from literary_system.orchestrators.scene_generation_orchestrator import (
            SceneGenerationOrchestrator, _DefaultSceneMetrics, _DRSE_AVAILABLE
        )
        if not _DRSE_AVAILABLE:
            pytest.skip("DRSE 환경 없음")
        sgo = SceneGenerationOrchestrator(bridge=_make_mock_bridge())
        result = sgo._collect_metrics("s", "텍스트")
        assert not isinstance(result, _DefaultSceneMetrics), \
            "dummy metrics 경로에 도달함 — P1-2 실패"

    def test_explicit_none_falls_back_gracefully(self):
        """scene_metrics_collector=None 명시 시 폴백 정상 작동."""
        from literary_system.orchestrators.scene_generation_orchestrator import (
            SceneGenerationOrchestrator
        )
        sgo = SceneGenerationOrchestrator(
            bridge=_make_mock_bridge(),
            scene_metrics_collector=None,
        )
        # DRSE 사용 가능하면 기본값으로 교체됨, 아니면 None
        result = sgo._collect_metrics("s", "텍스트")
        assert result is not None  # 어떤 경우든 결과 반환


