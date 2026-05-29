"""
V325 - MultiLLMRouter  (Phase 4)
다중 LLM 프로바이더 라우팅 인터페이스.

설계 원칙 (V326 연계 준비):
  - 실제 GeminiAdapter / GPTAdapter는 V326에서 구현
  - V325에서는 인터페이스 + 비용 라우팅 전략 + MockBridge 폴백만 정의
  - ClaudeAdapter가 등록되면 즉시 사용 가능
  - RoutingStrategy: QUALITY(최고품질) / SPEED(빠름) / COST(최저비용) / ROUND_ROBIN
  - LLM 0회 평가 원칙 준수 (라우터 자체 로직은 로컬)
"""
from __future__ import annotations

from enum import Enum
from typing import Any

# ────────────────────────────────────────────────────────────────
# 라우팅 전략
# ────────────────────────────────────────────────────────────────

class RoutingStrategy(str, Enum):
    QUALITY     = "quality"       # 가장 높은 품질 모델 선택
    SPEED       = "speed"         # 가장 빠른 모델 선택
    COST        = "cost"          # 가장 저렴한 모델 선택
    ROUND_ROBIN = "round_robin"   # 순환 선택


# ────────────────────────────────────────────────────────────────
# ProviderProfile — 프로바이더 메타데이터
# ────────────────────────────────────────────────────────────────

class ProviderProfile:
    """LLM 프로바이더 등록 정보."""

    def __init__(
        self,
        name:          str,
        quality_score: float = 0.5,   # 0.0~1.0 품질 점수
        speed_score:   float = 0.5,   # 0.0~1.0 속도 점수
        cost_score:    float = 0.5,   # 0.0~1.0 비용 효율 (높을수록 저렴)
        available:     bool  = True,
    ) -> None:
        self.name          = name
        self.quality_score = quality_score
        self.speed_score   = speed_score
        self.cost_score    = cost_score
        self.available     = available

    def to_dict(self) -> dict[str, Any]:
        return {
            "name":          self.name,
            "quality_score": self.quality_score,
            "speed_score":   self.speed_score,
            "cost_score":    self.cost_score,
            "available":     self.available,
        }


# ────────────────────────────────────────────────────────────────
# 기본 프로바이더 프로파일 (V325 시점 기준)
# ────────────────────────────────────────────────────────────────

DEFAULT_PROFILES: dict[str, ProviderProfile] = {
    "claude-opus-4-6": ProviderProfile(
        name="claude-opus-4-6",
        quality_score=0.95,
        speed_score=0.60,
        cost_score=0.30,
    ),
    "claude-sonnet-4-6": ProviderProfile(
        name="claude-sonnet-4-6",
        quality_score=0.85,
        speed_score=0.80,
        cost_score=0.65,
    ),
    "claude-haiku-4-5": ProviderProfile(
        name="claude-haiku-4-5-20251001",
        quality_score=0.65,
        speed_score=0.95,
        cost_score=0.95,
    ),
    "ollama-llama3": ProviderProfile(
        name="ollama-llama3",
        quality_score=0.55,
        speed_score=0.80,
        cost_score=1.00,
    ),
    "ollama-mistral": ProviderProfile(
        name="ollama-mistral",
        quality_score=0.60,
        speed_score=0.85,
        cost_score=1.00,
    ),
    "mock": ProviderProfile(
        name="mock",
        quality_score=0.0,
        speed_score=1.0,
        cost_score=1.0,
    ),
    # V326에서 추가 예정
    "gemini-2.0-flash": ProviderProfile(
        name="gemini-2.0-flash",
        quality_score=0.80,
        speed_score=0.85,
        cost_score=0.75,
        available=False,   # V326 구현 예정
    ),
    "gpt-4o": ProviderProfile(
        name="gpt-4o",
        quality_score=0.88,
        speed_score=0.75,
        cost_score=0.55,
        available=False,   # V326 구현 예정
    ),
}


# ────────────────────────────────────────────────────────────────
# MultiLLMRouter
# ────────────────────────────────────────────────────────────────

