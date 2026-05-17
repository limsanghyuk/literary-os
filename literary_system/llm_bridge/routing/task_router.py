"""
V411-D — TaskRouter
narrative_fitness 기반 LLM 프로바이더 자동 선택.

LLM-0 원칙 엄수:
  route() 메서드의 콜 스택에 LLM 호출이 절대 없음.
  오직 narrative_fitness 수치와 provider_hint 문자열로만 결정.

설계:
  - fitness 구간(THRESHOLDS)으로 3개 티어: local/speed/quality
  - provider_hint 있으면 fitness 무시하고 힌트 우선
  - ProviderHealthMonitor 연동 — 비활성 프로바이더 자동 건너뜀
  - 폴백 체인: local → speed → quality → fallback_adapter
  - 모든 결정은 O(1) 수치 비교 (LLM 불필요)
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from literary_system.llm_bridge.llm_bridge_interface import LLMBridgeInterface
from literary_system.llm_bridge.llm_context import LLMContext


class TaskRouter:
    """
    LLM-0 준수 순수 수치 라우터.

    Args:
        providers:      {tier_name: LLMBridgeInterface} 티어별 어댑터 맵
        health_monitor: ProviderHealthMonitor (None이면 가용성 체크 생략)
        fallback:       모든 티어 실패 시 최후 폴백 어댑터
    """

    # 티어 → (fitness_min, fitness_max) 구간 (normalized 0.0~1.0)
    THRESHOLDS: Dict[str, Tuple[float, float]] = {
        "local":   (0.00, 0.40),   # Ollama (비용 0)
        "speed":   (0.40, 0.75),   # Claude Haiku
        "quality": (0.75, 1.01),   # Claude Sonnet
    }

    # 폴백 순서
    FALLBACK_CHAIN: List[str] = ["local", "speed", "quality"]

    # provider_hint 문자열 → 티어 매핑
    HINT_TO_TIER: Dict[str, str] = {
        "cost":    "local",
        "local":   "local",
        "speed":   "speed",
        "fast":    "speed",
        "quality": "quality",
        "high":    "quality",
    }

    def __init__(
        self,
        providers: Optional[Dict[str, LLMBridgeInterface]] = None,
        health_monitor=None,   # ProviderHealthMonitor (순환 임포트 방지)
        fallback: Optional[LLMBridgeInterface] = None,
    ) -> None:
        self._providers: Dict[str, LLMBridgeInterface] = providers or {}
        self._health    = health_monitor
        self._fallback  = fallback

    # ── 공개 API ─────────────────────────────────────────────────

    def route(self, context: LLMContext) -> LLMBridgeInterface:
        """
        context 기반 최적 프로바이더 반환.

        결정 순서:
          1. provider_hint 있으면 힌트 티어 우선
          2. 없으면 narrative_fitness로 자동 티어 선택
          3. 선택 티어 건강 확인 → 불건강이면 폴백 체인 순회
          4. 전부 실패 시 fallback_adapter 또는 첫 번째 등록 어댑터
        """
        # LLM-0 보장: 이 메서드 내에서 LLM generate() 호출 없음
        if context.provider_hint:
            tier = self.HINT_TO_TIER.get(context.provider_hint.lower(), "quality")
            adapter = self._get_healthy(tier)
            if adapter:
                return adapter

        # fitness 기반 자동 라우팅
        norm = context.normalized_fitness()
        primary_tier = self._fitness_to_tier(norm)
        adapter = self._get_healthy(primary_tier)
        if adapter:
            return adapter

        # 폴백 체인 순회 (primary_tier 제외)
        for tier in self.FALLBACK_CHAIN:
            if tier == primary_tier:
                continue
            adapter = self._get_healthy(tier)
            if adapter:
                return adapter

        # 최후 폴백
        if self._fallback:
            return self._fallback
        if self._providers:
            return next(iter(self._providers.values()))
        raise RuntimeError("TaskRouter: no providers registered")

    def register(self, tier: str, adapter: LLMBridgeInterface) -> None:
        """프로바이더 등록."""
        self._providers[tier] = adapter

    def set_fallback(self, adapter: LLMBridgeInterface) -> None:
        """최후 폴백 어댑터 설정."""
        self._fallback = adapter

    def tier_for_fitness(self, fitness_normalized: float) -> str:
        """fitness 값에 대응하는 티어 이름 반환 (테스트용)."""
        return self._fitness_to_tier(fitness_normalized)

    def available_tiers(self) -> List[str]:
        """등록된 티어 목록."""
        return list(self._providers.keys())

    # ── 내부 메서드 ─────────────────────────────────────────────

    def _fitness_to_tier(self, norm: float) -> str:
        """정규화된 fitness(0~1) → 티어 이름."""
        for tier, (lo, hi) in self.THRESHOLDS.items():
            if lo <= norm < hi:
                return tier
        return "quality"  # 1.0 이상

    def _is_tier_healthy(self, tier: str) -> bool:
        """티어의 어댑터가 건강한지 확인.

        설계 결정 (H5/ADR-V481):
          ProviderHealthMonitor는 provider_id("ollama"/"haiku"/"sonnet")로 키됨.
          tier 이름("local"/"speed"/"quality")과 다르므로 get_provider_id()로 변환.
          blueprint "tier 직접 조회" 문구는 이 간접 변환을 포함한 의미임.
        """
        if tier not in self._providers:
            return False
        if self._health is None:
            return True   # 모니터 없으면 항상 건강으로 간주
        pid = self._providers[tier].get_provider_id()   # tier → provider_id 변환
        return self._health.is_healthy(pid)

    def _get_healthy(self, tier: str) -> Optional[LLMBridgeInterface]:
        """건강한 경우에만 어댑터 반환. 아니면 None."""
        if self._is_tier_healthy(tier):
            return self._providers.get(tier)
        return None
