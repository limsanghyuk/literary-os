"""
literary_system/ops/analytics_dashboard.py
V478 — AnalyticsDashboard + PublicAPIDoc v2 (ADR-015)

인터페이스:
  track_event(name, user_id, props) → None
  compute_nps(scores) → float
  cohort_analysis(events, window_days) → CohortReport
  generate_openapi() → dict

LLM-0 준수: 순수 계산, 외부 의존 없음
"""
from __future__ import annotations

import statistics
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

# ── 데이터 모델 ──────────────────────────────────────────────

@dataclass
class AnalyticsEvent:
    event_id:   str
    name:       str
    user_id:    str
    timestamp:  float = field(default_factory=time.time)
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CohortReport:
    window_days:    int
    total_users:    int
    returning:      int
    churned:        int
    retention_rate: float   # 0~1
    churn_rate:     float   # 0~1


@dataclass
class NPSResult:
    score:      float   # -100~100
    promoters:  int     # 9~10
    passives:   int     # 7~8
    detractors: int     # 0~6
    total:      int


# ── AnalyticsDashboard ───────────────────────────────────────

class AnalyticsDashboard:
    """
    사용자 행동 분석 + NPS + 코호트 대시보드.
    """

    def __init__(self) -> None:
        self._events: List[AnalyticsEvent] = []
        self._counter: int = 0

    # ── 이벤트 추적 ─────────────────────────────────────────

    def track_event(
        self,
        name: str,
        user_id: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> AnalyticsEvent:
        self._counter += 1
        evt = AnalyticsEvent(
            event_id=f"evt_{self._counter:06d}",
            name=name,
            user_id=user_id,
            properties=properties or {},
        )
        self._events.append(evt)
        return evt

    def event_count(self) -> int:
        return len(self._events)

    def events_by_name(self, name: str) -> List[AnalyticsEvent]:
        return [e for e in self._events if e.name == name]

    def unique_users(self) -> int:
        return len({e.user_id for e in self._events})

    # ── NPS 계산 ────────────────────────────────────────────

    def compute_nps(self, scores: List[int]) -> NPSResult:
        """
        Net Promoter Score 계산.
        scores: 0~10 정수 리스트
        """
        if not scores:
            raise ValueError("compute_nps: 점수 없음")
        for s in scores:
            if not (0 <= s <= 10):
                raise ValueError(f"compute_nps: 유효하지 않은 점수 {s} (0~10)")

        promoters  = sum(1 for s in scores if s >= 9)
        passives   = sum(1 for s in scores if 7 <= s <= 8)
        detractors = sum(1 for s in scores if s <= 6)
        total      = len(scores)

        nps = round(((promoters - detractors) / total) * 100, 1)
        return NPSResult(
            score=nps,
            promoters=promoters,
            passives=passives,
            detractors=detractors,
            total=total,
        )

    # ── 코호트 분석 ──────────────────────────────────────────

    def cohort_analysis(
        self,
        window_days: int = 30,
        reference_event: str = "login",
    ) -> CohortReport:
        """
        window_days 기간 내 재방문율 / 이탈율 계산.
        """
        now = time.time()
        cutoff = now - window_days * 86400

        # window 이전에 첫 이벤트가 있는 사용자 = 기존 사용자
        all_users: Dict[str, float] = {}
        for e in self._events:
            if e.user_id not in all_users or e.timestamp < all_users[e.user_id]:
                all_users[e.user_id] = e.timestamp

        existing = {uid for uid, ts in all_users.items() if ts < cutoff}
        if not existing:
            return CohortReport(
                window_days=window_days,
                total_users=0,
                returning=0,
                churned=0,
                retention_rate=0.0,
                churn_rate=0.0,
            )

        # window 기간 내 재방문한 기존 사용자
        active_in_window = {
            e.user_id for e in self._events
            if e.user_id in existing and e.timestamp >= cutoff
        }
        returning = len(active_in_window)
        churned   = len(existing) - returning
        total     = len(existing)

        return CohortReport(
            window_days=window_days,
            total_users=total,
            returning=returning,
            churned=churned,
            retention_rate=round(returning / total, 4) if total else 0.0,
            churn_rate=round(churned / total, 4) if total else 0.0,
        )

    # ── 요약 통계 ────────────────────────────────────────────

    def summary(self) -> Dict[str, Any]:
        event_names: Dict[str, int] = defaultdict(int)
        for e in self._events:
            event_names[e.name] += 1
        return {
            "total_events":  len(self._events),
            "unique_users":  self.unique_users(),
            "event_breakdown": dict(event_names),
        }


# ── PublicAPIDoc v2 ───────────────────────────────────────────

class PublicAPIDoc:
    """
    OpenAPI 3.1 문서 생성기.
    Literary OS 공개 API 스펙 자동 생성.
    """

    VERSION = "2.0.0"
    TITLE   = "Literary OS Studio API"

    # SP1~SP5 핵심 엔드포인트 정의
    _ENDPOINTS = [
        # Studio API 기본
        {"method": "POST",   "path": "/api/v2/generate",      "tag": "generate",    "summary": "산문 생성"},
        {"method": "POST",   "path": "/api/v2/analyze",       "tag": "analyze",     "summary": "원고 분석"},
        {"method": "GET",    "path": "/api/v2/jobs/{job_id}", "tag": "jobs",        "summary": "작업 상태 조회"},
        {"method": "POST",   "path": "/api/v2/jobs",          "tag": "jobs",        "summary": "비동기 작업 생성"},
        {"method": "GET",    "path": "/api/v2/io/export",     "tag": "io",          "summary": "원고 내보내기"},
        {"method": "POST",   "path": "/api/v2/io/import",     "tag": "io",          "summary": "원고 가져오기"},
        # 테넌트
        {"method": "POST",   "path": "/api/v2/tenants",       "tag": "tenants",     "summary": "테넌트 생성"},
        {"method": "GET",    "path": "/api/v2/tenants/{id}",  "tag": "tenants",     "summary": "테넌트 조회"},
        # 온보딩
        {"method": "POST",   "path": "/api/v2/onboard",       "tag": "onboarding",  "summary": "사용자 가입"},
        {"method": "POST",   "path": "/api/v2/subscriptions", "tag": "billing",     "summary": "구독 생성"},
        # 파인튜닝
        {"method": "POST",   "path": "/api/v2/finetune/jobs", "tag": "finetune",    "summary": "파인튜닝 작업 제출"},
        {"method": "GET",    "path": "/api/v2/finetune/jobs/{job_id}", "tag": "finetune", "summary": "파인튜닝 상태"},
        # 게이트
        {"method": "GET",    "path": "/api/v2/gates/status",  "tag": "gates",       "summary": "릴리즈 게이트 상태"},
        # 관측성
        {"method": "GET",    "path": "/api/v2/metrics",       "tag": "ops",         "summary": "Prometheus 메트릭"},
        {"method": "GET",    "path": "/api/v2/health",        "tag": "ops",         "summary": "헬스 체크"},
        {"method": "GET",    "path": "/api/v2/analytics",     "tag": "analytics",   "summary": "분석 요약"},
    ]

    def generate_openapi(self) -> Dict[str, Any]:
        """OpenAPI 3.1 스펙 딕셔너리 생성."""
        paths: Dict[str, Any] = {}
        for ep in self._ENDPOINTS:
            path = ep["path"]
            method = ep["method"].lower()
            if path not in paths:
                paths[path] = {}
            paths[path][method] = {
                "tags":       [ep["tag"]],
                "summary":    ep["summary"],
                "operationId": f"{method}_{path.strip('/').replace('/', '_').replace('{', '').replace('}', '')}",
                "responses": {
                    "200": {"description": "성공"},
                    "400": {"description": "잘못된 요청"},
                    "401": {"description": "인증 필요"},
                    "500": {"description": "서버 오류"},
                },
            }

        tags = sorted({ep["tag"] for ep in self._ENDPOINTS})

        return {
            "openapi": "3.1.0",
            "info": {
                "title":   self.TITLE,
                "version": self.VERSION,
                "description": "Literary OS Studio API — Phase 3 SP5",
            },
            "tags":  [{"name": t} for t in tags],
            "paths": paths,
            "components": {
                "securitySchemes": {
                    "BearerAuth": {
                        "type":   "http",
                        "scheme": "bearer",
                        "bearerFormat": "JWT",
                    }
                }
            },
            "security": [{"BearerAuth": []}],
        }

    def endpoint_count(self) -> int:
        return len(self._ENDPOINTS)
