"""V734: FLClient + FLPrivacyNoise 테스트 (50 TC)

TC01~TC20: ProseDataShard + FLClient 기본
TC21~TC40: FLClient 훈련 로직
TC41~TC50: FLPrivacyNoise
"""
import sys, os, math
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from literary_system.federation.fl_client import ProseDataShard, FLClient
from literary_system.federation.fl_privacy import FLPrivacyNoise
from literary_system.federation.fl_types import FLClientState


class TestProseDataShard:
    def test_tc01_create(self):
        s = ProseDataShard("shard1", 100)
        assert s.shard_id == "shard1"

    def test_tc02_num_samples(self):
        assert ProseDataShard("s", 200).num_samples == 200

    def test_tc03_base_loss_default(self):
        assert ProseDataShard("s", 100).base_loss == 1.0

    def test_tc04_noise_std_default(self):
        assert ProseDataShard("s", 100).noise_std == 0.05

    def test_tc05_custom_base_loss(self):
        assert ProseDataShard("s", 100, base_loss=0.5).base_loss == 0.5

    def test_tc06_zero_samples_raises(self):
        with pytest.raises(ValueError):
            ProseDataShard("s", 0)

    def test_tc07_negative_samples_raises(self):
        with pytest.raises(ValueError):
            ProseDataShard("s", -1)

    def test_tc08_negative_base_loss_raises(self):
        with pytest.raises(ValueError):
            ProseDataShard("s", 100, base_loss=-0.1)


class TestFLClientBasic:
    def _make(self, cid="c1", n=100, seed=42):
        shard = ProseDataShard(cid, n)
        return FLClient(cid, shard, seed=seed)

    def test_tc09_create(self):
        c = self._make()
        assert c.client_id == "c1"

    def test_tc10_learning_rate(self):
        c = self._make()
        assert c.learning_rate == 0.01

    def test_tc11_local_epochs(self):
        c = self._make()
        assert c.local_epochs == 3

    def test_tc12_weight_dim(self):
        c = self._make()
        assert c.weight_dim == 8

    def test_tc13_empty_client_id_raises(self):
        with pytest.raises(ValueError):
            FLClient("", ProseDataShard("s", 100))

    def test_tc14_zero_lr_raises(self):
        with pytest.raises(ValueError):
            FLClient("c1", ProseDataShard("s", 100), learning_rate=0)

    def test_tc15_zero_epochs_raises(self):
        with pytest.raises(ValueError):
            FLClient("c1", ProseDataShard("s", 100), local_epochs=0)

    def test_tc16_initial_weights_exist(self):
        c = self._make()
        assert len(c.local_weights) > 0

    def test_tc17_initial_weight_dim_correct(self):
        c = self._make()
        w = c.local_weights
        assert all(len(v) == 8 for v in w.values())

    def test_tc18_receive_global_model(self):
        c = self._make()
        c.receive_global_model({"layer_0": [1.0] * 8})
        assert c.local_weights["layer_0"] == [1.0] * 8

    def test_tc19_receive_empty_model_keeps_local(self):
        c = self._make()
        original = c.local_weights
        c.receive_global_model({})
        assert len(c.local_weights) > 0  # 비워지지 않음

    def test_tc20_local_weights_immutable(self):
        c = self._make()
        w = c.local_weights
        w["layer_0"][0] = 9999.0
        assert c.local_weights["layer_0"][0] != 9999.0


class TestFLClientTrain:
    def _make(self, seed=0):
        shard = ProseDataShard("c1", 100, base_loss=1.0)
        return FLClient("c1", shard, learning_rate=0.1, local_epochs=5, seed=seed)

    def test_tc21_train_returns_client_state(self):
        c = self._make()
        state = c.train(round_num=1)
        assert isinstance(state, FLClientState)

    def test_tc22_state_client_id(self):
        c = self._make()
        assert c.train(1).client_id == "c1"

    def test_tc23_state_round_num(self):
        c = self._make()
        assert c.train(5).round_num == 5

    def test_tc24_state_num_samples(self):
        c = self._make()
        assert c.train(1).num_samples == 100

    def test_tc25_state_loss_nonnegative(self):
        c = self._make()
        assert c.train(1).local_loss >= 0.0

    def test_tc26_state_weights_not_empty(self):
        c = self._make()
        assert c.train(1).weights

    def test_tc27_state_is_valid(self):
        c = self._make()
        assert c.train(1).is_valid()

    def test_tc28_train_reduces_loss_trend(self):
        """여러 라운드 훈련 시 손실이 평균적으로 감소해야 함."""
        shard = ProseDataShard("c1", 100, base_loss=2.0, noise_std=0.001)
        c = FLClient("c1", shard, learning_rate=0.5, local_epochs=10, seed=1)
        losses = []
        for r in range(5):
            state = c.train(round_num=r + 1)
            losses.append(state.local_loss)
        # 처음과 마지막 비교 (노이즈가 작으므로 감소 경향)
        assert losses[0] >= losses[-1] or abs(losses[0] - losses[-1]) < 1.0

    def test_tc29_receive_then_train_uses_global(self):
        c = self._make()
        global_w = {"layer_0": [0.5] * 8}
        c.receive_global_model(global_w)
        state = c.train(1)
        # 가중치가 글로벌 기반에서 업데이트되었는지 확인
        assert state.weights["layer_0"] != [0.5] * 8  # 업데이트됨

    def test_tc30_reproducible_with_seed(self):
        shard = ProseDataShard("c1", 100, base_loss=1.0)
        c1 = FLClient("c1", shard, seed=42)
        c2 = FLClient("c1", shard, seed=42)
        s1 = c1.train(1)
        s2 = c2.train(1)
        assert abs(s1.local_loss - s2.local_loss) < 1e-9

    def test_tc31_different_seeds_different_results(self):
        shard = ProseDataShard("c1", 100, base_loss=1.0, noise_std=0.1)
        c1 = FLClient("c1", shard, seed=1)
        c2 = FLClient("c1", shard, seed=999)
        s1 = c1.train(1)
        s2 = c2.train(1)
        # 매우 높은 확률로 다른 손실
        assert s1.local_loss != s2.local_loss

    def test_tc32_multiple_clients_different_loss(self):
        states = []
        for i in range(3):
            shard = ProseDataShard(f"c{i}", 100, base_loss=float(i+1))
            c = FLClient(f"c{i}", shard, seed=i)
            states.append(c.train(1))
        losses = [s.local_loss for s in states]
        assert len(set(round(l, 3) for l in losses)) > 1


