"""
V420 통합 테스트 — apps/studio_api v2
ADR-005: baseline 2,897 PASS 유지 + 신규 테스트 추가.
FastAPI/httpx 없으면 단위 테스트로 fallback.
"""
from __future__ import annotations

import pytest
import uuid


# ═══════════════════════════════════════════════════════════════
# A. SchemaMapper 단위 테스트
# ═══════════════════════════════════════════════════════════════

class TestSchemaMapper:
    def test_analyze_request_defaults(self):
        from apps.studio_api.schema.mapper import AnalyzeRequest
        req = AnalyzeRequest(series_id="S1", scene_id="SC1", content="테스트 씬")
        assert req.episode == 1
        assert req.delta_only is True
        assert req.characters == []

    def test_analyze_request_max_length(self):
        from apps.studio_api.schema.mapper import AnalyzeRequest
        from pydantic import ValidationError
        with pytest.raises((ValidationError, ValueError)):
            AnalyzeRequest(
                series_id="S1",
                scene_id="SC1",
                content="x" * 16385,  # max_length=16384 초과
            )

    def test_voice_vector_13d_defaults(self):
        from apps.studio_api.schema.mapper import VoiceVector13D
        v = VoiceVector13D()
        assert v.sentence_length_dist == 0.5
        assert v.metaphor_density == 0.5
        # 13개 필드 확인
        fields = v.model_dump()
        assert len(fields) == 13

    def test_gate_request_required_fields(self):
        from apps.studio_api.schema.mapper import GateRequest
        from pydantic import ValidationError
        with pytest.raises((ValidationError, TypeError)):
            GateRequest()  # series_id 필수

    def test_import_request_schema(self):
        from apps.studio_api.schema.mapper import ImportRequest
        req = ImportRequest(series_id="S2", format="txt", content="본문")
        assert req.series_id == "S2"
        assert req.format == "txt"

    def test_export_request_schema(self):
        from apps.studio_api.schema.mapper import ExportRequest
        req = ExportRequest(
            series_id="S3",
            format="docx",
            scene_ids=["SC1", "SC2"],
        )
        assert len(req.scene_ids) == 2

    def test_cost_ledger_request_schema(self):
        from apps.studio_api.schema.mapper import CostLedgerRequest
        req = CostLedgerRequest(
            series_id="S1",
            operation_type="analyze",
            cost_usd=0.005,
            token_count=1000,
            model="claude-sonnet-4-6",
        )
        assert req.cost_usd == 0.005

    def test_cost_ledger_request_negative_cost_rejected(self):
        from apps.studio_api.schema.mapper import CostLedgerRequest
        from pydantic import ValidationError
        with pytest.raises((ValidationError, ValueError)):
            CostLedgerRequest(
                series_id="S1",
                operation_type="analyze",
                cost_usd=-1.0,
            )

    def test_job_status_response_schema(self):
        from apps.studio_api.schema.mapper import JobStatusResponse
        r = JobStatusResponse(
            job_id="abc",
            status="running",
            progress=50,
            created_at="2026-05-14T00:00:00Z",
            updated_at="2026-05-14T00:01:00Z",
        )
        assert r.status == "running"
        assert r.progress == 50

    def test_extra_fields_ignored(self):
        """Pydantic v2 extra='ignore' 정책 검증."""
        from apps.studio_api.schema.mapper import AnalyzeRequest
        req = AnalyzeRequest(
            series_id="S1",
            scene_id="SC1",
            content="테스트",
            unknown_field="should_be_ignored",  # 무시되어야 함
        )
        assert not hasattr(req, "unknown_field")


# ═══════════════════════════════════════════════════════════════
# B. Auth 미들웨어 단위 테스트
# ═══════════════════════════════════════════════════════════════

class TestAuthMiddleware:
    def test_dev_mode_returns_default_payload(self):
        import os
        os.environ["LITERARY_OS_DEV_MODE"] = "true"
        # 모듈 재로드 없이 함수 직접 호출
        from apps.studio_api.auth.middleware import verify_jwt, TokenPayload
        payload = verify_jwt("any_token")
        assert isinstance(payload, TokenPayload)

    def test_token_payload_defaults(self):
        from apps.studio_api.auth.middleware import TokenPayload
        p = TokenPayload()
        assert p.sub == "dev"
        assert "read" in p.roles
        assert "write" in p.roles

    def test_require_role_passes_with_correct_role(self):
        from apps.studio_api.auth.middleware import TokenPayload, require_role
        payload = TokenPayload(sub="user1", roles=["admin"])
        # 예외 없이 통과해야 함
        require_role("admin")(payload)

    def test_require_role_fails_with_wrong_role(self):
        from apps.studio_api.auth.middleware import TokenPayload, require_role
        from fastapi import HTTPException
        payload = TokenPayload(sub="user1", roles=["read"])
        with pytest.raises(HTTPException) as exc_info:
            require_role("admin")(payload)
        assert exc_info.value.status_code == 403


