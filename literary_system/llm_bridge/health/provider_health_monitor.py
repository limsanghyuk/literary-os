"""
V411-E — ProviderHealthMonitor
프로바이더 가용성 실시간 감지 + 자동 폴백 트리거.

설계 원칙:
  - 헬스체크 결과를 HEALTH_CHECK_INTERVAL 동안 캐시 (반복 호출 비용 없음)
  - FAILURE_THRESHOLD 연속 실패 시 DEGRADED 상태로 전환
  - RECOVERY_INTERVAL 경과 후 복구 재확인
  - 테스트 환경에서 is_available() 오버라이드 가능
  - LLM-0 원칙: 헬스체크 자체는 LLM 호출 없음
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

from literary_system.llm_bridge.llm_bridge_interface import LLMBridgeInterface


class ProviderStatus(str, Enum):
    UNKNOWN    = "unknown"
    HEALTHY    = "healthy"
    DEGRADED   = "degraded"
    RECOVERING = "recovering"


@dataclass
class HealthRecord:
    provider_id: str
    status: ProviderStatus = ProviderStatus.UNKNOWN
    last_check_time: float = 0.0
    consecutive_failures: int = 0
    last_error: str = ""
    total_checks: int = 0
    total_failures: int = 0


class ProviderHealthMonitor:
    """등록된 LLM 프로바이더의 가용성을 추적하고 캐시한다."""

    HEALTH_CHECK_INTERVAL: int = 60
    FAILURE_THRESHOLD: int = 3
    RECOVERY_INTERVAL: int = 300
    CHECK_TIMEOUT: int = 5

    def __init__(
        self,
        providers: Optional[Dict[str, LLMBridgeInterface]] = None,
    ) -> None:
        self._providers: Dict[str, LLMBridgeInterface] = providers or {}
        self._records: Dict[str, HealthRecord] = {
            pid: HealthRecord(provider_id=pid)
            for pid in self._providers
        }

    def register(self, provider_id: str, adapter: LLMBridgeInterface) -> None:
        self._providers[provider_id] = adapter
        if provider_id not in self._records:
            self._records[provider_id] = HealthRecord(provider_id=provider_id)

    def is_healthy(self, provider_id: str) -> bool:
        if provider_id not in self._records:
            return False
        record = self._records[provider_id]
        now = time.monotonic()
        if record.status == ProviderStatus.DEGRADED:
            if now - record.last_check_time >= self.RECOVERY_INTERVAL:
                return self._do_check(provider_id)
            return False
        if (record.status == ProviderStatus.UNKNOWN or
                now - record.last_check_time >= self.HEALTH_CHECK_INTERVAL):
            return self._do_check(provider_id)
        return record.status == ProviderStatus.HEALTHY

    def get_healthy_providers(self) -> List[str]:
        return [pid for pid in self._providers if self.is_healthy(pid)]

    def mark_failed(self, provider_id: str, error: str = "") -> None:
        if provider_id not in self._records:
            self._records[provider_id] = HealthRecord(provider_id=provider_id)
        record = self._records[provider_id]
        record.consecutive_failures += 1
        record.total_failures += 1
        if error:
            record.last_error = error
        if record.consecutive_failures >= self.FAILURE_THRESHOLD:
            record.status = ProviderStatus.DEGRADED

    def mark_healthy(self, provider_id: str) -> None:
        if provider_id not in self._records:
            self._records[provider_id] = HealthRecord(provider_id=provider_id)
        record = self._records[provider_id]
        record.consecutive_failures = 0
        record.status = ProviderStatus.HEALTHY

    def force_check(self, provider_id: str) -> bool:
        """캐시 무시하고 즉시 헬스체크 수행. 결과(bool) 반환."""
        return self._do_check(provider_id)

    def get_status(self, provider_id: str) -> Optional[ProviderStatus]:
        """프로바이더 현재 상태 반환 (None이면 미등록)."""
        record = self._records.get(provider_id)
        return record.status if record else None

    def check_all(self) -> dict:
        """모든 등록 프로바이더 즉시 체크 -> {provider_id: bool} 반환."""
        return {pid: self._do_check(pid) for pid in self._providers}

    def _do_check(self, provider_id: str) -> bool:
        """실제 is_available() 호출 후 레코드 갱신. bool 반환."""
        if provider_id not in self._providers:
            return False
        adapter = self._providers[provider_id]
        record = self._records.setdefault(
            provider_id, HealthRecord(provider_id=provider_id)
        )
        record.total_checks += 1
        record.last_check_time = time.monotonic()
        try:
            ok = adapter.is_available()
        except Exception as e:
            ok = False
            record.last_error = str(e)

        if ok:
            record.consecutive_failures = 0
            record.status = ProviderStatus.HEALTHY
        else:
            record.consecutive_failures += 1
            record.total_failures += 1
            if record.consecutive_failures >= self.FAILURE_THRESHOLD:
                record.status = ProviderStatus.DEGRADED

        return ok  # Bug-Fix A: missing return caused force_check() -> None

    def get_record(self, provider_id: str) -> Optional[HealthRecord]:
        return self._records.get(provider_id)

    def all_records(self) -> dict:
        return dict(self._records)
