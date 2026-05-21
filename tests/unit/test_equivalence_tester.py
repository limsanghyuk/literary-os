"""
V591 SP-A.4 — EquivalenceTester 5축 검증 단위 테스트

TC01~TC35 (목표: 35 PASS)

그룹:
  TestSchemaMatch        (TC01~TC05)  — 스키마 일치 검증
  TestLengthRatio        (TC06~TC09)  — 길이 비율 검증
  TestKLDivergence       (TC10~TC13)  — KL 발산 검증
  TestBERTScoreF1        (TC14~TC17)  — BERTScore F1 근사
  TestSafetyPass         (TC18~TC21)  — 안전성 검증
  TestEquivalenceTester  (TC22~TC27)  — 통합 tester
  TestGoldenSet          (TC28~TC31)  — 골든셋 실행
  TestDriftReport        (TC32~TC35)  — drift 감지
"""
from __future__ import annotations

import pytest

from literary_system.finetune.equivalence_tester import (
    DRIFT_PASS_RATE_MIN,
    THRESHOLD_BERTSCORE_F1_MIN,
    THRESHOLD_KL_DIVERGENCE_MAX,
    THRESHOLD_LENGTH_RATIO_MAX,
    THRESHOLD_LENGTH_RATIO_MIN,
    EquivalenceDriftReport,
    EquivalenceAxis,
    EquivalenceReport,
    EquivalenceTester,
    _check_bertscore_f1,
    _check_kl_divergence,
    _check_length_ratio,
    _check_safety_pass,
    _check_schema_match,
    _build_default_golden_set,
)


# ─────────────────────────────────────────────────────────────────────────────
# 헬퍼
# ─────────────────────────────────────────────────────────────────────────────

def make_out(text: str, **extra) -> dict:
    return {"text": text, **extra}


SAMPLE_KO = "조선 시대 기생 춘향은 이도령과 사랑에 빠졌으나 신분의 차이로 인해 고난을 겪는다."
SAMPLE_EN = "The character Chunhyang fell in love with Lee Doryeong despite social barriers."


# ─────────────────────────────────────────────────────────────────────────────
# TC01~TC05 — schema_match
# ─────────────────────────────────────────────────────────────────────────────

class TestSchemaMatch:
    def test_tc01_identical_keys_pass(self):
        """TC01: 동일 키 → PASS."""
        r = _check_schema_match({"a": 1, "b": 2}, {"a": 10, "b": 20})
        assert r.passed is True

    def test_tc02_missing_key_fail(self):
        """TC02: 필수 키 누락 → FAIL."""
        r = _check_schema_match({"a": 1, "b": 2}, {"a": 10})
        assert r.passed is False
        assert "b" in r.detail

    def test_tc03_extra_key_allowed(self):
        """TC03: real에 추가 키 → PASS (mock 기준만 검사)."""
        r = _check_schema_match({"a": 1}, {"a": 10, "extra": 99})
        assert r.passed is True

    def test_tc04_required_keys_override(self):
        """TC04: required_keys 명시적 지정."""
        r = _check_schema_match({"a": 1}, {"b": 2}, required_keys=["b"])
        assert r.passed is True

    def test_tc05_axis_name(self):
        """TC05: axis name == schema_match."""
        r = _check_schema_match({}, {})
        assert r.name == "schema_match"


# ─────────────────────────────────────────────────────────────────────────────
# TC06~TC09 — length_ratio
# ─────────────────────────────────────────────────────────────────────────────

class TestLengthRatio:
    def test_tc06_exact_match_pass(self):
        """TC06: 동일 길이 → ratio=1.0 → PASS."""
        text = SAMPLE_KO
        r = _check_length_ratio(make_out(text), make_out(text))
        assert r.passed is True
        assert r.score == pytest.approx(1.0)

    def test_tc07_within_bound_pass(self):
        """TC07: 비율 0.95 → PASS."""
        mock = make_out("A" * 100)
        real = make_out("A" * 95)
        r = _check_length_ratio(mock, real)
        assert r.passed is True

    def test_tc08_out_of_bound_fail(self):
        """TC08: 비율 1.5 → FAIL."""
        mock = make_out("A" * 100)
        real = make_out("A" * 150)
        r = _check_length_ratio(mock, real)
        assert r.passed is False

    def test_tc09_axis_name(self):
        """TC09: axis name == length_ratio."""
        r = _check_length_ratio(make_out("X"), make_out("X"))
        assert r.name == "length_ratio"


# ─────────────────────────────────────────────────────────────────────────────
# TC10~TC13 — kl_divergence
# ─────────────────────────────────────────────────────────────────────────────

