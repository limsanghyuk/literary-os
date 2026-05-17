"""
V498 테스트 — PhysicsRewardBridge + NIEContainer
ADR-015: LLM-0 원칙, Policy Gradient Lite, R_baseline EMA
ADR-016: NIE-L7 Container 배선
"""
import pytest
from unittest.mock import MagicMock

import sys
sys.path.insert(0, ".")

from literary_system.nie.physics_reward_bridge import (
    PhysicsRewardBridge, BridgeResult, _compute_reward,
)
from literary_system.nie.nie_l7_container import NIEContainer, NIEConfig
from literary_system.evaluation.mae_orchestrator import MAEOrchestrator, MAEResult
from literary_system.evaluation.mae_agents import AgentVerdict
from literary_system.evaluation.scene_metrics_collector import SceneMetrics
from literary_system.learning.physics_coefficient_updater import PhysicsCoefficientUpdater
from literary_system.physics.coefficient_store import PhysicsCoefficientStore
from literary_system.physics.scene_feature_extractor import SceneFeature


# ── 픽스처 ──────────────────────────────────────────────────────────

def _make_verdict(passed: bool) -> AgentVerdict:
    v = MagicMock(spec=AgentVerdict)
    v.passed = passed
    v.to_dict.return_value = {"passed": passed}
    return v


def _make_mae_result(pass_count: int, total: int, consensus: bool) -> MAEResult:
    votes = [_make_verdict(i < pass_count) for i in range(total)]
    r = MagicMock(spec=MAEResult)
    r.pass_count = pass_count
    r.votes = votes
    r.consensus = consensus
    return r


def _make_metrics() -> SceneMetrics:
    m = MagicMock(spec=SceneMetrics)
    return m


def _make_bridge(pass_count=3, total=3, consensus=True):
    store = PhysicsCoefficientStore()
    updater = PhysicsCoefficientUpdater(store)
    mae = MagicMock(spec=MAEOrchestrator)
    mae.evaluate.return_value = _make_mae_result(pass_count, total, consensus)
    bridge = PhysicsRewardBridge(
        mae_orchestrator=mae,
        coefficient_updater=updater,
        coefficient_store=store,
    )
    return bridge, store, mae


# ── 단위 테스트 ─────────────────────────────────────────────────────

class TestComputeReward:
    def test_all_pass_with_consensus(self):
        r = _make_mae_result(3, 3, True)
        reward = _compute_reward(r)
        assert reward == pytest.approx(1.0)  # 3/3 + 0.1 → clamp 1.0

    def test_all_pass_no_consensus(self):
        r = _make_mae_result(3, 3, False)
        reward = _compute_reward(r)
        assert reward == pytest.approx(1.0)  # 3/3 + 0 = 1.0

    def test_partial_pass(self):
        r = _make_mae_result(2, 3, True)
        reward = _compute_reward(r)
        assert reward == pytest.approx(2/3 + 0.1)

    def test_all_fail(self):
        r = _make_mae_result(0, 3, False)
        reward = _compute_reward(r)
        assert reward == pytest.approx(0.0)

    def test_clamp_at_1(self):
        r = _make_mae_result(3, 3, True)
        reward = _compute_reward(r)
        assert reward <= 1.0


