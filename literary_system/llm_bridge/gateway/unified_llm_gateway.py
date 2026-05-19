"""
V411-F — UnifiedLLMGateway
Literary OS LLM 호출의 단일 진입점.

모든 파이프라인(NarrativeConductor, LongformEnduranceOrchestrator 등)은
반드시 이 게이트웨이를 통해서만 LLM을 호출한다.

흐름:
  1. ProviderHealthMonitor → 건강한 프로바이더 목록 확인
  2. TaskRouter → context 기반 최적 프로바이더 선택
  3. PhysicsAwareRouter (옵션) → 앙상블 보정
  4. 선택된 어댑터 → generate() 호출
  5. 실패 시 ProviderHealthMonitor.mark_failed() → 폴백 재시도
  6. CostLedger (V412 완성) → 비용 기록 stub

LLM-0 보장:
  - TaskRouter.route()는 LLM 호출 없음
  - 실제 generate()는 선택된 어댑터에서만 발생
"""
from __future__ import annotations

import time
from typing import List, Optional, Union

from literary_system.llm_bridge.llm_bridge_interface import LLMBridgeInterface
from literary_system.llm_bridge.llm_context import LLMContext, LLMResponse, coerce_context
from literary_system.llm_bridge.routing.task_router import TaskRouter
from literary_system.llm_bridge.health.provider_health_monitor import ProviderHealthMonitor


class UnifiedLLMGateway:
    """
    Literary OS LLM 호출의 유일한 진입점.

    Args:
        task_router:     TaskRouter 인스턴스
        health_monitor:  ProviderHealthMonitor 인스턴스
        physics_router:  PhysicsAwareRouter (옵션, 앙상블 전략)
        max_retries:     폴백 최대 재시도 횟수
    """

    DEFAULT_MAX_RETRIES: int = len(TaskRouter.FALLBACK_CHAIN)

    def __init__(
        self,
        task_router: TaskRouter,
        health_monitor: Optional[ProviderHealthMonitor] = None,
        physics_router=None,    # PhysicsAwareRouter (순환 임포트 방지)
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> None:
        self._router  = task_router
        self._health  = health_monitor
        self._physics = physics_router
        self._max_retries = max_retries
        self._call_count  = 0
        self._error_count = 0

    # ── 공개 API ─────────────────────────────────────────────────

    def call(
        self,
        prompt: str,
        context: Union[LLMContext, dict, None] = None,
    ) -> LLMResponse:
        """
        LLM 호출 전체 흐름 실행 후 LLMResponse 반환.
        실패 시 자동 폴백 재시도 (max_retries 회).
        """
        ctx = coerce_context(context or {})
        tried: List[str] = []

        for attempt in range(self._max_retries + 1):
            adapter = self._select_adapter(ctx, exclude=tried)
            if adapter is None:
                break

            pid = adapter.get_provider_id()
            tried.append(pid)

            t0 = time.monotonic()
            try:
                text = adapter.generate(prompt, ctx)
                latency = (time.monotonic() - t0) * 1000.0
                self._call_count += 1
                if self._health:
                    self._health.mark_healthy(pid)
                return LLMResponse(
                    text=text,
                    provider_id=pid,
                    latency_ms=round(latency, 2),
                    fallback_used=(attempt > 0),
                )
            except Exception as e:
                latency = (time.monotonic() - t0) * 1000.0
                self._error_count += 1
                if self._health:
                    self._health.mark_failed(pid, str(e))

        # 모든 재시도 실패 — 마지막 어댑터에서 fallback 텍스트 반환
        adapter = self._select_adapter(ctx, exclude=[])
        if adapter:
            text = adapter.generate(prompt, ctx)
            return LLMResponse(
                text=text,
                provider_id=adapter.get_provider_id(),
                fallback_used=True,
            )
        return LLMResponse(
            text=f"[UnifiedLLMGateway:error] all_providers_failed prompt_len={len(prompt)}",
            provider_id="none",
            fallback_used=True,
        )

    def call_text(
        self,
        prompt: str,
        context: Union[LLMContext, dict, None] = None,
    ) -> str:
        """텍스트만 반환하는 편의 메서드."""
        return self.call(prompt, context).text

    @property
    def call_count(self) -> int:
        return self._call_count

    @property
    def error_count(self) -> int:
        return self._error_count

    # ── 내부 메서드 ─────────────────────────────────────────────

    def _select_adapter(
        self,
        ctx: LLMContext,
        exclude: List[str],
    ) -> Optional[LLMBridgeInterface]:
        """exclude 목록 제외 후 TaskRouter로 어댑터 선택."""
        if not exclude:
            try:
                return self._router.route(ctx)
            except RuntimeError:
                return None

        # Bug-Fix: mark_failed() permanently increases consecutive_failures and may
        # trigger DEGRADED status. Using it just for routing exclusion is a harmful
        # side effect. Replace with post-route pid-in-exclude check instead.
        try:
            adapter = self._router.route(ctx)
            pid = adapter.get_provider_id()
            if pid in exclude:
                return None
            return adapter
        except RuntimeError:
            return None


# ────────────────────────────────────────────────────────────────
# 팩토리 함수 — 기본 구성 게이트웨이 생성
# ────────────────────────────────────────────────────────────────

def make_default_gateway(
    ollama_model: str = "llama3.2",
    ollama_base_url: str = "http://localhost:11434",
    claude_haiku_key: str = "",
    claude_sonnet_key: str = "",
    mock_fallback: bool = True,
    call_fn=None,
) -> UnifiedLLMGateway:
    """
    기본 3티어 게이트웨이 생성 (V577: G3 캐노니컬 어댑터 사용).

    - local  → CanonicalLLMBridge(RealOllamaAdapter)
    - speed  → CanonicalLLMBridge(RealClaudeAdapter, haiku)
    - quality→ CanonicalLLMBridge(RealClaudeAdapter, sonnet)
    - fallback→ MockLLMBridge (테스트 환경)

    ADR-035: G1/G2 ClaudeAdapter 대신 G3 adapters_live/ 캐노니컬 사용.
    LLM-0: call_fn 주입으로 CI에서 실 API 호출 차단 가능.
    """
    from literary_system.llm_bridge.canonical_adapter import (
        make_canonical_claude,
        make_canonical_ollama,
    )
    from literary_system.llm_bridge.mock_llm_bridge import MockLLMBridge

    providers = {}

    try:
        providers["local"] = make_canonical_ollama(
            model=ollama_model,
            base_url=ollama_base_url,
            call_fn=call_fn,
        )
    except Exception:
        providers["local"] = MockLLMBridge(scripted_response="[ollama_mock]")

    try:
        providers["speed"] = make_canonical_claude(
            model="claude-haiku-4-5-20251001",
            call_fn=call_fn,
        )
        providers["quality"] = make_canonical_claude(
            model="claude-sonnet-4-6",
            call_fn=call_fn,
        )
    except Exception:
        providers["speed"]   = MockLLMBridge(scripted_response="[haiku_mock]")
        providers["quality"] = MockLLMBridge(scripted_response="[sonnet_mock]")

    health  = ProviderHealthMonitor(providers)
    router  = TaskRouter(providers=providers, health_monitor=health,
                         fallback=MockLLMBridge() if mock_fallback else None)
    return UnifiedLLMGateway(task_router=router, health_monitor=health)
  