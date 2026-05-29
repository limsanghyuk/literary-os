"""test_v736_fl_orchestrator.py — FLOrchestrator 단위 테스트 (V736, 40 TC)"""
import math
import pytest

from literary_system.federation.fl_client import FLClient, ProseDataShard
from literary_system.federation.fl_orchestrator import FLOrchestrator, FLRunResult


# ──────────────────────────────────────────────────────────────────────────────
# 픽스처
# ──────────────────────────────────────────────────────────────────────────────

def _make_clients(n=3, lr=0.01):
    shards = [ProseDataShard(shard_id=f"s{i}", num_samples=50+i*10, base_loss=1.0) for i in range(n)]
    return [FLClient(f"c{i}", shards[i], learning_rate=lr, local_epochs=2, seed=i) for i in range(n)]


def _make_orch(n=3, max_rounds=3, use_privacy=True, dp_epsilon=1.0):
    clients = _make_clients(n)
    return FLOrchestrator(clients=clients, max_rounds=max_rounds,
                          dp_epsilon=dp_epsilon, use_privacy=use_privacy)


# ──────────────────────────────────────────────────────────────────────────────
# TestFLOrchestratorInit
# ──────────────────────────────────────────────────────────────────────────────

class TestFLOrchestratorInit:
    def test_tc01_requires_min_clients(self):
        shard = ProseDataShard("s0", num_samples=50)
        with pytest.raises(ValueError):
            FLOrchestrator(clients=[FLClient("c0", shard, learning_rate=0.01)], min_clients=2)

    def test_tc02_valid_init(self):
        orch = _make_orch()
        assert len(orch.clients) == 3

    def test_tc03_coordinator_clients_registered(self):
        orch = _make_orch()
        assert len(orch.coordinator.registered_clients) == 3

    def test_tc04_invalid_max_rounds(self):
        with pytest.raises(ValueError):
            _make_orch(max_rounds=0)

    def test_tc05_invalid_dp_epsilon(self):
        with pytest.raises(ValueError):
            _make_orch(dp_epsilon=-0.1)

    def test_tc06_result_none_before_run(self):
        orch = _make_orch()
        assert orch.result is None

    def test_tc07_aggregator_accessible(self):
        orch = _make_orch()
        assert orch.aggregator is not None

    def test_tc08_privacy_accessible(self):
        orch = _make_orch()
        assert orch.privacy is not None

    def test_tc09_summary_before_run(self):
        orch = _make_orch()
        s = orch.summary()
        assert "num_clients" in s
        assert s["num_clients"] == 3

    def test_tc10_privacy_sigma_computed(self):
        orch = _make_orch(dp_epsilon=1.0)
        budget = orch.privacy.privacy_budget
        expected = 1.0 * math.sqrt(2 * math.log(1.25 / 1e-5)) / 1.0
        assert abs(budget["sigma"] - expected) < 1e-9


# ──────────────────────────────────────────────────────────────────────────────
# TestFLOrchestratorRun
# ──────────────────────────────────────────────────────────────────────────────

class TestFLOrchestratorRun:
    def test_tc11_run_returns_result(self):
        orch = _make_orch()
        result = orch.run_federation()
        assert isinstance(result, FLRunResult)

    def test_tc12_total_rounds_positive(self):
        orch = _make_orch(max_rounds=3)
        result = orch.run_federation()
        assert result.total_rounds > 0

    def test_tc13_final_loss_float(self):
        orch = _make_orch()
        result = orch.run_federation()
        assert isinstance(result.final_global_loss, float)
        assert result.final_global_loss >= 0.0

    def test_tc14_loss_trend_nonempty(self):
        orch = _make_orch()
        result = orch.run_federation()
        assert len(result.loss_trend) > 0

    def test_tc15_privacy_budget_in_result(self):
        orch = _make_orch()
        result = orch.run_federation()
        assert "epsilon" in result.privacy_budget
        assert "sigma" in result.privacy_budget

    def test_tc16_round_summaries_match_total(self):
        orch = _make_orch(max_rounds=3)
        result = orch.run_federation()
        assert len(result.round_summaries) == result.total_rounds

    def test_tc17_elapsed_seconds_positive(self):
        orch = _make_orch()
        result = orch.run_federation()
        assert result.elapsed_seconds >= 0.0

    def test_tc18_result_accessible_via_property(self):
        orch = _make_orch()
        r1 = orch.run_federation()
        r2 = orch.result
        assert r1 is r2

    def test_tc19_to_dict_has_keys(self):
        orch = _make_orch()
        result = orch.run_federation()
        d = result.to_dict()
        for k in ("total_rounds", "converged", "final_global_loss", "loss_trend",
                  "privacy_budget", "round_count", "elapsed_seconds"):
            assert k in d

    def test_tc20_max_rounds_respected(self):
        orch = _make_orch(max_rounds=2)
        result = orch.run_federation()
        assert result.total_rounds <= 2