# ═══════════════════════════════════════════════════════════════
# C. Rate Limiter 단위 테스트
# ═══════════════════════════════════════════════════════════════

class TestRateLimiter:
    def test_allow_within_burst(self):
        from apps.studio_api.ratelimit.bucket import InMemoryTokenBucket
        bucket = InMemoryTokenBucket(rate=10, burst=5)
        for _ in range(5):
            assert bucket.allow("client1") is True

    def test_deny_after_burst(self):
        from apps.studio_api.ratelimit.bucket import InMemoryTokenBucket
        bucket = InMemoryTokenBucket(rate=0, burst=3)  # rate=0 → 충전 없음
        for _ in range(3):
            bucket.allow("client2")
        assert bucket.allow("client2") is False

    def test_different_clients_independent(self):
        from apps.studio_api.ratelimit.bucket import InMemoryTokenBucket
        bucket = InMemoryTokenBucket(rate=0, burst=1)
        bucket.allow("A")
        assert bucket.allow("A") is False
        assert bucket.allow("B") is True  # B는 독립적


# ═══════════════════════════════════════════════════════════════
# D. Job Queue 단위 테스트
# ═══════════════════════════════════════════════════════════════

class TestJobQueue:
    def test_create_job_returns_id(self):
        from apps.studio_api.jobs.queue import create_job, get_job
        job_id = create_job(lambda: {"result": "ok"})
        assert isinstance(job_id, str)
        assert len(job_id) == 36  # UUID

    def test_get_nonexistent_job_returns_none(self):
        from apps.studio_api.jobs.queue import get_job
        assert get_job("nonexistent-id") is None

    def test_cancel_nonexistent_job_returns_false(self):
        from apps.studio_api.jobs.queue import cancel_job
        assert cancel_job("nonexistent-id") is False

    def test_job_initial_status(self):
        import time
        from apps.studio_api.jobs.queue import create_job, get_job
        job_id = create_job(lambda: time.sleep(10))  # 오래 걸리는 작업
        job = get_job(job_id)
        assert job is not None
        assert job["status"] in ("pending", "running", "queued")

    def test_list_jobs(self):
        from apps.studio_api.jobs.queue import create_job, list_jobs
        create_job(lambda: {})
        jobs = list_jobs(limit=10)
        assert isinstance(jobs, list)


# ═══════════════════════════════════════════════════════════════
# E. OTel setup 단위 테스트
# ═══════════════════════════════════════════════════════════════

class TestOtelSetup:
    def test_start_span_context_manager(self):
        from apps.studio_api.otel.setup import start_span
        with start_span("test.op", trace_id="t123") as span:
            span.set_attribute("key", "value")
            span.add_event("test_event", {"x": 1})
        assert span.duration_ms >= 0

    def test_slo_constants(self):
        from apps.studio_api.otel.setup import SLO
        assert SLO["/api/v1/analyze"] == 1.5
        assert SLO["/api/v1/generate"] == 30.0
        assert SLO["/api/v1/gate"] == 5.0


# ═══════════════════════════════════════════════════════════════
# F. Circuit Breaker 단위 테스트
# ═══════════════════════════════════════════════════════════════

class TestCircuitBreaker:
    def test_initial_state_closed(self):
        from apps.studio_api.resilience.circuit_breaker import CircuitBreaker, CBState
        cb = CircuitBreaker("test_cb", failure_threshold=3)
        assert cb.state == CBState.CLOSED

    def test_transitions_to_open_after_threshold(self):
        from apps.studio_api.resilience.circuit_breaker import (
            CircuitBreaker, CBState, CircuitBreakerOpen
        )
        cb = CircuitBreaker("test_cb2", failure_threshold=3, recovery_timeout=9999)
        for _ in range(3):
            try:
                cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
            except ValueError:
                pass
        assert cb.state == CBState.OPEN

    def test_open_raises_circuit_breaker_open(self):
        from apps.studio_api.resilience.circuit_breaker import (
            CircuitBreaker, CBState, CircuitBreakerOpen
        )
        cb = CircuitBreaker("test_cb3", failure_threshold=1, recovery_timeout=9999)
        try:
            cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
        except ValueError:
            pass
        with pytest.raises(CircuitBreakerOpen):
            cb.call(lambda: None)

    def test_reset_returns_to_closed(self):
        from apps.studio_api.resilience.circuit_breaker import (
            CircuitBreaker, CBState
        )
        cb = CircuitBreaker("test_cb4", failure_threshold=1, recovery_timeout=9999)
        try:
            cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
        except ValueError:
            pass
        cb.reset()
        assert cb.state == CBState.CLOSED

    def test_successful_call_returns_value(self):
        from apps.studio_api.resilience.circuit_breaker import CircuitBreaker
        cb = CircuitBreaker("test_cb5")
        result = cb.call(lambda: 42)
        assert result == 42

    def test_status_dict_structure(self):
        from apps.studio_api.resilience.circuit_breaker import CircuitBreaker
        cb = CircuitBreaker("test_cb6")
        status = cb.status()
        assert "name" in status
        assert "state" in status
        assert "failure_count" in status

    def test_preconfigured_instances_exist(self):
        from apps.studio_api.resilience.circuit_breaker import (
            drse_cb, nkg_cb, gate_cb, voice_cb
        )
        assert drse_cb.name == "drse_engine"
        assert gate_cb.failure_threshold == 3  # gate는 3으로 설정


