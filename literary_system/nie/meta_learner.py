"""
MetaLearner — V515
ADR-020: NIL Outer-loop Meta-Learning

- 활성화 조건: 누적 작품 수 >= ACTIVATION_WORKS (기본 30)
- Meta-parameters: AMW LR / λ(NarrativeTensionCurve) / agent_weight / LR scaling
- Outer-loop SGD: advantage = L_final - L_baseline (EMA decay=0.90)
- NILStabilityModule 과 협력: advantage 가 크게 음수 → LR 제약 완화
"""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# ─── 상수 ─────────────────────────────────────────────────────────────────────
ACTIVATION_WORKS: int = 30             # MetaLearner 활성화 임계값
META_LR: float = 0.01                  # outer-loop 학습률
BASELINE_DECAY: float = 0.90           # L_final EMA 감쇠 계수
BASELINE_INIT: float = 0.50            # 초기 EMA 기준선

# Meta-parameter 범위
AMW_LR_MIN: float = 0.001
AMW_LR_MAX: float = 0.050
LAMBDA_MIN: float = 0.10
LAMBDA_MAX: float = 0.80
LR_FACTOR_MIN: float = 0.30
LR_FACTOR_MAX: float = 1.50

# 개선 판정 임계값
IMPROVE_THRESHOLD: float = -0.10       # advantage < -0.10 → 개선 중 → LR 완화
WORSEN_THRESHOLD: float = +0.10        # advantage > +0.10 → 악화 중 → LR 강화

# 기본 meta-parameter 초기값
DEFAULT_AMW_LR: float = 0.005
DEFAULT_LAMBDA: float = 0.30
DEFAULT_LR_FACTOR: float = 1.0


# ─── 결과 데이터 클래스 ───────────────────────────────────────────────────────
@dataclass
class MetaUpdateResult:
    works_count: int
    advantage: float
    l_final: float
    baseline: float
    updates: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_improving(self) -> bool:
        return self.advantage < IMPROVE_THRESHOLD

    @property
    def is_worsening(self) -> bool:
        return self.advantage > WORSEN_THRESHOLD


@dataclass
class MetaState:
    """현재 meta-parameter 스냅샷."""
    amw_lr: float = DEFAULT_AMW_LR
    lam: float = DEFAULT_LAMBDA
    lr_factor: float = DEFAULT_LR_FACTOR

    def as_dict(self) -> Dict[str, float]:
        return {"amw_lr": self.amw_lr, "lam": self.lam, "lr_factor": self.lr_factor}


