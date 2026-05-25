"""CanonicalBridgeV2 — 외부+로컬 LLM 동시 지원 브리지 (V606, ADR-066, LLM-0 원칙 준수)."""
from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ModelType:
    """지원 모델 타입 상수."""

    EXTERNAL = "external"
    LOCAL = "local"


@dataclass
class BridgeConfig:
    """CanonicalBridgeV2 설정."""

    model_type: str = ModelType.EXTERNAL
    adapter_name: str = "default"
    fallback_enabled: bool = True
    fallback_model_type: str = ModelType.LOCAL
    max_tokens: int = 512
    temperature: float = 0.7
    timeout_sec: float = 30.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BridgeResponse:
    """LLM 브리지 응답 컨테이너."""

    text: str
    model_type: str
    adapter_name: str
    used_fallback: bool = False
    tokens_used: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CanonicalBridgeV2:
    """외부 LLM + 로컬 LoRA 모델 동시 지원 브리지.

    LLM-0 원칙: 실 API 호출 없음. 외부 어댑터 주입 방식으로 동작.

    사용 예::

        bridge = CanonicalBridgeV2(BridgeConfig(model_type="external"))
        bridge.register_external_adapter(my_adapter)
        resp = bridge.generate("씬 생성 프롬프트")
    """

    VERSION = "2.0.0"

    def __init__(
        self,
        config: Optional[BridgeConfig] = None,
        external_adapter: Optional[Any] = None,
        local_adapter: Optional[Any] = None,
    ) -> None:
        self.config = config or BridgeConfig()
        self._external_adapter = external_adapter
        self._local_adapter = local_adapter
        self._call_count: int = 0
        self._fallback_count: int = 0

    def register_external_adapter(self, adapter: Any) -> None:
        """외부 LLM 어댑터 주입 (Claude / GPT / Gemini 등)."""
        self._external_adapter = adapter

    def register_local_adapter(self, adapter: Any) -> None:
        """로컬 LoRA 어댑터 주입 (LoRAInferenceGateway 등)."""
        self._local_adapter = adapter

    def generate(
        self,
        prompt: str,
        model_type: Optional[str] = None,
        **kwargs: Any,
    ) -> BridgeResponse:
        """프롬프트 → 응답 생성.

        Args:
            prompt: 입력 프롬프트.
            model_type: ``"external"`` 또는 ``"local"``. None 이면 config 기본값 사용.
            **kwargs: 어댑터에 추가 전달할 인자.

        Returns:
            BridgeResponse 인스턴스.

        Raises:
            ValueError: 알 수 없는 model_type 지정 시.
            RuntimeError: 어댑터 미등록 상태에서 폴백 비활성화 시.
        """
        target = model_type or self.config.model_type
        self._call_count += 1

        try:
            if target == ModelType.EXTERNAL:
                return self._call_external(prompt, **kwargs)
            elif target == ModelType.LOCAL:
                return self._call_local(prompt, **kwargs)
            else:
                raise ValueError(f"Unknown model_type: {target!r}")
        except (ValueError, TypeError):
            raise
        except Exception as exc:
            if self.config.fallback_enabled:
                logger.warning("Primary %r failed (%s). Falling back.", target, exc)
                return self._fallback(prompt, target, **kwargs)
            raise

    def _call_external(self, prompt: str, **kwargs: Any) -> BridgeResponse:
        """외부 LLM 어댑터 호출."""
        if self._external_adapter is None:
            raise RuntimeError(
                "외부 LLM 어댑터가 주입되지 않았습니다. "
                "register_external_adapter()로 어댑터를 먼저 등록하세요."
            )
        raw = self._external_adapter.generate(prompt, **kwargs)
        text = raw if isinstance(raw, str) else str(raw)
        return BridgeResponse(
            text=text,
            model_type=ModelType.EXTERNAL,
            adapter_name=self.config.adapter_name,
        )

    def _call_local(self, prompt: str, **kwargs: Any) -> BridgeResponse:
        """로컬 LoRA 어댑터 호출."""
        if self._local_adapter is None:
            raise RuntimeError(
                "로컬 LoRA 어댑터가 주입되지 않았습니다. "
                "register_local_adapter()로 어댑터를 먼저 등록하세요."
            )
        raw = self._local_adapter.generate(prompt, **kwargs)
        text = raw if isinstance(raw, str) else str(raw)
        return BridgeResponse(
            text=text,
            model_type=ModelType.LOCAL,
            adapter_name=self.config.adapter_name,
        )

    def _fallback(
        self,
        prompt: str,
        failed_type: str,
        **kwargs: Any,
    ) -> BridgeResponse:
        """폴백: failed_type의 반대 타입으로 재시도."""
        fallback_type = self.config.fallback_model_type
        if fallback_type == failed_type:
            fallback_type = (
                ModelType.LOCAL
                if failed_type == ModelType.EXTERNAL
                else ModelType.EXTERNAL
            )
        self._fallback_count += 1
        # 폴백 재귀 방지: fallback_enabled=False 로 재호출
        prev_enabled = self.config.fallback_enabled
        self.config.fallback_enabled = False
        try:
            resp = self.generate(prompt, model_type=fallback_type, **kwargs)
        finally:
            self.config.fallback_enabled = prev_enabled
        resp.used_fallback = True
        return resp

    def status(self) -> Dict[str, Any]:
        """브리지 현재 상태 요약 (7키)."""
        return {
            "version": self.VERSION,
            "config_model_type": self.config.model_type,
            "external_adapter_registered": self._external_adapter is not None,
            "local_adapter_registered": self._local_adapter is not None,
            "call_count": self._call_count,
            "fallback_count": self._fallback_count,
            "fallback_enabled": self.config.fallback_enabled,
        }


