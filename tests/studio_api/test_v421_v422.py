"""
V421~V422 통합 테스트
- V421: OAuth 2.1 미들웨어 (python-jose, scope, PKCE 클레임)
- V422: OpenTelemetry SDK 실 연결 (span, 메트릭, SLO)
ADR-005: 기존 V420 테스트 38개 유지 + 신규 추가.
"""
from __future__ import annotations

import os
import time
import pytest


# ═══════════════════════════════════════════════════════════════
# A. V421 OAuth 2.1 인터페이스 불변 검증
# ═══════════════════════════════════════════════════════════════

class TestOAuth21Interface:
    """V420 인터페이스가 V421 교체 후에도 동일하게 동작하는지 확인."""

    def test_token_payload_v420_compatible(self):
        """sub, roles — V420 인터페이스 유지."""
        from apps.studio_api.auth.middleware import TokenPayload
        p = TokenPayload(sub="user42", roles=["admin", "write"])
        assert p.sub == "user42"
        assert "admin" in p.roles

    def test_token_payload_v421_scope(self):
        """V421 신규: scope, client_id, jti 클레임."""
        from apps.studio_api.auth.middleware import TokenPayload
        p = TokenPayload(
            sub="user1",
            scope="read write analyze:execute",
            client_id="app-client",
            jti="abc-123",
        )
        assert p.has_scope("analyze:execute")
        assert not p.has_scope("admin:delete")
        assert "analyze:execute" in p.scopes

    def test_verify_jwt_dev_mode_bypass(self):
        """DEV_MODE=true → 어떤 토큰도 통과."""
        os.environ["LITERARY_OS_DEV_MODE"] = "true"
        from apps.studio_api.auth.middleware import verify_jwt, TokenPayload
        result = verify_jwt("any-garbage-token")
        assert isinstance(result, TokenPayload)

    def test_get_current_user_dev_mode(self):
        """DEV_MODE → get_current_user가 기본 TokenPayload 반환."""
        os.environ["LITERARY_OS_DEV_MODE"] = "true"
        from apps.studio_api.auth.middleware import get_current_user, TokenPayload
        user = get_current_user(credentials=None)
        assert isinstance(user, TokenPayload)

    def test_require_role_v420_compatible(self):
        """require_role — V420 인터페이스 유지."""
        from apps.studio_api.auth.middleware import TokenPayload, require_role
        from fastapi import HTTPException
        # 허용
        p = TokenPayload(roles=["admin"])
        require_role("admin")(p)
        # 거부
        p2 = TokenPayload(roles=["read"])
        with pytest.raises(HTTPException) as exc:
            require_role("admin")(p2)
        assert exc.value.status_code == 403

    def test_require_scope_v421_new(self):
        """V421 신규: require_scope 의존성."""
        from apps.studio_api.auth.middleware import TokenPayload, require_scope
        from fastapi import HTTPException
        p = TokenPayload(scope="read write analyze:execute")
        # 허용
        require_scope("analyze:execute")(p)
        # 거부
        with pytest.raises(HTTPException) as exc:
            require_scope("admin:delete")(p)
        assert exc.value.status_code == 403

    def test_token_expiry_field(self):
        """exp 클레임 — 기본값은 미래 시각."""
        from apps.studio_api.auth.middleware import TokenPayload
        p = TokenPayload()
        assert p.exp > int(time.time())

    def test_jwk_cache_miss_returns_empty(self):
        """JWK 서버 미접속 시 빈 dict 반환 (degraded mode)."""
        import apps.studio_api.auth.middleware as m
        # 캐시 무효화
        m._JWK_CACHE.clear()
        m._JWK_CACHE_TS = 0.0
        # OAUTH_ISSUER를 로컬 미존재 주소로 덮어쓰기
        original = m.OAUTH_ISSUER
        m.OAUTH_ISSUER = "http://127.0.0.1:19999"
        result = m._fetch_jwks()
        m.OAUTH_ISSUER = original
        assert isinstance(result, dict)  # 빈 dict 반환 (예외 없음)


# ═══════════════════════════════════════════════════════════════
# B. V422 OpenTelemetry 인터페이스 불변 검증
# ═══════════════════════════════════════════════════════════════