# ─── MetaLearner ──────────────────────────────────────────────────────────────
class MetaLearner:
    """
    NIL Outer-loop MetaLearner (V515, ADR-020).

    record_work_loss() 를 매 작품 완료 시 호출하고,
    maybe_meta_update() 로 AMW / NarrativeTensionCurve / NILStabilityModule 을 갱신.
    """

    def __init__(self, activation_works: int = ACTIVATION_WORKS) -> None:
        self._activation_works = activation_works
        self._works_count: int = 0
        self._loss_history: List[float] = []
        self._baseline: float = BASELINE_INIT
        self._state = MetaState()
        self._active: bool = False
        self._update_history: List[MetaUpdateResult] = []

    # ── 공개 API ─────────────────────────────────────────────────────────────
    def record_work_loss(self, l_final: float, genre: Optional[str] = None) -> None:
        """
        작품 1편 완료 후 L_final 을 기록한다.
        누적 작품 수가 activation_works 에 도달하면 자동 활성화.
        """
        self._works_count += 1
        self._loss_history.append(l_final)
        self._baseline = (
            BASELINE_DECAY * self._baseline
            + (1 - BASELINE_DECAY) * l_final
        )
        if self._works_count >= self._activation_works:
            self._active = True

    def maybe_meta_update(
        self,
        amw=None,                   # AdaptiveMomentumWeights (optional)
        tension_curve=None,         # NarrativeTensionCurve (optional)
        orchestrator=None,          # MAEOrchestratorV2 (optional)
        stability=None,             # NILStabilityModule (optional)
    ) -> Optional[MetaUpdateResult]:
        """
        활성화 조건 충족 시 outer-loop 갱신 수행.
        컴포넌트가 None 이면 해당 파라미터 갱신을 건너뛴다.
        """
        if not self._active:
            return None
        if not self._loss_history:
            return None

        l_final = self._loss_history[-1]
        advantage = l_final - self._baseline
        updates: Dict[str, Any] = {}

        # 1) AMW LR 갱신
        if amw is not None:
            new_lr = self._state.amw_lr - META_LR * advantage
            new_lr = _clamp(new_lr, AMW_LR_MIN, AMW_LR_MAX)
            self._state.amw_lr = new_lr
            # AMW 에 새 LR 주입 (AMW 는 LR_AMW 속성 또는 set_lr 메서드 사용)
            if hasattr(amw, "set_lr"):
                amw.set_lr(new_lr)
            elif hasattr(amw, "LR_AMW"):
                amw.LR_AMW = new_lr
            updates["amw_lr"] = new_lr

        # 2) λ 갱신 (NarrativeTensionCurve)
        if tension_curve is not None:
            new_lam = self._state.lam - META_LR * advantage
            new_lam = _clamp(new_lam, LAMBDA_MIN, LAMBDA_MAX)
            self._state.lam = new_lam
            tension_curve.update_lambda(new_lam)
            updates["lambda"] = new_lam

        # 3) NILStabilityModule LR 제약 조정
        if stability is not None:
            if advantage < IMPROVE_THRESHOLD:
                # 개선 중 → LR 제약 완화 (최대 1.0 까지)
                cur = stability.get_effective_lr("amw", 1.0)
                relaxed = min(1.0, cur * 1.10)
                stability.set_module_lr_factor("amw", relaxed)
                updates["stability_relaxed"] = True
            elif advantage > WORSEN_THRESHOLD:
                # 악화 중 → LR 제약 강화
                cur = stability.get_effective_lr("amw", 1.0)
                tightened = max(LR_FACTOR_MIN, cur * 0.90)
                stability.set_module_lr_factor("amw", tightened)
                updates["stability_tightened"] = True

        # 4) agent_weight 조정 (orchestrator 가 있을 때)
        if orchestrator is not None and advantage > WORSEN_THRESHOLD:
            # 악화 시 가중치 약간 균등화 (과도한 편중 완화)
            if hasattr(orchestrator, "_weights"):
                old_w = dict(orchestrator._weights)
                mean_w = sum(old_w.values()) / max(len(old_w), 1)
                new_w = {
                    a: _clamp(w - META_LR * (w - mean_w), 0.05, 0.70)
                    for a, w in old_w.items()
                }
                total = sum(new_w.values())
                new_w = {a: v / total for a, v in new_w.items()}
                orchestrator.update_weights(new_w)
                updates["agent_weights"] = new_w

        result = MetaUpdateResult(
            works_count=self._works_count,
            advantage=advantage,
            l_final=l_final,
            baseline=self._baseline,
            updates=updates,
        )
        self._update_history.append(result)
        return result

    def force_activate(self) -> None:
        """테스트·수동 강제 활성화."""
        self._active = True

    @property
    def active(self) -> bool:
        return self._active

    @property
    def works_count(self) -> int:
        return self._works_count

    @property
    def baseline(self) -> float:
        return self._baseline

    @property
    def state(self) -> MetaState:
        return self._state

    @property
    def update_history(self) -> List[MetaUpdateResult]:
        return list(self._update_history)

    def get_meta_param(self, key: str) -> Optional[float]:
        return self._state.as_dict().get(key)


# ─── 유틸 ─────────────────────────────────────────────────────────────────────
def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))
