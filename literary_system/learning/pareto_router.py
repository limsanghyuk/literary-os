"""
learning/pareto_router.py — 파레토 라우팅 + 모드 디스패처 (V770, ADR-230).

설계도 §4.1 진화방향 E2: 규칙 기반 라우팅(V768)을 **비용 vs 예상품질 파레토 최적**으로 승급.
+ TrainingMode 디스패처: 개발자가 CLOUD/LOCAL/HYBRID/AUTO 중 지정하면 그대로 작동.

품질은 '용량 기반 휴리스틱 추정치'(측정 아님) — 결정 보조용. 최종 진실은 인간 GT/보상모델.
- 로컬·RunPod = QLoRA(4bit) → 품질계수 0.85 (연구: 풀FT의 80~90%)
- Lambda H100 = 풀FT 가능 → 품질계수 1.0
하드 제약(R1 force/R2 민감→LOCAL/R3 용량/R4 스케줄)은 ParetoRouter보다 우선(안전).
LLM-0: 외부 LLM 미호출.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from literary_system.finetune.gpu_adapter import get_adapter, GPUProvider, LocalGPUAdapter
from literary_system.learning.provider_router import (
    ProviderRouter, RoutingSignals, RoutingDecision)
from literary_system.learning.rlaif_orchestrator import RLAIFTrainingSpec

QLORA_QUALITY_FACTOR = 0.85     # QLoRA ~ 풀FT의 80~90%
FULL_FT_FACTOR       = 1.0
HEADROOM_CLOSE       = 0.5      # 1회 학습이 닫는 격차 비율(보수 추정)


@dataclass
class ParetoCandidate:
    provider:          str
    method:            str       # "qlora" | "full_ft"
    cost_usd:          float
    expected_quality:  float     # 추정 학습후 승률 [0,1] (측정 아님)
    fits:              bool

    def dominates(self, other: "ParetoCandidate") -> bool:
        """비용↓·품질↑ 모두 우세(하나는 강하게)면 지배."""
        return (self.cost_usd <= other.cost_usd and self.expected_quality >= other.expected_quality
                and (self.cost_usd < other.cost_usd or self.expected_quality > other.expected_quality))

    def to_dict(self) -> Dict[str, Any]:
        return {"provider": self.provider, "method": self.method, "cost_usd": self.cost_usd,
                "expected_quality": self.expected_quality, "fits": self.fits}


def pareto_frontier(cands: List[ParetoCandidate]) -> List[ParetoCandidate]:
    """비지배 후보 집합."""
    return [c for c in cands if not any(o.dominates(c) for o in cands if o is not c)]


class ParetoRouter:
    """비용/예상품질 파레토 최적 라우터. 하드 제약은 ProviderRouter에 위임."""

    def __init__(self, base_router: Optional[ProviderRouter] = None,
                 preference: str = "balanced", hours: float = 2.0,
                 vram_limit_gb: float = 12.0) -> None:
        if preference not in ("cost", "balanced", "quality"):
            raise ValueError("preference ∈ cost|balanced|quality")
        self._base = base_router or ProviderRouter()
        self._pref = preference
        self._hours = hours
        self._local = LocalGPUAdapter(vram_limit_gb=vram_limit_gb)

    def _quality(self, spec: RLAIFTrainingSpec, factor: float) -> float:
        base = spec.baseline_win_rate
        return round(base + (1.0 - base) * factor * HEADROOM_CLOSE, 4)

    def candidates(self, spec: RLAIFTrainingSpec) -> List[ParetoCandidate]:
        fits = self._local.fits_locally(spec.base_model)
        out: List[ParetoCandidate] = []
        if fits:
            out.append(ParetoCandidate("local", "qlora",
                       round(self._local.estimate_electricity(self._hours), 4),
                       self._quality(spec, QLORA_QUALITY_FACTOR), True))
            out.append(ParetoCandidate("runpod", "qlora",
                       get_adapter(GPUProvider.RUNPOD).estimate_cost(self._hours),
                       self._quality(spec, QLORA_QUALITY_FACTOR), True))
        else:
            out.append(ParetoCandidate("runpod", "qlora",
                       get_adapter(GPUProvider.RUNPOD).estimate_cost(self._hours),
                       self._quality(spec, QLORA_QUALITY_FACTOR), False))
        # Lambda H100 = 풀FT(최고 품질, 최고 비용) — 항상 후보
        out.append(ParetoCandidate("lambda_labs", "full_ft",
                   get_adapter(GPUProvider.LAMBDA_LABS).estimate_cost(self._hours),
                   self._quality(spec, FULL_FT_FACTOR), True))
        return out

    def _score(self, c: ParetoCandidate, cmin: float, cmax: float,
               qmin: float, qmax: float) -> float:
        nc = 0.0 if cmax == cmin else (c.cost_usd - cmin) / (cmax - cmin)
        nq = 0.0 if qmax == qmin else (c.expected_quality - qmin) / (qmax - qmin)
        lam = {"cost": 0.8, "balanced": 0.5, "quality": 0.2}[self._pref]
        return lam * (1.0 - nc) + (1.0 - lam) * nq      # 비용↓·품질↑ 높을수록 우수

    def select(self, spec: RLAIFTrainingSpec,
               signals: Optional[RoutingSignals] = None) -> RoutingDecision:
        sig = signals or RoutingSignals()
        # 1) 하드 제약 먼저(R1/R2/R3/R4/R6) — 안전·프라이버시 우선
        hard = self._base.select(spec, sig)
        if hard.rule in ("R1", "R2", "R4", "R6"):
            hard.reason += " [pareto:skip(하드제약 우선)]"
            return hard
        # 2) 파레토 최적 선택 (R3/R5 영역)
        front = pareto_frontier(self.candidates(spec))
        cmin = min(c.cost_usd for c in front); cmax = max(c.cost_usd for c in front)
        qmin = min(c.expected_quality for c in front); qmax = max(c.expected_quality for c in front)
        best = max(front, key=lambda c: self._score(c, cmin, cmax, qmin, qmax))
        prov = GPUProvider(best.provider)
        dec = RoutingDecision(prov, f"pareto_{self._pref}({best.method}, ${best.cost_usd}, q≈{best.expected_quality})",
                              best.fits, "P*")
        dec.warnings.append(f"품질은 용량기반 추정치(측정 아님). frontier={len(front)}개")
        return dec


# ---------------------------------------------------------------------------
# TrainingMode 디스패처 — 개발자 지정 모드 작동 보장
# ---------------------------------------------------------------------------

class TrainingMode(str, Enum):
    CLOUD  = "cloud"     # 강제 클라우드(RunPod 기본)
    LOCAL  = "local"     # 강제 로컬(4070)
    HYBRID = "hybrid"    # 분업(로컬 선별→클라우드 강화)
    AUTO   = "auto"      # 파레토 최적 자동


def _cloud_adapter(provider: GPUProvider, use_real: bool, api_key: str):
    """클라우드 provider면서 use_real이면 RealRunPodAdapter 주입(없으면 None=기본 Mock)."""
    if use_real and provider == GPUProvider.RUNPOD:
        from literary_system.finetune.runpod_real_adapter import RealRunPodAdapter
        return RealRunPodAdapter(api_key=api_key)
    return None


def dispatch_training(spec: RLAIFTrainingSpec, mode: TrainingMode,
                      signals: Optional[RoutingSignals] = None,
                      dry_run: bool = True, preference: str = "balanced",
                      real: bool = False, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    개발자가 지정한 모드로 학습 디스패치. 3방식(CLOUD/LOCAL/HYBRID)+AUTO 단일 진입점.
    real=True 또는 RUNPOD_API_KEY 존재 시 클라우드 단계가 RealRunPodAdapter(실 RunPod)로 흐름.
    dry_run=True(기본)면 실 어댑터라도 네트워크 미호출(안전). 실 학습은 dry_run=False+키 필요.
    """
    import os
    from literary_system.learning.rlaif_trigger import RLAIFTrigger
    sig = signals or RoutingSignals()
    key = api_key or os.environ.get("RUNPOD_API_KEY", "")
    use_real = bool(real or key)

    if mode == TrainingMode.HYBRID:
        from literary_system.learning.split_pipeline import SplitPipeline
        rep = SplitPipeline().plan(sig)
        out = {"mode": "hybrid", "stages": [s.to_dict() for s in rep.stages],
               "hybrid_cost_usd": rep.hybrid_cost_usd, "savings_pct": rep.savings_pct,
               "status": "planned", "summary": rep.summary, "real_cloud": use_real}
        # StageB(클라우드)면 실 어댑터로 트리거(로컬 단계는 PC에서 train_local 실행)
        cloud = next((st for st in rep.stages if st.provider != "local"), None)
        if cloud is not None:
            prov = GPUProvider(cloud.provider)
            adp = _cloud_adapter(prov, use_real, key)
            r = RLAIFTrigger(provider=prov, dry_run=dry_run, adapter=adp).trigger(spec)
            out["cloud_stage"] = {"provider": prov.value, "status": r.status,
                                  "real_adapter": adp is not None, "summary": r.summary}
        return out

    if mode == TrainingMode.AUTO:
        dec = ParetoRouter(preference=preference).select(spec, sig)
    elif mode == TrainingMode.LOCAL:
        dec = ProviderRouter().select(spec, RoutingSignals(force_provider=GPUProvider.LOCAL))
    else:  # CLOUD
        dec = ProviderRouter().select(spec, RoutingSignals(force_provider=GPUProvider.RUNPOD))

    adp = None if dec.provider == GPUProvider.LOCAL else _cloud_adapter(dec.provider, use_real, key)
    res = RLAIFTrigger(provider=dec.provider, dry_run=dry_run, adapter=adp).trigger(spec)
    return {"mode": mode.value, "provider": dec.provider.value, "rule": dec.rule,
            "reason": dec.reason, "status": res.status, "summary": res.summary,
            "real_adapter": adp is not None}
