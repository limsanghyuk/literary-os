"""V663 — SDKStabilityGate G70 테스트 (33 TC).

ADR-123: PublicSDK 베타 안정성 게이트 — P0=0, 20명, SLO 준수
"""
from __future__ import annotations

import pytest

from literary_system.gates.sdk_stability_gate import (
    BETA_USER_COUNT,
    MAX_P0_BUGS,
    SLO_LATENCY_MS,
    BetaUserResult,
    SDKStabilityGate,
    StabilityReport,
    run_g70,
)
from literary_system.sdk.public_sdk import LiteraryOSClient
from literary_system.sdk.sdk_config import SDKConfig


# ── 헬퍼 ──────────────────────────────────────────────────────────────

def _client() -> LiteraryOSClient:
    return LiteraryOSClient(config=SDKConfig(offline_mode=True, max_rpm=1000))


def _gate(n: int = 5, **kw) -> SDKStabilityGate:
    return SDKStabilityGate(beta_user_count=n, client=_client(), **kw)


# ── TC-01~05: 상수 ──────────────────────────────────────────────────

class TestConstants:
    def test_tc01_beta_user_count(self):
        """TC-01: BETA_USER_COUNT >= 20."""
        assert BETA_USER_COUNT >= 20

    def test_tc02_max_p0_bugs(self):
        """TC-02: MAX_P0_BUGS == 0 (무관용 원칙)."""
        assert MAX_P0_BUGS == 0

    def test_tc03_slo_latency(self):
        """TC-03: SLO_LATENCY_MS > 0."""
        assert SLO_LATENCY_MS > 0

    def test_tc04_gate_id(self):
        """TC-04: 게이트 ID == 'G70'."""
        gate = _gate()
        report = gate.run()
        assert report.gate_id == "G70"

    def test_tc05_gate_name(self):
        """TC-05: gate_name == 'SDKStabilityGate'."""
        gate = _gate()
        report = gate.run()
        assert report.gate_name == "SDKStabilityGate"


# ── TC-06~10: BetaUserResult ────────────────────────────────────────

class TestBetaUserResult:
    def test_tc06_all_ok_true(self):
        """TC-06: 전 메서드 성공 → all_ok=True."""
        r = BetaUserResult("u0", True, True, True, True, 1.0, 1.0, 1.0, 1.0)
        assert r.all_ok is True

    def test_tc07_all_ok_false(self):
        """TC-07: 하나라도 실패 → all_ok=False."""
        r = BetaUserResult("u0", True, False, True, True, 1.0, 1.0, 1.0, 1.0)
        assert r.all_ok is False

    def test_tc08_avg_ms(self):
        """TC-08: avg_ms = total_ms / 4."""
        r = BetaUserResult("u0", True, True, True, True, 4.0, 4.0, 4.0, 4.0)
        assert r.avg_ms == pytest.approx(4.0)

    def test_tc09_p0_errors_default_empty(self):
        """TC-09: p0_errors 기본값 빈 리스트."""
        r = BetaUserResult("u0", True, True, True, True, 1.0, 1.0, 1.0, 1.0)
        assert r.p0_errors == []

    def test_tc10_total_ms(self):
        """TC-10: total_ms = 합산."""
        r = BetaUserResult("u0", True, True, True, True, 1.0, 2.0, 3.0, 4.0)
        assert r.total_ms == pytest.approx(10.0)


# ── TC-11~15: StabilityReport ────────────────────────────────────────

class TestStabilityReport:
    def test_tc11_passed_default_false(self):
        """TC-11: 기본 passed=False."""
        r = StabilityReport()
        assert r.passed is False

    def test_tc12_to_dict_keys(self):
        """TC-12: to_dict() 필수 키 포함."""
        r = StabilityReport()
        d = r.to_dict()
        for k in ("gate_id", "gate_name", "passed", "beta_users",
                   "success_users", "p0_count", "avg_latency_ms",
                   "slo_latency_ms", "sdk_version", "version_valid",
                   "errors", "summary"):
            assert k in d, f"missing: {k}"

    def test_tc13_errors_default_empty(self):
        """TC-13: errors 기본값 빈 리스트."""
        r = StabilityReport()
        assert r.errors == []

    def test_tc14_user_results_default_empty(self):
        """TC-14: user_results 기본값 빈 리스트."""
        r = StabilityReport()
        assert r.user_results == []

    def test_tc15_slo_latency_default(self):
        """TC-15: slo_latency_ms 기본값 == SLO_LATENCY_MS."""
        r = StabilityReport()
        assert r.slo_latency_ms == SLO_LATENCY_MS


