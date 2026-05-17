"""
tests/test_v382_pipeline_survival.py
=====================================
Literary OS V382 — 파이프라인 구조 보증 + 핵심 로직 생존 매트릭스 테스트

SOVEREIGN_OS V305 test_sovereign_core.py 패턴을 Literary OS에 이식:
  1. TestPipelineStateModule       — LiteraryPipelineState + trace 유틸리티
  2. TestCheckpointSystem          — save/restore/autosave 체크포인트
  3. TestPipelineStructureGuarantee — 소스 파일 구조 검증 (src.index 패턴)
  4. TestCoreLogicSurvival         — 실제 실행 trace 기반 핵심 모듈 생존 확인
  5. TestForbiddenPatterns         — 금지 패턴 코드베이스 침투 방지
  6. TestMinimalPipelineIntegration — run_minimal_pipeline() 통합 검증
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# 경로 설정
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

ORCHESTRATOR_PY = ROOT / "literary_system" / "orchestrators" / "build_opening_orchestrator.py"
PIPELINE_PY     = ROOT / "literary_system" / "pipeline" / "pipeline_state.py"


# ─────────────────────────────────────────────────────────────────────────────
# 1. TestPipelineStateModule
# ─────────────────────────────────────────────────────────────────────────────
class TestPipelineStateModule:
    """LiteraryPipelineState와 append_trace() 기본 동작 검증."""

    def test_state_has_execution_trace(self):
        from literary_system.pipeline import LiteraryPipelineState
        s = LiteraryPipelineState()
        assert hasattr(s, "execution_trace")
        assert isinstance(s.execution_trace, list)
        assert s.execution_trace == []

    def test_state_has_checkpoints(self):
        from literary_system.pipeline import LiteraryPipelineState
        s = LiteraryPipelineState()
        assert hasattr(s, "checkpoints")
        assert isinstance(s.checkpoints, dict)

    def test_state_has_last_good_node(self):
        from literary_system.pipeline import LiteraryPipelineState
        s = LiteraryPipelineState()
        assert hasattr(s, "last_good_node")
        assert s.last_good_node == ""

    def test_state_has_run_id(self):
        from literary_system.pipeline import LiteraryPipelineState
        s = LiteraryPipelineState()
        assert s.run_id.startswith("run_")
        assert len(s.run_id) > 4

    def test_run_ids_are_unique(self):
        from literary_system.pipeline import LiteraryPipelineState
        ids = {LiteraryPipelineState().run_id for _ in range(20)}
        assert len(ids) == 20

    def test_append_trace_records_message(self):
        from literary_system.pipeline import LiteraryPipelineState, append_trace
        s = LiteraryPipelineState()
        append_trace(s, "[TestNode] 테스트 노드 시작")
        assert len(s.execution_trace) == 1
        assert "[TestNode] 테스트 노드 시작" in s.execution_trace[0]

    def test_append_trace_includes_timestamp(self):
        from literary_system.pipeline import LiteraryPipelineState, append_trace
        s = LiteraryPipelineState()
        append_trace(s, "타임스탬프 테스트")
        # 형식: [HH:MM:SS.mmm] 메시지
        assert s.execution_trace[0].startswith("[")
        assert "]" in s.execution_trace[0]

    def test_append_trace_accumulates(self):
        from literary_system.pipeline import LiteraryPipelineState, append_trace
        s = LiteraryPipelineState()
        for i in range(5):
            append_trace(s, f"[Node_{i}] 노드 {i} 실행")
        assert len(s.execution_trace) == 5

    def test_prune_trace_keeps_recent(self):
        from literary_system.pipeline import LiteraryPipelineState, append_trace, prune_trace
        s = LiteraryPipelineState()
        for i in range(200):
            append_trace(s, f"entry_{i}")
        prune_trace(s, keep=50)
        assert len(s.execution_trace) == 50
        # 최신 항목이 유지되어야 함
        assert "entry_199" in s.execution_trace[-1]

    def test_status_default_running(self):
        from literary_system.pipeline import LiteraryPipelineState
        s = LiteraryPipelineState()
        assert s.status == "running"


# ─────────────────────────────────────────────────────────────────────────────
# 2. TestCheckpointSystem
# ─────────────────────────────────────────────────────────────────────────────
class TestCheckpointSystem:
    """save_literary_checkpoint / restore_literary_checkpoint 검증."""

    def test_save_checkpoint_stores_fields(self):
        from literary_system.pipeline import (
            LiteraryPipelineState, append_trace, save_literary_checkpoint
        )
        s = LiteraryPipelineState(project_id="test_proj", arc_node_count=16)
        s.execution_trace = []
        save_literary_checkpoint(s, "node_arc", ["project_id", "arc_node_count"])
        assert "node_arc" in s.checkpoints
        assert s.checkpoints["node_arc"]["project_id"] == "test_proj"
        assert s.checkpoints["node_arc"]["arc_node_count"] == 16

    def test_save_checkpoint_updates_last_good_node(self):
        from literary_system.pipeline import (
            LiteraryPipelineState, append_trace, save_literary_checkpoint
        )
        s = LiteraryPipelineState()
        s.execution_trace = []
        save_literary_checkpoint(s, "node_knowledge", ["run_id"])
        assert s.last_good_node == "node_knowledge"

    def test_save_checkpoint_records_trace(self):
        from literary_system.pipeline import (
            LiteraryPipelineState, append_trace, save_literary_checkpoint
        )
        s = LiteraryPipelineState()
        s.execution_trace = []
        save_literary_checkpoint(s, "node_x", ["run_id"])
        trace_text = "\n".join(s.execution_trace)
        assert "checkpoint saved: node_x" in trace_text

    def test_restore_checkpoint_restores_values(self):
        from literary_system.pipeline import (
            LiteraryPipelineState, append_trace,
            save_literary_checkpoint, restore_literary_checkpoint
        )
        s = LiteraryPipelineState(arc_node_count=8)
        s.execution_trace = []
        save_literary_checkpoint(s, "before_change", ["arc_node_count"])
        s.arc_node_count = 999  # 변조
        restore_literary_checkpoint(s, "before_change")
        assert s.arc_node_count == 8

    def test_restore_missing_checkpoint_returns_false(self):
        from literary_system.pipeline import (
            LiteraryPipelineState, restore_literary_checkpoint
        )
        s = LiteraryPipelineState()
        s.execution_trace = []
        result = restore_literary_checkpoint(s, "nonexistent_checkpoint")
        assert result is False

    def test_restore_existing_checkpoint_returns_true(self):
        from literary_system.pipeline import (
            LiteraryPipelineState, append_trace,
            save_literary_checkpoint, restore_literary_checkpoint
        )
        s = LiteraryPipelineState()
        s.execution_trace = []
        save_literary_checkpoint(s, "exists", ["run_id"])
        result = restore_literary_checkpoint(s, "exists")
        assert result is True

    def test_autosave_creates_file(self, tmp_path):
        from literary_system.pipeline import (
            LiteraryPipelineState, append_trace, autosave_literary_state
        )
        s = LiteraryPipelineState(out_root=str(tmp_path))
        s.execution_trace = []
        path = autosave_literary_state(s, "test_label", out_root=str(tmp_path))
        assert path is not None
        assert Path(path).exists()

    def test_autosave_contains_status(self, tmp_path):
        import json
        from literary_system.pipeline import (
            LiteraryPipelineState, append_trace, autosave_literary_state
        )
        s = LiteraryPipelineState(out_root=str(tmp_path))
        s.execution_trace = []
        path = autosave_literary_state(s, "completed_label",
                                        status="completed", out_root=str(tmp_path))
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        assert data["status"] == "completed"
        assert data["checkpoint_label"] == "completed_label"

    def test_multiple_checkpoints_independent(self):
        from literary_system.pipeline import (
            LiteraryPipelineState, append_trace, save_literary_checkpoint
        )
        s = LiteraryPipelineState(arc_node_count=4, budget_episodes=2)
        s.execution_trace = []
        save_literary_checkpoint(s, "cp1", ["arc_node_count"])
        s.arc_node_count = 16
        save_literary_checkpoint(s, "cp2", ["arc_node_count", "budget_episodes"])
        assert s.checkpoints["cp1"]["arc_node_count"] == 4
        assert s.checkpoints["cp2"]["arc_node_count"] == 16


# ─────────────────────────────────────────────────────────────────────────────
# 3. TestPipelineStructureGuarantee
# ─────────────────────────────────────────────────────────────────────────────
class TestPipelineStructureGuarantee:
    """
    소스 파일을 직접 읽어 파이프라인 구조를 검증.

    SOVEREIGN_OS V305 패턴:
      src.index("X") < src.index("Y")  →  X가 Y보다 먼저 파이프라인에 위치
    """

    def _orch_src(self) -> str:
        return ORCHESTRATOR_PY.read_text(encoding="utf-8")

    def _pipeline_src(self) -> str:
        return PIPELINE_PY.read_text(encoding="utf-8")

    # ── 필수 임포트 ───────────────────────────────────────────────────────
    def test_orchestrator_imports_pipeline(self):
        src = self._orch_src()
        assert "from literary_system.pipeline import" in src, \
            "build_opening_orchestrator가 pipeline 모듈을 import하지 않음"

    def test_orchestrator_imports_append_trace(self):
        src = self._orch_src()
        assert "append_trace" in src

    def test_orchestrator_imports_save_checkpoint(self):
        src = self._orch_src()
        assert "save_literary_checkpoint" in src

    # ── 파이프라인 내 노드 순서 ───────────────────────────────────────────
    def test_seed_compiler_before_style_engine(self):
        src = self._orch_src()
        seed_pos  = src.index("Node_SeedCompiler")
        style_pos = src.index("Node_StyleDNAEngine")
        assert seed_pos < style_pos, "SeedCompiler가 StyleDNAEngine 이후에 위치"

    def test_style_engine_before_v312_bridge(self):
        src = self._orch_src()
        style_pos  = src.index("Node_StyleDNAEngine")
        bridge_pos = src.index("Node_V312Bridge")
        assert style_pos < bridge_pos, "StyleDNAEngine이 V312Bridge 이후에 위치"

    def test_v312_bridge_before_episodes(self):
        src = self._orch_src()
        bridge_pos  = src.index("Node_V312Bridge")
        episode_pos = src.index("Node_Episode_")
        assert bridge_pos < episode_pos, "V312Bridge가 에피소드 루프 이후에 위치"

    def test_run_quick_has_pipeline_state_init(self):
        src = self._orch_src()
        assert "LiteraryPipelineState()" in src or \
               "LiteraryPipelineState(project_id" in src, \
            "run_quick에 LiteraryPipelineState 초기화 없음"

    def test_run_quick_returns_pipeline_trace(self):
        src = self._orch_src()
        assert "pipeline_trace" in src, \
            "run_quick 반환값에 pipeline_trace 없음"

    def test_run_quick_returns_pipeline_checkpoints(self):
        src = self._orch_src()
        assert "pipeline_checkpoints" in src

    # ── pipeline_state.py 내부 구조 ───────────────────────────────────────
    def test_pipeline_state_has_run_minimal_pipeline(self):
        src = self._pipeline_src()
        assert "def run_minimal_pipeline(" in src

    def test_minimal_pipeline_calls_series_arc_planner(self):
        src = self._pipeline_src()
        assert "SeriesArcPlanner" in src

    def test_minimal_pipeline_calls_causal_plot_graph(self):
        src = self._pipeline_src()
        assert "CausalPlotGraph" in src

    def test_minimal_pipeline_calls_episode_reveal_budget(self):
        src = self._pipeline_src()
        assert "EpisodeRevealBudget" in src

    def test_minimal_pipeline_calls_knowledge_tracker(self):
        src = self._pipeline_src()
        assert "KnowledgeStateTracker" in src

    def test_minimal_pipeline_calls_prose_bridge(self):
        src = self._pipeline_src()
        assert "CharacterKnowledgeProseBridge" in src

    def test_node_order_in_minimal_pipeline(self):
        """최소 파이프라인 내 노드 순서 검증."""
        src = self._pipeline_src()
        arc_pos      = src.index("Node_SeriesArcPlanner")
        causal_pos   = src.index("Node_CausalPlotGraph")
        budget_pos   = src.index("Node_EpisodeRevealBudget")
        tracker_pos  = src.index("Node_KnowledgeStateTracker")
        bridge_pos   = src.index("Node_CharacterKnowledgeProseBridge")
        assert arc_pos < causal_pos,  "SeriesArcPlanner가 CausalPlotGraph 이후에 위치"
        assert causal_pos < budget_pos, "CausalPlotGraph가 EpisodeRevealBudget 이후에 위치"
        assert budget_pos < tracker_pos, "EpisodeRevealBudget이 KnowledgeStateTracker 이후에 위치"
        assert tracker_pos < bridge_pos, "KnowledgeStateTracker가 ProseBridge 이후에 위치"

    def test_autosave_called_after_each_node(self):
        """최소 파이프라인에서 각 노드 후 autosave 호출."""
        src = self._pipeline_src()
        # 각 핵심 노드 이름 다음에 autosave가 나타나는지 확인
        nodes = ["series_arc_planner", "causal_plot_graph",
                 "episode_reveal_budget", "knowledge_state_tracker"]
        for node in nodes:
            idx = src.index(f'"{node}"')
            snippet = src[idx:idx + 300]
            assert "autosave_literary_state" in snippet, \
                f"Node {node} 후 autosave 없음"


# ─────────────────────────────────────────────────────────────────────────────
# 4. TestCoreLogicSurvival
# ─────────────────────────────────────────────────────────────────────────────
class TestCoreLogicSurvival:
    """
    run_minimal_pipeline() 실제 실행 후 execution_trace를 검사.
    모든 핵심 모듈이 파이프라인에서 실제로 실행됐음을 보증.

    이것이 "조용한 죽음" 방지의 핵심이다:
    모듈이 존재해도 실행되지 않으면 FAIL.
    """

    @pytest.fixture(scope="class")
    def pipeline_result(self, tmp_path_factory):
        from literary_system.pipeline import run_minimal_pipeline
        tmp = tmp_path_factory.mktemp("v382_survival")
        return run_minimal_pipeline(
            seed_text="생존 매트릭스 테스트 — 형사가 진실을 추적한다",
            episodes=2,
            out_root=str(tmp),
        )

    def test_pipeline_completes(self, pipeline_result):
        assert pipeline_result.status == "completed"

    def test_execution_trace_not_empty(self, pipeline_result):
        assert len(pipeline_result.execution_trace) > 0

    def test_seed_compiler_survives(self, pipeline_result):
        trace = "\n".join(pipeline_result.execution_trace)
        assert "Node_SeedCompiler" in trace, \
            "SeedCompiler가 파이프라인에서 실행되지 않음 — 조용한 죽음 감지"

    def test_series_arc_planner_survives(self, pipeline_result):
        trace = "\n".join(pipeline_result.execution_trace)
        assert "SeriesArcPlanner" in trace, \
            "SeriesArcPlanner가 파이프라인에서 실행되지 않음 — 조용한 죽음 감지"

    def test_causal_plot_graph_survives(self, pipeline_result):
        trace = "\n".join(pipeline_result.execution_trace)
        assert "CausalPlotGraph" in trace, \
            "CausalPlotGraph가 파이프라인에서 실행되지 않음 — 조용한 죽음 감지"

    def test_episode_reveal_budget_survives(self, pipeline_result):
        trace = "\n".join(pipeline_result.execution_trace)
        assert "EpisodeRevealBudget" in trace, \
            "EpisodeRevealBudget이 파이프라인에서 실행되지 않음 — 조용한 죽음 감지"

    def test_knowledge_state_tracker_survives(self, pipeline_result):
        trace = "\n".join(pipeline_result.execution_trace)
        assert "KnowledgeStateTracker" in trace, \
            "KnowledgeStateTracker가 파이프라인에서 실행되지 않음 — 조용한 죽음 감지"

    def test_character_knowledge_prose_bridge_survives(self, pipeline_result):
        trace = "\n".join(pipeline_result.execution_trace)
        assert "CharacterKnowledgeProseBridge" in trace, \
            "CharacterKnowledgeProseBridge가 파이프라인에서 실행되지 않음 — 조용한 죽음 감지"

    def test_all_6_checkpoints_saved(self, pipeline_result):
        """6개 핵심 노드 모두 체크포인트가 저장됐는지 확인."""
        REQUIRED_CHECKPOINTS = [
            "seed_compiler", "series_arc_planner", "causal_plot_graph",
            "episode_reveal_budget", "knowledge_state_tracker",
            "character_knowledge_prose_bridge",
        ]
        for cp in REQUIRED_CHECKPOINTS:
            assert cp in pipeline_result.checkpoints, \
                f"체크포인트 '{cp}' 없음 — 해당 노드가 실행되지 않았거나 checkpoint 저장 누락"

    def test_arc_node_count_positive(self, pipeline_result):
        """SeriesArcPlanner가 실제로 노드를 생성했는지 확인."""
        assert pipeline_result.arc_node_count > 0, \
            "SeriesArcPlanner가 아크 노드를 생성하지 않음"

    def test_knowledge_facts_registered(self, pipeline_result):
        """KnowledgeStateTracker가 실제로 사실을 등록했는지 확인."""
        assert pipeline_result.knowledge_facts > 0, \
            "KnowledgeStateTracker에 등록된 사실 없음"

    def test_pipeline_completion_traced(self, pipeline_result):
        """파이프라인 완료 흔적이 있는지 확인."""
        trace = "\n".join(pipeline_result.execution_trace)
        assert "Pipeline" in trace and "완료" in trace, \
            "파이프라인 완료 흔적 없음"

    def test_last_good_node_set(self, pipeline_result):
        """마지막으로 성공한 노드가 기록됐는지 확인."""
        assert pipeline_result.last_good_node != "", \
            "last_good_node가 설정되지 않음"

    def test_disk_autosave_created(self, pipeline_result):
        """디스크 autosave가 실제로 생성됐는지 확인."""
        assert pipeline_result.last_disk_checkpoint_path != "", \
            "disk autosave 경로가 없음"
        # 파일이 실제 존재하는지 확인
        path = Path(pipeline_result.last_disk_checkpoint_path)
        assert path.exists(), f"autosave 파일이 존재하지 않음: {path}"


# ─────────────────────────────────────────────────────────────────────────────
# 5. TestForbiddenPatterns
# ─────────────────────────────────────────────────────────────────────────────
class TestForbiddenPatterns:
    """
    금지 패턴이 코드베이스에 침투하지 않았는지 검증.
    SOVEREIGN_OS V305의 'not in src' 패턴 이식.
    """

    def test_no_direct_openai_call_in_orchestrator(self):
        """LLM-0 원칙: 오케스트레이터에서 OpenAI 직접 호출 금지."""
        src = ORCHESTRATOR_PY.read_text(encoding="utf-8")
        assert "openai.ChatCompletion" not in src
        assert "openai.chat.completions.create" not in src

    def test_no_direct_anthropic_call_in_orchestrator(self):
        """LLM-0 원칙: 오케스트레이터에서 Anthropic 직접 호출 금지."""
        src = ORCHESTRATOR_PY.read_text(encoding="utf-8")
        assert "anthropic.messages.create" not in src
        assert "client.messages.create" not in src

    def test_no_global_state_in_pipeline(self):
        """파이프라인 상태를 모듈 전역 변수로 저장 금지."""
        src = PIPELINE_PY.read_text(encoding="utf-8")
        # 전역 수준 _state = LiteraryPipelineState() 패턴 금지
        for i, line in enumerate(src.splitlines()):
            if "_state = LiteraryPipelineState()" in line:
                assert line.startswith("    ") or line.startswith("\t"), \
                    f"전역 파이프라인 상태 감지 L{i+1}: {line.strip()}"

    def test_no_blocking_sleep_in_pipeline(self):
        """파이프라인 동기 차단 금지."""
        src = PIPELINE_PY.read_text(encoding="utf-8")
        assert "time.sleep(" not in src, "pipeline_state.py에 blocking sleep 있음"

    def test_pipeline_state_module_exists(self):
        """V382 핵심 파일이 존재하는지 확인."""
        assert PIPELINE_PY.exists(), "literary_system/pipeline/pipeline_state.py 없음"

    def test_pipeline_init_exports_all(self):
        """__init__.py가 핵심 심볼을 모두 export하는지 확인."""
        init_py = ROOT / "literary_system" / "pipeline" / "__init__.py"
        src = init_py.read_text(encoding="utf-8")
        for symbol in ["LiteraryPipelineState", "append_trace",
                        "save_literary_checkpoint", "restore_literary_checkpoint",
                        "autosave_literary_state", "run_minimal_pipeline"]:
            assert symbol in src, f"__init__.py에 {symbol} 없음"

    def test_no_hardcoded_run_id_in_pipeline(self):
        """run_id를 하드코딩하지 않음 — uuid 기반이어야 함."""
        src = PIPELINE_PY.read_text(encoding="utf-8")
        assert "run_id = \"" not in src, "하드코딩된 run_id 발견"

    def test_os_version_v382_in_pipeline(self):
        """pipeline_state.py가 V382 명시."""
        src = PIPELINE_PY.read_text(encoding="utf-8")
        assert "V382" in src


# ─────────────────────────────────────────────────────────────────────────────
# 6. TestMinimalPipelineIntegration
# ─────────────────────────────────────────────────────────────────────────────
class TestMinimalPipelineIntegration:
    """run_minimal_pipeline() 통합 테스트."""

    def test_returns_literary_pipeline_state(self):
        from literary_system.pipeline import run_minimal_pipeline, LiteraryPipelineState
        result = run_minimal_pipeline(seed_text="단순 테스트", episodes=1, out_root="/tmp/v382_int")
        assert isinstance(result, LiteraryPipelineState)

    def test_seed_text_affects_project_id(self):
        from literary_system.pipeline import run_minimal_pipeline
        r1 = run_minimal_pipeline(seed_text="씨드A", episodes=1, out_root="/tmp/v382_int")
        r2 = run_minimal_pipeline(seed_text="씨드B", episodes=1, out_root="/tmp/v382_int")
        assert r1.project_id != r2.project_id

    def test_episodes_param_affects_budget(self):
        from literary_system.pipeline import run_minimal_pipeline
        r2 = run_minimal_pipeline(seed_text="예산 테스트", episodes=2, out_root="/tmp/v382_int")
        r4 = run_minimal_pipeline(seed_text="예산 테스트", episodes=4, out_root="/tmp/v382_int")
        assert r4.budget_episodes >= r2.budget_episodes

    def test_run_is_idempotent_structure(self):
        """두 번 실행해도 같은 구조적 결과 (체크포인트 이름 동일)."""
        from literary_system.pipeline import run_minimal_pipeline
        r1 = run_minimal_pipeline(seed_text="멱등성 테스트", episodes=1, out_root="/tmp/v382_int")
        r2 = run_minimal_pipeline(seed_text="멱등성 테스트", episodes=1, out_root="/tmp/v382_int")
        assert set(r1.checkpoints.keys()) == set(r2.checkpoints.keys())

    def test_trace_contains_node_markers(self):
        from literary_system.pipeline import run_minimal_pipeline
        result = run_minimal_pipeline(seed_text="마커 테스트", episodes=1, out_root="/tmp/v382_int")
        trace = "\n".join(result.execution_trace)
        for marker in ["Node_SeedCompiler", "Node_SeriesArcPlanner",
                        "Node_CausalPlotGraph", "Node_EpisodeRevealBudget",
                        "Node_KnowledgeStateTracker", "Node_CharacterKnowledgeProseBridge"]:
            assert marker in trace, f"trace에 {marker} 없음"

    def test_different_run_ids_each_call(self):
        from literary_system.pipeline import run_minimal_pipeline
        runs = [run_minimal_pipeline(seed_text="ID 테스트", out_root="/tmp/v382_int") for _ in range(3)]
        ids = {r.run_id for r in runs}
        assert len(ids) == 3, "run_id가 중복됨 — 세션 간 오염 가능"