class MultiLLMRouter:
    """
    다중 LLM 프로바이더 라우터.

    V325: ClaudeAdapter(등록 시) + MockLLMBridge(폴백)
    V326: GeminiAdapter, GPTAdapter 추가 예정

    사용 예:
        router = MultiLLMRouter(strategy=RoutingStrategy.QUALITY)
        router.register("claude", ClaudeAdapter())
        bridge = router.select()
        text   = bridge.generate(prompt, context)
    """

    def __init__(
        self,
        strategy: RoutingStrategy = RoutingStrategy.QUALITY,
        fallback_to_mock: bool = True,
    ) -> None:
        self._strategy      = strategy
        self._fallback      = fallback_to_mock
        self._bridges:      dict[str, Any] = {}   # name → LLMBridgeInterface
        self._profiles:     dict[str, ProviderProfile] = dict(DEFAULT_PROFILES)
        self._rr_index:     int = 0
        self._call_counts:  dict[str, int] = {}

    # ── 등록 ─────────────────────────────────────────────────────

    @property
    def strategy(self) -> RoutingStrategy:
        return self._strategy

    def register(
        self,
        name:    str,
        bridge:  Any,                               # LLMBridgeInterface
        profile: ProviderProfile | None = None,
    ) -> None:
        """
        프로바이더 등록.

        Args:
            name:    프로바이더 식별자
            bridge:  LLMBridgeInterface 구현체
            profile: None이면 DEFAULT_PROFILES에서 조회
        """
        self._bridges[name]      = bridge
        self._call_counts[name]  = 0
        if profile is not None:
            self._profiles[name] = profile
        elif name not in self._profiles:
            self._profiles[name] = ProviderProfile(name=name)

    def unregister(self, name: str) -> None:
        """프로바이더 제거."""
        self._bridges.pop(name, None)
        self._call_counts.pop(name, None)

    # ── 라우팅 ───────────────────────────────────────────────────

    def select(self, scene_context: dict[str, Any] | None = None) -> Any:
        """
        전략에 따라 최적 브릿지 선택.

        Args:
            scene_context: 씬 컨텍스트 (향후 adaptive routing에 활용)

        Returns:
            LLMBridgeInterface 구현체

        Raises:
            RuntimeError: 사용 가능한 브릿지 없음
        """
        available = {
            name: bridge
            for name, bridge in self._bridges.items()
            if self._profiles.get(name, ProviderProfile(name)).available
        }

        if not available:
            if self._fallback:
                return self._get_mock_fallback()
            raise RuntimeError("MultiLLMRouter: 등록된 브릿지가 없습니다.")

        name = self._route(available)
        self._call_counts[name] = self._call_counts.get(name, 0) + 1
        return self._bridges[name]

    def generate(self, prompt: str, context: dict[str, Any]) -> str:
        """select() → generate() 단축 호출."""
        bridge = self.select(scene_context=context)
        return bridge.generate(prompt, context)

    # ── 통계 ─────────────────────────────────────────────────────

    def stats(self) -> dict[str, Any]:
        """라우팅 통계."""
        total = sum(self._call_counts.values())
        return {
            "strategy":    self._strategy.value,
            "total_calls": total,
            "by_provider": dict(self._call_counts),
            "registered":  list(self._bridges.keys()),
        }

    def list_providers(self) -> list[dict[str, Any]]:
        """등록된 프로바이더 목록 반환."""
        return [
            {**self._profiles[n].to_dict(), "registered": True}
            for n in self._bridges
            if n in self._profiles
        ]

    # ── 내부 헬퍼 ────────────────────────────────────────────────

    def _route(self, available: dict[str, Any]) -> str:
        """전략별 라우팅 로직."""
        if self._strategy == RoutingStrategy.QUALITY:
            return max(
                available,
                key=lambda n: self._profiles.get(n, ProviderProfile(n)).quality_score,
            )
        elif self._strategy == RoutingStrategy.SPEED:
            return max(
                available,
                key=lambda n: self._profiles.get(n, ProviderProfile(n)).speed_score,
            )
        elif self._strategy == RoutingStrategy.COST:
            return max(
                available,
                key=lambda n: self._profiles.get(n, ProviderProfile(n)).cost_score,
            )
        elif self._strategy == RoutingStrategy.ROUND_ROBIN:
            names = list(available.keys())
            name  = names[self._rr_index % len(names)]
            self._rr_index += 1
            return name
        # 기본: 첫 번째
        return next(iter(available))

    def _get_mock_fallback(self) -> Any:
        """MockLLMBridge 폴백 (anthropic 없는 환경용)."""
        try:
            from literary_system.llm_bridge.mock_llm_bridge import MockLLMBridge
            return MockLLMBridge()
        except ImportError:
            raise RuntimeError("MultiLLMRouter: MockLLMBridge도 불러올 수 없습니다.")
