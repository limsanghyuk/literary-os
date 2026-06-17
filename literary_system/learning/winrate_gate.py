"""
learning/winrate_gate.py — G_LOOPC_WINRATE 수용 게이트 (V774, ADR-234).

회사 설계도(v773_loopC_closure_design) §3 구현. 학습된 어댑터를 채택할지 판정:
  1차(필수): ΔW = W₁ − W₀ > 0  (학습 후 명작 대비 승률 상승)
  2차(가드): KL(학습 ‖ 기준) ≤ τ  (과적합·붕괴 방지)
  3차(비퇴행): 구조 게이트 R 평균이 학습 전 대비 하락 없음
세 조건 AND → 채택, 하나라도 실패 → 롤백.
※단일 라운드·소수 쌍은 ΔW가 노이즈 → 신뢰조건(최소 라운드/표본) 동반 권고(정직 표기).
LLM-0: 순수 판정 로직(외부 LLM 미호출).
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional

TAU_KL_DEFAULT = 0.1
R_REGRESSION_TOL = 0.0          # 구조 R 비퇴행 허용 오차
MIN_PAIRS_RELIABLE = 50         # 이하면 ΔW 통계적 신뢰 약함(경고)


@dataclass
class WinrateGateResult:
    w0: float
    w1: float
    delta_w: float
    c1_winrate: bool            # ΔW > 0
    c2_kl: bool                 # KL ≤ τ
    c3_structure: bool          # R 비퇴행
    passed: bool
    decision: str               # "adopt" | "rollback"
    reliable: bool              # 표본 충분(통계 신뢰)
    detail: str

    def to_dict(self) -> Dict[str, Any]:
        return {"w0": self.w0, "w1": self.w1, "delta_w": self.delta_w,
                "c1_winrate": self.c1_winrate, "c2_kl": self.c2_kl, "c3_structure": self.c3_structure,
                "passed": self.passed, "decision": self.decision, "reliable": self.reliable,
                "detail": self.detail}


def g_loopc_winrate(w0: float, w1: float, kl: float = 0.0,
                    r_before: Optional[float] = None, r_after: Optional[float] = None,
                    n_pairs: int = 0, tau_kl: float = TAU_KL_DEFAULT,
                    r_tol: float = R_REGRESSION_TOL) -> WinrateGateResult:
    delta = round(w1 - w0, 4)
    c1 = delta > 0
    c2 = kl <= tau_kl
    c3 = True if (r_before is None or r_after is None) else (r_after >= r_before - r_tol)
    passed = c1 and c2 and c3
    reliable = n_pairs >= MIN_PAIRS_RELIABLE
    notes = []
    if not c1: notes.append(f"ΔW={delta}≤0(승률 미상승)")
    if not c2: notes.append(f"KL={kl}>τ={tau_kl}(붕괴 위험)")
    if not c3: notes.append("구조 R 퇴행")
    if passed and not reliable:
        notes.append(f"표본 {n_pairs}<{MIN_PAIRS_RELIABLE} → ΔW 통계 신뢰 약함(라운드 누적/표본 확대 권고)")
    detail = "채택(3조건 충족)" if passed else "롤백: " + ", ".join(notes)
    if passed and not reliable:
        detail = "조건부 채택(신뢰 약함): " + (", ".join(notes) or "")
    return WinrateGateResult(w0, w1, delta, c1, c2, c3, passed,
                             "adopt" if passed else "rollback", reliable, detail)
