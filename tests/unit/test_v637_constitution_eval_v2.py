"""
V637 — ConstitutionEvalV2 테스트 (TC-01~33)

ADR-079 | SP-C.1 헌법 멀티축 평가기 V2
"""

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from literary_system.constitution.constitution_eval_v2 import (
    EVAL_THRESHOLD,
    DEFAULT_DIMENSION_NAMES,
    ConstitutionEvalV2,
    EvalDimension,
    ConstitutionEvalResult,
    EvalScore,
    _DEFAULT_WEIGHT,
)


# ── 픽스처 ────────────────────────────────────────────────────────────
@pytest.fixture
def default_eval():
    return ConstitutionEvalV2()


@pytest.fixture
def full_pass_scores():
    """모든 차원 1.0 → final_score = 1.0 (PASS)"""
    return {name: 1.0 for name in DEFAULT_DIMENSION_NAMES}


@pytest.fixture
def full_fail_scores():
    """모든 차원 0.0 → final_score = 0.0 (FAIL)"""
    return {name: 0.0 for name in DEFAULT_DIMENSION_NAMES}


@pytest.fixture
def boundary_scores():
    """경계값: 정확히 EVAL_THRESHOLD = 0.70 → PASS"""
    return {name: EVAL_THRESHOLD for name in DEFAULT_DIMENSION_NAMES}


# ── TC-01~05: 상수 및 초기 상태 ──────────────────────────────────────
class TestConstants:
    def test_tc01_eval_threshold(self):
        """TC-01: EVAL_THRESHOLD = 0.70"""
        assert EVAL_THRESHOLD == 0.70

    def test_tc02_default_dimension_count(self):
        """TC-02: DEFAULT_DIMENSION_NAMES 5개"""
        assert len(DEFAULT_DIMENSION_NAMES) == 5

    def test_tc03_default_dimension_names(self):
        """TC-03: 5축 이름 정확성"""
        expected = {
            "coherence", "authenticity", "style_adherence",
            "emotional_resonance", "narrative_flow",
        }
        assert set(DEFAULT_DIMENSION_NAMES) == expected

    def test_tc04_default_weight(self):
        """TC-04: 기본 가중치 = 0.2"""
        assert abs(_DEFAULT_WEIGHT - 0.2) < 1e-9

    def test_tc05_initial_state_empty(self, default_eval):
        """TC-05: 초기 상태 — count=0, history=[], last_result=None"""
        assert default_eval.count() == 0
        assert default_eval.history() == []
        assert default_eval.last_result() is None


# ── TC-06~10: evaluate() 기본 동작 ───────────────────────────────────
class TestEvaluate:
    def test_tc06_evaluate_returns_eval_result(self, default_eval, full_pass_scores):
        """TC-06: evaluate() → ConstitutionEvalResult 반환"""
        result = default_eval.evaluate("scene-1", full_pass_scores)
        assert isinstance(result, ConstitutionEvalResult)

    def test_tc07_result_id_is_uuid(self, default_eval, full_pass_scores):
        """TC-07: result_id는 UUID4 형식"""
        import uuid
        result = default_eval.evaluate("scene-1", full_pass_scores)
        uuid.UUID(result.result_id)  # 형식 오류 시 ValueError

    def test_tc08_scores_count_equals_dimensions(self, default_eval, full_pass_scores):
        """TC-08: scores 수 = 차원 수 (5)"""
        result = default_eval.evaluate("scene-1", full_pass_scores)
        assert len(result.scores) == 5

    def test_tc09_scene_id_preserved(self, default_eval, full_pass_scores):
        """TC-09: scene_id 보존"""
        result = default_eval.evaluate("my-scene-42", full_pass_scores)
        assert result.scene_id == "my-scene-42"

    def test_tc10_evaluated_at_is_iso(self, default_eval, full_pass_scores):
        """TC-10: evaluated_at ISO-8601 형식"""
        result = default_eval.evaluate("scene-1", full_pass_scores)
        dt = datetime.fromisoformat(result.evaluated_at)
        assert dt.tzinfo is not None


