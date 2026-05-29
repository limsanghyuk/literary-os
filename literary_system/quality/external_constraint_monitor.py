"""
V450: ExternalConstraintMonitor (M-12)
외부 제약 조건 모니터링 모듈.

원칙:
  - 설정된 제약 조건(토큰 한도, 비용 예산, 응답 시간, 컨텍스트 길이 등) 위반 감지
  - 위반 시 즉시 alert_fn 콜백 호출
  - LLM 0회 — 순수 규칙/수치 기반
  - 제약 위반 이력은 append-only ConstraintEvent 목록으로 관리
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── 제약 종류 ─────────────────────────────────────────────────────

CONSTRAINT_TYPES = {
    "token_limit":       "토큰 한도 초과",
    "cost_budget":       "비용 예산 초과",
    "response_time":     "응답 시간 한도 초과",
    "context_length":    "컨텍스트 길이 한도 초과",
    "hallucination_rate":"허상 탐지율 한도 초과",
    "safety_block_rate": "안전 차단율 한도 초과",
    "custom":            "커스텀 제약 위반",
}


@dataclass(frozen=True)
class ConstraintEvent:
    """단일 제약 위반 이벤트 (불변)."""
    event_id:        str
    constraint_type: str
    limit:           float
    observed:        float
    unit:            str
    severity:        str     # "warning" | "critical"
    message:         str
    context:         Dict[str, Any]
    timestamp:       str

    def to_dict(self) -> dict:
        return {
            "event_id":        self.event_id,
            "constraint_type": self.constraint_type,
            "limit":           self.limit,
            "observed":        self.observed,
            "unit":            self.unit,
            "severity":        self.severity,
            "message":         self.message,
            "timestamp":       self.timestamp,
        }


@dataclass
class ConstraintCheckResult:
    """ExternalConstraintMonitor.check() 반환값."""
    passed:     bool
    events:     List[ConstraintEvent]
    checked_at: str

    def to_dict(self) -> dict:
        return {
            "passed":       self.passed,
            "event_count":  len(self.events),
            "events":       [e.to_dict() for e in self.events],
            "checked_at":   self.checked_at,
        }


# ── 기본 제약 조건 세트 ───────────────────────────────────────────

DEFAULT_CONSTRAINTS: Dict[str, float] = {
    "token_limit":        4096.0,   # 토큰
    "cost_budget":        1.00,     # USD per 1K 토큰
    "response_time":      10.0,     # 초
    "context_length":     8192.0,   # 토큰
    "hallucination_rate": 0.30,     # 30%
    "safety_block_rate":  0.10,     # 10%
}

DEFAULT_UNITS: Dict[str, str] = {
    "token_limit":        "tokens",
    "cost_budget":        "USD/1K",
    "response_time":      "seconds",
    "context_length":     "tokens",
    "hallucination_rate": "ratio",
    "safety_block_rate":  "ratio",
}


class ExternalConstraintMonitor:
    """
    외부 제약 조건 모니터링기.

    constraints: {constraint_type: limit_value} — 기본값은 DEFAULT_CONSTRAINTS
    alert_fn:    위반 감지 시 호출되는 콜백 (event: ConstraintEvent) -> None
    """

    def __init__(
        self,
        constraints: Dict[str, float] = None,
        alert_fn:    Callable          = None,
        units:       Dict[str, str]    = None,
    ):
        self.constraints = constraints if constraints is not None else dict(DEFAULT_CONSTRAINTS)
        self.alert_fn    = alert_fn
        self.units       = units if units is not None else dict(DEFAULT_UNITS)
        self._events:    List[ConstraintEvent] = []

    def check(
        self,
        metrics:  Dict[str, float],
        context:  Dict[str, Any] = None,
    ) -> ConstraintCheckResult:
        """
        현재 지표를 제약 조건과 비교해 위반 이벤트를 생성.

        metrics: {constraint_type: observed_value}
        """
        context  = context or {}
        events   = []

        for c_type, observed in metrics.items():
            limit = self.constraints.get(c_type)
            if limit is None:
                continue  # 등록되지 않은 제약은 무시

            if observed > limit:
                severity = "critical" if observed > limit * 1.5 else "warning"
                label    = CONSTRAINT_TYPES.get(c_type, "unknown")
                unit     = self.units.get(c_type, "")
                event    = ConstraintEvent(
                    event_id=str(uuid.uuid4())[:8],
                    constraint_type=c_type,
                    limit=limit,
                    observed=observed,
                    unit=unit,
                    severity=severity,
                    message=f"{label}: {observed}{unit} > 한도 {limit}{unit}",
                    context=dict(context),
                    timestamp=_now_iso(),
                )
                events.append(event)
                self._events.append(event)

                if self.alert_fn is not None:
                    try:
                        self.alert_fn(event)
                    except Exception:
                        pass  # alert 실패는 모니터링을 막지 않음

        return ConstraintCheckResult(
            passed=len(events) == 0,
            events=events,
            checked_at=_now_iso(),
        )

    def add_constraint(self, c_type: str, limit: float, unit: str = "") -> None:
        """런타임에 새 제약 추가."""
        self.constraints[c_type] = limit
        if unit:
            self.units[c_type] = unit

    def remove_constraint(self, c_type: str) -> bool:
        """제약 제거. 존재했으면 True 반환."""
        removed = c_type in self.constraints
        self.constraints.pop(c_type, None)
        self.units.pop(c_type, None)
        return removed

    def all_events(self) -> List[ConstraintEvent]:
        return list(self._events)

    def critical_events(self) -> List[ConstraintEvent]:
        return [e for e in self._events if e.severity == "critical"]

    def stats(self) -> dict:
        total    = len(self._events)
        critical = len(self.critical_events())
        warning  = total - critical
        types    = list({e.constraint_type for e in self._events})
        return {
            "total_events":    total,
            "critical_count":  critical,
            "warning_count":   warning,
            "constraint_types_violated": types,
        }
