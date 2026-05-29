"""V340: NKGPipeline 통합 테스트 (Phase 3 + 4 완전 구현 확인)."""
from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, "/tmp/v329_work/literary_os_v329")

from literary_system.nkg.pipeline import NKGPhaseResult, NKGPipeline


# ── 헬퍼 ────────────────────────────────────────────────────

def _make_draft(scene_id, content, episode_id="ep01", ev=None, idx=0):
    """SceneDraftOutput 모의 객체 — adapter가 읽는 모든 속성 명시 설정."""
    m = MagicMock(spec=[])          # spec=[] → auto-attribute 생성 비활성화
    m.scene_id         = scene_id
    m.draft_text       = content    # adapter 우선순위 1위
    m.content          = content
    m.episode_id       = episode_id
    m.episode_no       = episode_id
    m.emotional_vector = ev or [0.5, 0.5, 0.3, 0.0]
    m.scene_index      = idx
    m.quality          = "PASS"
    m.mae_score        = 0.0
    return m


def _run_ep01(n=5, use_causal_kw=False):
    pipe   = NKGPipeline()
    drafts = []
    for i in range(n):
        if use_causal_kw and i > 0:
            content = f"그래서 이 사건이 일어났다 — 장면 {i}"
        else:
            content = f"장면 {i} 기본 내용입니다."
        drafts.append(_make_draft(f"s{i:02d}", content, idx=i))
    pipe.run_full("ep01", drafts)
    return pipe


# ── TestPipelineFullRun ──────────────────────────────────────

class TestPipelineFullRun:

    def test_returns_list_of_phase_results(self):
        pipe    = NKGPipeline()
        results = pipe.run_full("ep01", [_make_draft("s01", "내용")])
        assert isinstance(results, list)
        assert len(results) == 5

    def test_all_phases_named(self):
        pipe    = NKGPipeline()
        results = pipe.run_full("ep01", [_make_draft("s01", "내용")])
        names   = [r.phase_name for r in results]
        for name in ("scan", "node_extract", "edge_infer", "emotional", "commit"):
            assert name in names

    def test_all_phases_succeed_with_valid_input(self):
        pipe    = _run_ep01(3)
        results = pipe.last_results()
        for r in results:
            assert r.success, f"Phase {r.phase_name} failed: {r.error}"

    def test_scan_phase_counts_non_none(self):
        pipe    = NKGPipeline()
        drafts  = [_make_draft("s01", "a"), None, _make_draft("s02", "b")]
        results = pipe.run_full("ep01", drafts)
        scan_r  = next(r for r in results if r.phase_name == "scan")
        assert scan_r.success
        assert scan_r.nodes_added == 2

    def test_node_extract_phase_adds_nodes(self):
        pipe = _run_ep01(4)
        ne_r = next(r for r in pipe.last_results() if r.phase_name == "node_extract")
        assert ne_r.nodes_added == 4

    def test_graph_has_scene_nodes_after_run(self):
        pipe = _run_ep01(3)
        st   = pipe.graph.stats()
        assert st["nodes"] >= 3

    def test_empty_input_all_phases_succeed(self):
        pipe    = NKGPipeline()
        results = pipe.run_full("ep_empty", [])
        for r in results:
            assert r.success, f"{r.phase_name}: {r.error}"

    def test_none_only_input_filtered(self):
        pipe    = NKGPipeline()
        results = pipe.run_full("ep01", [None, None])
        scan_r  = next(r for r in results if r.phase_name == "scan")
        assert scan_r.nodes_added == 0

    def test_duration_ms_non_negative(self):
        pipe    = _run_ep01(2)
        for r in pipe.last_results():
            if r.success:
                assert r.duration_ms >= 0.0

    def test_last_results_matches_return(self):
        pipe     = NKGPipeline()
        returned = pipe.run_full("ep01", [_make_draft("s01", "x")])
        assert returned == pipe.last_results()


# ── TestPhase3EdgeInfer ──────────────────────────────────────

