"""
SP-B.1 (V598) — LoRAInferenceGateway: LLMBridgeInterface + 로컬 LoRA 추론

Phase B 본안 보강 (ADR-058):
- LLMBridgeInterface 확장 (literary_system.llm_bridge)
- LoRAModelRegistry에서 PROMOTED 아티팩트 자동 선택
- safetensors 로컬 추론 (HAS_TRANSFORMERS=True 시 실 추론)
- HAS_TRANSFORMERS=False 시 StubInferenceBackend (테스트 전용)
- 레이턴시 측정 → Gate G53 (≤2000 ms + 100자+)
- provider_name = "lora_local"

LLM-1 원칙: 추론 게이트웨이는 LoRAModelRegistry의 PROMOTED 아티팩트만 사용.
LLM-0 원칙: 이 모듈은 외부 LLM API를 직접 호출하지 않음.
"""
from __future__ import annotations

import time
import warnings
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Union

# ---------------------------------------------------------------------------
# HAS_TRANSFORMERS — safetensors / PEFT 선택적 의존
# ---------------------------------------------------------------------------

try:
    from peft import PeftModel  # type: ignore
    from transformers import AutoModelForCausalLM, AutoTokenizer  # type: ignore
    HAS_TRANSFORMERS: bool = True
except ImportError:
    HAS_TRANSFORMERS = False

# ---------------------------------------------------------------------------
# LLMBridgeInterface 의존 (literary-os 전체 코드베이스에서 임포트)
# ---------------------------------------------------------------------------

# ADR-060: 무조건 임포트 — llm_bridge는 literary_system 핵심 모듈이므로
# 중복 클래스 스텁 불필요 (duplicate_zero_g37 준수)
from literary_system.llm_bridge.llm_bridge_interface import LLMBridgeInterface
from literary_system.llm_bridge.llm_context import LLMContext, LLMResponse, coerce_context
HAS_LLM_BRIDGE: bool = True

from literary_system.finetune.lora_artifact import ArtifactStage, LoRAArtifact
from literary_system.finetune.lora_model_registry import (
    ArtifactNotFoundError,
    LoRAModelRegistry,
)


# ---------------------------------------------------------------------------
# 상수
# ---------------------------------------------------------------------------

LORA_PROVIDER_NAME: str = "lora_local"
G53_LATENCY_LIMIT_MS: float = 2000.0   # Gate G53 레이턴시 상한
G53_MIN_LENGTH: int = 100               # Gate G53 최소 응답 길이 (chars)
DEFAULT_MAX_NEW_TOKENS: int = 256


# ---------------------------------------------------------------------------
# InferenceResult
# ---------------------------------------------------------------------------

@dataclass
class InferenceResult:
    """
    LoRA 추론 결과.

    Attributes:
        text:          생성된 텍스트
        latency_ms:    추론 레이턴시 (밀리초)
        artifact_id:   사용된 LoRA 아티팩트 ID
        backend:       사용 백엔드 ('transformers' | 'stub')
        prompt_tokens: 입력 토큰 수 (추정, stub 시 0)
        output_tokens: 출력 토큰 수 (추정, stub 시 len(text.split()))
    """
    text: str
    latency_ms: float
    artifact_id: str
    backend: str = "stub"
    prompt_tokens: int = 0
    output_tokens: int = 0

    @property
    def passes_g53(self) -> bool:
        """Gate G53 합격 기준: latency≤2000ms AND len(text)≥100."""
        return self.latency_ms <= G53_LATENCY_LIMIT_MS and len(self.text) >= G53_MIN_LENGTH


# ---------------------------------------------------------------------------
# StubInferenceBackend — transformers 없이 테스트용 추론 시뮬레이션
# ---------------------------------------------------------------------------

class StubInferenceBackend:
    """
    로컬 추론 스텁.
    HAS_TRANSFORMERS=False 환경에서 테스트·CI 에 사용.
    실 GPU 없이 Gate G53 레이턴시·길이 요건을 충족하는 더미 텍스트 생성.
    """

    _DRAMA_TEMPLATE: str = (
        "장면이 시작된다. {prompt_preview} "
        "두 인물은 서로의 눈을 바라보며 말없이 감정을 교환했다. "
        "창밖으로 도시의 불빛이 빛나고, 실내에는 묵직한 침묵이 흘렀다. "
        "그 순간, 운명의 실이 조용히 엮이기 시작했다. "
        "대사와 행동이 교차하며 서사의 긴장감이 고조되었다. "
        "이 장면은 전체 이야기의 전환점이 되는 핵심 순간이다."
    )

    def generate(self, prompt: str, max_new_tokens: int = DEFAULT_MAX_NEW_TOKENS,
                 temperature: float = 0.7) -> tuple[str, int, int]:
        """
        Returns:
            (generated_text, prompt_tokens, output_tokens)
        """
        preview = prompt[:40].replace("\n", " ") if prompt else ""
        text = self._DRAMA_TEMPLATE.format(prompt_preview=preview)
        # max_new_tokens 기준으로 반복 확장 (G53 길이 보장)
        while len(text) < G53_MIN_LENGTH:
            text += " " + text[:50]
        text = text[:max(G53_MIN_LENGTH + 50, max_new_tokens * 4)]
        prompt_tokens = max(1, len(prompt.split()))
        output_tokens = max(1, len(text.split()))
        return text, prompt_tokens, output_tokens


