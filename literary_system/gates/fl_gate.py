"""fl_gate.py — G90 FL Gate (V737, SP-D.4)

FL-1~FL-5 5개 축 검사:
  FL-1  최소 클라이언트 등록 (≥2)
  FL-2  FedAvg 가중 평균 정확성
  FL-3  DP 프라이버시 예산 접근 가능
  FL-4  수렴 감지 동작
  FL-5  E2E 파이프라인 정상 완료
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List

from literary_system.federation.fl_client import FLClient, ProseDataShard
from literary_system.federation.fl_coordinator import FLCoordinator
from literary_system.federation.fl_orchestrator import FLOrchestrator
from literary_system.federation.fedavg import FedAvgAggregator
from literary_system.federation.fl_privacy import FLPrivacyNoise
from literary_system.federation.fl_types import FLClientState


@dataclass
class FLGateResult:
    check_id: str
    description: str
    passed: bool
    message: str

    def to_dict(self) -> Dict:
        return {
            "check_id": self.check_id,
            "description": self.description,
            "passed": self.passed,
            "message": self.message,
        }


# ─────────────────────────────────────────────────────────────────────────────
# FL-1: 최소 클라이언트 등록 (≥2)
# ─────────────────────────────────────────────────────────────────────────────

def check_fl1_min_clients() -> FLGateResult:
    """FLCoordinator에 최소 2개 클라이언트를 등록할 수 있는지 검사."""
    coord = FLCoordinator(min_clients=2)
    coord.register_client("c1")
    coord.register_client("c2")
    count = len(coord.registered_clients)
    passed = count >= 2
    return FLGateResult(
        check_id="FL-1",
        description="FL coordinator min-clients registration (≥2)",
        passed=passed,
        message=f"registered_clients={count}" if passed else f"only {count} client(s)",
    )


# ─────────────────────────────────────────────────────────────────────────────
# FL-2: FedAvg 가중 평균 정확성
# ─────────────────────────────────────────────────────────────────────────────

def check_fl2_fedavg_accuracy() -> FLGateResult:
    """FedAvg 집계 결과가 가중 평균 공식과 일치하는지 검사."""
    agg = FedAvgAggregator()
    states = [
        FLClientState(
            client_id="c1", round_num=1, num_samples=80, local_loss=0.5,
            weights={"w": [1.0, 2.0]},
        ),
        FLClientState(
            client_id="c2", round_num=1, num_samples=20, local_loss=0.3,
            weights={"w": [3.0, 4.0]},
        ),
    ]
    gm = agg.aggregate(states, round_num=1)

    # 기댓값: w_global = (80/100)*[1,2] + (20/100)*[3,4] = [1.4, 2.4]
    expected = [1.4, 2.4]
    actual = gm.global_weights.get("w", [])
    ok = all(abs(a - e) < 1e-9 for a, e in zip(actual, expected))

    return FLGateResult(
        check_id="FL-2",
        description="FedAvg weighted-mean accuracy",
        passed=ok,
        message=f"w={actual} (expected {expected})" if ok else f"MISMATCH w={actual}",
    )


# ─────────────────────────────────────────────────────────────────────────────
# FL-3: DP 프라이버시 예산 접근 가능
# ─────────────────────────────────────────────────────────────────────────────

def check_fl3_privacy_budget() -> FLGateResult:
    """FLPrivacyNoise.privacy_budget에 epsilon/delta/sigma 키가 모두 존재하는지 검사."""
    dp = FLPrivacyNoise(epsilon=1.0, delta=1e-5, clip_norm=1.0)
    budget = dp.privacy_budget
    required_keys = {"epsilon", "delta", "sigma"}
    missing = required_keys - set(budget.keys())

    # sigma 수식 검증: σ = clip_norm * sqrt(2 * ln(1.25/δ)) / ε
    expected_sigma = 1.0 * math.sqrt(2 * math.log(1.25 / 1e-5)) / 1.0
    sigma_ok = abs(budget.get("sigma", -1) - expected_sigma) < 1e-9

    passed = (not missing) and sigma_ok
    if passed:
        msg = f"sigma={budget['sigma']:.6f} (expected {expected_sigma:.6f})"
    else:
        msg = f"missing={missing}, sigma_ok={sigma_ok}"

    return FLGateResult(
        check_id="FL-3",
        description="DP privacy budget accessible (epsilon/delta/sigma)",
        passed=passed,
        message=msg,
    )


# ─────────────────────────────────────────────────────────────────────────────
# FL-4: 수렴 감지 동작
# ─────────────────────────────────────────────────────────────────────────────

def check_fl4_convergence_detection() -> FLGateResult:
    """손실 차이가 threshold 이하일 때 수렴 플래그가 True로 설정되는지 검사."""
    coord = FLCoordinator(min_clients=2, convergence_threshold=0.1)
    coord.register_client("c1")
    coord.register_client("c2")

    # 첫 라운드 — 손실 1.0
    from literary_system.federation.fl_types import FLGlobalModel
    r1 = coord.start_round()
    gm1 = FLGlobalModel(round_num=1, global_weights={}, global_loss=1.0)
    coord.finalize_round(gm1)

    # 두 번째 라운드 — 손실 1.05 (Δ=0.05 < 0.1 → 수렴)
    r2 = coord.start_round()
    gm2 = FLGlobalModel(round_num=2, global_weights={}, global_loss=1.05)
    coord.finalize_round(gm2)

    converged = coord.is_converged()
    return FLGateResult(
        check_id="FL-4",
        description="FL convergence detection (Δloss < threshold)",
        passed=converged,
        message="converged=True (Δloss=0.05 < 0.1)" if converged
                else "convergence not detected (unexpected)",
    )


# ─────────────────────────────────────────────────────────────────────────────
# FL-5: E2E 파이프라인 정상 완료
# ─────────────────────────────────────────────────────────────────────────────

def check_fl5_e2e_pipeline() -> FLGateResult:
    """FLOrchestrator.run_federation()이 예외 없이 완료되는지 검사."""
    try:
        shards = [
            ProseDataShard(shard_id=f"s{i}", num_samples=50 + i * 10, base_loss=1.0)
            for i in range(3)
        ]
        clients = [
            FLClient(f"c{i}", shards[i], learning_rate=0.01, local_epochs=2, seed=i)
            for i in range(3)
        ]
        orch = FLOrchestrator(
            clients=clients,
            max_rounds=3,
            dp_epsilon=1.0,
            dp_delta=1e-5,
            use_privacy=True,
        )
        result = orch.run_federation()

        ok = (
            result.total_rounds > 0
            and isinstance(result.final_global_loss, float)
            and len(result.loss_trend) > 0
        )
        msg = (
            f"rounds={result.total_rounds}, "
            f"final_loss={result.final_global_loss:.4f}, "
            f"converged={result.converged}"
        )
    except Exception as exc:
        ok = False
        msg = f"EXCEPTION: {exc}"

    return FLGateResult(
        check_id="FL-5",
        description="FL E2E pipeline completes without exception",
        passed=ok,
        message=msg,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Gate G90 진입점
# ─────────────────────────────────────────────────────────────────────────────

def run_fl_gate() -> Dict:
    """G90 FL Gate — FL-1~FL-5 전체 실행."""
    checks = [
        check_fl1_min_clients(),
        check_fl2_fedavg_accuracy(),
        check_fl3_privacy_budget(),
        check_fl4_convergence_detection(),
        check_fl5_e2e_pipeline(),
    ]

    all_passed = all(c.passed for c in checks)
    return {
        "gate": "G90",
        "name": "FL Gate",
        "version": "V737",
        "approved": all_passed,
        "checks": [c.to_dict() for c in checks],
        "summary": f"{sum(c.passed for c in checks)}/{len(checks)} checks passed",
    }