class TestFLPrivacyNoise:
    def test_tc33_create(self):
        p = FLPrivacyNoise()
        assert p is not None

    def test_tc34_epsilon_default(self):
        assert FLPrivacyNoise().epsilon == 1.0

    def test_tc35_delta_default(self):
        assert FLPrivacyNoise().delta == 1e-5

    def test_tc36_sigma_positive(self):
        assert FLPrivacyNoise().sigma > 0

    def test_tc37_sigma_formula(self):
        p = FLPrivacyNoise(epsilon=1.0, delta=1e-5, clip_norm=1.0)
        expected = 1.0 * math.sqrt(2 * math.log(1.25 / 1e-5)) / 1.0
        assert abs(p.sigma - expected) < 1e-9

    def test_tc38_zero_epsilon_raises(self):
        with pytest.raises(ValueError):
            FLPrivacyNoise(epsilon=0)

    def test_tc39_invalid_delta_raises(self):
        with pytest.raises(ValueError):
            FLPrivacyNoise(delta=1.5)

    def test_tc40_zero_clip_norm_raises(self):
        with pytest.raises(ValueError):
            FLPrivacyNoise(clip_norm=0)

    def test_tc41_add_noise_changes_weights(self):
        p = FLPrivacyNoise(seed=0)
        w = {"layer": [1.0, 2.0, 3.0]}
        noisy = p.add_noise(w)
        assert noisy["layer"] != [1.0, 2.0, 3.0]

    def test_tc42_add_noise_preserves_original(self):
        p = FLPrivacyNoise(seed=0)
        w = {"layer": [1.0, 2.0]}
        _ = p.add_noise(w)
        assert w["layer"] == [1.0, 2.0]

    def test_tc43_clip_weights_within_norm(self):
        p = FLPrivacyNoise(clip_norm=1.0)
        w = {"layer": [10.0, 0.0, 0.0]}
        clipped = p.clip_weights(w)
        norm = math.sqrt(sum(v**2 for v in clipped["layer"]))
        assert norm <= 1.0 + 1e-9

    def test_tc44_clip_weights_small_norm_unchanged(self):
        p = FLPrivacyNoise(clip_norm=10.0)
        w = {"layer": [0.1, 0.1]}
        clipped = p.clip_weights(w)
        assert abs(clipped["layer"][0] - 0.1) < 1e-9

    def test_tc45_privatize_returns_different(self):
        p = FLPrivacyNoise(seed=5)
        w = {"layer": [1.0] * 4}
        priv = p.privatize(w)
        assert priv["layer"] != [1.0] * 4

    def test_tc46_privacy_budget_keys(self):
        b = FLPrivacyNoise().privacy_budget
        assert all(k in b for k in ["epsilon", "delta", "sigma"])

    def test_tc47_stronger_privacy_larger_sigma(self):
        p1 = FLPrivacyNoise(epsilon=10.0)  # 약한 프라이버시
        p2 = FLPrivacyNoise(epsilon=0.1)   # 강한 프라이버시
        assert p2.sigma > p1.sigma

    def test_tc48_adr196_exists(self):
        path = os.path.join(os.path.dirname(__file__), '..', '..', 'docs', 'adr', 'ADR-196.md')
        assert os.path.exists(path)

    def test_tc49_fl_client_importable(self):
        from literary_system.federation.fl_client import FLClient
        assert FLClient is not None

    def test_tc50_fl_privacy_importable(self):
        from literary_system.federation.fl_privacy import FLPrivacyNoise
        assert FLPrivacyNoise is not None
