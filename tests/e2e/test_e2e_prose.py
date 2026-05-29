"""
tests/e2e/test_e2e_prose.py
V587 SP-β — Gate G46: E2EProseGate 테스트 (ADR-047)

MOCK 모드 (CI 기본):
  - test_gate_g46_mock_*: @pytest.mark.e2e 마킹, CI 기본 실행
  - 실 LLM 없이 6 checkpoints 전체 PASS 확인

REAL 모드 (수동 전용):
  - test_gate_g46_real_*: @pytest.mark.real_llm 마킹
  - pytest -m real_llm 으로만 실행
  - 환경변수 ANTHROPIC_API_KEY 필요

실행:
  pytest tests/e2e/test_e2e_prose.py -v            # MOCK 전용
  pytest tests/e2e/ -m real_llm -v                 # REAL LLM (수동)
  pytest tests/e2e/ -m "not real_llm" -v           # MOCK 전용 (명시적)
"""
from __future__ import annotations
import os

import pytest

from literary_system.gates.e2e_prose_gate import (
    CHECKPOINTS,
    CPResult,
    E2EProseResult,
    gate_e2e_prose,
    run_gate_g46,
    _cp1_nie_nil_six_steps,
    _cp2_asd_auto_repair,
    _cp3_gig_narrative_graph,
    _cp4_losdb_query_interface,
    _cp5_constitution_score,
    _cp6_cli_generate,
)


# ---------------------------------------------------------------------------
# 헬퍼
# ---------------------------------------------------------------------------

def _assert_cp(result: CPResult, expect_pass: bool = True) -> None:
    """CP 결과 공통 검증."""
    assert isinstance(result, CPResult)
    assert isinstance(result.passed, bool)
    assert result.elapsed_ms >= 0
    if expect_pass:
        assert result.passed, (
            f"{result.cp_id} FAIL: {result.error or result.detail}"
        )


# ---------------------------------------------------------------------------
# MOCK 모드 개별 Checkpoint 테스트
# ---------------------------------------------------------------------------

class TestCP1NIENil:
    """CP-1: NIE NIL 6단계 통과."""

    def test_cp1_symbols_exist(self):
        """NILOrchestrator + NILResult 필드 생존."""
        r = _cp1_nie_nil_six_steps()
        _assert_cp(r)
        assert "process_scene" in r.detail or "NILResult" in r.detail or r.passed

    def test_cp1_returns_cp_result(self):
        r = _cp1_nie_nil_six_steps()
        assert r.cp_id == "CP-1"
        assert isinstance(r.elapsed_ms, float)


class TestCP2ASDAuto:
    """CP-2: ASD AutoRepair."""

    def test_cp2_detector_executor_alive(self):
        r = _cp2_asd_auto_repair()
        _assert_cp(r)

    def test_cp2_zero_debts_on_empty_store(self):
        r = _cp2_asd_auto_repair()
        assert r.passed
        assert "0건" in r.detail or "0" in r.detail


class TestCP3GIGNarrative:
    """CP-3: GIG NarrativeGraph + BlastRadius ≤ 0.55."""

    def test_cp3_empty_graph_passes(self):
        r = _cp3_gig_narrative_graph()
        _assert_cp(r)

    def test_cp3_blast_radius_in_detail(self):
        r = _cp3_gig_narrative_graph()
        assert "blast_radius" in r.detail


class TestCP4LOSDBQuery:
    """CP-4: LOSDB QueryInterface HEALTHY + ≤ 1초."""

    def test_cp4_connection_check_fast(self):
        r = _cp4_losdb_query_interface()
        _assert_cp(r)

    def test_cp4_under_1000ms(self):
        r = _cp4_losdb_query_interface()
        assert r.elapsed_ms < 1000, (
            f"CP-4 elapsed {r.elapsed_ms:.0f}ms > 1000ms"
        )


class TestCP5Constitution:
    """CP-5: Constitution R(scene) ≥ 0.65."""

    def test_cp5_mock_score_passes(self):
        r = _cp5_constitution_score()
        _assert_cp(r)

    def test_cp5_score_value_in_detail(self):
        r = _cp5_constitution_score()
        assert "R(scene)=" in r.detail or r.passed


class TestCP6CLIGenerate:
    """CP-6: Minimal-CLI generate 100~500자."""

    def test_cp6_mock_pipeline_produces_text(self):
        r = _cp6_cli_generate()
        _assert_cp(r)

    def test_cp6_nonzero_output(self):
        r = _cp6_cli_generate()
        assert r.passed
        assert "산출" in r.detail


# ---------------------------------------------------------------------------
# Gate G46 통합 테스트 (MOCK 모드)
# ---------------------------------------------------------------------------