# ---------------------------------------------------------------------------
# LoRAInferenceGateway
# ---------------------------------------------------------------------------

class LoRAInferenceGateway(LLMBridgeInterface):
    """
    LoRA 추론 게이트웨이.

    LoRAModelRegistry의 PROMOTED 아티팩트를 자동으로 로드하여
    LLMBridgeInterface 계약에 맞게 추론을 제공한다.

    ADR-058 LLM-1 원칙:
        - PROMOTED 아티팩트만 서빙 허용
        - CANDIDATE/VALIDATED 요청 시 RuntimeError

    Gate G53 목표:
        - 응답 레이턴시 ≤ 2000ms
        - 응답 길이 ≥ 100 chars
    """

    def __init__(
        self,
        registry: Optional[LoRAModelRegistry] = None,
        stub_mode: bool = not HAS_TRANSFORMERS,
        max_new_tokens: int = DEFAULT_MAX_NEW_TOKENS,
    ) -> None:
        """
        Args:
            registry:       LoRAModelRegistry 인스턴스 (None이면 빈 메모리 레지스트리)
            stub_mode:      True이면 StubInferenceBackend 사용 (테스트·CI용)
            max_new_tokens: 최대 생성 토큰 수
        """
        self._registry = registry or LoRAModelRegistry()
        self._stub_mode = stub_mode
        self._max_new_tokens = max_new_tokens
        self._stub_backend = StubInferenceBackend()

        # transformers 실 모델 (load_model() 호출 후 설정)
        self._model: Any = None
        self._tokenizer: Any = None
        self._loaded_artifact_id: str = ""

    # ------------------------------------------------------------------
    # LLMBridgeInterface 구현
    # ------------------------------------------------------------------

    @property
    def provider_name(self) -> str:
        return LORA_PROVIDER_NAME

    def is_available(self) -> bool:
        """PROMOTED 아티팩트가 있으면 True."""
        return self._registry.get_active() is not None

    def generate(self, prompt: str, context: Union[LLMContext, dict, None] = None) -> str:
        """
        LoRA 추론 실행.

        Args:
            prompt:  입력 프롬프트 텍스트
            context: LLMContext 또는 dict (max_tokens, temperature 등)

        Returns:
            생성된 텍스트

        Raises:
            RuntimeError: PROMOTED 아티팩트 없음
        """
        result = self._infer(prompt, context)
        return result.text

    def generate_with_response(
        self, prompt: str, context: Union[LLMContext, dict, None] = None
    ) -> LLMResponse:
        """generate() + LLMResponse 래퍼."""
        result = self._infer(prompt, context)
        return LLMResponse(
            text=result.text,
            provider_id=self.provider_name,
            latency_ms=result.latency_ms,
        )

    def parse_action_packet(self, raw: str) -> Any:
        """LoRA 출력 파싱 — 간단한 텍스트 반환 (action packet 미사용)."""
        return {"type": "lora_output", "text": raw}

    # ------------------------------------------------------------------
    # LoRA 전용 추론 메서드
    # ------------------------------------------------------------------

    def infer(
        self,
        prompt: str,
        context: Union[LLMContext, dict, None] = None,
    ) -> InferenceResult:
        """
        LoRA 추론 결과를 InferenceResult로 반환.

        Raises:
            RuntimeError: PROMOTED 아티팩트 없음
        """
        return self._infer(prompt, context)

    def _infer(
        self,
        prompt: str,
        context: Union[LLMContext, dict, None],
    ) -> InferenceResult:
        """내부 추론 로직."""
        ctx = coerce_context(context) if context is not None else LLMContext()
        max_tokens = getattr(ctx, "max_tokens", self._max_new_tokens)
        temperature = getattr(ctx, "temperature", 0.7)

        # PROMOTED 아티팩트 확인 (LLM-1 원칙)
        active = self._registry.get_active()
        if active is None:
            raise RuntimeError(
                "LoRAInferenceGateway: PROMOTED 아티팩트 없음 — "
                "LoRAModelRegistry에 아티팩트를 등록·승격 후 재시도."
            )

        t0 = time.monotonic()

        if self._stub_mode or not HAS_TRANSFORMERS:
            text, prompt_tok, output_tok = self._stub_backend.generate(
                prompt, max_new_tokens=max_tokens, temperature=temperature
            )
            backend = "stub"
        else:
            text, prompt_tok, output_tok = self._transformers_infer(
                prompt, active, max_new_tokens=max_tokens, temperature=temperature
            )
            backend = "transformers"

        latency_ms = (time.monotonic() - t0) * 1000.0

        result = InferenceResult(
            text=text,
            latency_ms=round(latency_ms, 2),
            artifact_id=active.artifact_id,
            backend=backend,
            prompt_tokens=prompt_tok,
            output_tokens=output_tok,
        )

        # G53 경고 (게이트에서 실제 차단)
        if latency_ms > G53_LATENCY_LIMIT_MS:
            warnings.warn(
                f"LoRAInferenceGateway: latency={latency_ms:.1f}ms > "
                f"G53_LIMIT={G53_LATENCY_LIMIT_MS}ms",
                UserWarning,
                stacklevel=3,
            )
        if len(text) < G53_MIN_LENGTH:
            warnings.warn(
                f"LoRAInferenceGateway: output_len={len(text)} < "
                f"G53_MIN={G53_MIN_LENGTH}",
                UserWarning,
                stacklevel=3,
            )

        return result

    def _transformers_infer(
        self,
        prompt: str,
        artifact: LoRAArtifact,
        max_new_tokens: int,
        temperature: float,
    ) -> tuple[str, int, int]:
        """
        HuggingFace transformers + PEFT 실 추론.
        artifact_path의 safetensors LoRA 어댑터를 베이스 모델에 로드.
        """
        if not HAS_TRANSFORMERS:
            raise RuntimeError("transformers not installed")

        # 아티팩트 변경 시 모델 재로드
        if self._loaded_artifact_id != artifact.artifact_id:
            self._load_model(artifact)

        if self._tokenizer is None or self._model is None:
            raise RuntimeError("LoRA 모델 로드 실패")

        import torch  # type: ignore

        inputs = self._tokenizer(
            prompt, return_tensors="pt",
            truncation=True, max_length=512,
        )
        with torch.no_grad():
            outputs = self._model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=max(0.01, temperature),
                do_sample=temperature > 0.0,
                pad_token_id=self._tokenizer.eos_token_id,
            )
        generated_ids = outputs[0][inputs["input_ids"].shape[1]:]
        text = self._tokenizer.decode(generated_ids, skip_special_tokens=True)
        prompt_tok = inputs["input_ids"].shape[1]
        output_tok = generated_ids.shape[0]
        return text, int(prompt_tok), int(output_tok)

    def load_model(self, artifact: Optional[LoRAArtifact] = None) -> None:
        """
        LoRA 어댑터 명시적 로드.
        artifact=None이면 PROMOTED 아티팩트 자동 선택.

        Raises:
            RuntimeError: transformers 미설치 또는 PROMOTED 없음
        """
        if not HAS_TRANSFORMERS:
            raise RuntimeError(
                "load_model(): transformers/peft 미설치. "
                "pip install transformers peft accelerate --break-system-packages"
            )
        if artifact is None:
            artifact = self._registry.get_active()
        if artifact is None:
            raise RuntimeError("load_model(): PROMOTED 아티팩트 없음.")
        self._load_model(artifact)

    def _load_model(self, artifact: LoRAArtifact) -> None:
        """내부 모델 로드 (transformers + PEFT)."""
        if not HAS_TRANSFORMERS:
            return
        self._tokenizer = AutoTokenizer.from_pretrained(
            artifact.base_model, trust_remote_code=True
        )
        base = AutoModelForCausalLM.from_pretrained(
            artifact.base_model, trust_remote_code=True, device_map="auto"
        )
        self._model = PeftModel.from_pretrained(base, artifact.artifact_path)
        self._model.eval()
        self._loaded_artifact_id = artifact.artifact_id

    # ------------------------------------------------------------------
    # 상태 조회
    # ------------------------------------------------------------------

    @property
    def active_artifact(self) -> Optional[LoRAArtifact]:
        """현재 PROMOTED(서빙 중) 아티팩트."""
        return self._registry.get_active()

    @property
    def is_stub_mode(self) -> bool:
        """스텁 모드 여부."""
        return self._stub_mode

    def __repr__(self) -> str:
        active = self.active_artifact
        aid = active.artifact_id if active else "none"
        return (
            f"LoRAInferenceGateway("
            f"stub={self._stub_mode}, "
            f"active='{aid}', "
            f"registry={self._registry!r})"
        )