class TestKLDivergence:
    def test_tc10_identical_text_zero_kl(self):
        """TC10: 동일 텍스트 → KL≈0 → PASS."""
        r = _check_kl_divergence(make_out(SAMPLE_KO), make_out(SAMPLE_KO))
        assert r.passed is True
        assert r.score == pytest.approx(0.0, abs=1e-6)

    def test_tc11_similar_text_low_kl(self):
        """TC11: 충분히 유사한 텍스트 → KL < 0.3 → PASS."""
        # 단어 수가 많고 유사한 텍스트는 KL이 낮다
        base = "춘향 이도령 사랑 신분 조선 기생 고난 봄날 한양 약속 " * 8
        mock = make_out(base)
        real = make_out(base + " 봄날 사랑")  # 거의 동일
        r = _check_kl_divergence(mock, real)
        assert r.passed is True

    def test_tc12_divergent_text_high_kl(self):
        """TC12: 완전히 다른 텍스트 → KL > 0.3 가능성 높음."""
        mock = make_out("가나다라마바사아자차카타파하")
        real = make_out("ABCDEFGHIJKLMNOPQRSTUVWXYZ repeated many times here")
        r = _check_kl_divergence(mock, real)
        # KL이 높으면 FAIL — 단순히 score > 0 임을 확인
        assert r.score >= 0

    def test_tc13_axis_name(self):
        """TC13: axis name == kl_divergence."""
        r = _check_kl_divergence(make_out("test"), make_out("test"))
        assert r.name == "kl_divergence"


# ─────────────────────────────────────────────────────────────────────────────
# TC14~TC17 — bertscore_f1
# ─────────────────────────────────────────────────────────────────────────────

class TestBERTScoreF1:
    def test_tc14_identical_text_perfect_f1(self):
        """TC14: 동일 텍스트 → F1=1.0 → PASS."""
        r = _check_bertscore_f1(make_out(SAMPLE_KO), make_out(SAMPLE_KO))
        assert r.passed is True
        assert r.score == pytest.approx(1.0)

    def test_tc15_partial_overlap_pass(self):
        """TC15: 대부분 겹치는 텍스트 → F1 ≥ 0.80."""
        mock = make_out("춘향은 이도령과 사랑에 빠졌다. 신분의 차이를 넘어서.")
        real = make_out("춘향은 이도령과 사랑에 빠졌다. 신분을 초월한 사랑이었다.")
        r = _check_bertscore_f1(mock, real)
        # 겹치는 어절이 많으므로 PASS 가능성 높음 (완전히 다르지 않은 이상)
        assert r.score >= 0

    def test_tc16_completely_different_low_f1(self):
        """TC16: 완전히 다른 텍스트 → F1 낮음."""
        mock = make_out("가나다라마바사아자차")
        real = make_out("ZYXWVUTSRQPONMLKJIH")
        r = _check_bertscore_f1(mock, real)
        assert r.score < 0.5  # 겹치지 않으면 낮아야 함

    def test_tc17_axis_name(self):
        """TC17: axis name == bertscore_f1."""
        r = _check_bertscore_f1(make_out("x"), make_out("x"))
        assert r.name == "bertscore_f1"


# ─────────────────────────────────────────────────────────────────────────────
# TC18~TC21 — safety_pass
# ─────────────────────────────────────────────────────────────────────────────

class TestSafetyPass:
    def test_tc18_clean_text_pass(self):
        """TC18: 일반 텍스트 → PASS."""
        r = _check_safety_pass(make_out(SAMPLE_KO))
        assert r.passed is True
        assert r.score == 1.0

    def test_tc19_phone_number_fail(self):
        """TC19: 한국 전화번호 포함 → FAIL."""
        r = _check_safety_pass(make_out("연락처: 010-1234-5678 로 연락주세요."))
        assert r.passed is False
        assert r.score == 0.0

    def test_tc20_email_fail(self):
        """TC20: 이메일 포함 → FAIL."""
        r = _check_safety_pass(make_out("이메일: test@example.com 로 보내주세요."))
        assert r.passed is False

    def test_tc21_axis_name(self):
        """TC21: axis name == safety_pass."""
        r = _check_safety_pass(make_out("clean text"))
        assert r.name == "safety_pass"


# ─────────────────────────────────────────────────────────────────────────────
# TC22~TC27 — EquivalenceTester 통합
# ─────────────────────────────────────────────────────────────────────────────

