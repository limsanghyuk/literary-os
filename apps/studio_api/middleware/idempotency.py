"""
V420: Idempotency-Key 미들웨어
클라이언트가 Idempotency-Key 헤더를 포함하면 동일 키의 재시도 요청에
캐시된 응답을 반환한다. POST 메서드에만 적용.
TTL: 24시간 (인메모리 — V430 Redis 교체 예정).
"""
from __future__ import annotations

import hashlib
import json
import time
from typing import Any

try:
    from fastapi import Request, Response
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.types import ASGIApp
    _FA = True
except ImportError:
    _FA = False

_CACHE: dict[str, dict[str, Any]] = {}  # key → {body, status_code, headers, ts}
_TTL = 86_400  # 24h


def _evict_expired() -> None:
    now = time.time()
    expired = [k for k, v in _CACHE.items() if now - v["ts"] > _TTL]
    for k in expired:
        del _CACHE[k]


if _FA:
    class IdempotencyMiddleware(BaseHTTPMiddleware):
        """
        POST 요청의 Idempotency-Key 헤더를 처리.
        동일 키 재요청 → 캐시 응답 반환 (429 없음, 멱등 보장).
        """

        async def dispatch(self, request: Request, call_next):
            idem_key = request.headers.get("Idempotency-Key")

            # GET/HEAD 등은 패스
            if request.method != "POST" or not idem_key:
                return await call_next(request)

            # 캐시 키: Idempotency-Key + path (경로가 다르면 별도)
            cache_key = hashlib.sha256(
                f"{idem_key}:{request.url.path}".encode()
            ).hexdigest()

            _evict_expired()

            if cache_key in _CACHE:
                cached = _CACHE[cache_key]
                return Response(
                    content=cached["body"],
                    status_code=cached["status_code"],
                    headers={
                        **cached["headers"],
                        "X-Idempotency-Replayed": "true",
                    },
                    media_type="application/json",
                )

            response = await call_next(request)

            # 성공 응답만 캐시 (2xx)
            if 200 <= response.status_code < 300:
                body = b""
                async for chunk in response.body_iterator:
                    body += chunk
                _CACHE[cache_key] = {
                    "body": body,
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "ts": time.time(),
                }
                return Response(
                    content=body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type="application/json",
                )

            return response

else:
    class IdempotencyMiddleware:  # type: ignore
        """FastAPI 미설치 환경 — 더미."""
        def __init__(self, app=None):
            self.app = app
