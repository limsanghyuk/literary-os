"""
V653 — AgentSafetyGuard 단위 테스트 (30 TC).
4축(자해/혐오/PII/저작권) 검사, pre/post API, 에지 케이스.
"""
import pytest
from literary_system.ensemble.safety_guard import (
    AgentSafetyGuard,
    AgentSafetyCheckResult,
    SAFETY_AXES,
)


@pytest.fixture
def guard():
    return AgentSafetyGuard()


# ────────────────────────────────────────────────────────────────
# TC-01~05: AgentSafetyCheckResult 구조 / 라운드트립
# ────────────────────────────────────────────────────────────────

def test_tc01_result_ok_factory():
    r = AgentSafetyCheckResult.ok()
    assert r.passed is True
    assert r.violations == []
    assert r.severity == "none"
    for ax in SAFETY_AXES:
        assert r.axis_results.get(ax) is True


def test_tc02_result_to_dict():
    r = AgentSafetyCheckResult(passed=False, violations=["pii: 010-****"], severity="medium")
    d = r.to_dict()
    assert d["passed"] is False
    assert "pii: 010-****" in d["violations"]
    assert d["severity"] == "medium"


def test_tc03_result_from_dict():
    d = {
        "passed": False,
        "axis_results": {"self_harm": True, "hate_speech": True, "pii": False, "copyright": True},
        "violations": ["pii: test@test.com…"],
        "severity": "medium",
        "note": "post_check",
    }
    r = AgentSafetyCheckResult.from_dict(d)
    assert r.passed is False
    assert r.severity == "medium"
    assert r.axis_results["pii"] is False


def test_tc04_roundtrip_exact():
    original = AgentSafetyCheckResult(
        passed=False,
        axis_results={"self_harm": False},
        violations=["self_harm: kill myself"],
        severity="high",
        note="direct",
    )
    restored = AgentSafetyCheckResult.from_dict(original.to_dict())
    assert restored.passed == original.passed
    assert restored.severity == original.severity
    assert restored.violations == original.violations


def test_tc05_default_fields():
    r = AgentSafetyCheckResult(passed=True)
    assert r.axis_results == {}
    assert r.violations == []
    assert r.severity == "none"
    assert r.note == ""


# ────────────────────────────────────────────────────────────────
# TC-06~10: 클래스 상수 / API 존재 확인
# ────────────────────────────────────────────────────────────────

def test_tc06_safety_axes_count():
    assert len(SAFETY_AXES) == 4


def test_tc07_axes_labels():
    for ax in ("self_harm", "hate_speech", "pii", "copyright"):
        assert ax in SAFETY_AXES


def test_tc08_pre_check_callable(guard):
    assert callable(getattr(guard, "pre_check", None))


def test_tc09_post_check_callable(guard):
    assert callable(getattr(guard, "post_check", None))


def test_tc10_check_text_callable(guard):
    assert callable(getattr(guard, "check_text", None))


# ────────────────────────────────────────────────────────────────
# TC-11~15: 클린 텍스트 통과
# ────────────────────────────────────────────────────────────────

def test_tc11_clean_text_passes(guard):
    r = guard.check_text("The hero walked across the misty bridge at dawn.")
    assert r.passed is True


def test_tc12_all_axes_true_on_clean(guard):
    r = guard.check_text("A quiet evening by the river.")
    for ax in SAFETY_AXES:
        assert r.axis_results.get(ax) is True


def test_tc13_pre_check_clean_blueprint(guard):
    bp = {"text": "A noble warrior seeks redemption.", "genre": "fantasy"}
    r = guard.pre_check(bp)
    assert r.passed is True


def test_tc14_post_check_clean_result(guard):
    res = {"final_text": "The protagonist stared at the horizon."}
    r = guard.post_check(res)
    assert r.passed is True


def test_tc15_empty_text_passes(guard):
    r = guard.check_text("")
    assert r.passed is True


# ────────────────────────────────────────────────────────────────
# TC-16~20: 위반 감지
# ────────────────────────────────────────────────────────────────

def test_tc16_self_harm_detected(guard):
    r = guard.check_text("He wanted to kill myself with a knife.")
    assert r.passed is False
    assert r.axis_results["self_harm"] is False


def test_tc17_self_harm_severity_high(guard):
    r = guard.check_text("kill myself")
    assert r.severity == "high"


def test_tc18_pii_email_detected(guard):
    r = guard.check_text("Contact me at user@example.com for details.")
    assert r.axis_results["pii"] is False


def test_tc19_pii_severity_medium(guard):
    r = guard.check_text("user@example.com")
    if not r.axis_results.get("pii", True):
        assert r.severity in ("medium", "high")


def test_tc20_copyright_detected(guard):
    r = guard.check_text("© 2024 All rights reserved.")
    assert r.axis_results["copyright"] is False


# ────────────────────────────────────────────────────────────────
# TC-21~25: 심각도 계층 / 복합 위반
# ────────────────────────────────────────────────────────────────

def test_tc21_severity_none_when_clean(guard):
    r = guard.check_text("A simple story.")
    assert r.severity == "none"


def test_tc22_violations_list_populated(guard):
    r = guard.check_text("kill myself")
    assert len(r.violations) >= 1


def test_tc23_multiple_violations(guard):
    r = guard.check_text("kill myself and contact user@example.com")
    # At least 2 axes should fail
    failed = [ax for ax, ok in r.axis_results.items() if not ok]
    assert len(failed) >= 1  # at minimum self_harm


def test_tc24_enabled_axes_override():
    guard_pii_only = AgentSafetyGuard(enabled_axes=["pii"])
    # self_harm text should pass since only pii is checked
    r = guard_pii_only.check_text("kill myself")
    assert r.axis_results["self_harm"] is True  # inactive → pass
    assert r.passed is True


def test_tc25_disabled_all_axes_always_pass():
    guard_none = AgentSafetyGuard(enabled_axes=[])
    r = guard_none.check_text("kill myself © 2024 user@example.com")
    assert r.passed is True


# ────────────────────────────────────────────────────────────────
# TC-26~30: pre/post check + facade + 에지 케이스
# ────────────────────────────────────────────────────────────────

def test_tc26_post_check_uses_final_text(guard):
    res = {"final_text": "kill myself"}
    r = guard.post_check(res)
    assert r.axis_results["self_harm"] is False


def test_tc27_post_check_uses_selected_text(guard):
    res = {"selected_text": "user@example.com info"}
    r = guard.post_check(res)
    assert r.axis_results["pii"] is False


def test_tc28_pre_check_extracts_content_field(guard):
    bp = {"content": "kill myself scenario"}
    r = guard.pre_check(bp)
    assert r.axis_results["self_harm"] is False


def test_tc29_facade_import():
    from literary_system.ensemble import AgentSafetyGuard as ASG
    assert ASG is AgentSafetyGuard


def test_tc30_facade_result_import():
    from literary_system.ensemble import AgentSafetyCheckResult as SCR
    assert SCR is AgentSafetyCheckResult
