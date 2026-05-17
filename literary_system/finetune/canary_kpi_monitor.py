"""
CanaryKPIMonitor — 카나리 배포 KPI 모니터 (V472)

ADR-017: Canary Deployment (5분 슬라이딩 윈도우, 자동 롤백)

설계:
  - 5분 슬라이딩 윈도우 KPI 집계
  - Coherence / HallucinationRate / SafetyViolationRate 3축
  - 임계 초과 시 자동 롤백 신호 발생
  - LLM-0: 룰 기반 모니터링 (외부 LLM 없음)
"""
from __future__ import annotations

import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any


# ---------------------------------------------------------------------------
# KPI 임계값 (ADR-017)
# ---------------------------------------------------------------------------

KPI_THRESHOLDS = {
    "coherence_min": 0.55,          # 최소 연결성 (낮으면 롤백)
    "hallucination_max": 0.30,      # 최대 허상율 (높으면 롤백)
    "safety_violation_max": 0.05,   # 최대 안전 위반율 (높으면 롤백)
}

WINDOW_MINUTES = 5  # 슬라이딩 윈도우 크기


# ---------------------------------------------------------------------------
# 데이터 클래스
# ---------------------------------------------------------------------------

@dataclass
class KPIRecord:
    record_id: str
    version_id: str
    coherence: float
    hallucination_rate: float
    safety_violation_rate: float
    latency_ms: float
    recorded_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "version_id": self.version_id,
            "coherence": self.coherence,
            "hallucination_rate": self.hallucination_rate,
            "safety_violation_rate": self.safety_violation_rate,
            "latency_ms": self.latency_ms,
            "recorded_at": self.recorded_at,
        }


@dataclass
class KPIWindow:
    """슬라이딩 윈도우 집계 결과"""
    version_id: str
    window_minutes: int
    record_count: int
    avg_coherence: float
    avg_hallucination: float
    avg_safety_violation: float
    avg_latency_ms: float
    rollback_triggered: bool
    rollback_reasons: list[str]
    computed_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "version_id": self.version_id,
            "window_minutes": self.window_minutes,
            "record_count": self.record_count,
            "avg_coherence": self.avg_coherence,
            "avg_hallucination": self.avg_hallucination,
            "avg_safety_violation": self.avg_safety_violation,
            "avg_latency_ms": self.avg_latency_ms,
            "rollback_triggered": self.rollback_triggered,
            "rollback_reasons": self.rollback_reasons,
            "computed_at": self.computed_at,
        }


@dataclass
class RollbackEvent:
    event_id: str
    version_id: str
    reasons: list[str]
    kpi_snapshot: dict[str, float]
    triggered_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "version_id": self.version_id,
            "reasons": self.reasons,
            "kpi_snapshot": self.kpi_snapshot,
            "triggered_at": self.triggered_at,
        }


# ---------------------------------------------------------------------------
# CanaryKPIMonitor
# ---------------------------------------------------------------------------

