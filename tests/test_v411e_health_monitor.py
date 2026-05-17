"""V411-E 테스트 — ProviderHealthMonitor."""
from __future__ import annotations
import time
import pytest
from literary_system.llm_bridge.health.provider_health_monitor import (
    ProviderHealthMonitor, ProviderStatus, HealthRecord
)
from literary_system.llm_bridge.mock_llm_bridge import MockLLMBridge


class _AlwaysAvailable(MockLLMBridge):
    def is_available(self): return True

class _NeverAvailable(MockLLMBridge):
    def is_available(self): return False


# ── 1. 기본 생성 ─────────────────────────────────────────────────
def test_create_empty():
    mon = ProviderHealthMonitor()
    assert mon.get_healthy_providers() == []


# ── 2. register ──────────────────────────────────────────────────
def test_register_provider():
    mon = ProviderHealthMonitor()
    mon.register("mock", MockLLMBridge())
    assert "mock" in mon._providers


# ── 3. is_healthy — 항상 가용 어댑터 ─────────────────────────────
def test_is_healthy_always_available():
    p = _AlwaysAvailable()
    p._provider_id = "ok_provider"  # get_provider_id() 위해
    mon = ProviderHealthMonitor({"ok": p})
    assert mon.is_healthy("ok") == True


# ── 4. is_healthy — 항상 불가 어댑터 ─────────────────────────────
def test_is_healthy_never_available():
    p = _NeverAvailable()
    mon = ProviderHealthMonitor({"bad": p})
    assert mon.is_healthy("bad") == False


# ── 5. is_healthy — 미등록 프로바이더 ────────────────────────────
def test_is_healthy_unknown_provider():
    mon = ProviderHealthMonitor()
    assert mon.is_healthy("nonexistent") == False


# ── 6. get_healthy_providers ─────────────────────────────────────
def test_get_healthy_providers():
    mon = ProviderHealthMonitor({
        "good": _AlwaysAvailable(),
        "bad":  _NeverAvailable(),
    })
    healthy = mon.get_healthy_providers()
    assert "good" in healthy
    assert "bad" not in healthy


# ── 7. mark_failed 단일 ──────────────────────────────────────────
def test_mark_failed_single():
    p = _AlwaysAvailable()
    mon = ProviderHealthMonitor({"p": p})
    mon.mark_failed("p", "timeout")
    rec = mon.get_record("p")
    assert rec.consecutive_failures == 1
    assert rec.last_error == "timeout"


# ── 8. mark_failed FAILURE_THRESHOLD → DEGRADED ──────────────────
def test_mark_failed_threshold():
    mon = ProviderHealthMonitor()
    mon.register("p", _AlwaysAvailable())
    for _ in range(ProviderHealthMonitor.FAILURE_THRESHOLD):
        mon.mark_failed("p")
    assert mon.get_status("p") == ProviderStatus.DEGRADED


# ── 9. mark_healthy 초기화 ───────────────────────────────────────
def test_mark_healthy_resets():
    mon = ProviderHealthMonitor()
    mon.register("p", _NeverAvailable())
    for _ in range(3):
        mon.mark_failed("p")
    mon.mark_healthy("p")
    rec = mon.get_record("p")
    assert rec.consecutive_failures == 0
    assert rec.status == ProviderStatus.HEALTHY


# ── 10. force_check 캐시 무시 ────────────────────────────────────
def test_force_check_bypasses_cache():
    p = _AlwaysAvailable()
    mon = ProviderHealthMonitor({"p": p})
    mon.mark_failed("p"); mon.mark_failed("p"); mon.mark_failed("p")
    # DEGRADED 상태지만 force_check는 실제 어댑터 호출
    result = mon.force_check("p")
    assert result == True
    assert mon.get_status("p") == ProviderStatus.HEALTHY


# ── 11. check_all ─────────────────────────────────────────────────
def test_check_all():
    mon = ProviderHealthMonitor({
        "good": _AlwaysAvailable(),
        "bad":  _NeverAvailable(),
    })
    results = mon.check_all()
    assert results["good"] == True
    assert results["bad"]  == False


# ── 12. DEGRADED 상태 is_healthy == False ────────────────────────
def test_degraded_is_not_healthy():
    mon = ProviderHealthMonitor()
    mon.register("p", _NeverAvailable())
    for _ in range(3):
        mon.mark_failed("p")
    assert mon.is_healthy("p") == False


# ── 13. HealthRecord 필드 확인 ───────────────────────────────────
def test_health_record_fields():
    rec = HealthRecord(provider_id="test")
    assert rec.status == ProviderStatus.UNKNOWN
    assert rec.consecutive_failures == 0
    assert rec.total_checks == 0


# ── 14. total_checks 누적 ────────────────────────────────────────
def test_total_checks_accumulate():
    mon = ProviderHealthMonitor({"p": _AlwaysAvailable()})
    mon.force_check("p")
    mon.force_check("p")
    rec = mon.get_record("p")
    assert rec.total_checks >= 2


# ── 15. ProviderStatus 열거값 ────────────────────────────────────
def test_provider_status_values():
    assert ProviderStatus.HEALTHY  == "healthy"
    assert ProviderStatus.DEGRADED == "degraded"
    assert ProviderStatus.UNKNOWN  == "unknown"


# ── 16. 빈 providers로 check_all ─────────────────────────────────
def test_check_all_empty():
    mon = ProviderHealthMonitor()
    assert mon.check_all() == {}


# ── 17. register 후 is_healthy ───────────────────────────────────
def test_register_then_check():
    mon = ProviderHealthMonitor()
    mon.register("new", _AlwaysAvailable())
    assert mon.is_healthy("new") == True


# ── 18. 예외 발생 어댑터 처리 ────────────────────────────────────
def test_adapter_raises_exception():
    class ExceptionAdapter(MockLLMBridge):
        def is_available(self): raise RuntimeError("conn refused")
    mon = ProviderHealthMonitor({"err": ExceptionAdapter()})
    assert mon.is_healthy("err") == False
    rec = mon.get_record("err")
    assert "conn refused" in rec.last_error


# ── 19. get_record None for unknown ──────────────────────────────
def test_get_record_unknown():
    mon = ProviderHealthMonitor()
    assert mon.get_record("nope") is None


# ── 20. mark_failed 미등록 프로바이더 생성 ───────────────────────
def test_mark_failed_creates_record():
    mon = ProviderHealthMonitor()
    mon.mark_failed("new_provider", "test_error")
    rec = mon.get_record("new_provider")
    assert rec is not None
    assert rec.last_error == "test_error"
