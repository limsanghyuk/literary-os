"""
V430 — CostLedger (V412 이월 완성)
에피소드별 LLM 비용 누적 추적 데이터 모델.

V411 스코프: 구조 정의 + 기록 메서드 완성
V430 (V412 이월): provider별 pricing table 기반 실제 비용 계산 완성

설계:
  - EpisodeMemory.cost_ledger: Optional[CostLedger] = None 으로 연동
  - provider_id별 호출수/토큰/레이턴시 누적
  - estimated_cost_usd: provider_id 패턴 매칭으로 자동 계산 (USD/1K tokens)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional


# ─────────────────────────────────────────────────────────────────────────────
# Provider Pricing Table (USD per 1,000 tokens, blended input+output avg)
# 출처: 2025-05 공개 가격 기준 (입력 60% + 출력 40% 가중 평균)
# ─────────────────────────────────────────────────────────────────────────────
_PRICING_TABLE: Dict[str, float] = {
    # ── Anthropic Claude ──────────────────────────────────────────
    "claude-opus-4":       0.045000,   # $15/$75 per M input/output
    "claude-opus-3":       0.045000,
    "claude-opus":         0.045000,
    "claude-sonnet-4":     0.009000,   # $3/$15 per M
    "claude-sonnet-3-7":   0.009000,
    "claude-sonnet-3-5":   0.009000,
    "claude-sonnet":       0.009000,
    "claude-haiku-4":      0.000750,   # $0.25/$1.25 per M
    "claude-haiku-3-5":    0.000750,
    "claude-haiku":        0.000750,
    # ── OpenAI GPT ───────────────────────────────────────────────
    "gpt-4o":              0.006250,   # $2.50/$10 per M
    "gpt-4o-mini":         0.000375,   # $0.15/$0.60 per M
    "gpt-4-turbo":         0.013000,   # $10/$30 per M
    "gpt-4":               0.048000,   # $30/$60 per M
    "gpt-3.5-turbo":       0.001000,   # $0.50/$1.50 per M
    "o1":                  0.090000,   # $15/$60 per M (reasoning)
    "o1-mini":             0.004800,   # $3/$12 per M
    "o3-mini":             0.003300,   # $1.10/$4.40 per M
    # ── Local / OSS ─────────────────────────────────────────────
    "ollama":              0.000000,
    "local":               0.000000,
    "mock":                0.000000,
}

# 알 수 없는 provider 기본값 (USD/1K tokens)
_DEFAULT_COST_PER_1K = 0.001000


def _lookup_cost_per_1k(provider_id: str) -> float:
    """
    provider_id에서 1K 토큰당 비용(USD)을 조회.
    부분 매칭(startswith/contains) 순으로 탐색.
    """
    pid = provider_id.lower().strip()

    # 정확 매칭 우선
    if pid in _PRICING_TABLE:
        return _PRICING_TABLE[pid]

    # 로컬/목업 키워드
    for kw in ("mock", "local", "ollama", "test", "dummy", "stub"):
        if kw in pid:
            return 0.0

    # 모델명 패턴 매칭 (긴 키 우선)
    for key in sorted(_PRICING_TABLE, key=len, reverse=True):
        if key in pid:
            return _PRICING_TABLE[key]

    return _DEFAULT_COST_PER_1K


# ─────────────────────────────────────────────────────────────────────────────
# ProviderCallRecord — 단일 프로바이더 호출 집계
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ProviderCallRecord:
    """프로바이더별 누적 호출 기록."""
    provider_id:       str
    call_count:        int   = 0
    total_tokens:      int   = 0
    total_latency_ms:  float = 0.0
    success_count:     int   = 0
    failure_count:     int   = 0

    @property
    def avg_latency_ms(self) -> float:
        if self.call_count == 0:
            return 0.0
        return self.total_latency_ms / self.call_count

    @property
    def success_rate(self) -> float:
        if self.call_count == 0:
            return 0.0
        return self.success_count / self.call_count

    @property
    def estimated_cost_usd(self) -> float:
        """이 프로바이더의 토큰 사용량에 대한 USD 비용 추정."""
        rate = _lookup_cost_per_1k(self.provider_id)
        return round(self.total_tokens / 1000.0 * rate, 8)

    def to_dict(self) -> dict:
        return {
            "provider_id":          self.provider_id,
            "call_count":           self.call_count,
            "total_tokens":         self.total_tokens,
            "total_latency_ms":     self.total_latency_ms,
            "success_count":        self.success_count,
            "failure_count":        self.failure_count,
            "avg_latency_ms":       round(self.avg_latency_ms, 2),
            "success_rate":         round(self.success_rate, 4),
            "estimated_cost_usd":   self.estimated_cost_usd,
        }


# ─────────────────────────────────────────────────────────────────────────────
# CostLedger — 에피소드 비용 원장
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class CostLedger:
    """
    에피소드별 LLM 비용 누적 원장.

    Attributes:
        episode_idx:         에피소드 인덱스
        series_id:           시리즈 ID
        records:             {provider_id: ProviderCallRecord}
        created_at:          원장 생성 시각 (ISO8601)

    Note:
        estimated_cost_usd 는 property — 모든 record의 비용 합산.
        pricing table: literary_system.llm_bridge.cost_ledger._PRICING_TABLE
    """
    episode_idx: int
    series_id:   str = ""
    records:     Dict[str, ProviderCallRecord] = field(default_factory=dict)
    created_at:  str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    # ── 비용 계산 (property) ────────────────────────────────────────

    @property
    def estimated_cost_usd(self) -> float:
        """전체 provider 합산 USD 비용 추정 (V430 완성)."""
        return round(sum(r.estimated_cost_usd for r in self.records.values()), 8)

    # ── 기록 메서드 ─────────────────────────────────────────────

    def record_call(self, response) -> None:
        """
        LLMResponse에서 호출 기록 갱신.
        response: LLMResponse dataclass (provider_id, tokens_used, latency_ms)
        """
        pid = getattr(response, "provider_id", "unknown")
        if pid not in self.records:
            self.records[pid] = ProviderCallRecord(provider_id=pid)
        rec = self.records[pid]
        rec.call_count       += 1
        rec.total_tokens     += getattr(response, "tokens_used", 0)
        rec.total_latency_ms += getattr(response, "latency_ms", 0.0)
        if not getattr(response, "fallback_used", False):
            rec.success_count += 1
        else:
            rec.failure_count += 1

    def record_raw(
        self,
        provider_id: str,
        tokens: int = 0,
        latency_ms: float = 0.0,
        success: bool = True,
    ) -> None:
        """직접 수치로 기록 (테스트/수동 입력용)."""
        if provider_id not in self.records:
            self.records[provider_id] = ProviderCallRecord(provider_id=provider_id)
        rec = self.records[provider_id]
        rec.call_count       += 1
        rec.total_tokens     += tokens
        rec.total_latency_ms += latency_ms
        if success:
            rec.success_count += 1
        else:
            rec.failure_count += 1

    # ── 집계 속성 ────────────────────────────────────────────────

    @property
    def total_calls(self) -> int:
        return sum(r.call_count for r in self.records.values())

    @property
    def total_tokens(self) -> int:
        return sum(r.total_tokens for r in self.records.values())

    @property
    def total_latency_ms(self) -> float:
        return sum(r.total_latency_ms for r in self.records.values())

    @property
    def provider_ids(self):
        return list(self.records.keys())

    def get_record(self, provider_id: str) -> Optional[ProviderCallRecord]:
        return self.records.get(provider_id)

    def to_dict(self) -> dict:
        return {
            "episode_idx":          self.episode_idx,
            "series_id":            self.series_id,
            "estimated_cost_usd":   self.estimated_cost_usd,
            "total_calls":          self.total_calls,
            "total_tokens":         self.total_tokens,
            "created_at":           self.created_at,
            "records": {
                pid: rec.to_dict() for pid, rec in self.records.items()
            },
        }