# ══════════════════════════════════════════════════════════════════════════════
#  V621 확장 — AgentEnvelope 지원 (P-IF-01, ADR-088)
# ══════════════════════════════════════════════════════════════════════════════

from literary_system.llm_bridge.agent_envelope import (  # noqa: E402
    AgentEnvelope,
    AgentRole,
    RoutingDecision,
    RoutingPolicy,
)


def _bridge_generate_with_envelope(
    bridge: "CanonicalBridgeV2",
    prompt_or_envelope: "str | AgentEnvelope",
    policy: "RoutingPolicy | None" = None,
    **kwargs: Any,
) -> BridgeResponse:
    """AgentEnvelope 또는 str을 받아 generate() 하위 호환 래퍼.

    - str 입력: 기존 generate() 그대로 위임
    - AgentEnvelope 입력: policy 기반 라우팅 결정 후 generate() 위임

    Args:
        bridge:              CanonicalBridgeV2 인스턴스.
        prompt_or_envelope:  str 프롬프트 또는 AgentEnvelope.
        policy:              RoutingPolicy (None이면 기본 정책 사용).
        **kwargs:            generate()에 전달할 추가 인자.

    Returns:
        BridgeResponse
    """
    if isinstance(prompt_or_envelope, str):
        return bridge.generate(prompt_or_envelope, **kwargs)

    env = prompt_or_envelope
    effective_policy = policy or RoutingPolicy()
    decision = effective_policy.decide_for_agent(env)

    model_type_map = {
        RoutingDecision.LOCAL_LORA:   ModelType.LOCAL,
        RoutingDecision.EXTERNAL_LLM: ModelType.EXTERNAL,
        RoutingDecision.CASCADE:      None,  # CASCADE: 외부 → 로컬 폴백 순서
    }

    mt = model_type_map.get(decision)
    if mt is None:
        # CASCADE: 외부 우선, 실패 시 로컬
        kwargs.setdefault("model_type", ModelType.EXTERNAL)
    else:
        kwargs.setdefault("model_type", mt)

    return bridge.generate(env.prompt, **kwargs)


# 하위 호환 임포트를 위해 모듈 레벨에 재노출
__all__ = [
    "BridgeConfig",
    "BridgeResponse",
    "CanonicalBridgeV2",
    "ModelType",
    "AgentEnvelope",
    "AgentRole",
    "RoutingDecision",
    "RoutingPolicy",
    "_bridge_generate_with_envelope",
]
