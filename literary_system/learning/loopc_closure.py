"""
learning/loopc_closure.py — loop-C 폐회로 오케스트레이션 (V774, ADR-234).

회사 설계도 §1~2 구현. RLAIF 부품(트리거·라우터·어댑터·first_training_kit)을
"선호쌍 → 학습 → 명작 대비 재측정 → 수용판정 → 다음 라운드"의 닫힌 루프로 잇는 글루.
실 학습은 GPU(4070/클라우드)에서 수행 → 본 모듈은 ①라운드 계획(dry) + ⑤수용판정 + ⑥결정.
LLM-0: 생성기만 학습 대상. 외부 LLM 미호출.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from literary_system.learning.pareto_router import dispatch_training, TrainingMode
from literary_system.learning.provider_router import RoutingSignals
from literary_system.learning.rlaif_orchestrator import RLAIFOrchestrator
from literary_system.learning.loop_c import load_preference_pairs, generation_win_rate
from literary_system.learning.winrate_gate import g_loopc_winrate, WinrateGateResult

TARGET_W_DEFAULT = 0.60         # 단계적 상향(0.55→0.60→...) 목표 승률


@dataclass
class LoopCRoundReport:
    round_idx:     int
    n_pairs:       int
    w0:            float
    w1:            Optional[float]
    training_plan: Dict[str, Any]
    gate:          Optional[WinrateGateResult]
    next_action:   str
    summary:       str

    def to_dict(self) -> Dict[str, Any]:
        return {"round_idx": self.round_idx, "n_pairs": self.n_pairs, "w0": self.w0, "w1": self.w1,
                "training_plan": self.training_plan,
                "gate": self.gate.to_dict() if self.gate else None,
                "next_action": self.next_action, "summary": self.summary}


class LoopCClosure:
    """1 라운드: 선호쌍 → 학습계획 → (실측 W₁ 주입) → 수용판정 → 다음행동."""

    def __init__(self, mode: TrainingMode = TrainingMode.LOCAL,
                 target_w: float = TARGET_W_DEFAULT, tau_kl: float = 0.1,
                 base_model: str = "meta-llama/Llama-3.2-3B") -> None:
        self._mode = mode
        self._target = target_w
        self._tau = tau_kl
        self._base = base_model

    def plan_round(self, pairs_path: str, signals: Optional[RoutingSignals] = None,
                   real: bool = False, api_key: Optional[str] = None) -> Dict[str, Any]:
        """①~③ 계획(dry): 선호쌍 적재 → 스펙 → dispatch(dry_run) 학습 계획."""
        import tempfile, os
        pairs = load_preference_pairs(pairs_path)
        w0 = generation_win_rate(pairs)
        fd, out = tempfile.mkstemp(suffix=".jsonl"); os.close(fd)
        spec = RLAIFOrchestrator(base_model=self._base).prepare(pairs, out)
        plan = dispatch_training(spec, self._mode, signals or RoutingSignals(),
                                 dry_run=True, real=real, api_key=api_key)
        return {"w0": w0, "n_pairs": len(pairs), "base_model": self._base,
                "mode": self._mode.value, "dispatch": plan}

    def evaluate_round(self, round_idx: int, w0: float, w1: float, n_pairs: int,
                       kl: float = 0.0, r_before: Optional[float] = None,
                       r_after: Optional[float] = None,
                       training_plan: Optional[Dict[str, Any]] = None) -> LoopCRoundReport:
        """⑤수용판정 + ⑥⑦결정(채택→다음/완료, 롤백→약점피드백)."""
        gate = g_loopc_winrate(w0, w1, kl=kl, r_before=r_before, r_after=r_after,
                               n_pairs=n_pairs, tau_kl=self._tau)
        if gate.passed:
            if w1 >= self._target:
                action = "adopt_done(목표 승률 도달 — 종료조건)"
            else:
                action = "adopt_continue(채택 → 선호쌍 확대 후 다음 라운드)"
        else:
            action = "rollback_feedback(폐기 → 약한 기능축 데이터트랙 피드백)"
        summary = (f"R{round_idx}: W {w0}→{w1} (ΔW {gate.delta_w:+}) | {gate.decision} | {action} "
                   f"| {'신뢰O' if gate.reliable else '신뢰약(표본↑)'}")
        return LoopCRoundReport(round_idx, n_pairs, w0, w1, training_plan or {}, gate, action, summary)

    def run_round(self, pairs_path: str, round_idx: int = 1,
                  measured_w1: Optional[float] = None, kl: float = 0.0,
                  r_before: Optional[float] = None, r_after: Optional[float] = None,
                  signals: Optional[RoutingSignals] = None,
                  real: bool = False, api_key: Optional[str] = None) -> LoopCRoundReport:
        """계획 + (실측 W₁ 있으면) 수용판정까지. 실측 없으면 계획만(학습 대기)."""
        plan = self.plan_round(pairs_path, signals, real, api_key)
        if measured_w1 is None:
            return LoopCRoundReport(round_idx, plan["n_pairs"], plan["w0"], None, plan,
                                    None, "await_training(GPU 학습 후 W₁ 재측정 필요)",
                                    f"R{round_idx} 계획: W₀={plan['w0']} → 4070/클라우드 학습 대기")
        return self.evaluate_round(round_idx, plan["w0"], measured_w1, plan["n_pairs"],
                                   kl, r_before, r_after, plan)