class TestPhase3EdgeInfer:

    def test_edge_infer_phase_success(self):
        pipe = _run_ep01(5)
        ei_r = next(r for r in pipe.last_results() if r.phase_name == "edge_infer")
        assert ei_r.success

    def test_edge_infer_adds_edges_nonneg(self):
        pipe = _run_ep01(5)
        ei_r = next(r for r in pipe.last_results() if r.phase_name == "edge_infer")
        assert ei_r.edges_added >= 0

    def test_edge_infer_with_causal_keywords(self):
        pipe   = NKGPipeline()
        drafts = [
            _make_draft("s00", "사건이 있었다.", idx=0),
            _make_draft("s01", "그래서 모든 것이 바뀌었다.", idx=1),
            _make_draft("s02", "결국 그는 떠났다.", idx=2),
        ]
        pipe.run_full("ep01", drafts)
        st = pipe.graph.stats()
        assert st["edges"] >= 1

    def test_edge_infer_with_char_names(self):
        pipe   = NKGPipeline()
        drafts = [
            _make_draft("s00", "지수가 달려갔다.", idx=0),
            _make_draft("s01", "지수는 멈추지 않았다.", idx=1),
        ]
        pipe.run_full("ep01", drafts, char_names=["지수"])
        ei_r = next(r for r in pipe.last_results() if r.phase_name == "edge_infer")
        assert ei_r.success

    def test_edge_infer_fallback_sequential(self):
        """engine 비활성 → 순서 기반 fallback n-1 엣지."""
        pipe = NKGPipeline()
        pipe._edge_engine = None
        drafts = [_make_draft(f"s{i:02d}", f"내용{i}", idx=i) for i in range(4)]
        pipe.run_full("ep01", drafts)
        ei_r = next(r for r in pipe.last_results() if r.phase_name == "edge_infer")
        assert ei_r.success
        assert ei_r.edges_added == 3

    def test_edge_infer_foreshadow_scene_nodes_exist(self):
        pipe   = NKGPipeline()
        drafts = [
            _make_draft("s00", "언젠가 반드시 돌아올 것이라 예감했다.", idx=0),
            _make_draft("s01", "평범한 하루였다.", idx=1),
            _make_draft("s02", "드디어 그가 돌아왔다. 사실은 계획된 것이었다.", idx=2),
        ]
        pipe.run_full("ep01", drafts)
        st = pipe.graph.stats()
        assert st["nodes"] >= 3

    def test_edge_infer_result_data_is_dict(self):
        pipe   = NKGPipeline()
        drafts = [
            _make_draft("s00", "그래서 결과가 나타났다.", idx=0),
            _make_draft("s01", "따라서 이어졌다.", idx=1),
        ]
        pipe.run_full("ep01", drafts)
        ei_r = next(r for r in pipe.last_results() if r.phase_name == "edge_infer")
        assert isinstance(ei_r.data, dict)


# ── TestPhase4Emotional ──────────────────────────────────────

class TestPhase4Emotional:

    def test_emotional_phase_success(self):
        pipe  = _run_ep01(5)
        emo_r = next(r for r in pipe.last_results() if r.phase_name == "emotional")
        assert emo_r.success

    def test_identical_ev_create_resonance(self):
        pipe = NKGPipeline()
        ev   = [0.8, 0.6, 0.4, 0.2]
        drafts = [
            _make_draft("s00", "내용A", ev=ev, idx=0),
            _make_draft("s01", "내용B", ev=ev, idx=1),
        ]
        pipe.run_full("ep01", drafts)
        emo_r = next(r for r in pipe.last_results() if r.phase_name == "emotional")
        assert emo_r.success
        assert emo_r.edges_added >= 1

    def test_orthogonal_ev_no_edges(self):
        pipe   = NKGPipeline()
        drafts = [
            _make_draft("s00", "A", ev=[1.0, 0.0, 0.0, 0.0], idx=0),
            _make_draft("s01", "B", ev=[0.0, 1.0, 0.0, 0.0], idx=1),
        ]
        pipe.run_full("ep01", drafts)
        emo_r = next(r for r in pipe.last_results() if r.phase_name == "emotional")
        assert emo_r.success
        assert emo_r.edges_added == 0

    def test_emotional_phase_with_emt_param(self):
        pipe = NKGPipeline()
        ev   = [0.7, 0.7, 0.5, 0.3]
        drafts = [_make_draft(f"s{i:02d}", f"내용{i}", ev=ev, idx=i) for i in range(3)]
        fake_emt         = MagicMock(spec=[])
        fake_emt.history = [ev] * 3
        pipe.run_full("ep01", drafts, emt=fake_emt)
        emo_r = next(r for r in pipe.last_results() if r.phase_name == "emotional")
        assert emo_r.success

    def test_emotional_fallback_when_linker_unavailable(self):
        pipe = NKGPipeline()
        pipe._emo_linker = None
        ev   = [0.8, 0.8, 0.8, 0.8]
        drafts = [_make_draft(f"s{i:02d}", f"내용{i}", ev=ev, idx=i) for i in range(3)]
        pipe.run_full("ep01", drafts)
        emo_r = next(r for r in pipe.last_results() if r.phase_name == "emotional")
        assert emo_r.success
        assert emo_r.edges_added == 0

    def test_single_node_no_emotional_edges(self):
        pipe = NKGPipeline()
        pipe.run_full("ep01", [_make_draft("s00", "단독 장면")])
        emo_r = next(r for r in pipe.last_results() if r.phase_name == "emotional")
        assert emo_r.success
        assert emo_r.edges_added == 0

    def test_high_similarity_ev_returns_int_edges(self):
        pipe   = NKGPipeline()
        ev_a   = [0.9, 0.8, 0.7, 0.6]
        ev_b   = [0.8, 0.7, 0.6, 0.5]
        drafts = [
            _make_draft("s00", "A", ev=ev_a, idx=0),
            _make_draft("s01", "B", ev=ev_b, idx=1),
        ]
        pipe.run_full("ep01", drafts)
        emo_r = next(r for r in pipe.last_results() if r.phase_name == "emotional")
        assert emo_r.success
        assert isinstance(emo_r.edges_added, int)