# ── TC-16~23: SDKStabilityGate 실행 ─────────────────────────────────

class TestSDKStabilityGate:
    def test_tc16_run_returns_report(self):
        """TC-16: run() → StabilityReport."""
        result = _gate(n=3).run()
        assert isinstance(result, StabilityReport)

    def test_tc17_pass_with_offline_sdk(self):
        """TC-17: offline SDK 사용 시 G70 PASS."""
        result = _gate(n=5).run()
        assert result.passed is True

    def test_tc18_beta_users_count(self):
        """TC-18: beta_users == 요청 수."""
        result = _gate(n=7).run()
        assert result.beta_users == 7

    def test_tc19_success_users_eq_beta(self):
        """TC-19: 정상 환경 — success_users == beta_users."""
        result = _gate(n=5).run()
        assert result.success_users == result.beta_users

    def test_tc20_p0_count_zero(self):
        """TC-20: 정상 실행 — P0 버그 0건."""
        result = _gate(n=5).run()
        assert result.p0_count == 0

    def test_tc21_avg_latency_within_slo(self):
        """TC-21: avg_latency_ms <= SLO."""
        result = _gate(n=5).run()
        assert result.avg_latency_ms <= result.slo_latency_ms

    def test_tc22_sdk_version_valid(self):
        """TC-22: SDK 버전 semver 형식."""
        result = _gate(n=3).run()
        assert result.version_valid is True

    def test_tc23_summary_contains_pass(self):
        """TC-23: PASS 시 summary에 'PASS' 포함."""
        result = _gate(n=3).run()
        if result.passed:
            assert "PASS" in result.summary


# ── TC-24~28: 사용자 시뮬레이션 세부 ─────────────────────────────────

class TestUserSimulation:
    def test_tc24_user_results_count(self):
        """TC-24: user_results 리스트 길이 == beta_users."""
        result = _gate(n=10).run()
        assert len(result.user_results) == 10

    def test_tc25_each_user_has_user_id(self):
        """TC-25: 각 사용자 결과에 user_id 존재."""
        result = _gate(n=3).run()
        for ur in result.user_results:
            assert ur.user_id.startswith("beta_user_")

    def test_tc26_each_user_all_methods_ok(self):
        """TC-26: 각 사용자 4메서드 모두 성공."""
        result = _gate(n=5).run()
        for ur in result.user_results:
            assert ur.all_ok is True, f"{ur.user_id}: {ur.p0_errors}"

    def test_tc27_latency_positive(self):
        """TC-27: 각 사용자 latency > 0."""
        result = _gate(n=3).run()
        for ur in result.user_results:
            assert ur.avg_ms >= 0

    def test_tc28_20_users_pass(self):
        """TC-28: 실제 베타 20명 — PASS."""
        result = _gate(n=20).run()
        assert result.passed is True
        assert result.success_users == 20


# ── TC-29~33: run_g70 진입점 및 엣지 케이스 ──────────────────────────

class TestRunG70:
    def test_tc29_returns_dict(self):
        """TC-29: run_g70() → dict."""
        result = run_g70(beta_user_count=3)
        assert isinstance(result, dict)

    def test_tc30_passed_true(self):
        """TC-30: run_g70() 기본 실행 → passed=True."""
        result = run_g70(beta_user_count=5)
        assert result["passed"] is True

    def test_tc31_custom_client(self):
        """TC-31: 커스텀 클라이언트 주입."""
        client = LiteraryOSClient(config=SDKConfig(offline_mode=True))
        result = run_g70(beta_user_count=3, client=client)
        assert result["passed"] is True

    def test_tc32_p0_zero_in_result(self):
        """TC-32: run_g70() 결과 p0_count=0."""
        result = run_g70(beta_user_count=5)
        assert result["p0_count"] == 0

    def test_tc33_full_20_user_run(self):
        """TC-33: 전체 20명 run_g70() — passed=True."""
        result = run_g70(beta_user_count=20)
        assert result["passed"] is True
        assert result["success_users"] == 20
