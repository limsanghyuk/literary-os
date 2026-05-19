"""
Gate25 — V522
NIE v2.0 릴리즈 게이트

통과 조건 (ADR-016 + 설계도 V2.0):
  G1. L_final ≤ 0.15
  G2. agent σ ≤ 0.10
  G3. NPS ≥ +25  (Net Promoter Score, 정수)
  G4. Cost SLO 충족 (이 레이어에서는 mock 검증)
  G5. 16-에피소드 전체 씬 패스율 ≥ 0.90
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

# ─── 기준값 상수 ─────────────────────────────────────────────────────────────
GATE_L_FINAL_MAX: float = 0.15
GATE_SIGMA_MAX: float = 0.10
GATE_NPS_MIN: int = 25
GATE_EPISODE_PASS_RATE_MIN: float = 0.90
GATE_COST_SLO_MAX_USD: float = 5.00        # 에피소드당 최대 비용(달러) — mock

TOTAL_GATES: int = 5


# ─── 결과 클래스 ─────────────────────────────────────────────────────────────
@dataclass
class GateCheckItem:
    gate_id: str            # "G1"~"G5"
    label: str
    measured: float
    threshold: float
    passed: bool
    detail: str = ""


@dataclass
class Gate25Result:
    checks: List[GateCheckItem] = field(default_factory=list)
    overall_passed: bool = False
    fail_reasons: List[str] = field(default_factory=list)

    def summary(self) -> str:
        status = "PASS" if self.overall_passed else "FAIL"
        lines = [f"[Gate25] {status}"]
        for c in self.checks:
            mark = "✓" if c.passed else "✗"
            lines.append(f"  {mark} {c.gate_id} {c.label}: {c.measured:.4f} (threshold {c.threshold})")
        if self.fail_reasons:
            lines.append("  Fail reasons: " + "; ".join(self.fail_reasons))
        return "\n".join(lines)


# ─── Gate25 ──────────────────────────────────────────────────────────────────
class Gate25:
    """
    NIE v2.0 릴리즈 게이트 (V522).

    run() 에 측정값을 전달하면 5개 기준을 점검하고 Gate25Result 를 반환한다.
    """

    def run(
        self,
        l_final: float,
        agent_sigma: float,
        nps: int,
        cost_usd_per_episode: float,
        episode_pass_rate: float,
    ) -> Gate25Result:
        checks: List[GateCheckItem] = []

        # G1: L_final
        g1 = GateCheckItem(
            gate_id="G1",
            label="L_final ≤ 0.15",
            measured=l_final,
            threshold=GATE_L_FINAL_MAX,
            passed=l_final <= GATE_L_FINAL_MAX,
            detail="Narrative tension loss",
        )
        checks.append(g1)

        # G2: agent σ
        g2 = GateCheckItem(
            gate_id="G2",
            label="agent σ ≤ 0.10",
            measured=agent_sigma,
            threshold=GATE_SIGMA_MAX,
            passed=agent_sigma <= GATE_SIGMA_MAX,
            detail="MAE agent standard deviation",
        )
        checks.append(g2)

        # G3: NPS
        g3 = GateCheckItem(
            gate_id="G3",
            label="NPS ≥ +25",
            measured=float(nps),
            threshold=float(GATE_NPS_MIN),
            passed=nps >= GATE_NPS_MIN,
            detail="Net Promoter Score",
        )
        checks.append(g3)

        # G4: Cost SLO
        g4 = GateCheckItem(
            gate_id="G4",
            label=f"Cost ≤ ${GATE_COST_SLO_MAX_USD:.2f}/ep",
            measured=cost_usd_per_episode,
            threshold=GATE_COST_SLO_MAX_USD,
            passed=cost_usd_per_episode <= GATE_COST_SLO_MAX_USD,
            detail="LLM API cost per episode (USD)",
        )
        checks.append(g4)

        # G5: 16-episode pass rate
        g5 = GateCheckItem(
            gate_id="G5",
            label="Episode pass rate ≥ 0.90",
            measured=episode_pass_rate,
            threshold=GATE_EPISODE_PASS_RATE_MIN,
            passed=episode_pass_rate >= GATE_EPISODE_PASS_RATE_MIN,
            detail="Fraction of scenes passing MAE across 16 episodes",
        )
        checks.append(g5)

        # 종합
        fail_reasons = [
            f"{c.gate_id}:{c.label} ({c.measured:.4f})"
            for c in checks if not c.passed
        ]
        overall = all(c.passed for c in checks)

        return Gate25Result(
            checks=checks,
            overall_passed=overall,
            fail_reasons=fail_reasons,
        )

    def run_from_orchestrator(
        self,
        orchestrator,               # NILOrchestrator
        nps: int,
        cost_usd_per_episode: float,
        episode_pass_rate: float,
    ) -> Gate25Result:
        """
        NILOrchestrator 에서 직접 측정값을 추출해 Gate25 를 실행한다.
        """
        l_result = orchestrator.get_l_final()
        sigma = orchestrator.get_mae_sigma()
        return self.run(
            l_final=l_result.l_final,
            agent_sigma=sigma,
            nps=nps,
            cost_usd_per_episode=cost_usd_per_episode,
            episode_pass_rate=episode_pass_rate,
        )
