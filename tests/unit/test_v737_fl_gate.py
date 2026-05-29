"""test_v737_fl_gate.py — G90 FL Gate 단위 테스트 (V737, 30 TC)"""
import math
import pytest

from literary_system.gates.fl_gate import (
    check_fl1_min_clients,
    check_fl2_fedavg_accuracy,
    check_fl3_privacy_budget,
    check_fl4_convergence_detection,
    check_fl5_e2e_pipeline,
    run_fl_gate,
    FLGateResult,
)


# ──────────────────────────────────────────────────────────────────────────────
# TestFL1MinClients
# ──────────────────────────────────────────────────────────────────────────────

class TestFL1MinClients:
    def test_tc01_passes(self):
        r = check_fl1_min_clients()
        assert r.passed

    def test_tc02_check_id(self):
        r = check_fl1_min_clients()
        assert r.check_id == "FL-1"

    def test_tc03_message_contains_count(self):
        r = check_fl1_min_clients()
        assert "2" in r.message


# ──────────────────────────────────────────────────────────────────────────────
# TestFL2FedAvg
# ──────────────────────────────────────────────────────────────────────────────

class TestFL2FedAvg:
    def test_tc04_passes(self):
        r = check_fl2_fedavg_accuracy()
        assert r.passed

    def test_tc05_check_id(self):
        r = check_fl2_fedavg_accuracy()
        assert r.check_id == "FL-2"

    def test_tc06_message_contains_expected(self):
        r = check_fl2_fedavg_accuracy()
        assert "1.4" in r.message

    def test_tc07_weighted_mean_correct(self):
        # 독립 검증: (80/100)*[1,2] + (20/100)*[3,4] = [1.4, 2.4]
        from literary_system.federation.fedavg import FedAvgAggregator
        from literary_system.federation.fl_types import FLClientState
        agg = FedAvgAggregator()
        states = [
            FLClientState("a", 1, 80, 0.5, {"w": [1.0, 2.0]}),
            FLClientState("b", 1, 20, 0.3, {"w": [3.0, 4.0]}),
        ]
        gm = agg.aggregate(states, round_num=1)
        assert abs(gm.global_weights["w"][0] - 1.4) < 1e-9
        assert abs(gm.global_weights["w"][1] - 2.4) < 1e-9


# ──────────────────────────────────────────────────────────────────────────────
# TestFL3PrivacyBudget
# ──────────────────────────────────────────────────────────────────────────────

class TestFL3PrivacyBudget:
    def test_tc08_passes(self):
        r = check_fl3_privacy_budget()
        assert r.passed

    def test_tc09_check_id(self):
        r = check_fl3_privacy_budget()
        assert r.check_id == "FL-3"

    def test_tc10_sigma_in_message(self):
        r = check_fl3_privacy_budget()
        assert "sigma" in r.message

    def test_tc11_sigma_formula(self):
        # σ = clip_norm * sqrt(2 * ln(1.25/δ)) / ε
        epsilon, delta, clip_norm = 1.0, 1e-5, 1.0
        expected = clip_norm * math.sqrt(2 * math.log(1.25 / delta)) / epsilon
        from literary_system.federation.fl_privacy import FLPrivacyNoise
        dp = FLPrivacyNoise(epsilon=epsilon, delta=delta, clip_norm=clip_norm)
        assert abs(dp.privacy_budget["sigma"] - expected) < 1e-9

    def test_tc12_all_budget_keys_present(self):
        from literary_system.federation.fl_privacy import FLPrivacyNoise
        dp = FLPrivacyNoise(epsilon=1.0, delta=1e-5, clip_norm=1.0)
        for k in ("epsilon", "delta", "sigma"):
            assert k in dp.privacy_budget


# ──────────────────────────────────────────────────────────────────────────────
# TestFL4Convergence
# ──────────────────────────────────────────────────────────────────────────────

class TestFL4Convergence:
    def test_tc13_passes(self):
        r = check_fl4_convergence_detection()
        assert r.passed

    def test_tc14_check_id(self):
        r = check_fl4_convergence_detection()
        assert r.check_id == "FL-4"

    def test_tc15_message_mentions_converged(self):
        r = check_fl4_convergence_detection()
        assert "converged" in r.message.lower()

    def test_tc16_no_convergence_large_delta(self):
        from literary_system.federation.fl_coordinator import FLCoordinator
        from literary_system.federation.fl_types import FLGlobalModel
        coord = FLCoordinator(min_clients=2, convergence_threshold=0.001)
        coord.register_client("x1")
        coord.register_client("x2")
        coord.start_round()
        coord.finalize_round(FLGlobalModel(1, {}, global_loss=1.0))
        coord.start_round()
        coord.finalize_round(FLGlobalModel(2, {}, global_loss=0.5))  # Δ=0.5 > 0.001
        assert not coord.is_converged()


# ──────────────────────────────────────────────────────────────────────────────
# TestFL5E2E
# ──────────────────────────────────────────────────────────────────────────────

class TestFL5E2E:
    def test_tc17_passes(self):
        r = check_fl5_e2e_pipeline()
        assert r.passed

    def test_tc18_check_id(self):
        r = check_fl5_e2e_pipeline()
        assert r.check_id == "FL-5"

    def test_tc19_message_contains_rounds(self):
        r = check_fl5_e2e_pipeline()
        assert "rounds" in r.message

    def test_tc20_result_to_dict(self):
        r = check_fl5_e2e_pipeline()
        d = r.to_dict()
        for k in ("check_id", "description", "passed", "message"):
            assert k in d


# ──────────────────────────────────────────────────────────────────────────────
# TestRunFlGate
# ──────────────────────────────────────────────────────────────────────────────

class TestRunFlGate:
    def test_tc21_gate_approved(self):
        result = run_fl_gate()
        assert result["approved"] is True

    def test_tc22_gate_id(self):
        result = run_fl_gate()
        assert result["gate"] == "G90"

    def test_tc23_five_checks(self):
        result = run_fl_gate()
        assert len(result["checks"]) == 5

    def test_tc24_summary_5_5(self):
        result = run_fl_gate()
        assert "5/5" in result["summary"]

    def test_tc25_all_check_ids_present(self):
        result = run_fl_gate()
        ids = {c["check_id"] for c in result["checks"]}
        assert ids == {"FL-1", "FL-2", "FL-3", "FL-4", "FL-5"}

    def test_tc26_all_checks_passed(self):
        result = run_fl_gate()
        for c in result["checks"]:
            assert c["passed"], f"{c['check_id']}: {c['message']}"

    def test_tc27_version_v737(self):
        result = run_fl_gate()
        assert result.get("version") == "V737"

    def test_tc28_g90_in_release_gate(self):
        from literary_system.gates.release_gate import GATES
        ids = [g[0] for g in GATES]
        assert "fl_g90" in ids

    def test_tc29_release_gate_g90_passes(self):
        from literary_system.gates.release_gate import GATES
        gate_fn = next(fn for gid, _, fn in GATES if gid == "fl_g90")
        r = gate_fn()
        assert r.get("passed") or r.get("pass"), f"G90 failed: {r}"

    def test_tc30_fl_gate_module_importable(self):
        from literary_system.gates import fl_gate  # noqa: F401
        assert hasattr(fl_gate, "run_fl_gate")