# ──────────────────────────────────────────────────────────────────────────────
# TestFLOrchestratorPrivacy
# ──────────────────────────────────────────────────────────────────────────────

class TestFLOrchestratorPrivacy:
    def test_tc21_no_privacy_runs(self):
        orch = _make_orch(use_privacy=False)
        result = orch.run_federation()
        assert result.total_rounds > 0

    def test_tc22_privacy_budget_epsilon(self):
        orch = _make_orch(dp_epsilon=2.0)
        result = orch.run_federation()
        assert result.privacy_budget["epsilon"] == 2.0

    def test_tc23_higher_epsilon_different_sigma(self):
        orch_low = _make_orch(dp_epsilon=0.5)
        orch_high = _make_orch(dp_epsilon=2.0)
        s_low = orch_low.privacy.privacy_budget["sigma"]
        s_high = orch_high.privacy.privacy_budget["sigma"]
        assert s_low > s_high  # 낮은 ε → 더 많은 노이즈

    def test_tc24_no_exception_with_privacy(self):
        orch = _make_orch(use_privacy=True, dp_epsilon=0.5)
        result = orch.run_federation()
        assert isinstance(result, FLRunResult)

    def test_tc25_round_summary_has_global_loss(self):
        orch = _make_orch()
        result = orch.run_federation()
        for rs in result.round_summaries:
            assert "global_loss" in rs
            assert isinstance(rs["global_loss"], float)

    def test_tc26_round_summary_participants_count(self):
        orch = _make_orch(n=3)
        result = orch.run_federation()
        for rs in result.round_summaries:
            assert rs["participants"] == 3

    def test_tc27_round_summary_has_round_num(self):
        orch = _make_orch()
        result = orch.run_federation()
        nums = [rs["round"] for rs in result.round_summaries]
        assert nums == sorted(nums)

    def test_tc28_adr_198_exists(self):
        import os
        path = "docs/adr/ADR-198.md"
        assert os.path.exists(path), f"ADR-198 missing: {path}"

    def test_tc29_adr_199_exists(self):
        import os
        path = "docs/adr/ADR-199.md"
        assert os.path.exists(path), f"ADR-199 missing: {path}"

    def test_tc30_fl_orchestrator_module_importable(self):
        from literary_system.federation import fl_orchestrator  # noqa: F401
        assert hasattr(fl_orchestrator, "FLOrchestrator")


# ──────────────────────────────────────────────────────────────────────────────
# TestFLOrchestratorEdgeCases
# ──────────────────────────────────────────────────────────────────────────────

class TestFLOrchestratorEdgeCases:
    def test_tc31_two_clients_minimum(self):
        shards = [ProseDataShard(f"s{i}", num_samples=50) for i in range(2)]
        clients = [FLClient(f"c{i}", shards[i], learning_rate=0.01, seed=i) for i in range(2)]
        orch = FLOrchestrator(clients=clients, max_rounds=2, min_clients=2)
        result = orch.run_federation()
        assert result.total_rounds > 0

    def test_tc32_five_clients(self):
        shards = [ProseDataShard(f"s{i}", num_samples=40+i*5) for i in range(5)]
        clients = [FLClient(f"c{i}", shards[i], learning_rate=0.01, seed=i) for i in range(5)]
        orch = FLOrchestrator(clients=clients, max_rounds=2)
        result = orch.run_federation()
        assert result.total_rounds > 0

    def test_tc33_convergence_flag_accessible(self):
        orch = _make_orch(max_rounds=3)
        result = orch.run_federation()
        assert isinstance(result.converged, bool)

    def test_tc34_loss_trend_length_matches_rounds(self):
        orch = _make_orch(max_rounds=3)
        result = orch.run_federation()
        assert len(result.loss_trend) == result.total_rounds

    def test_tc35_summary_after_run_has_total_rounds(self):
        orch = _make_orch()
        orch.run_federation()
        s = orch.summary()
        assert "total_rounds" in s

    def test_tc36_summary_after_run_has_converged(self):
        orch = _make_orch()
        orch.run_federation()
        s = orch.summary()
        assert "converged" in s

    def test_tc37_single_round_result_valid(self):
        orch = _make_orch(max_rounds=1)
        result = orch.run_federation()
        assert result.total_rounds == 1
        assert len(result.loss_trend) == 1

    def test_tc38_repeated_run_updates_result(self):
        orch = _make_orch(max_rounds=1)
        r1 = orch.run_federation()
        # FLOrchestrator는 stateful — 수렴 후 두 번째 실행은 바로 종료
        r2 = orch.run_federation()
        assert r2 is not None

    def test_tc39_g90_gate_pass(self):
        from literary_system.gates.fl_gate import run_fl_gate
        result = run_fl_gate()
        assert result["approved"] is True
        assert result["gate"] == "G90"

    def test_tc40_g90_all_checks_pass(self):
        from literary_system.gates.fl_gate import run_fl_gate
        result = run_fl_gate()
        for c in result["checks"]:
            assert c["passed"], f"{c['check_id']} failed: {c['message']}"
