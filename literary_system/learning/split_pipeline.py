"""
learning/split_pipeline.py — 하이브리드 분업 파이프라인 PoC (V769, ADR-229).

설계도 §4.1 진화방향 E1: **로컬 3B 후보 선별 → 클라우드 8B 최종 강화**.
- Stage A (로컬): 생성 후보 N개를 보상모델(쌍대)로 채점 → 상위 top-k 선별. provider=LOCAL($0).
- Stage B (클라우드): 선별 결과로 8B 최종 DPO 강화. provider=CLOUD(8B 초과→R3).
하이브리드 비용을 "전부 클라우드" 대비 정량 비교 → 하이브리드 실효 측정.
LLM-0: 보상모델 judge는 critic(LLM-1 경계 내). 어댑터·라우터는 외부 LLM 미호출.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from literary_system.finetune.gpu_adapter import get_adapter, GPUProvider, LocalGPUAdapter
from literary_system.learning.provider_router import ProviderRouter, RoutingSignals
from literary_system.learning.reward_model import PairwiseRewardModel, RewardScore
from literary_system.learning.rlaif_orchestrator import RLAIFTrainingSpec


@dataclass
class StagePlan:
    name:                str
    role:                str       # "candidate_selection" | "final_reinforce"
    model:               str
    provider:            str
    rule:                str
    hours:               float
    cost_usd:            float
    electricity_usd:     float

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "role": self.role, "model": self.model,
                "provider": self.provider, "rule": self.rule, "hours": self.hours,
                "cost_usd": self.cost_usd, "electricity_usd": self.electricity_usd}


@dataclass
class SplitReport:
    stages:             List[StagePlan]
    hybrid_cost_usd:    float
    all_cloud_cost_usd: float
    savings_usd:        float
    savings_pct:        float
    selected:           List[str] = field(default_factory=list)
    note:               str = ""

    @property
    def summary(self) -> str:
        return (f"Split-PoC: 하이브리드 ${self.hybrid_cost_usd} vs 올클라우드 "
                f"${self.all_cloud_cost_usd} → 절감 ${self.savings_usd} ({self.savings_pct}%). "
                f"선별 {len(self.selected)}건. {self.note}")

    def to_dict(self) -> Dict[str, Any]:
        return {"stages": [s.to_dict() for s in self.stages],
                "hybrid_cost_usd": self.hybrid_cost_usd,
                "all_cloud_cost_usd": self.all_cloud_cost_usd,
                "savings_usd": self.savings_usd, "savings_pct": self.savings_pct,
                "selected": list(self.selected), "note": self.note}


class SplitPipeline:
    """로컬 선별 + 클라우드 강화 분업 PoC."""

    def __init__(self, router: Optional[ProviderRouter] = None,
                 small_model: str = "llama-3.2-3b", large_model: str = "llama-13b",
                 stage_a_hours: float = 0.5, stage_b_hours: float = 2.0,
                 cloud_provider: GPUProvider = GPUProvider.RUNPOD) -> None:
        self._router = router or ProviderRouter(cloud_provider=cloud_provider)
        self._small = small_model
        self._large = large_model
        self._ha = stage_a_hours
        self._hb = stage_b_hours
        self._cloud = cloud_provider
        self._local = LocalGPUAdapter()

    def _spec(self, model: str) -> RLAIFTrainingSpec:
        return RLAIFTrainingSpec("/x/dpo.jsonl", 12, 0.58, model, 16, "dpo", "prepared")

    def _stage(self, name: str, role: str, model: str, hours: float,
               signals: RoutingSignals) -> StagePlan:
        dec = self._router.select(self._spec(model), signals)
        if dec.provider == GPUProvider.LOCAL:
            cost, elec = 0.0, self._local.estimate_electricity(hours)
        else:
            cost, elec = get_adapter(dec.provider).estimate_cost(hours), 0.0
        return StagePlan(name, role, model, dec.provider.value, dec.rule, hours, cost, elec)

    def select_candidates(self, candidates: Sequence[Tuple[str, str]],
                          refs: Sequence[str], judge: Callable[[str, str], str],
                          top_k: int = 1) -> List[RewardScore]:
        """Stage A 산물: 후보(id,text)를 보상모델로 채점→상위 top_k. (로컬 실행분)."""
        rm = PairwiseRewardModel(judge)
        scores = rm.batch([(cid, ctext, refs) for cid, ctext in candidates])
        return sorted(scores, key=lambda s: s.reward, reverse=True)[:top_k]

    def plan(self, signals: Optional[RoutingSignals] = None,
             selected: Optional[List[str]] = None) -> SplitReport:
        sig = signals or RoutingSignals()
        a = self._stage("StageA", "candidate_selection", self._small, self._ha, sig)
        b = self._stage("StageB", "final_reinforce", self._large, self._hb, sig)
        hybrid = round(a.cost_usd + b.cost_usd, 4)
        # 올클라우드 베이스라인: 두 스테이지 모두 클라우드
        cloud_rate = get_adapter(self._cloud).cost_per_hour
        all_cloud = round(cloud_rate * (self._ha + self._hb), 4)
        savings = round(all_cloud - hybrid, 4)
        pct = round(100.0 * savings / all_cloud, 1) if all_cloud else 0.0
        note = ("StageA 로컬($0)·StageB 클라우드 분업"
                if a.provider == "local" else "이 환경 GPU 없음→StageA도 폴백(4070에선 로컬 분업)")
        return SplitReport([a, b], hybrid, all_cloud, savings, pct, selected or [], note)


def run_split_poc(candidates: Sequence[Tuple[str, str]], refs: Sequence[str],
                  judge: Callable[[str, str], str],
                  signals: Optional[RoutingSignals] = None,
                  pipeline: Optional[SplitPipeline] = None) -> SplitReport:
    """1사이클 PoC: 후보 선별(StageA) → 비용 분석 리포트."""
    p = pipeline or SplitPipeline()
    top = p.select_candidates(candidates, refs, judge, top_k=max(1, len(candidates) // 3))
    return p.plan(signals, selected=[s.draft_id for s in top])