# ═══════════════════════════════════════════════════════════════
# G. main.py v2 팩토리 테스트
# ═══════════════════════════════════════════════════════════════

class TestMainFactory:
    def test_create_studio_app_returns_app(self):
        from apps.studio_api.main import create_studio_app
        app = create_studio_app(out_root="/tmp/v420_test_out")
        assert app is not None

    def test_mock_app_fallback(self):
        from apps.studio_api.main import _MockStudioApp
        mock = _MockStudioApp("/tmp/out", None)
        result = mock.run_generate("테스트 프롬프트")
        assert result["status"] == "mock"

    def test_health_endpoint_registered(self):
        """FastAPI 앱에 /health 라우트 등록 확인."""
        try:
            from fastapi import FastAPI
            from apps.studio_api.main import create_studio_app
            app = create_studio_app()
            routes = [r.path for r in app.routes if hasattr(r, "path")]
            assert "/health" in routes
        except ImportError:
            pytest.skip("FastAPI not installed")

    def test_all_routers_registered(self):
        """V420 신규 라우터 9개 모두 등록 확인."""
        try:
            from fastapi import FastAPI
            from apps.studio_api.main import create_studio_app
            app = create_studio_app()
            paths = {r.path for r in app.routes if hasattr(r, "path")}
            required_paths = {
                "/api/v1/analyze",
                "/api/v1/gate",
                "/api/v1/import",
                "/api/v1/export",
                "/api/v1/cost/ledger",
                "/api/v1/cost/summary",
                "/api/v1/generate",
                "/api/v1/edit",
            }
            for p in required_paths:
                assert p in paths, f"라우트 누락: {p}"
        except ImportError:
            pytest.skip("FastAPI not installed")


# ═══════════════════════════════════════════════════════════════
# H. WebSocket 에너지 스트림 단위 테스트 (로직 레벨)
# ═══════════════════════════════════════════════════════════════

class TestWebSocketEnergy:
    def test_ws_router_registered(self):
        try:
            from fastapi import FastAPI
            from apps.studio_api.ws.energy import router
            assert router is not None
        except ImportError:
            pytest.skip("FastAPI not installed")

    @pytest.mark.asyncio
    async def test_stream_energy_produces_7_updates(self):
        """V426: _stream_energy가 7-레이어 에너지 업데이트를 생성하는지 확인."""
        from apps.studio_api.ws.energy import _stream_energy
        messages = []

        class MockWS:
            async def send_json(self, data):
                messages.append(data)

        await _stream_energy(MockWS(), "S1", "SC1", 1)
        energy_updates = [m for m in messages if m.get("type") == "energy_update"]
        assert len(energy_updates) == 7  # V426: 7-layer
        stream_ends = [m for m in messages if m.get("type") == "stream_end"]
        assert len(stream_ends) == 1


# ═══════════════════════════════════════════════════════════════
# I. Cost Ledger 라우터 로직 테스트
# ═══════════════════════════════════════════════════════════════

class TestCostLedger:
    def test_cost_ledger_in_memory_accumulation(self):
        """인메모리 원장에 항목이 누적되는지 확인."""
        from apps.studio_api.routers import cost as cost_module
        # 원장 초기화
        cost_module._LEDGER.clear()
        cost_module._LEDGER.append({
            "entry_id": str(uuid.uuid4()),
            "series_id": "S1",
            "operation_type": "analyze",
            "cost_usd": 0.01,
            "token_count": 500,
            "model": "test",
            "recorded_by": "tester",
            "timestamp": "2026-05-14T00:00:00Z",
        })
        assert len(cost_module._LEDGER) == 1
        assert cost_module._LEDGER[0]["cost_usd"] == 0.01