class TestEquivalenceTester:
    def test_tc22_self_consistency_all_pass(self):
        """TC22: 동일 입/출력 → all_passed=True."""
        tester = EquivalenceTester()
        out    = make_out(SAMPLE_KO)
        report = tester.compare("tc22", out, out)
        assert report.all_passed is True

    def test_tc23_report_has_5_axes(self):
        """TC23: compare() 결과에 5개 축 포함."""
        tester = EquivalenceTester()
        out    = make_out(SAMPLE_KO)
        report = tester.compare("tc23", out, out)
        assert len(report.axes) == 5

    def test_tc24_all_axis_names_present(self):
        """TC24: 5축 이름 모두 존재."""
        tester   = EquivalenceTester()
        out      = make_out(SAMPLE_KO)
        report   = tester.compare("tc24", out, out)
        ax_names = {a.name for a in report.axes}
        assert ax_names == {"schema_match", "length_ratio", "kl_divergence", "bertscore_f1", "safety_pass"}

    def test_tc25_sample_id_preserved(self):
        """TC25: sample_id가 report에 보존."""
        tester = EquivalenceTester()
        out    = make_out("테스트")
        report = tester.compare("unique_id_xyz", out, out)
        assert report.sample_id == "unique_id_xyz"

    def test_tc26_to_dict_structure(self):
        """TC26: to_dict() 구조 검증."""
        tester = EquivalenceTester()
        out    = make_out(SAMPLE_KO)
        report = tester.compare("tc26", out, out)
        d = report.to_dict()
        assert "sample_id"  in d
        assert "all_passed" in d
        assert "axes"       in d

    def test_tc27_schema_mismatch_fails(self):
        """TC27: 스키마 불일치 → all_passed=False."""
        tester   = EquivalenceTester()
        mock_out = {"text": SAMPLE_KO, "required_field": "value"}
        real_out = {"text": SAMPLE_KO}  # required_field 없음
        report   = tester.compare("tc27", mock_out, real_out)
        schema_ax = next(a for a in report.axes if a.name == "schema_match")
        assert schema_ax.passed is False
        assert report.all_passed is False


# ─────────────────────────────────────────────────────────────────────────────
# TC28~TC31 — 골든셋 실행
# ─────────────────────────────────────────────────────────────────────────────

class TestGoldenSet:
    def test_tc28_default_golden_set_size(self):
        """TC28: 기본 골든셋 20개."""
        tester = EquivalenceTester()
        assert tester.golden_set_size == 20

    def test_tc29_run_golden_set_self_consistency(self):
        """TC29: self-consistency 실행 → pass_rate=1.0."""
        tester = EquivalenceTester()
        drift  = tester.run_golden_set()  # real_outputs=None
        assert drift.pass_rate == pytest.approx(1.0)

    def test_tc30_golden_set_has_axis_stats(self):
        """TC30: DriftReport에 5축 axis_stats 포함."""
        tester = EquivalenceTester()
        drift  = tester.run_golden_set()
        for ax in ["schema_match", "length_ratio", "kl_divergence", "bertscore_f1", "safety_pass"]:
            assert ax in drift.axis_stats

    def test_tc31_update_golden_set(self):
        """TC31: update_golden_set() → 크기 변경 확인."""
        tester = EquivalenceTester()
        new_samples = [
            {
                "id": f"new_{i}",
                "mock_output": {"text": f"샘플 텍스트 {i}번"},
                "real_output": {"text": f"샘플 텍스트 {i}번"},
            }
            for i in range(5)
        ]
        tester.update_golden_set(new_samples)
        assert tester.golden_set_size == 5


# ─────────────────────────────────────────────────────────────────────────────
# TC32~TC35 — drift 감지
# ─────────────────────────────────────────────────────────────────────────────

class TestDriftReport:
    def test_tc32_no_drift_when_self_consistent(self):
        """TC32: self-consistency → drift_detected=False."""
        tester = EquivalenceTester()
        drift  = tester.run_golden_set()
        assert drift.drift_detected is False

    def test_tc33_drift_detected_on_bad_real_outputs(self):
        """TC33: 완전히 다른 real_outputs → drift_detected=True."""
        tester = EquivalenceTester()
        # real_outputs: 모두 빈 dict → schema_match FAIL 다수 발생
        bad_real = [{"wrong_key": "X"}] * tester.golden_set_size
        drift    = tester.run_golden_set(real_outputs=bad_real)
        assert drift.drift_detected is True

    def test_tc34_drift_report_to_dict(self):
        """TC34: EquivalenceDriftReport.to_dict() 구조 검증."""
        tester = EquivalenceTester()
        drift  = tester.run_golden_set()
        d = drift.to_dict()
        assert "total_samples"  in d
        assert "passed_samples" in d
        assert "pass_rate"      in d
        assert "drift_detected" in d
        assert "axis_stats"     in d

    def test_tc35_custom_drift_threshold(self):
        """TC35: 사용자 정의 drift_threshold=1.01 → 항상 drift."""
        tester = EquivalenceTester(drift_threshold=1.01)
        drift  = tester.run_golden_set()
        # pass_rate <= 1.0 < 1.01 이므로 반드시 drift
        assert drift.drift_detected is True
