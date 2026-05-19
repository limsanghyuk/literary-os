"""
V411-A — LLMContext + LLMResponse 강타입 계약.

설계 원칙:
  - LLMBridgeInterface.generate(prompt, context: dict) → context: LLMContext 로 갱신
  - 모든 프로바이더 어댑터가 동일 계약을 준수하도록 강제
  - narrative_fitness는 PhysicsGate 산출값을 그대로 전달 (LLM-0 원칙)
  - provider_hint: "quality"|"speed"|"cost"|"" — TaskRouter 힌트
  - 하위 호환: context: dict 입력 시 자동 변환 헬퍼 제공
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

# ────────────────────────────────────────────────────────────────
# LLMContext — LLM 호출 계약 기반 타입
# ────────────────────────────────────────────────────────────────

@dataclass
class LLMContext:
    """
    LLM 프로바이더 호출 시 전달되는 구조화된 컨텍스트.

    Attributes:
        series_id:          현재 시리즈 ID
        episode_idx:        현재 에피소드 인덱스
        narrative_fitness:  PhysicsGate 산출 피트니스 점수 (0.0~10.0)
                            TaskRouter가 0.0~1.0 정규화값으로 활용
        provider_hint:      라우팅 힌트 ("quality"|"speed"|"cost"|"")
                            비어있으면 TaskRouter가 fitness 기반 자동 선택
        max_tokens:         최대 생성 토큰 수
        temperature:        생성 다양성 (0.0~2.0)
        timeout:            HTTP 타임아웃 (초)
        extra:              추가 메타데이터 (scene_id, chars 등 기존 context dict 잔존값)
    """
    series_id: str = ""
    episode_idx: int = 0
    narrative_fitness: float = 0.0
    provider_hint: str = ""          # "quality" | "speed" | "cost" | ""
    max_tokens: int = 2000
    temperature: float = 0.7
    timeout: int = 30
    extra: Dict = field(default_factory=dict)

    def normalized_fitness(self) -> float:
        """narrative_fitness를 0.0~1.0 범위로 정규화 (10점 만점 기준)."""
        return max(0.0, min(1.0, self.narrative_fitness / 10.0))

    @classmethod
    def from_dict(cls, d: dict) -> "LLMContext":
        """
        기존 context: dict 를 LLMContext 로 변환하는 하위 호환 헬퍼.

        알려진 필드만 매핑하고 나머지는 extra 에 보존한다.
        """
        known = {
            "series_id", "episode_idx", "narrative_fitness",
            "provider_hint", "max_tokens", "temperature", "timeout",
        }
        kwargs = {k: v for k, v in d.items() if k in known}
        extra  = {k: v for k, v in d.items() if k not in known}
        return cls(**kwargs, extra=extra)

    def to_dict(self) -> dict:
        """dict 표현으로 직렬화."""
        return {
            "series_id":         self.series_id,
            "episode_idx":       self.episode_idx,
            "narrative_fitness": self.narrative_fitness,
            "provider_hint":     self.provider_hint,
            "max_tokens":        self.max_tokens,
            "temperature":       self.temperature,
            "timeout":           self.timeout,
            **self.extra,
        }


# ────────────────────────────────────────────────────────────────
# LLMResponse — LLM 호출 결과 타입
# ────────────────────────────────────────────────────────────────

@dataclass
class LLMResponse:
    """
    LLM 프로바이더 호출 결과.

    Attributes:
        text:                생성된 텍스트
        provider_id:         실제 호출된 프로바이더 식별자
        tokens_used:         사용된 토큰 수 (불명시 0)
        latency_ms:          호출 소요 시간 (밀리초)
        cost_estimate_usd:   비용 추정 (V412 완성, V411은 0.0)
        fallback_used:       폴백 어댑터 사용 여부
    """
    text: str
    provider_id: str = ""
    tokens_used: int = 0
    latency_ms: float = 0.0
    cost_estimate_usd: float = 0.0
    fallback_used: bool = False


# ────────────────────────────────────────────────────────────────
# 유틸리티
# ────────────────────────────────────────────────────────────────

def coerce_context(ctx) -> LLMContext:
    """
    context가 dict이면 LLMContext 로, 이미 LLMContext이면 그대로 반환.
    기존 코드의 하위 호환을 보장한다.
    """
    if isinstance(ctx, LLMContext):
        return ctx
    if isinstance(ctx, dict):
        return LLMContext.from_dict(ctx)
    return LLMContext()