# ── TC-11~15: PASS/FAIL 조건 ─────────────────────────────────────────
class TestPassFail:
    def test_tc11_full_pass(self, default_eval, full_pass_scores):
        """TC-11: 모든 차원 1.0 → passed=True"""
        result = default_eval.evaluate("s1", full_pass_scores)
        assert result.passed is True
        assert abs(result.final_score - 1.0) < 1e-9

    def test_tc12_full_fail(self, default_eval, full_fail_scores):
        """TC-12: 모든 차원 0.0 → passed=False"""
        result = default_eval.evaluate("s1", full_fail_scores)
        assert result.passed is False
        assert abs(result.final_score) < 1e-9

    def test_tc13_boundary_pass(self, default_eval, boundary_scores):
        """TC-13: 경계값 0.70 → passed=True (≥ 기준)"""
        result = default_eval.evaluate("s1", boundary_scores)
        assert result.passed is True

    def test_tc14_just_below_threshold_fail(self, default_eval):
        """TC-14: 0.69... → passed=False"""
        scores = {name: 0.699 for name in DEFAULT_DIMENSION_NAMES}
        result = default_eval.evaluate("s1", scores)
        assert result.passed is False

    def test_tc15_threshold_stored_in_result(self, default_eval, full_pass_scores):
        """TC-15: result.threshold = EVAL_THRESHOLD"""
        result = default_eval.evaluate("s1", full_pass_scores)
        assert result.threshold == EVAL_THRESHOLD


# ── TC-16~20: 가중 평균 계산 ─────────────────────────────────────────
class TestWeightedScore:
    def test_tc16_weighted_score_per_dim(self, default_eval):
        """TC-16: weighted_score = raw_score × weight"""
        scores = {name: 0.8 for name in DEFAULT_DIMENSION_NAMES}
        result = default_eval.evaluate("s1", scores)
        for es in result.scores:
            assert abs(es.weighted_score - 0.8 * _DEFAULT_WEIGHT) < 1e-9

    def test_tc17_final_score_sum_of_weighted(self, default_eval):
        """TC-17: final_score = Σ weighted_score"""
        scores = {name: 0.8 for name in DEFAULT_DIMENSION_NAMES}
        result = default_eval.evaluate("s1", scores)
        total = sum(es.weighted_score for es in result.scores)
        assert abs(result.final_score - total) < 1e-9

    def test_tc18_missing_dim_defaults_zero(self, default_eval):
        """TC-18: 누락 차원 raw_score=0.0 처리"""
        # coherence만 제공
        partial = {"coherence": 1.0}
        result = default_eval.evaluate("s1", partial)
        coherence_score = next(
            es for es in result.scores if es.dimension_id == "coherence"
        )
        assert abs(coherence_score.raw_score - 1.0) < 1e-9
        # 나머지 차원은 0.0
        others = [es for es in result.scores if es.dimension_id != "coherence"]
        for es in others:
            assert es.raw_score == 0.0

    def test_tc19_custom_dimensions_weighted(self):
        """TC-19: 사용자 정의 차원 가중치 반영"""
        dims = [
            EvalDimension("dim_a", "A", weight=0.6),
            EvalDimension("dim_b", "B", weight=0.4),
        ]
        ev = ConstitutionEvalV2(dimensions=dims)
        result = ev.evaluate("s1", {"dim_a": 1.0, "dim_b": 0.0})
        assert abs(result.final_score - 0.6) < 1e-9
        assert result.passed is False  # 0.6 < 0.70

    def test_tc20_raw_score_out_of_range_raises(self, default_eval):
        """TC-20: raw_score > 1.0 → ValueError"""
        with pytest.raises(ValueError):
            default_eval.evaluate("s1", {"coherence": 1.5})


# ── TC-21~25: history / last_result / pass_rate ───────────────────────
class TestHistory:
    def test_tc21_count_increments(self, default_eval, full_pass_scores):
        """TC-21: evaluate() 호출마다 count 증가"""
        for i in range(3):
            default_eval.evaluate(f"s{i}", full_pass_scores)
        assert default_eval.count() == 3

    def test_tc22_history_order(self, default_eval, full_pass_scores, full_fail_scores):
        """TC-22: history() 시간순 보존"""
        default_eval.evaluate("s1", full_pass_scores)
        default_eval.evaluate("s2", full_fail_scores)
        h = default_eval.history()
        assert h[0].scene_id == "s1"
        assert h[1].scene_id == "s2"

    def test_tc23_last_result(self, default_eval, full_pass_scores, full_fail_scores):
        """TC-23: last_result() = 가장 최근 결과"""
        default_eval.evaluate("s1", full_pass_scores)
        default_eval.evaluate("s2", full_fail_scores)
        assert default_eval.last_result().scene_id == "s2"

    def test_tc24_pass_rate_all_pass(self, default_eval, full_pass_scores):
        """TC-24: 모두 PASS → pass_rate = 1.0"""
        for i in range(5):
            default_eval.evaluate(f"s{i}", full_pass_scores)
        assert abs(default_eval.pass_rate() - 1.0) < 1e-9

    def test_tc25_pass_rate_mixed(self, default_eval, full_pass_scores, full_fail_scores):
        """TC-25: 2 PASS, 2 FAIL → pass_rate = 0.5"""
        default_eval.evaluate("s1", full_pass_scores)
        default_eval.evaluate("s2", full_pass_scores)
        default_eval.evaluate("s3", full_fail_scores)
        default_eval.evaluate("s4", full_fail_scores)
        assert abs(default_eval.pass_rate() - 0.5) < 1e-9