# ── TestPhaseCommit ──────────────────────────────────────────

class TestPhaseCommit:

    def test_commit_phase_success(self):
        pipe     = _run_ep01(3)
        commit_r = next(r for r in pipe.last_results() if r.phase_name == "commit")
        assert commit_r.success

    def test_dirty_flags_cleared_after_commit(self):
        pipe = _run_ep01(3)
        st   = pipe.staleness.stats()
        assert st["dirty_count"] == 0

    def test_commit_data_has_cleared_key(self):
        pipe     = _run_ep01(4)
        commit_r = next(r for r in pipe.last_results() if r.phase_name == "commit")
        assert "_commit_cleared" in commit_r.data


# ── TestIncrementalUpdate ────────────────────────────────────

class TestIncrementalUpdate:

    def test_returns_phase_result(self):
        pipe   = _run_ep01(3)
        draft  = _make_draft("s00", "완전히 새로운 내용으로 교체됨")
        result = pipe.update_incremental("s00", draft, episode_id="ep01")
        assert isinstance(result, NKGPhaseResult)
        assert result.phase_name == "incremental_update"

    def test_new_content_succeeds(self):
        pipe  = _run_ep01(3)
        draft = _make_draft("s00", "완전히 달라진 내용 변경됨 버전 2")
        result = pipe.update_incremental("s00", draft, episode_id="ep01")
        assert result.success

    def test_same_content_skipped(self):
        """동일 내용 → content_hash 동일 → skipped=True."""
        pipe  = NKGPipeline()
        draft = _make_draft("s00", "변하지 않는 내용")
        pipe.run_full("ep01", [draft])
        result = pipe.update_incremental("s00", draft, episode_id="ep01")
        assert result.success
        assert result.data.get("skipped") is True

    def test_new_content_nodes_added_one(self):
        pipe  = _run_ep01(3)
        draft = _make_draft("s00", "완전히 다른 새 내용 ABC DEF GHI")
        result = pipe.update_incremental("s00", draft, episode_id="ep01")
        assert result.nodes_added == 1


# ── TestPipelineStats ────────────────────────────────────────

class TestPipelineStats:

    def test_stats_returns_dict(self):
        assert isinstance(NKGPipeline().stats(), dict)

    def test_stats_has_required_keys(self):
        st = NKGPipeline().stats()
        for key in ("graph", "staleness", "phases", "edge_infer_ready", "emotional_ready"):
            assert key in st

    def test_stats_phases_is_five(self):
        assert NKGPipeline().stats()["phases"] == 5

    def test_stats_engine_flags_bool(self):
        st = NKGPipeline().stats()
        assert isinstance(st["edge_infer_ready"], bool)
        assert isinstance(st["emotional_ready"],  bool)

    def test_stats_edge_infer_ready_true(self):
        from literary_system.nkg import pipeline as pl_mod
        assert pl_mod._EDGE_INFER_AVAILABLE is True

    def test_stats_emotional_ready_true(self):
        from literary_system.nkg import pipeline as pl_mod
        assert pl_mod._EMOTIONAL_LINKER_AVAILABLE is True

    def test_stats_graph_has_node_info(self):
        pipe = _run_ep01(3)
        st   = pipe.stats()
        assert st["graph"]["nodes"] >= 3

    def test_stats_after_empty_run(self):
        pipe = NKGPipeline()
        pipe.run_full("ep_empty", [])
        st = pipe.stats()
        assert st["graph"]["nodes"] >= 0