class TestPhysicsRewardBridge:
    def test_bridge_result_type(self):
        bridge, _, _ = _make_bridge()
        result = bridge.process("s001", _make_metrics())
        assert isinstance(result, BridgeResult)
        assert result.scene_id == "s001"

    def test_reward_range(self):
        bridge, _, _ = _make_bridge(pass_count=2, total=3, consensus=False)
        result = bridge.process("s001", _make_metrics())
        assert 0.0 <= result.reward <= 1.0

    def test_baseline_ema_updates(self):
        bridge, _, _ = _make_bridge()
        init_baseline = bridge.get_baseline()
        bridge.process("s001", _make_metrics())
        assert bridge.get_baseline() != init_baseline

    def test_advantage_sign_positive(self):
        """높은 reward → positive advantage"""
        bridge, _, _ = _make_bridge(pass_count=3, total=3, consensus=True)
        # init baseline=0.5, reward=1.0 → advantage > 0
        result = bridge.process("s001", _make_metrics())
        assert result.advantage > 0

    def test_advantage_sign_negative(self):
        """낮은 reward → negative advantage"""
        bridge, _, _ = _make_bridge(pass_count=0, total=3, consensus=False)
        # init baseline=0.5, reward=0.0 → advantage < 0
        result = bridge.process("s001", _make_metrics())
        assert result.advantage < 0

    def test_no_feature_no_update(self):
        bridge, _, _ = _make_bridge()
        result = bridge.process("s001", _make_metrics(), feature=None)
        assert result.coefficients_updated is False
        assert result.delta == {}

    def test_with_feature_updates_coefficients(self):
        bridge, store, _ = _make_bridge()
        feature = SceneFeature(
            conflict_intensity=0.8,
            scene_energy_ratio=0.7,
            motif_residue_score=0.6,
            curiosity_gradient=0.5,
            reader_uncertainty=0.4,
            reader_pull=0.3,
        )
        old = store.as_dict().copy()
        result = bridge.process("s001", _make_metrics(), feature=feature)
        assert result.coefficients_updated is True
        new = store.as_dict()
        # 최소 1개 계수가 변경되었는지 확인
        changed = any(abs(new[k] - old[k]) > 1e-8 for k in new)
        assert changed

    def test_history_accumulates(self):
        bridge, _, _ = _make_bridge()
        bridge.process("s001", _make_metrics())
        bridge.process("s002", _make_metrics())
        assert len(bridge.get_history()) == 2

    def test_reset_clears_history(self):
        bridge, _, _ = _make_bridge()
        bridge.process("s001", _make_metrics())
        bridge.reset_baseline()
        assert len(bridge.get_history()) == 0
        assert bridge.get_baseline() == pytest.approx(PhysicsRewardBridge.BASELINE_INIT)

    def test_batch_processing(self):
        bridge, _, _ = _make_bridge()
        scenes = [
            {"scene_id": f"s{i:03d}", "metrics": _make_metrics()}
            for i in range(5)
        ]
        results = bridge.process_batch(scenes)
        assert len(results) == 5
        assert all(isinstance(r, BridgeResult) for r in results)

    def test_to_dict_serializable(self):
        bridge, _, _ = _make_bridge()
        result = bridge.process("s001", _make_metrics())
        d = result.to_dict()
        assert "scene_id" in d
        assert "reward" in d
        assert "advantage" in d
        assert "baseline" in d
        assert "coefficients_updated" in d

    def test_stability_module_lr_injection(self):
        """NILStabilityModule이 LR을 조정할 때 반영 여부"""
        stability = MagicMock()
        stability.get_effective_lr.return_value = 0.001  # 절반 축소
        store = PhysicsCoefficientStore()
        updater = PhysicsCoefficientUpdater(store)
        mae = MagicMock(spec=MAEOrchestrator)
        mae.evaluate.return_value = _make_mae_result(3, 3, True)
        bridge = PhysicsRewardBridge(
            mae_orchestrator=mae,
            coefficient_updater=updater,
            coefficient_store=store,
            stability_module=stability,
        )
        feature = SceneFeature(conflict_intensity=0.9)
        bridge.process("s001", _make_metrics(), feature=feature)
        stability.get_effective_lr.assert_called_once_with("physics", PhysicsRewardBridge.LR_PHYSICS)
        assert updater.LR == pytest.approx(0.001)


class TestNIEContainer:
    def _make_container(self):
        store = PhysicsCoefficientStore()
        mae = MagicMock(spec=MAEOrchestrator)
        mae.evaluate.return_value = _make_mae_result(3, 3, True)
        config = NIEConfig(version="NIE-v2.0-TEST")
        container = NIEContainer(
            mae_orchestrator=mae,
            coefficient_store=store,
            config=config,
        )
        return container, store

    def test_run_scene_returns_bridge_result(self):
        container, _ = self._make_container()
        result = container.run_scene("s001", _make_metrics())
        assert isinstance(result, BridgeResult)

    def test_get_status_structure(self):
        container, _ = self._make_container()
        container.run_scene("s001", _make_metrics())
        status = container.get_status()
        assert "version" in status
        assert "physics_coefficients" in status
        assert "reward_baseline" in status
        assert "processed_scenes" in status
        assert status["processed_scenes"] == 1

    def test_reset_clears_state(self):
        container, _ = self._make_container()
        container.run_scene("s001", _make_metrics())
        container.reset()
        status = container.get_status()
        assert status["processed_scenes"] == 0

    def test_config_flags_default_false(self):
        container, _ = self._make_container()
        status = container.get_status()
        assert status["config"]["stability"] is False
        assert status["config"]["temporal_cim"] is False
        assert status["config"]["meta_learner"] is False

    def test_sample_rate_in_status(self):
        container, _ = self._make_container()
        status = container.get_status()
        assert status["config"]["sample_rate"] == pytest.approx(0.27)

    def test_bridge_property(self):
        container, _ = self._make_container()
        assert isinstance(container.bridge, PhysicsRewardBridge)

    def test_store_property(self):
        container, store = self._make_container()
        assert container.store is store

    def test_adr015_llm_zero_mae_evaluate_called(self):
        """ADR-015: MAEOrchestrator.evaluate()가 호출되는지 확인"""
        store = PhysicsCoefficientStore()
        mae = MagicMock(spec=MAEOrchestrator)
        mae.evaluate.return_value = _make_mae_result(2, 3, True)
        container = NIEContainer(mae_orchestrator=mae, coefficient_store=store)
        container.run_scene("s001", _make_metrics())
        mae.evaluate.assert_called_once()

    def test_adr016_nie_version_string(self):
        """ADR-016: NIE 버전 문자열 포함 확인"""
        container, _ = self._make_container()
        status = container.get_status()
        assert "NIE" in status["version"]
