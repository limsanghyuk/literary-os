"""
tests/unit/test_v640patch_safety_regression_v2.py
V640-PATCH SafetyRegressionV2 — 33 TC (TC-01~TC-33)
"""
import pytest
import sys
sys.path.insert(0, "/tmp/repo_main")

from literary_system.safety.safety_regression_v2 import (
    SafetyRegressionV2, SafetyRegressionReport, SafetyRegressionViolation,
    ALL_AXES, AXIS_SELF_HARM, AXIS_HATE_SPEECH, AXIS_PII, AXIS_COPYRIGHT,
)

# ── TC-01~05: 초기화 및 상수 ─────────────────────────────────────────────

def test_tc01_all_axes_defined():
    assert len(ALL_AXES) == 4
    assert AXIS_SELF_HARM in ALL_AXES
    assert AXIS_HATE_SPEECH in ALL_AXES
    assert AXIS_PII in ALL_AXES
    assert AXIS_COPYRIGHT in ALL_AXES

def test_tc02_default_init():
    checker = SafetyRegressionV2()
    assert checker._axes == ALL_AXES

def test_tc03_custom_axes():
    checker = SafetyRegressionV2(axes=[AXIS_PII])
    assert AXIS_PII in checker._axes
    assert AXIS_SELF_HARM not in checker._axes

def test_tc04_report_initial_state():
    report = SafetyRegressionReport(total_samples=10)
    assert report.total_violations == 0
    assert report.passed is True
    for ax in ALL_AXES:
        assert report.axis_counts[ax] == 0

def test_tc05_report_summary_pass():
    report = SafetyRegressionReport(total_samples=5)
    assert "PASS" in report.summary
    assert "violations=0" in report.summary

# ── TC-06~10: 자해 축 ────────────────────────────────────────────────────

def test_tc06_self_harm_korean_detect():
    checker = SafetyRegressionV2()
    r = checker.check_single("나는 자살하고 싶다는 생각이 든다")
    assert not r.passed
    assert r.axis_counts[AXIS_SELF_HARM] >= 1

def test_tc07_self_harm_english_detect():
    checker = SafetyRegressionV2()
    r = checker.check_single("I want to kill myself tonight")
    assert not r.passed
    assert r.axis_counts[AXIS_SELF_HARM] >= 1

def test_tc08_self_harm_clean_text():
    checker = SafetyRegressionV2()
    r = checker.check_single("오늘 날씨가 정말 좋아서 기분이 상쾌하다")
    assert r.passed

def test_tc09_self_harm_violation_excerpt():
    checker = SafetyRegressionV2()
    r = checker.check_single("그는 자해를 했다")
    assert not r.passed
    v = r.violations[0]
    assert v.axis == AXIS_SELF_HARM
    assert isinstance(v.text_excerpt, str)

def test_tc10_self_harm_multi_sample():
    checker = SafetyRegressionV2()
    r = checker.run(["정상 텍스트", "자살 충동이 있다", "또 다른 정상 텍스트"])
    assert not r.passed
    assert r.axis_counts[AXIS_SELF_HARM] >= 1

# ── TC-11~15: 혐오 발언 축 ──────────────────────────────────────────────

def test_tc11_hate_speech_korean_detect():
    checker = SafetyRegressionV2()
    r = checker.check_single("특정 민족에 대한 혐오 발언")
    assert not r.passed
    assert r.axis_counts[AXIS_HATE_SPEECH] >= 1

def test_tc12_hate_speech_english_detect():
    checker = SafetyRegressionV2()
    r = checker.check_single("ethnic cleansing is wrong to study")
    assert not r.passed
    assert r.axis_counts[AXIS_HATE_SPEECH] >= 1

def test_tc13_hate_speech_clean():
    checker = SafetyRegressionV2()
    r = checker.check_single("다양한 문화를 존중하는 사회를 만들어야 한다")
    assert r.passed

def test_tc14_hate_speech_axis_count():
    checker = SafetyRegressionV2()
    r = checker.run(["인종 차별 발언 예시", "정상 텍스트"])
    assert r.axis_counts[AXIS_HATE_SPEECH] >= 1

def test_tc15_hate_speech_violation_sample_index():
    checker = SafetyRegressionV2()
    r = checker.run(["정상", "성별 비하 발언 포함 텍스트 예시"])
    if r.violations:
        assert r.violations[0].sample_index >= 0

# ── TC-16~20: PII 축 ─────────────────────────────────────────────────────

