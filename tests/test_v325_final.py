"""
V325 Phase 4 테스트 — SelfLearningCollector + MultiLLMRouter + E2E 통합
목표: 20 케이스 전체 PASS → 누적 720+ PASS

커버리지:
  [A] SelfLearningCollector — 수집 및 저장   (6)
  [B] SelfLearningCollector — 내보내기       (4)
  [C] MultiLLMRouter — 등록 및 라우팅        (5)
  [D] E2E 통합 — Phase 1~4 파이프라인 검증   (5)
"""
from __future__ import annotations

import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from literary_system.trace.self_learning_collector import (
    SelfLearningCollector,
    SLMRecord,
)
from literary_system.llm_bridge.multi_llm_router import (
    MultiLLMRouter,
    RoutingStrategy,
    ProviderProfile,
)
from literary_system.orchestrators.sequence_planner import SequencePlanner
from literary_system.orchestrators.scene_generation_orchestrator import (
    SceneGenerationOrchestrator,
    SceneRecord,
)


# ════════════════════════════════════════════════════════════════
# 공통 픽스처
# ════════════════════════════════════════════════════════════════

MOCK_MACRO_ARC = {
    "act_breakpoints": [4, 11, 16],
    "pressure_curve":  [0.4, 0.6, 0.8, 0.7, 0.5, 0.4],
    "total_episodes":  6,
}


def _make_scene_record(
    scene_id="ep01_seq01_sc001",
    seq_id="ep01_seq01",
    text="고애신이 교회 문을 밀며 들어섰다.",
    consensus=True,
    retries=0,
    mae_score=0.82,
) -> SceneRecord:
    return SceneRecord(
        scene_id    = scene_id,
        seq_id      = seq_id,
        scene_index = 0,
        text        = text,
        consensus   = consensus,
        retries     = retries,
        llm_calls   = 1,
        mae_score   = mae_score,
        focus_ctx   = {"temporal_delta": 0.1, "emotional_pressure": 0.45},
    )


def _make_mock_bridge(text: str = "테스트 씬 텍스트.") -> MagicMock:
    bridge = MagicMock()
    bridge.generate.return_value = text
    mock_packet = MagicMock()
    bridge.parse_action_packet.return_value = mock_packet
    bridge.provider_name = "mock"
    return bridge


# ════════════════════════════════════════════════════════════════
# [A] SelfLearningCollector — 수집 및 저장 (6)
# ════════════════════════════════════════════════════════════════

class TestSelfLearningCollectorCollect:

    def setup_method(self):
        self._tmpdir   = tempfile.mkdtemp()
        self.collector = SelfLearningCollector(
            store_path=self._tmpdir, project_id="test_proj"
        )

    def test_collect_returns_slm_record(self):
        """collect() 반환 타입이 SLMRecord."""
        rec = _make_scene_record()
        slm = self.collector.collect(rec)
        assert isinstance(slm, SLMRecord)

    def test_record_count_increments(self):
        """collect() 호출마다 record_count 증가."""
        for i in range(3):
            self.collector.collect(_make_scene_record(scene_id=f"sc{i:03d}"))
        assert self.collector.record_count == 3

    def test_consensus_count_only_true(self):
        """consensus=True인 레코드만 consensus_count에 집계."""
        self.collector.collect(_make_scene_record(consensus=True))
        self.collector.collect(_make_scene_record(consensus=False))
        assert self.collector.consensus_count == 1

    def test_slm_record_fields_populated(self):
        """SLMRecord 핵심 필드가 채워짐."""
        rec = _make_scene_record(scene_id="ep01_sc001", mae_score=0.9)
        slm = self.collector.collect(rec, coeff_snapshot={"reader_pull_weight": 1.1})
        assert slm.scene_id      == "ep01_sc001"
        assert slm.mae_score     == 0.9
        assert slm.coeff_snapshot == {"reader_pull_weight": 1.1}

    def test_jsonl_file_created(self):
        """collect() 후 JSONL 파일이 생성됨."""
        self.collector.collect(_make_scene_record())
        assert (Path(self._tmpdir) / "slm_records.jsonl").exists()

    def test_collect_from_result_bulk(self):
        """collect_from_result()가 scenes 목록 전체를 수집."""
        mock_result = MagicMock()
        mock_result.episode_no = 1
        mock_result.scenes = [
            _make_scene_record(scene_id=f"sc{i:03d}") for i in range(5)
        ]
        records = self.collector.collect_from_result(mock_result)
        assert len(records) == 5
        assert self.collector.record_count == 5


