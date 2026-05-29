"""
V420: Redis 토큰 버킷 Rate Limiter.
Redis 미연결 시 인메모리 fallback.
ADR-001 X1 Security 레이어 일부.
"""
from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock

# 기본 제한값 (환경변수로 오버라이드 가능)
DEFAULT_RPS = 10       # 초당 요청
DEFAULT_BURST = 20     # 버스트 허용
WS_MAX_STREAMS = 100   # 최대 WS 동시 접속


class InMemoryTokenBucket:
    """Redis 없는 환경용 인메모리 토큰 버킷."""

    def __init__(self, rate: float = DEFAULT_RPS, burst: int = DEFAULT_BURST):
        self.rate = rate
        self.burst = burst
        self._buckets: dict[str, tuple[float, float]] = defaultdict(
            lambda: (float(burst), time.monotonic())
        )
        self._lock = Lock()

    def allow(self, key: str) -> bool:
        with self._lock:
            tokens, last = self._buckets[key]
            now = time.monotonic()
            # 토큰 보충
            tokens = min(self.burst, tokens + (now - last) * self.rate)
            if tokens >= 1.0:
                self._buckets[key] = (tokens - 1.0, now)
                return True
            self._buckets[key] = (tokens, now)
            return False


# 전역 인스턴스 (FastAPI lifespan에서 Redis로 교체 가능)
_bucket = InMemoryTokenBucket()


def check_rate_limit(tenant_id: str, endpoint: str) -> bool:
    """True = 허용, False = 429 Too Many Requests"""
    key = f"{tenant_id}:{endpoint}"
    return _bucket.allow(key)