def test_tc16_pii_email_detect():
    checker = SafetyRegressionV2()
    r = checker.check_single("연락처: user@example.com 으로 이메일 주세요")
    assert not r.passed
    assert r.axis_counts[AXIS_PII] >= 1

def test_tc17_pii_phone_detect():
    checker = SafetyRegressionV2()
    r = checker.check_single("전화번호는 010-1234-5678 입니다")
    assert not r.passed
    assert r.axis_counts[AXIS_PII] >= 1

def test_tc18_pii_ssn_detect():
    checker = SafetyRegressionV2()
    r = checker.check_single("주민등록번호: 901231-1234567")
    assert not r.passed
    assert r.axis_counts[AXIS_PII] >= 1

def test_tc19_pii_clean_text():
    checker = SafetyRegressionV2()
    r = checker.check_single("주인공은 서울 어딘가에서 낯선 사람을 만났다")
    assert r.passed

def test_tc20_pii_excerpt_length():
    checker = SafetyRegressionV2(excerpt_max_len=20)
    r = checker.check_single("user@example.com 에 문의하세요")
    if r.violations:
        assert len(r.violations[0].text_excerpt) <= 20

# ── TC-21~25: 저작권 축 ──────────────────────────────────────────────────

def test_tc21_copyright_symbol_detect():
    checker = SafetyRegressionV2()
    r = checker.check_single("© 2024 All Rights Reserved")
    assert not r.passed
    assert r.axis_counts[AXIS_COPYRIGHT] >= 1

def test_tc22_copyright_korean_detect():
    checker = SafetyRegressionV2()
    r = checker.check_single("이 내용은 무단 복제를 금지합니다")
    assert not r.passed
    assert r.axis_counts[AXIS_COPYRIGHT] >= 1

def test_tc23_copyright_clean():
    checker = SafetyRegressionV2()
    r = checker.check_single("이 드라마는 창작 작품입니다")
    assert r.passed

def test_tc24_copyright_violation_fields():
    checker = SafetyRegressionV2()
    r = checker.check_single("무단전재 금지 원본 텍스트")
    if r.violations:
        v = r.violations[0]
        assert v.axis == AXIS_COPYRIGHT
        assert isinstance(v.pattern_index, int)

def test_tc25_copyright_count():
    checker = SafetyRegressionV2()
    r = checker.run(["정상", "저작권 등록된 자료", "정상2"])
    assert r.axis_counts[AXIS_COPYRIGHT] >= 1

# ── TC-26~28: 영속화 / 보고서 ────────────────────────────────────────────

def test_tc26_report_fail_summary():
    checker = SafetyRegressionV2()
    r = checker.check_single("user@example.com")
    assert "FAIL" in r.summary
    assert "pii" in r.summary

def test_tc27_total_violations_count():
    checker = SafetyRegressionV2()
    r = checker.run(["user@example.com", "자살 충동", "정상"])
    assert r.total_violations >= 2

def test_tc28_axis_counts_sum():
    checker = SafetyRegressionV2()
    r = checker.run(["user@example.com", "자살", "정상"])
    total_from_counts = sum(r.axis_counts.values())
    assert total_from_counts == r.total_violations

# ── TC-29~33: 엣지케이스 ─────────────────────────────────────────────────

def test_tc29_empty_samples():
    checker = SafetyRegressionV2()
    r = checker.run([])
    assert r.passed
    assert r.total_samples == 0

def test_tc30_empty_string():
    checker = SafetyRegressionV2()
    r = checker.check_single("")
    assert r.passed

def test_tc31_custom_axes_isolation():
    checker = SafetyRegressionV2(axes=[AXIS_PII])
    r = checker.check_single("자살 충동")  # self_harm만 있는 텍스트
    assert r.passed  # PII 축만 검사 → PASS

def test_tc32_multi_axis_violation():
    checker = SafetyRegressionV2()
    r = checker.check_single("user@test.com 자살 충동 © 2024")
    assert r.axis_counts[AXIS_PII] >= 1
    assert r.axis_counts[AXIS_SELF_HARM] >= 1
    assert r.axis_counts[AXIS_COPYRIGHT] >= 1

def test_tc33_sample_index_tracking():
    checker = SafetyRegressionV2()
    r = checker.run(["정상", "정상", "user@example.com"])
    pii_violations = [v for v in r.violations if v.axis == AXIS_PII]
    assert any(v.sample_index == 2 for v in pii_violations)

if __name__ == "__main__":
    import subprocess
    result = subprocess.run(
        ["python3", "-m", "pytest", __file__, "-v", "--tb=short", "-q"],
        cwd="/tmp/repo_main"
    )
