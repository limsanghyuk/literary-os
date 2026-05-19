"""
Literary OS V460 -- ProductionMonitor

SLO 추적 (ADR-015 v2):
  - API 응답 p95 < 3s (베타) / < 2s (GA)
  - 가용성 99.0% (베타) / 99.5% (GA)
  - AlertRule: 임계값 초과 시 자동 알림 (alert_fn 주입)
  - SLOReport: 시간 윈도우별 SLO 달성 현황

LLM-0: alert_fn 주입으로 실 알림 API(PagerDuty 등) 격리.
"""
from __future__ import annotations

import statistics
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# 열거형
# ---------------------------------------------------------------------------

class SLOTier(str, Enum):
    BETA = "BETA"   # p95 < 3s, 99.0%
    GA   = "GA"     # p95 < 2s, 99.5%


class AlertSeverity(str, Enum):
    INFO     = "INFO"
    WARNING  = "WARNING"
    CRITICAL = "CRITICAL"


class RequestOutcome(str, Enum):
    SUCCESS = "SUCCESS"
    ERROR   = "ERROR"
    TIMEOUT = "TIMEOUT"


# ---------------------------------------------------------------------------
# 요청 메트릭 샘플
# ---------------------------------------------------------------------------

@dataclass
class RequestSample:
    """단건 요청 메트릭."""
    tenant_id:    str
    latency_ms:   float
    outcome:      RequestOutcome
    sampled_at:   datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    endpoint:     str = ""


# ---------------------------------------------------------------------------
# SLO 보고서
# ---------------------------------------------------------------------------

@dataclass
class SLOReport:
    """SLO 달성 현황 보고서."""
    tenant_id:         str
    tier:              SLOTier
    window_minutes:    int
    total_requests:    int
    success_count:     int
    p95_latency_ms:    float
    p50_latency_ms:    float
    availability_pct:  float
    slo_p95_target_ms: float
    slo_avail_target:  float
    p95_ok:            bool
    avail_ok:          bool
    overall_ok:        bool
    generated_at:      datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "tenant_id":        self.tenant_id,
            "tier":             self.tier.value,
            "window_minutes":   self.window_minutes,
            "total_requests":   self.total_requests,
            "p95_latency_ms":   round(self.p95_latency_ms, 1),
            "p50_latency_ms":   round(self.p50_latency_ms, 1),
            "availability_pct": round(self.availability_pct, 4),
            "p95_target_ms":    self.slo_p95_target_ms,
            "avail_target":     self.slo_avail_target,
            "p95_ok":           self.p95_ok,
            "avail_ok":         self.avail_ok,
            "overall_ok":       self.overall_ok,
        }


# ---------------------------------------------------------------------------
# 알림 규칙
# ---------------------------------------------------------------------------

@dataclass
class AlertRule:
    """SLO 알림 규칙."""
    rule_id:    str
    name:       str
    severity:   AlertSeverity
    condition:  str   # 사람이 읽기 위한 설명
    # 실제 조건 함수: (SLOReport) -> bool
    check_fn:   Callable[["SLOReport"], bool] = field(repr=False)


@dataclass
class AlertEvent:
    """발생한 알림 이벤트."""
    rule_id:    str
    rule_name:  str
    severity:   AlertSeverity
    tenant_id:  str
    message:    str
    fired_at:   datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "rule_id":  self.rule_id,
            "severity": self.severity.value,
            "tenant_id": self.tenant_id,
            "message":  self.message,
            "fired_at": self.fired_at.isoformat(),
        }


# ---------------------------------------------------------------------------
# ProductionMonitor
# ---------------------------------------------------------------------------