# ── TC-26~28: JSONL 영속화 ────────────────────────────────────────────
class TestPersistence:
    def test_tc26_file_created_on_evaluate(self, full_pass_scores):
        """TC-26: evaluate() 후 JSONL 파일 생성"""
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "eval.jsonl"
            ev = ConstitutionEvalV2(db_path=db)
            ev.evaluate("s1", full_pass_scores)
            assert db.exists()

    def test_tc27_file_contains_valid_json(self, full_pass_scores):
        """TC-27: JSONL 파일 — 각 줄이 유효한 JSON"""
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "eval.jsonl"
            ev = ConstitutionEvalV2(db_path=db)
            ev.evaluate("s1", full_pass_scores)
            ev.evaluate("s2", full_pass_scores)
            lines = db.read_text().strip().split("\n")
            assert len(lines) == 2
            for line in lines:
                obj = json.loads(line)
                assert "result_id" in obj

    def test_tc28_reload_from_disk(self, full_pass_scores):
        """TC-28: 재로드 후 이력 복원"""
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "eval.jsonl"
            ev1 = ConstitutionEvalV2(db_path=db)
            ev1.evaluate("s1", full_pass_scores)
            ev1.evaluate("s2", full_pass_scores)

            ev2 = ConstitutionEvalV2(db_path=db)
            assert ev2.count() == 2
            assert ev2.history()[0].scene_id == "s1"


# ── TC-29~31: 엣지 케이스 ────────────────────────────────────────────
class TestEdgeCases:
    def test_tc29_empty_raw_scores(self, default_eval):
        """TC-29: 빈 raw_scores → final_score=0.0, FAIL"""
        result = default_eval.evaluate("s1", {})
        assert result.final_score == 0.0
        assert result.passed is False

    def test_tc30_results_by_scene(self, default_eval, full_pass_scores, full_fail_scores):
        """TC-30: results_by_scene() 필터링"""
        default_eval.evaluate("scene-A", full_pass_scores)
        default_eval.evaluate("scene-B", full_fail_scores)
        default_eval.evaluate("scene-A", full_pass_scores)
        results = default_eval.results_by_scene("scene-A")
        assert len(results) == 2
        assert all(r.scene_id == "scene-A" for r in results)

    def test_tc31_clear_resets_memory(self, default_eval, full_pass_scores):
        """TC-31: clear() 후 count=0, history=[]"""
        default_eval.evaluate("s1", full_pass_scores)
        default_eval.clear()
        assert default_eval.count() == 0
        assert default_eval.history() == []


# ── TC-32~33: 공개 API + 통합 시나리오 ──────────────────────────────
class TestPublicAPIAndIntegration:
    def test_tc32_public_api_from_init(self):
        """TC-32: constitution/__init__.py 공개 API 접근"""
        from literary_system.constitution import (
            ConstitutionEvalV2,
            EvalDimension,
            ConstitutionEvalResult,
            EvalScore,
            EVAL_THRESHOLD,
        )
        assert EVAL_THRESHOLD == 0.70
        ev = ConstitutionEvalV2()
        assert ev.threshold == 0.70

    def test_tc33_integration_batch_evaluate(self):
        """TC-33: 통합 — batch_evaluate 10장면, pass_rate 검증"""
        ev = ConstitutionEvalV2()
        items = []
        for i in range(10):
            # 짝수 인덱스: PASS (0.80), 홀수: FAIL (0.50)
            score_val = 0.80 if i % 2 == 0 else 0.50
            items.append((f"scene-{i}", {n: score_val for n in DEFAULT_DIMENSION_NAMES}))

        results = ev.batch_evaluate(items, evaluator_id="calibration-human-01")
        assert len(results) == 10
        assert ev.count() == 10

        pass_count = sum(1 for r in results if r.passed)
        assert pass_count == 5  # 짝수 5개 PASS
        assert abs(ev.pass_rate() - 0.5) < 1e-9

        # 마지막 결과 evaluator_id 확인
        assert results[-1].evaluator_id == "calibration-human-01"

        # summary() 형식 확인
        last = ev.last_result()
        assert "PASS" in last.summary() or "FAIL" in last.summary()