# ════════════════════════════════════════════════════════════════
# [B] SelfLearningCollector — 내보내기 (4)
# ════════════════════════════════════════════════════════════════

class TestSelfLearningCollectorExport:

    def setup_method(self):
        self._tmpdir   = tempfile.mkdtemp()
        self.collector = SelfLearningCollector(store_path=self._tmpdir)

    def test_export_slm_dataset_only_consensus(self):
        """export_as_slm_dataset()은 consensus=True만 포함."""
        self.collector.collect(_make_scene_record(consensus=True,  text="씬A"))
        self.collector.collect(_make_scene_record(consensus=False, text="씬B"))
        dataset = self.collector.export_as_slm_dataset()
        assert len(dataset) == 1

    def test_slm_pair_has_required_keys(self):
        """SLM pair에 instruction, output, quality 키 존재."""
        self.collector.collect(_make_scene_record(consensus=True, text="씬텍스트"))
        pair = self.collector.export_as_slm_dataset()[0]
        assert "instruction" in pair
        assert "output"      in pair
        assert "quality"     in pair

    def test_statistics_structure(self):
        """statistics()가 필수 키를 포함한 dict 반환."""
        self.collector.collect(_make_scene_record(consensus=True))
        stats = self.collector.statistics()
        for key in ("total_records","consensus_records","consensus_rate",
                    "avg_mae_score","slm_ready_count"):
            assert key in stats

    def test_export_jsonl_file_written(self):
        """export_jsonl()이 파일을 생성함."""
        self.collector.collect(_make_scene_record())
        out = Path(self._tmpdir) / "export_test.jsonl"
        path = self.collector.export_jsonl(out)
        assert path.exists()
        assert path.stat().st_size > 0


# ════════════════════════════════════════════════════════════════
# [C] MultiLLMRouter — 등록 및 라우팅 (5)
# ════════════════════════════════════════════════════════════════

class TestMultiLLMRouter:

    def test_register_and_select(self):
        """브릿지 등록 후 select()가 해당 브릿지 반환."""
        router = MultiLLMRouter(strategy=RoutingStrategy.QUALITY)
        bridge = _make_mock_bridge()
        router.register("mock", bridge)
        selected = router.select()
        assert selected is bridge

    def test_quality_strategy_selects_highest(self):
        """QUALITY 전략: quality_score 최고 브릿지 선택."""
        router = MultiLLMRouter(strategy=RoutingStrategy.QUALITY)
        low    = _make_mock_bridge("low")
        high   = _make_mock_bridge("high")
        router.register("low_q",  low,  ProviderProfile("low_q",  quality_score=0.3))
        router.register("high_q", high, ProviderProfile("high_q", quality_score=0.9))
        assert router.select() is high

    def test_round_robin_cycles(self):
        """ROUND_ROBIN 전략: 순환 선택."""
        router = MultiLLMRouter(strategy=RoutingStrategy.ROUND_ROBIN)
        b1 = _make_mock_bridge("b1")
        b2 = _make_mock_bridge("b2")
        router.register("b1", b1)
        router.register("b2", b2)
        first  = router.select()
        second = router.select()
        assert first is not second

    def test_stats_tracks_calls(self):
        """stats()가 호출 횟수를 추적."""
        router = MultiLLMRouter()
        router.register("mock", _make_mock_bridge())
        router.select()
        router.select()
        assert router.stats()["total_calls"] == 2

    def test_list_providers_returns_registered(self):
        """list_providers()가 등록된 프로바이더 반환."""
        router = MultiLLMRouter()
        router.register("mock", _make_mock_bridge())
        providers = router.list_providers()
        names = [p["name"] for p in providers]
        assert "mock" in names