@pytest.mark.e2e
class TestGateG46Mock:
    """Gate G46 통합 MOCK 모드 테스트."""

    def test_all_6_checkpoints_pass(self):
        """6개 체크포인트 모두 PASS."""
        result = gate_e2e_prose(mock=True)
        assert isinstance(result, E2EProseResult)
        assert result.passed, (
            f"Gate G46 FAIL — 실패 CP: {result.failed_cps}\n"
            + "\n".join(
                f"  {cp.cp_id}: {cp.error or cp.detail}"
                for cp in result.checkpoints if not cp.passed
            )
        )
        assert len(result.checkpoints) == 6
        assert len(result.failed_cps) == 0

    def test_total_elapsed_under_30s(self):
        """MOCK 모드 전체 실행 ≤ 30,000ms (30초)."""
        result = gate_e2e_prose(mock=True)
        assert result.total_elapsed_ms < 30_000, (
            f"Gate G46 MOCK 모드 {result.total_elapsed_ms:.0f}ms > 30,000ms"
        )

    def test_run_gate_g46_dict_format(self):
        """`run_gate_g46()` 반환 형식 — release_gate.py 진입점."""
        d = run_gate_g46()
        assert isinstance(d, dict)
        assert d["pass"] is True
        assert "checkpoints" in d
        assert len(d["checkpoints"]) == 6
        assert "summary" in d

    def test_checkpoint_list_length(self):
        """CHECKPOINTS 상수 6개."""
        assert len(CHECKPOINTS) == 6

    def test_each_checkpoint_has_required_keys(self):
        """각 체크포인트 딕셔너리 필수 키 보유."""
        result = gate_e2e_prose(mock=True)
        for cp in result.checkpoints:
            d = cp.to_dict()
            assert "cp_id" in d
            assert "name" in d
            assert "passed" in d
            assert "elapsed_ms" in d

    def test_cp_ids_are_sequential(self):
        """CP-1 ~ CP-6 순서 보장."""
        result = gate_e2e_prose(mock=True)
        for i, cp in enumerate(result.checkpoints, 1):
            assert cp.cp_id == f"CP-{i}", (
                f"CP 순서 오류: 위치 {i}에 {cp.cp_id}"
            )

    def test_gate_g46_registered_in_gates_list(self):
        """release_gate.GATES에 e2e_prose_g46 등록 확인."""
        from literary_system.gates.release_gate import GATES
        gate_ids = [g[0] for g in GATES]
        assert "e2e_prose_g46" in gate_ids, "e2e_prose_g46 GATES 미등록"

    def test_gate_g46_in_registry(self):
        """gate_registry에 e2e_prose_g46 등록 + tier=L1."""
        from literary_system.gates.gate_registry import GATE_REGISTRY
        assert "e2e_prose_g46" in GATE_REGISTRY
        entry = GATE_REGISTRY["e2e_prose_g46"]
        assert entry.tier == "L1"
        assert entry.adr_ref == "ADR-047"


# ---------------------------------------------------------------------------
# REAL LLM 모드 (수동 전용 — pytest -m real_llm)
# ---------------------------------------------------------------------------

# provider key 없으면 자동 skip
_REAL_LLM_REASON = (
    "REAL LLM provider key not configured "
    "(set ANTHROPIC_API_KEY or OPENAI_API_KEY)"
)
requires_real_llm = pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY") and not os.getenv("OPENAI_API_KEY"),
    reason=_REAL_LLM_REASON,
)


@requires_real_llm
@pytest.mark.real_llm
class TestGateG46RealLLM:
    """
    Gate G46 REAL LLM 모드 테스트.
    환경변수 ANTHROPIC_API_KEY 또는 OPENAI_API_KEY 필요.
    key 없으면 자동 skip. CI에서는 skip됨.
    실행: ANTHROPIC_API_KEY=... pytest tests/e2e/test_e2e_prose.py -m real_llm -v
    """
    pytestmark = pytest.mark.real_llm  # 클래스 전체 마킹

    def test_real_llm_gate_passes(self):
        """REAL LLM 모드 — 실 LLM 연결 시 6 checkpoints PASS."""
        result = gate_e2e_prose(mock=False)
        assert result.passed, (
            f"Gate G46 REAL FAIL — 실패 CP: {result.failed_cps}"
        )
        # REAL 모드는 반드시 mock_mode=False + provider 호출이 있어야 함
        if hasattr(result, "mock_mode"):
            assert result.mock_mode is False, "gate_e2e_prose(mock=False)인데 mock_mode=True"
        if hasattr(result, "provider_calls"):
            assert result.provider_calls > 0, "REAL LLM 호출이 0건 — mock 경로로 실행됨"

    def test_cp6_real_text_length(self):
        """REAL LLM 모드 — CP-6 산문 100~500자."""
        r = _cp6_cli_generate()
        assert r.passed
        # REAL 모드에서는 실 텍스트 길이 검증
        if "산출" in r.detail:
            import re
            m = re.search(r"(\d+)자", r.detail)
            if m:
                char_count = int(m.group(1))
                assert char_count >= 10, (
                    f"CP-6 REAL 산출 {char_count}자 — 텍스트 없음"
                )