class CanaryKPIMonitor:
    """
    ADR-017 카나리 KPI 5분 슬라이딩 윈도우 모니터.

    record(version_id, coherence, hallucination_rate, safety_violation_rate)
    evaluate(version_id) → KPIWindow
    is_rollback_required(version_id) → bool
    get_rollback_events(version_id) → list[RollbackEvent]

    LLM-0: 임계값 비교 규칙 기반.
    """

    def __init__(
        self,
        window_minutes: int = WINDOW_MINUTES,
        thresholds: dict[str, float] | None = None,
    ) -> None:
        self._window_minutes = window_minutes
        self._thresholds = thresholds or dict(KPI_THRESHOLDS)
        # version_id → deque of KPIRecord
        self._records: dict[str, deque[KPIRecord]] = {}
        self._rollback_events: list[RollbackEvent] = []

    # ------------------------------------------------------------------
    # KPI 기록
    # ------------------------------------------------------------------

    def record(
        self,
        version_id: str,
        coherence: float,
        hallucination_rate: float,
        safety_violation_rate: float,
        latency_ms: float = 0.0,
    ) -> KPIRecord:
        """KPI 데이터 포인트 기록"""
        now = datetime.now(timezone.utc)
        rec = KPIRecord(
            record_id=str(uuid.uuid4()),
            version_id=version_id,
            coherence=coherence,
            hallucination_rate=hallucination_rate,
            safety_violation_rate=safety_violation_rate,
            latency_ms=latency_ms,
            recorded_at=now.isoformat(),
        )
        if version_id not in self._records:
            self._records[version_id] = deque()
        self._records[version_id].append(rec)

        # 윈도우 밖 레코드 제거
        self._prune_window(version_id, now)
        return rec

    def _prune_window(self, version_id: str, now: datetime) -> None:
        cutoff = now - timedelta(minutes=self._window_minutes)
        cutoff_str = cutoff.isoformat()
        dq = self._records.get(version_id)
        if dq is None:
            return
        while dq and dq[0].recorded_at < cutoff_str:
            dq.popleft()

    # ------------------------------------------------------------------
    # 평가 (슬라이딩 윈도우 집계)
    # ------------------------------------------------------------------

    def evaluate(self, version_id: str) -> KPIWindow:
        """
        최근 N분 KPI 집계 + 롤백 필요 여부 판단.
        """
        now = datetime.now(timezone.utc)
        self._prune_window(version_id, now)
        records = list(self._records.get(version_id, []))

        if not records:
            # 데이터 없음 → 정상 간주
            return KPIWindow(
                version_id=version_id,
                window_minutes=self._window_minutes,
                record_count=0,
                avg_coherence=1.0,
                avg_hallucination=0.0,
                avg_safety_violation=0.0,
                avg_latency_ms=0.0,
                rollback_triggered=False,
                rollback_reasons=[],
                computed_at=now.isoformat(),
            )

        def avg(vals: list[float]) -> float:
            return round(sum(vals) / len(vals), 4) if vals else 0.0

        avg_coh = avg([r.coherence for r in records])
        avg_hall = avg([r.hallucination_rate for r in records])
        avg_safety = avg([r.safety_violation_rate for r in records])
        avg_lat = avg([r.latency_ms for r in records])

        # 롤백 조건 평가
        reasons: list[str] = []
        if avg_coh < self._thresholds["coherence_min"]:
            reasons.append(
                f"Coherence {avg_coh:.3f} < 임계값 {self._thresholds['coherence_min']}"
            )
        if avg_hall > self._thresholds["hallucination_max"]:
            reasons.append(
                f"HallucinationRate {avg_hall:.3f} > 임계값 {self._thresholds['hallucination_max']}"
            )
        if avg_safety > self._thresholds["safety_violation_max"]:
            reasons.append(
                f"SafetyViolationRate {avg_safety:.3f} > 임계값 {self._thresholds['safety_violation_max']}"
            )

        rollback_triggered = len(reasons) > 0
        if rollback_triggered:
            # 중복 이벤트 방지: 동일 버전의 마지막 이벤트가 윈도우 내이면 재생성 안 함
            cutoff = (now - timedelta(minutes=self._window_minutes)).isoformat()
            recent_for_version = [
                e for e in self._rollback_events
                if e.version_id == version_id and e.triggered_at >= cutoff
            ]
            if not recent_for_version:
                evt = RollbackEvent(
                    event_id=str(uuid.uuid4()),
                    version_id=version_id,
                    reasons=reasons,
                    kpi_snapshot={
                        "coherence": avg_coh,
                        "hallucination_rate": avg_hall,
                        "safety_violation_rate": avg_safety,
                    },
                    triggered_at=now.isoformat(),
                )
                self._rollback_events.append(evt)

        return KPIWindow(
            version_id=version_id,
            window_minutes=self._window_minutes,
            record_count=len(records),
            avg_coherence=avg_coh,
            avg_hallucination=avg_hall,
            avg_safety_violation=avg_safety,
            avg_latency_ms=avg_lat,
            rollback_triggered=rollback_triggered,
            rollback_reasons=reasons,
            computed_at=now.isoformat(),
        )

    def is_rollback_required(self, version_id: str) -> bool:
        """롤백 필요 여부 빠른 확인"""
        window = self.evaluate(version_id)
        return window.rollback_triggered

    # ------------------------------------------------------------------
    # 이벤트 조회
    # ------------------------------------------------------------------

    def get_rollback_events(
        self,
        version_id: str | None = None,
    ) -> list[RollbackEvent]:
        if version_id:
            return [e for e in self._rollback_events if e.version_id == version_id]
        return list(self._rollback_events)

    def get_records(
        self,
        version_id: str,
    ) -> list[KPIRecord]:
        return list(self._records.get(version_id, []))