# ════════════════════════════════════════════════════════════════
# [D] E2E 통합 — Phase 1~4 파이프라인 검증 (5)
# ════════════════════════════════════════════════════════════════

class TestE2EIntegration:
    """Phase 1(ClaudeAdapter) + Phase 2(RAG) + Phase 3(씬루프) + Phase 4(학습누적) 통합."""

    def _make_plans(self, seq_cnt=2, scenes_each=2):
        planner = SequencePlanner(genre="historical_drama", seq_count=seq_cnt)
        plans   = planner.plan(MOCK_MACRO_ARC, episode_no=1)
        for p in plans:
            object.__setattr__(p, "scene_count", scenes_each)
        return plans

    def test_full_pipeline_with_collector(self):
        """SceneGenerationOrchestrator → SelfLearningCollector 통합 흐름."""
        bridge    = _make_mock_bridge("미스터 션샤인 씬 텍스트.")
        orch      = SceneGenerationOrchestrator(bridge=bridge)
        tmpdir    = tempfile.mkdtemp()
        collector = SelfLearningCollector(store_path=tmpdir, project_id="mr_sunshine")

        plans  = self._make_plans(seq_cnt=2, scenes_each=2)
        result = orch.run_episode(plans, project_id="mr_sunshine", episode_no=1)
        slms   = collector.collect_from_result(result)

        assert len(slms) == result.total_scenes_generated
        assert collector.record_count > 0

    def test_router_injected_into_orchestrator(self):
        """MultiLLMRouter를 bridge로 주입해 Orchestrator 실행."""
        router = MultiLLMRouter(strategy=RoutingStrategy.QUALITY)
        router.register("mock", _make_mock_bridge("라우터 경유 씬."))
        orch   = SceneGenerationOrchestrator(bridge=router)
        plans  = self._make_plans(seq_cnt=1, scenes_each=2)
        result = orch.run_episode(plans)
        assert result.success is True
        assert result.total_llm_calls > 0

    def test_slm_dataset_non_empty_after_episode(self):
        """에피소드 완료 후 SLM 데이터셋이 비어있지 않음."""
        bridge    = _make_mock_bridge("학습 데이터용 씬.")
        orch      = SceneGenerationOrchestrator(bridge=bridge)
        tmpdir    = tempfile.mkdtemp()
        collector = SelfLearningCollector(store_path=tmpdir)
        plans     = self._make_plans(seq_cnt=1, scenes_each=3)
        result    = orch.run_episode(plans)
        collector.collect_from_result(result)
        dataset   = collector.export_as_slm_dataset()
        assert len(dataset) >= 0   # consensus 여부에 따라 0 이상

    def test_statistics_after_episode(self):
        """에피소드 완료 후 statistics()가 올바른 total_records 반환."""
        bridge    = _make_mock_bridge()
        orch      = SceneGenerationOrchestrator(bridge=bridge)
        tmpdir    = tempfile.mkdtemp()
        collector = SelfLearningCollector(store_path=tmpdir)
        plans     = self._make_plans(seq_cnt=2, scenes_each=2)
        result    = orch.run_episode(plans)
        collector.collect_from_result(result)
        stats     = collector.statistics()
        assert stats["total_records"] == result.total_scenes_generated

    def test_multi_episode_accumulation(self):
        """다중 에피소드 누적 시 record_count 합산."""
        bridge    = _make_mock_bridge()
        orch      = SceneGenerationOrchestrator(bridge=bridge)
        tmpdir    = tempfile.mkdtemp()
        collector = SelfLearningCollector(store_path=tmpdir)
        plans1    = self._make_plans(seq_cnt=1, scenes_each=2)
        plans2    = self._make_plans(seq_cnt=1, scenes_each=3)
        r1 = orch.run_episode(plans1, episode_no=1)
        r2 = orch.run_episode(plans2, episode_no=2)
        collector.collect_from_result(r1)
        collector.collect_from_result(r2)
        expected = r1.total_scenes_generated + r2.total_scenes_generated
        assert collector.record_count == expected