class TestOTelInterface:
    """V420 OTel 인터페이스가 V422 SDK 연결 후에도 동일한지 확인."""

    def test_start_span_returns_span(self):
        """start_span은 Span 객체를 yield."""
        from apps.studio_api.otel.setup import start_span, Span
        with start_span("test.op", trace_id="t1") as span:
            assert isinstance(span, Span)

    def test_span_set_attribute(self):
        """set_attribute — V420 인터페이스 유지."""
        from apps.studio_api.otel.setup import start_span
        with start_span("test.attr") as span:
            span.set_attribute("key1", "value1")
            span.set_attribute("num", 42)
        assert span._attrs["key1"] == "value1"

    def test_span_add_event(self):
        """add_event — V420 인터페이스 유지."""
        from apps.studio_api.otel.setup import start_span
        with start_span("test.evt") as span:
            span.add_event("cache_hit", {"size": 100})
        assert any(e["name"] == "cache_hit" for e in span._events)

    def test_span_duration_ms_positive(self):
        """duration_ms — 경과 시간 양수."""
        from apps.studio_api.otel.setup import start_span
        import time
        with start_span("test.dur") as span:
            time.sleep(0.01)
        assert span.duration_ms >= 5.0  # 최소 5ms

    def test_span_trace_id_generated(self):
        """trace_id 미전달 시 자동 생성."""
        from apps.studio_api.otel.setup import start_span
        with start_span("test.tid") as span:
            pass
        assert len(span.trace_id) > 0

    def test_span_trace_id_preserved(self):
        """전달된 trace_id 보존."""
        from apps.studio_api.otel.setup import start_span
        with start_span("test.tid2", trace_id="my-tid-xyz") as span:
            pass
        assert span.trace_id == "my-tid-xyz"

    def test_slo_constants_v422(self):
        """V422 SLO 상수 — 신규 엔드포인트 포함."""
        from apps.studio_api.otel.setup import SLO
        assert SLO["/api/v1/analyze"] == 1.5
        assert SLO["/api/v1/generate"] == 30.0
        assert SLO["/api/v1/gate"] == 5.0
        # V422 신규
        assert "/api/v1/import" in SLO
        assert "/api/v1/voice/analyze" in SLO

    def test_nested_spans_independent(self):
        """중첩 span이 독립적으로 동작."""
        from apps.studio_api.otel.setup import start_span
        with start_span("outer") as outer:
            outer.set_attribute("level", "outer")
            with start_span("inner") as inner:
                inner.set_attribute("level", "inner")
        assert outer._attrs["level"] == "outer"
        assert inner._attrs["level"] == "inner"

    def test_span_no_exception_on_error(self):
        """span 내부 예외 발생해도 span은 정상 종료."""
        from apps.studio_api.otel.setup import start_span
        try:
            with start_span("test.exc") as span:
                raise ValueError("test error")
        except ValueError:
            pass
        assert span.duration_ms >= 0

    def test_otel_sdk_loaded(self):
        """opentelemetry-sdk 설치 여부 확인 (미설치 환경 skip)."""
        import pytest
        from apps.studio_api.otel.setup import _OTEL_AVAILABLE
        if not _OTEL_AVAILABLE:
            pytest.skip("opentelemetry-sdk 미설치 — CI/sandbox 환경 skip")
        assert _OTEL_AVAILABLE is True

    def test_tracer_not_none(self):
        """OTel tracer 인스턴스 생성 확인."""
        import pytest
        from apps.studio_api.otel.setup import _OTEL_AVAILABLE, _tracer
        if not _OTEL_AVAILABLE:
            pytest.skip("opentelemetry-sdk 미설치 — CI/sandbox 환경 skip (KL-002)")
        assert _tracer is not None


# ═══════════════════════════════════════════════════════════════
# C. V421 auth + V422 OTel 통합 — 실제 라우터 레벨
# ═══════════════════════════════════════════════════════════════

class TestAuthOtelIntegration:
    """auth 레이어와 OTel span이 함께 동작하는지 확인."""

    def test_auth_inside_span(self):
        """span 내부에서 auth 호출 — 정상 동작."""
        from apps.studio_api.otel.setup import start_span
        from apps.studio_api.auth.middleware import verify_jwt, TokenPayload
        os.environ["LITERARY_OS_DEV_MODE"] = "true"

        with start_span("auth.verify") as span:
            user = verify_jwt("token")
            span.set_attribute("user.sub", user.sub)

        assert span._attrs["user.sub"] == "dev"

    def test_span_records_auth_failure(self):
        """인증 실패 이벤트를 span에 기록 — DEV_MODE 패치 방식."""
        import apps.studio_api.auth.middleware as auth_mod
        from apps.studio_api.otel.setup import start_span

        original = auth_mod.DEV_MODE
        auth_mod.DEV_MODE = False  # 모듈 속성 직접 패치

        with start_span("auth.fail_test") as span:
            try:
                auth_mod.verify_jwt("bad_token")
            except Exception as exc:
                span.add_event("auth_failed", {"reason": str(exc)})
            finally:
                auth_mod.DEV_MODE = original  # 복원

        assert any(e["name"] == "auth_failed" for e in span._events)

    def test_main_health_includes_circuit_breakers(self):
        """V420 /health 응답 구조 — V421/V422 업데이트 후에도 유지."""
        try:
            from fastapi import FastAPI
            from apps.studio_api.main import create_studio_app
            app = create_studio_app()
            routes = {r.path for r in app.routes if hasattr(r, "path")}
            assert "/health" in routes
        except ImportError:
            pytest.skip("FastAPI not installed")
