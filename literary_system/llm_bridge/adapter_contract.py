"""
V431 — LLMAdapterContract v2
ADR-004 Tiered Model 어댑터 6요소 표준 계약.

Phase 2 SubPhase 1 핵심: MockLLMBridge 의존 탈피 + 실 LLM 연결 표준화.

6요소:
  1. key        — API 키 관리 (환경변수 우선, 직접 주입 허용)
  2. retry      — 재시도 정책 (지수 백오프, 최대 횟수)
  3. timeout    — HTTP 타임아웃 (초 단위, 모델 티어별 기본값)
  4. token      — 토큰 카운팅 (입력/출력 분리, 예산 초과 차단)
  5. validation — 응답 검증 (빈 응답, 안전 필터, 길이 임계값)
  6. cost       — 비용 추적 (CostLedger 연동, RetryBudget 연결)

v4 보강:
  - retry_budget_id: RetryBudgetManager 연동 식별자

ADR 번호: ADR-004
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

# ─────────────────────────────────────────────────────────────────────────────
# 1. KEY — API 키 관리
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class KeyConfig:
    """
    API 키 설정.
    
    직접 주입 > 환경변수 > 빈 문자열 순으로 우선.
    """
    env_var: str = ""           # 환경변수 이름 (예: ANTHROPIC_API_KEY)
    _direct_key: str = field(default="", repr=False)  # 직접 주입 키 (로그 제외)

    def resolve(self) -> str:
        """키 해석: 직접 주입 > 환경변수."""
        if self._direct_key:
            return self._direct_key
        if self.env_var:
            import os
            return os.environ.get(self.env_var, "")
        return ""

    @property
    def is_set(self) -> bool:
        return bool(self.resolve())

    @classmethod
    def from_env(cls, env_var: str) -> "KeyConfig":
        return cls(env_var=env_var)

    @classmethod
    def from_direct(cls, key: str) -> "KeyConfig":
        return cls(_direct_key=key)


# ─────────────────────────────────────────────────────────────────────────────
# 2. RETRY — 재시도 정책
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class RetryPolicy:
    """
    지수 백오프 재시도 정책.
    
    대기 시간 = base_delay * (backoff_factor ** attempt), 최대 max_delay.
    """
    max_attempts:   int   = 3       # 최대 재시도 횟수 (첫 시도 포함)
    base_delay:     float = 1.0     # 첫 재시도 대기 (초)
    backoff_factor: float = 2.0     # 대기 시간 배수
    max_delay:      float = 30.0    # 최대 대기 시간 (초)
    jitter:         bool  = True    # 랜덤 지터 추가 (thundering herd 방지)
    retry_budget_id: str  = ""      # RetryBudgetManager 연동 ID (v4 보강)

    # 재시도 대상 예외 클래스명 (빈 목록 = 모든 예외)
    retryable_exceptions: list = field(default_factory=lambda: [
        "RateLimitError", "ServiceUnavailableError", "ConnectionError",
        "TimeoutError", "APIStatusError",
    ])

    def delay_for_attempt(self, attempt: int) -> float:
        """attempt 번째 재시도의 대기 시간 계산 (0-indexed)."""
        delay = min(self.base_delay * (self.backoff_factor ** attempt), self.max_delay)
        if self.jitter:
            import random
            delay *= (0.5 + random.random() * 0.5)
        return round(delay, 3)

    def should_retry(self, attempt: int, exception: Exception) -> bool:
        """현재 시도 횟수와 예외로 재시도 여부 판단."""
        if attempt >= self.max_attempts - 1:
            return False
        if not self.retryable_exceptions:
            return True
        exc_name = type(exception).__name__
        return any(r in exc_name for r in self.retryable_exceptions)


def execute_with_retry(
    fn: Callable,
    policy: RetryPolicy,
    *args,
    **kwargs,
) -> Any:
    """
    RetryPolicy에 따라 fn을 반복 실행.
    모든 재시도 소진 시 마지막 예외를 raise.
    """
    last_exc: Optional[Exception] = None
    for attempt in range(policy.max_attempts):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            last_exc = e
            if not policy.should_retry(attempt, e):
                raise
            delay = policy.delay_for_attempt(attempt)
            time.sleep(delay)
    raise last_exc  # type: ignore


# ─────────────────────────────────────────────────────────────────────────────
# 3. TIMEOUT — HTTP 타임아웃
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class TimeoutConfig:
    """
    HTTP 타임아웃 설정.
    
    모델 티어별 기본값:
      local (Ollama):  120초 (로컬 모델은 느릴 수 있음)
      speed (Haiku):   30초
      quality (Sonnet/Opus): 60초
    """
    connect_timeout: float = 10.0   # 연결 타임아웃 (초)
    read_timeout:    float = 30.0   # 읽기 타임아웃 (초)

    @property
    def total(self) -> float:
        return self.connect_timeout + self.read_timeout

    @classmethod
    def for_tier(cls, tier: str) -> "TimeoutConfig":
        """티어명에 따른 기본 타임아웃 반환."""
        presets = {
            "local":   cls(connect_timeout=5.0,  read_timeout=120.0),
            "speed":   cls(connect_timeout=10.0, read_timeout=30.0),
            "quality": cls(connect_timeout=10.0, read_timeout=60.0),
        }
        return presets.get(tier, cls())


# ─────────────────────────────────────────────────────────────────────────────
# 4. TOKEN — 토큰 카운팅 및 예산
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class TokenBudget:
    """
    입력/출력 토큰 예산 및 카운팅.
    
    실제 카운팅은 어댑터 구현체가 수행;
    이 클래스는 설정·추적·초과 차단만 담당.
    """
    max_input_tokens:  int = 8_192      # 입력 토큰 상한
    max_output_tokens: int = 2_048      # 출력 토큰 상한 (= max_tokens API 파라미터)
    model_context_limit: int = 200_000  # 모델 전체 컨텍스트 창 크기

    # 실 사용량 (어댑터가 호출 후 업데이트)
    _input_used:  int = field(default=0, repr=False)
    _output_used: int = field(default=0, repr=False)

    def count_input_tokens(self, text: str, model_id: str = "") -> int:
        """
        입력 텍스트 토큰 수 추정.
        tiktoken 또는 anthropic count_tokens 사용 가능 시 정확히 계산.
        미설치 환경: 4자=1토큰 근사.
        """
        try:
            import tiktoken
            enc = tiktoken.get_encoding("cl100k_base")
            return len(enc.encode(text))
        except ImportError:
            return max(1, len(text) // 4)

    def record_usage(self, input_tokens: int, output_tokens: int) -> None:
        self._input_used  += input_tokens
        self._output_used += output_tokens

    def would_exceed(self, estimated_input: int) -> bool:
        return estimated_input > self.max_input_tokens

    def to_dict(self) -> dict:
        return {
            "max_input_tokens":    self.max_input_tokens,
            "max_output_tokens":   self.max_output_tokens,
            "input_used":          self._input_used,
            "output_used":         self._output_used,
        }


# ─────────────────────────────────────────────────────────────────────────────
# 5. VALIDATION — 응답 검증
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ResponseValidator:
    """
    LLM 응답 유효성 검증.
    
    검증 항목:
      - 빈 응답 차단
      - 최소 길이 미달
      - 최대 길이 초과 (비정상 루프 방지)
      - 안전 필터 키워드 (선택적)
    """
    min_length:    int   = 1        # 최소 응답 길이 (문자)
    max_length:    int   = 100_000  # 최대 응답 길이 (문자)
    allow_empty:   bool  = False    # 빈 응답 허용 여부
    safety_keywords: list = field(default_factory=list)  # 차단 키워드

    def validate(self, response: str) -> tuple[bool, str]:
        """
        응답 검증. (is_valid, reason) 반환.
        """
        if not response and not self.allow_empty:
            return False, "빈 응답"
        if len(response) < self.min_length:
            return False, f"응답 길이 부족: {len(response)} < {self.min_length}"
        if len(response) > self.max_length:
            return False, f"응답 길이 초과: {len(response)} > {self.max_length}"
        for kw in self.safety_keywords:
            if kw.lower() in response.lower():
                return False, f"안전 키워드 감지: {kw}"
        return True, ""


# ─────────────────────────────────────────────────────────────────────────────
# 6. COST — 비용 추적
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class CostConfig:
    """
    비용 추적 설정 — CostLedger 연동.
    
    어댑터는 각 호출 후 record_call()을 통해 CostLedger에 기록.
    """
    enabled:             bool = True
    provider_id:         str  = ""       # CostLedger 기록용 provider ID
    daily_budget_usd:    float = 10.0    # 일 예산 상한 (초과 시 경고)
    monthly_budget_usd:  float = 100.0   # 월 예산 상한 (초과 시 차단)

    def is_over_daily(self, current_usd: float) -> bool:
        return self.enabled and current_usd >= self.daily_budget_usd

    def is_over_monthly(self, current_usd: float) -> bool:
        return self.enabled and current_usd >= self.monthly_budget_usd


# ─────────────────────────────────────────────────────────────────────────────
# ADR-004 통합 계약 — AdapterContractV2
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class AdapterContractV2:
    """
    V431 — LLMAdapterContract v2.
    
    6요소 통합 설정 컨테이너.
    모든 V431+ 어댑터는 이 계약을 수용해야 한다.
    
    사용 예:
        contract = AdapterContractV2.for_tier("speed")
        adapter = ClaudeAdapterV2(contract=contract)
    """
    key:        KeyConfig         = field(default_factory=KeyConfig)
    retry:      RetryPolicy       = field(default_factory=RetryPolicy)
    timeout:    TimeoutConfig     = field(default_factory=TimeoutConfig)
    token:      TokenBudget       = field(default_factory=TokenBudget)
    validation: ResponseValidator = field(default_factory=ResponseValidator)
    cost:       CostConfig        = field(default_factory=CostConfig)

    # 어댑터 식별 메타데이터
    adapter_id:  str = ""           # 고유 어댑터 ID
    model_id:    str = ""           # 사용 모델 ID (예: claude-haiku-4-5)
    tier:        str = "speed"      # local / speed / quality

    @classmethod
    def for_tier(cls, tier: str, **kwargs) -> "AdapterContractV2":
        """
        티어별 기본 설정으로 계약 생성.
        
        tier="local"   → Ollama 최적화 (긴 타임아웃, 0 비용)
        tier="speed"   → Haiku 최적화 (짧은 타임아웃, 낮은 비용)
        tier="quality" → Sonnet/Opus 최적화 (긴 타임아웃, 높은 비용)
        """
        tier_defaults = {
            "local": dict(
                retry=RetryPolicy(max_attempts=2, base_delay=2.0),
                timeout=TimeoutConfig.for_tier("local"),
                token=TokenBudget(max_input_tokens=4096, max_output_tokens=2048),
                cost=CostConfig(enabled=False),
            ),
            "speed": dict(
                retry=RetryPolicy(max_attempts=3, base_delay=1.0),
                timeout=TimeoutConfig.for_tier("speed"),
                token=TokenBudget(max_input_tokens=8192, max_output_tokens=2048),
                cost=CostConfig(enabled=True, daily_budget_usd=5.0),
            ),
            "quality": dict(
                retry=RetryPolicy(max_attempts=3, base_delay=2.0),
                timeout=TimeoutConfig.for_tier("quality"),
                token=TokenBudget(max_input_tokens=16384, max_output_tokens=4096),
                cost=CostConfig(enabled=True, daily_budget_usd=20.0),
            ),
        }
        defaults = tier_defaults.get(tier, tier_defaults["speed"])
        defaults["tier"] = tier
        defaults.update(kwargs)
        return cls(**defaults)

    def validate_response(self, response: str) -> tuple[bool, str]:
        """응답 유효성 검증 위임."""
        return self.validation.validate(response)

    def resolve_api_key(self) -> str:
        """API 키 해석 위임."""
        return self.key.resolve()

    def to_dict(self) -> dict:
        return {
            "adapter_id":  self.adapter_id,
            "model_id":    self.model_id,
            "tier":        self.tier,
            "key_set":     self.key.is_set,
            "retry":       {
                "max_attempts":    self.retry.max_attempts,
                "base_delay":      self.retry.base_delay,
                "retry_budget_id": self.retry.retry_budget_id,
            },
            "timeout":     {
                "connect": self.timeout.connect_timeout,
                "read":    self.timeout.read_timeout,
            },
            "token":       self.token.to_dict(),
            "cost_enabled": self.cost.enabled,
        }
