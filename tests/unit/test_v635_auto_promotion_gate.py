"""
test_v635_auto_promotion_gate.py — V635 AutoPromotionGate TC-01~33
SP-C.1 ADR-077: G62 자동 승격 게이트 검증

LLM-0 준수: 외부 LLM 호출 없음
"""
from __future__ import annotations

import json
import pytest
from datetime import datetime, timezone

from literary_system.gates.auto_promotion_gate import (
    AutoPromotionGate,
    GateResult,
    R_THRESHOLD,
    MAX_ROLLBACKS,
    run_g62_gate,
)
from literary_system.constitution import (
    AutoPromotionGate as APGFromConstitution,
    GateResult as GRFromConstitution,
    R_THRESHOLD as RT_FROM_CONST,
    MAX_ROLLBACKS as MR_FROM_CONST,
)


# ─────────────────────────────────────────────
# 픽스처
# ─────────────────────────────────────────────
@pytest.fixture
def gate():
    return AutoPromotionGate(store_path=":memory:")


@pytest.fixture
def t0():
    return datetime(2026, 5, 26, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def passing_scores():
    """R ≥ 0.78 보장 점수."""
    return [0.80, 0.82, 0.79, 0.83, 0.81]


@pytest.fixture
def failing_scores():
    """R < 0.78 점수."""
    return [0.60, 0.65, 0.70]


# ─────────────────────────────────────────────
# TC-01~05: 상수 및 초기 상태
# ─────────────────────────────────────────────
class TestConstants:
    def test_tc01_r_threshold_default(self):
        """TC-01: R_THRESHOLD 기본값 0.78."""
        assert R_THRESHOLD == pytest.approx(0.78)

    def test_tc02_max_rollbacks_default(self):
        """TC-02: MAX_ROLLBACKS 기본값 0."""
        assert MAX_ROLLBACKS == 0

    def test_tc03_initial_count_zero(self, gate):
        """TC-03: 초기 이력 0건."""
        assert gate.count() == 0

    def test_tc04_initial_history_empty(self, gate):
        """TC-04: 초기 history() 빈 리스트."""
        assert gate.history() == []

    def test_tc05_initial_last_result_none(self, gate):
        """TC-05: 초기 last_result() None."""
        assert gate.last_result() is None


# ─────────────────────────────────────────────
# TC-06~12: evaluate() PASS 케이스
# ─────────────────────────────────────────────
class TestEvaluatePass:
    def test_tc06_pass_r_above_threshold_no_rollbacks(self, gate, passing_scores, t0):
        """TC-06: R ≥ 0.78, rollback=0 → PASS."""
        r = gate.evaluate(passing_scores, rollback_count=0, now=t0)
        assert r.passed is True

    def test_tc07_pass_result_fields(self, gate, passing_scores, t0):
        """TC-07: PASS 시 GateResult 필드 검증."""
        r = gate.evaluate(passing_scores, rollback_count=0, note="test", now=t0)
        assert r.result_id  # UUID4 non-empty
        assert r.scene_count == len(passing_scores)
        assert r.rollback_count == 0
        assert r.note == "test"
        assert "G62 PASS" in r.reason

    def test_tc08_pass_r_exactly_threshold(self, gate, t0):
        """TC-08: R = 0.78 정확히 → PASS (≥ 조건)."""
        r = gate.evaluate([0.78, 0.78, 0.78], rollback_count=0, now=t0)
        assert r.passed is True

    def test_tc09_r_score_is_mean(self, gate, t0):
        """TC-09: r_score 는 장면 점수 평균."""
        scores = [0.80, 0.90]
        r = gate.evaluate(scores, rollback_count=0, now=t0)
        assert r.r_score == pytest.approx(0.85)

    def test_tc10_pass_single_scene(self, gate, t0):
        """TC-10: 단일 장면 점수로 평가 가능."""
        r = gate.evaluate([0.80], rollback_count=0, now=t0)
        assert r.passed is True

    def test_tc11_pass_many_scenes(self, gate, t0):
        """TC-11: 100개 장면, 평균 ≥ 0.78 → PASS."""
        scores = [0.80] * 100
        r = gate.evaluate(scores, rollback_count=0, now=t0)
        assert r.passed is True
        assert r.scene_count == 100

    def test_tc12_pass_reason_contains_r_and_rollback(self, gate, passing_scores, t0):
        """TC-12: PASS 사유에 R값과 rollback 수 포함."""
        r = gate.evaluate(passing_scores, rollback_count=0, now=t0)
        assert "R=" in r.reason
        assert "rollbacks=" in r.reason


# ─────────────────────────────────────────────
# TC-13~18: evaluate() FAIL 케이스
# ─────────────────────────────────────────────
class TestEvaluateFail:
    def test_tc13_fail_r_below_threshold(self, gate, failing_scores, t0):
        """TC-13: R < 0.78 → FAIL."""
        r = gate.evaluate(failing_scores, rollback_count=0, now=t0)
        assert r.passed is False

    def test_tc14_fail_rollback_exceeds_max(self, gate, passing_scores, t0):
        """TC-14: rollback_count=1 > MAX_ROLLBACKS=0 → FAIL."""
        r = gate.evaluate(passing_scores, rollback_count=1, now=t0)
        assert r.passed is False

    def test_tc15_fail_both_conditions(self, gate, failing_scores, t0):
        """TC-15: R < 0.78 AND rollback=1 → FAIL."""
        r = gate.evaluate(failing_scores, rollback_count=1, now=t0)
        assert r.passed is False
        assert "G62 FAIL" in r.reason

    def test_tc16_fail_reason_lists_all_failures(self, gate, failing_scores, t0):
        """TC-16: FAIL 사유에 두 조건 모두 기술."""
        r = gate.evaluate(failing_scores, rollback_count=2, now=t0)
        assert "R=" in r.reason
        assert "rollback_count=" in r.reason

    def test_tc17_fail_r_just_below_threshold(self, gate, t0):
        """TC-17: R = 0.7799 → FAIL."""
        scores = [0.7799] * 5
        r = gate.evaluate(scores, rollback_count=0, now=t0)
        assert r.passed is False

    def test_tc18_fail_empty_scores_raises(self, gate, t0):
        """TC-18: 빈 scene_scores → ValueError."""
        with pytest.raises(ValueError, match="비어 있습니다"):
            gate.evaluate([], rollback_count=0, now=t0)


# ─────────────────────────────────────────────
# TC-19~22: 파라미터 검증
# ─────────────────────────────────────────────
class TestParameterValidation:
    def test_tc19_invalid_r_threshold_zero(self):
        """TC-19: r_threshold=0 → ValueError."""
        with pytest.raises(ValueError):
            AutoPromotionGate(store_path=":memory:", r_threshold=0.0)

    def test_tc20_invalid_r_threshold_over_one(self):
        """TC-20: r_threshold=1.5 → ValueError."""
        with pytest.raises(ValueError):
            AutoPromotionGate(store_path=":memory:", r_threshold=1.5)

    def test_tc21_invalid_max_rollbacks_negative(self):
        """TC-21: max_rollbacks=-1 → ValueError."""
        with pytest.raises(ValueError):
            AutoPromotionGate(store_path=":memory:", max_rollbacks=-1)

    def test_tc22_invalid_negative_rollback_count(self, gate, passing_scores, t0):
        """TC-22: evaluate() 호출 시 rollback_count 음수 → ValueError."""
        with pytest.raises(ValueError):
            gate.evaluate(passing_scores, rollback_count=-1, now=t0)


# ─────────────────────────────────────────────
# TC-23~25: history / last_result
# ─────────────────────────────────────────────
class TestHistory:
    def test_tc23_history_order(self, gate, passing_scores, failing_scores, t0):
        """TC-23: history() 오래된 순."""
        gate.evaluate(passing_scores, rollback_count=0, now=t0)
        gate.evaluate(failing_scores, rollback_count=0, now=t0)
        h = gate.history()
        assert h[0].passed is True
        assert h[1].passed is False

    def test_tc24_last_result_most_recent(self, gate, passing_scores, failing_scores, t0):
        """TC-24: last_result() 가장 최근."""
        gate.evaluate(passing_scores, rollback_count=0, now=t0)
        gate.evaluate(failing_scores, rollback_count=0, now=t0)
        assert gate.last_result().passed is False

    def test_tc25_history_returns_copy(self, gate, passing_scores, t0):
        """TC-25: history() 반환값 수정이 내부에 영향 없음."""
        gate.evaluate(passing_scores, rollback_count=0, now=t0)
        h = gate.history()
        h.clear()
        assert gate.count() == 1


# ─────────────────────────────────────────────
# TC-26~28: 파일 모드 영속화
# ─────────────────────────────────────────────
class TestFilePersistence:
    def test_tc26_file_created_on_evaluate(self, tmp_path, passing_scores, t0):
        """TC-26: evaluate() 후 JSONL 파일 생성됨."""
        p = tmp_path / "sub" / "gate.jsonl"
        g = AutoPromotionGate(store_path=str(p))
        g.evaluate(passing_scores, rollback_count=0, now=t0)
        assert p.exists()

    def test_tc27_reload_from_file(self, tmp_path, passing_scores, t0):
        """TC-27: 파일 재로드 시 이력 복원."""
        p = tmp_path / "gate.jsonl"
        g1 = AutoPromotionGate(store_path=str(p))
        g1.evaluate(passing_scores, rollback_count=0, now=t0)

        g2 = AutoPromotionGate(store_path=str(p))
        assert g2.count() == 1
        assert g2.last_result().passed is True

    def test_tc28_clear_removes_file(self, tmp_path, passing_scores, t0):
        """TC-28: clear() 후 파일 삭제됨."""
        p = tmp_path / "gate.jsonl"
        g = AutoPromotionGate(store_path=str(p))
        g.evaluate(passing_scores, rollback_count=0, now=t0)
        g.clear()
        assert g.count() == 0
        assert not p.exists()


# ─────────────────────────────────────────────
# TC-29~31: 직렬화 + 공개 API
# ─────────────────────────────────────────────
class TestSerializationAndApi:
    def test_tc29_to_dict_from_dict_roundtrip(self, gate, passing_scores, t0):
        """TC-29: GateResult to_dict/from_dict 라운드트립."""
        r = gate.evaluate(passing_scores, rollback_count=0, note="rt", now=t0)
        d = r.to_dict()
        restored = GateResult.from_dict(d)
        assert restored.result_id == r.result_id
        assert restored.r_score == pytest.approx(r.r_score)
        assert restored.passed == r.passed
        assert restored.note == r.note

    def test_tc30_public_api_from_constitution(self):
        """TC-30: constitution/__init__.py 에서 임포트 가능."""
        assert APGFromConstitution is AutoPromotionGate
        assert GRFromConstitution is GateResult
        assert RT_FROM_CONST == pytest.approx(0.78)
        assert MR_FROM_CONST == 0

    def test_tc31_custom_thresholds(self, t0):
        """TC-31: 커스텀 r_threshold, max_rollbacks 적용 확인."""
        g = AutoPromotionGate(store_path=":memory:", r_threshold=0.90, max_rollbacks=2)
        assert g.r_threshold == pytest.approx(0.90)
        assert g.max_rollbacks == 2
        # 0.89 < 0.90 → FAIL
        r = g.evaluate([0.89], rollback_count=0, now=t0)
        assert r.passed is False
        # 0.91 ≥ 0.90, rollback=2 ≤ 2 → PASS
        r2 = g.evaluate([0.91], rollback_count=2, now=t0)
        assert r2.passed is True


# ─────────────────────────────────────────────
# TC-32~33: run_g62_gate() 통합
# ─────────────────────────────────────────────
class TestRunG62Gate:
    def test_tc32_run_g62_gate_pass(self):
        """TC-32: run_g62_gate() → 7/7 CP PASS."""
        result = run_g62_gate()
        assert result["pass"] is True
        assert result["passed_count"] == 7
        assert len(result["errors"]) == 0

    def test_tc33_run_g62_gate_checkpoints(self):
        """TC-33: run_g62_gate() 체크포인트 7개 반환."""
        result = run_g62_gate()
        assert len(result["checkpoints"]) == 7
        # 핵심 CP 확인
        cp_str = " ".join(result["checkpoints"])
        assert "CP-1" in cp_str
        assert "CP-4" in cp_str  # 골든셋 PASS
        assert "CP-7" in cp_str  # 직렬화