class ProductionMonitor:
    """
    Literary OS V460 Production Monitor.

    ADR-015 v2 SLO:
      BETA: p95 < 3000ms, availability >= 99.0%
      GA  : p95 < 2000ms, availability >= 99.5%

    LLM-0: alert_fn 주입.
    """

    # SLO 기준 (ms, %)
    _SLO_TABLE: Dict[SLOTier, Tuple[float, float]] = {
        SLOTier.BETA: (3000.0, 0.990),
        SLOTier.GA:   (2000.0, 0.995),
    }

    def __init__(
        self,
        tier:      SLOTier = SLOTier.BETA,
        alert_fn:  Optional[Callable[[AlertEvent], None]] = None,
        max_samples_per_tenant: int = 10_000,
    ):
        self._tier     = tier
        self._alert_fn = alert_fn
        self._max      = max_samples_per_tenant
        self._samples: Dict[str, List[RequestSample]] = {}
        self._alerts:  List[AlertEvent] = []
        self._rules:   List[AlertRule] = self._default_rules()
        self._lock = threading.Lock()

    # ── 메트릭 수집 ──────────────────────────────────────────────────────────

    def record(self, sample: RequestSample) -> None:
        """요청 샘플 기록."""
        with self._lock:
            tid = sample.tenant_id
            if tid not in self._samples:
                self._samples[tid] = []
            buf = self._samples[tid]
            buf.append(sample)
            # 오래된 샘플 순환 삭제
            if len(buf) > self._max:
                self._samples[tid] = buf[-self._max:]

    def record_batch(self, samples: List[RequestSample]) -> None:
        for s in samples:
            self.record(s)

    # ── SLO 보고서 생성 ───────────────────────────────────────────────────────

    def get_slo_report(
        self,
        tenant_id:      str,
        window_minutes: int = 60,
    ) -> SLOReport:
        """최근 window_minutes 분 내 SLO 달성 현황 계산."""
        p95_target, avail_target = self._SLO_TABLE[self._tier]

        with self._lock:
            samples = self._samples.get(tenant_id, [])

        # 윈도우 필터
        now = datetime.now(timezone.utc)
        cutoff_ts = now.timestamp() - window_minutes * 60
        windowed = [s for s in samples if s.sampled_at.timestamp() >= cutoff_ts]

        if not windowed:
            return SLOReport(
                tenant_id=tenant_id,
                tier=self._tier,
                window_minutes=window_minutes,
                total_requests=0,
                success_count=0,
                p95_latency_ms=0.0,
                p50_latency_ms=0.0,
                availability_pct=1.0,
                slo_p95_target_ms=p95_target,
                slo_avail_target=avail_target,
                p95_ok=True,
                avail_ok=True,
                overall_ok=True,
            )

        latencies = sorted(s.latency_ms for s in windowed)
        success_count = sum(1 for s in windowed if s.outcome == RequestOutcome.SUCCESS)
        total = len(windowed)

        p95 = self._percentile(latencies, 95)
        p50 = self._percentile(latencies, 50)
        avail = success_count / total if total > 0 else 1.0

        p95_ok   = p95 <= p95_target
        avail_ok = avail >= avail_target

        report = SLOReport(
            tenant_id=tenant_id,
            tier=self._tier,
            window_minutes=window_minutes,
            total_requests=total,
            success_count=success_count,
            p95_latency_ms=p95,
            p50_latency_ms=p50,
            availability_pct=avail,
            slo_p95_target_ms=p95_target,
            slo_avail_target=avail_target,
            p95_ok=p95_ok,
            avail_ok=avail_ok,
            overall_ok=p95_ok and avail_ok,
        )

        self._evaluate_rules(report)
        return report

    def get_global_report(self, window_minutes: int = 60) -> dict:
        """전체 테넌트 집계 보고서."""
        with self._lock:
            tenant_ids = list(self._samples.keys())
        reports = [self.get_slo_report(tid, window_minutes) for tid in tenant_ids]
        slo_ok = sum(1 for r in reports if r.overall_ok)
        return {
            "tier":             self._tier.value,
            "total_tenants":    len(reports),
            "slo_ok_count":     slo_ok,
            "slo_fail_count":   len(reports) - slo_ok,
            "global_slo_pass":  slo_ok == len(reports),
        }

    # ── 알림 ─────────────────────────────────────────────────────────────────

    def get_alerts(
        self,
        tenant_id: Optional[str] = None,
        severity:  Optional[AlertSeverity] = None,
        limit:     int = 50,
    ) -> List[AlertEvent]:
        with self._lock:
            evts = list(self._alerts)
        if tenant_id:
            evts = [e for e in evts if e.tenant_id == tenant_id]
        if severity:
            evts = [e for e in evts if e.severity == severity]
        return evts[-limit:]

    def add_rule(self, rule: AlertRule) -> None:
        with self._lock:
            self._rules.append(rule)

    # ── 내부 ─────────────────────────────────────────────────────────────────

    def _evaluate_rules(self, report: SLOReport) -> None:
        for rule in self._rules:
            try:
                if rule.check_fn(report):
                    msg = (
                        f"[{rule.severity.value}] {rule.name} | "
                        f"tenant={report.tenant_id} "
                        f"p95={report.p95_latency_ms:.0f}ms "
                        f"avail={report.availability_pct:.3%}"
                    )
                    evt = AlertEvent(
                        rule_id=rule.rule_id,
                        rule_name=rule.name,
                        severity=rule.severity,
                        tenant_id=report.tenant_id,
                        message=msg,
                    )
                    with self._lock:
                        self._alerts.append(evt)
                    if self._alert_fn:
                        try:
                            self._alert_fn(evt)
                        except Exception:
                            pass
            except Exception:
                pass

    @staticmethod
    def _percentile(sorted_vals: List[float], pct: int) -> float:
        if not sorted_vals:
            return 0.0
        idx = int(len(sorted_vals) * pct / 100)
        idx = min(idx, len(sorted_vals) - 1)
        return sorted_vals[idx]

    @staticmethod
    def _default_rules() -> List[AlertRule]:
        return [
            AlertRule(
                rule_id="P95_BREACH",
                name="p95 레이턴시 SLO 위반",
                severity=AlertSeverity.CRITICAL,
                condition="p95 > SLO 목표",
                check_fn=lambda r: not r.p95_ok and r.total_requests >= 10,
            ),
            AlertRule(
                rule_id="AVAIL_BREACH",
                name="가용성 SLO 위반",
                severity=AlertSeverity.CRITICAL,
                condition="availability < SLO 목표",
                check_fn=lambda r: not r.avail_ok and r.total_requests >= 10,
            ),
            AlertRule(
                rule_id="P95_WARNING",
                name="p95 레이턴시 경고 (SLO 80% 초과)",
                severity=AlertSeverity.WARNING,
                condition="p95 > SLO * 0.8",
                check_fn=lambda r: r.p95_ok and r.p95_latency_ms > r.slo_p95_target_ms * 0.8 and r.total_requests >= 5,
            ),
        ]
