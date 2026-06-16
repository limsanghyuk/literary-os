"""
learning/provider_router.py — GPU 3-모드 라우팅 정책 (V768, ADR-228).

RLAIFTrainingSpec + 환경 신호 → provider ∈ {LOCAL, RUNPOD, LAMBDA_LABS} 자동 선택.
설계도(2026-06-16_gpu_3mode_blueprint_v1.docx) §3.3 5규칙 + 폴백.

우선순위:
  R1 force_provider 명시 → 그대로
  R2 민감 코퍼스 → LOCAL 강제 (프라이버시 1순위, 클라우드 금지)
  R3 모델 8B 초과(로컬 VRAM 불가) → CLOUD
  R4 biweekly 무인 정기학습 → CLOUD
  R5 기본(개발 반복) + LocalPreflight PASS → LOCAL
  R6 LOCAL 후보지만 Preflight FAIL → CLOUD 폴백
LLM-0: 외부 LLM 미호출.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from literary_system.finetune.gpu_adapter import GPUProvider, LocalGPUAdapter
from literary_system.learning.rlaif_orchestrator import RLAIFTrainingSpec


@dataclass
class RoutingSignals:
    """라우팅 결정에 쓰이는 환경 신호."""
    sensitive_corpus:   bool = False
    biweekly_scheduled: bool = False
    force_provider:     Optional[GPUProvider] = None
    monthly_spend_usd:  float = 0.0


@dataclass
class RoutingDecision:
    provider:      GPUProvider
    reason:        str
    fits_locally:  bool
    rule:          str
    fallback_from: Optional[str] = None
    warnings:      List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider":      self.provider.value,
            "reason":        self.reason,
            "fits_locally":  self.fits_locally,
            "rule":          self.rule,
            "fallback_from": self.fallback_from,
            "warnings":      list(self.warnings),
        }


class ProviderRouter:
    """3-모드 provider 자동 선택 + 폴백."""

    def __init__(self, cloud_provider: GPUProvider = GPUProvider.RUNPOD,
                 local_adapter: Optional[LocalGPUAdapter] = None,
                 vram_limit_gb: float = 12.0) -> None:
        self._cloud = cloud_provider
        self._local = local_adapter or LocalGPUAdapter(vram_limit_gb=vram_limit_gb)

    def select(self, spec: RLAIFTrainingSpec,
               signals: Optional[RoutingSignals] = None) -> RoutingDecision:
        sig = signals or RoutingSignals()
        fits = self._local.fits_locally(spec.base_model)

        # R1 명시 override
        if sig.force_provider is not None:
            return RoutingDecision(sig.force_provider, "force_override(명시 지정)", fits, "R1")

        # R2 프라이버시 1순위 → LOCAL 강제 (클라우드 절대 금지)
        if sig.sensitive_corpus:
            warns: List[str] = []
            if not fits:
                warns.append("sensitive_oversize: 민감 데이터+8B초과 → 더 작은 모델 필요(클라우드 위임 금지)")
            return RoutingDecision(GPUProvider.LOCAL, "privacy_first(민감 코퍼스→LOCAL 강제)", fits, "R2", warnings=warns)

        # R3 용량 한계 → CLOUD
        if not fits:
            return RoutingDecision(self._cloud, "capacity(8B 초과·로컬 VRAM 불가→CLOUD)", fits, "R3")

        # R4 무인 정기학습 → CLOUD
        if sig.biweekly_scheduled:
            return RoutingDecision(self._cloud, "scheduled(무인 정기학습→CLOUD)", fits, "R4")

        # R5 기본 개발 반복 → LOCAL (Preflight 확인)
        pf = self._local._preflight.run()
        if pf.ok:
            return RoutingDecision(GPUProvider.LOCAL, "default_dev(개발 반복→LOCAL $0)", fits, "R5")

        # R6 폴백: LOCAL 후보지만 Preflight 실패 → CLOUD
        return RoutingDecision(self._cloud, f"fallback(로컬 Preflight 실패: {pf.detail})",
                               fits, "R6", fallback_from="local")

    def route_trigger(self, spec: RLAIFTrainingSpec,
                      signals: Optional[RoutingSignals] = None, dry_run: bool = True):
        """라우팅 결정 후 RLAIFTrigger 생성·실행. returns (RoutingDecision, TriggerResult)."""
        from literary_system.learning.rlaif_trigger import RLAIFTrigger
        dec = self.select(spec, signals)
        trig = RLAIFTrigger(provider=dec.provider, dry_run=dry_run)
        return dec, trig.trigger(spec)


def validate_routing(decision: RoutingDecision, signals: RoutingSignals) -> Dict[str, Any]:
    """
    G_GPU_ROUTING 검증 — 라우팅 결정의 안전성 규칙.
    V1: 민감 데이터는 절대 CLOUD로 안 감. V2: 폴백은 비민감일 때만. V3: provider 유효.
    """
    viol: List[str] = []
    if signals.sensitive_corpus and decision.provider != GPUProvider.LOCAL:
        viol.append("V1 위반: 민감 코퍼스가 CLOUD로 라우팅됨(프라이버시)")
    if decision.fallback_from == "local" and signals.sensitive_corpus:
        viol.append("V2 위반: 민감 데이터인데 CLOUD 폴백 발생")
    if decision.provider not in (GPUProvider.LOCAL, GPUProvider.RUNPOD,
                                 GPUProvider.LAMBDA_LABS, GPUProvider.HF_AUTOTRAIN):
        viol.append(f"V3 위반: 미지원 provider {decision.provider}")
    return {"passed": not viol, "violations": viol, "decision": decision.to_dict()}
