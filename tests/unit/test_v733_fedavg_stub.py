"""V733: FedAvg 스텁 테스트 (30 TC)

검증 범위:
  TC01~TC10: FedAvgAggregator 기본 집계
  TC11~TC20: 가중 평균 수식 정확성
  TC21~TC30: history/loss_trend/is_improving
"""
import sys, os, math
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from literary_system.federation.fl_types import FLClientState, FLGlobalModel
from literary_system.federation.fedavg import FedAvgAggregator


def _state(client_id, n, loss, weights=None):
    return FLClientState(
        client_id=client_id, round_num=1,
        num_samples=n, local_loss=loss,
        weights=weights or {}
    )


class TestFedAvgBasic:
    def test_tc01_create(self):
        a = FedAvgAggregator()
        assert a is not None

    def test_tc02_dp_noise_scale_default(self):
        assert FedAvgAggregator().dp_noise_scale == 0.0

    def test_tc03_dp_noise_scale_custom(self):
        assert FedAvgAggregator(dp_noise_scale=0.1).dp_noise_scale == 0.1

    def test_tc04_aggregate_returns_global_model(self):
        a = FedAvgAggregator()
        s = _state("c1", 100, 0.5)
        gm = a.aggregate([s], round_num=1)
        assert isinstance(gm, FLGlobalModel)

    def test_tc05_aggregated_from_count(self):
        a = FedAvgAggregator()
        gm = a.aggregate([_state("c1", 100, 0.5), _state("c2", 100, 0.3)], round_num=1)
        assert gm.aggregated_from == 2

    def test_tc06_empty_states_raises(self):
        with pytest.raises(ValueError):
            FedAvgAggregator().aggregate([], round_num=1)

    def test_tc07_invalid_state_filtered(self):
        a = FedAvgAggregator()
        bad = FLClientState(client_id="", round_num=1, num_samples=0, local_loss=-1)
        good = _state("c1", 100, 0.4)
        gm = a.aggregate([bad, good], round_num=1)
        assert gm.aggregated_from == 1

    def test_tc08_all_invalid_raises(self):
        a = FedAvgAggregator()
        bad = FLClientState(client_id="", round_num=1, num_samples=0, local_loss=-1)
        with pytest.raises(ValueError):
            a.aggregate([bad], round_num=1)

    def test_tc09_round_num_preserved(self):
        a = FedAvgAggregator()
        gm = a.aggregate([_state("c1", 100, 0.5)], round_num=7)
        assert gm.round_num == 7

    def test_tc10_global_loss_single_client(self):
        a = FedAvgAggregator()
        gm = a.aggregate([_state("c1", 100, 0.42)], round_num=1)
        assert abs(gm.global_loss - 0.42) < 1e-9


class TestFedAvgWeightedMean:
    def test_tc11_weighted_loss_two_equal(self):
        a = FedAvgAggregator()
        states = [_state("c1", 100, 0.6), _state("c2", 100, 0.4)]
        gm = a.aggregate(states, round_num=1)
        assert abs(gm.global_loss - 0.5) < 1e-9

    def test_tc12_weighted_loss_unequal(self):
        a = FedAvgAggregator()
        # 200 samples loss=0.6, 100 samples loss=0.3
        # expected = (200*0.6 + 100*0.3) / 300 = 150/300 = 0.5
        states = [_state("c1", 200, 0.6), _state("c2", 100, 0.3)]
        gm = a.aggregate(states, round_num=1)
        assert abs(gm.global_loss - 0.5) < 1e-9

    def test_tc13_weight_aggregation_single_key(self):
        a = FedAvgAggregator()
        s1 = _state("c1", 100, 0.5, weights={"layer": [1.0, 2.0]})
        s2 = _state("c2", 100, 0.5, weights={"layer": [3.0, 4.0]})
        gm = a.aggregate([s1, s2], round_num=1)
        # FedAvg: (1.0+3.0)/2=2.0, (2.0+4.0)/2=3.0
        assert abs(gm.global_weights["layer"][0] - 2.0) < 1e-9
        assert abs(gm.global_weights["layer"][1] - 3.0) < 1e-9

    def test_tc14_weight_aggregation_unequal_samples(self):
        a = FedAvgAggregator()
        s1 = _state("c1", 200, 0.5, weights={"w": [1.0]})
        s2 = _state("c2", 100, 0.5, weights={"w": [4.0]})
        gm = a.aggregate([s1, s2], round_num=1)
        # (200*1.0 + 100*4.0) / 300 = 600/300 = 2.0
        assert abs(gm.global_weights["w"][0] - 2.0) < 1e-9

    def test_tc15_missing_key_in_some_clients(self):
        a = FedAvgAggregator()
        s1 = _state("c1", 100, 0.5, weights={"a": [1.0], "b": [2.0]})
        s2 = _state("c2", 100, 0.5, weights={"a": [3.0]})   # no "b"
        gm = a.aggregate([s1, s2], round_num=1)
        assert "a" in gm.global_weights

    def test_tc16_no_weights_produces_empty_global(self):
        a = FedAvgAggregator()
        states = [_state("c1", 100, 0.5), _state("c2", 100, 0.3)]
        gm = a.aggregate(states, round_num=1)
        assert gm.global_weights == {}

    def test_tc17_three_clients_equal(self):
        a = FedAvgAggregator()
        states = [_state(f"c{i}", 100, float(i)) for i in range(1, 4)]
        gm = a.aggregate(states, round_num=1)
        # (1+2+3)/3 = 2.0
        assert abs(gm.global_loss - 2.0) < 1e-9

    def test_tc18_converged_false_by_default(self):
        a = FedAvgAggregator()
        gm = a.aggregate([_state("c1", 100, 0.5)], round_num=1)
        assert not gm.converged

    def test_tc19_aggregate_multiple_rounds(self):
        a = FedAvgAggregator()
        for i in range(3):
            a.aggregate([_state("c1", 100, 0.5 - i*0.1)], round_num=i+1)
        assert len(a.history) == 3

    def test_tc20_global_model_keys(self):
        a = FedAvgAggregator()
        gm = a.aggregate([_state("c1", 100, 0.5)], round_num=1)
        d = gm.to_dict()
        assert all(k in d for k in ["round_num", "aggregated_from", "global_loss"])


class TestFedAvgHistory:
    def test_tc21_history_empty_initially(self):
        assert FedAvgAggregator().history == []

    def test_tc22_history_grows(self):
        a = FedAvgAggregator()
        for i in range(4):
            a.aggregate([_state("c1", 100, 0.8 - i*0.1)], round_num=i+1)
        assert len(a.history) == 4

    def test_tc23_loss_trend_empty(self):
        assert FedAvgAggregator().loss_trend() == []

    def test_tc24_loss_trend_values(self):
        a = FedAvgAggregator()
        for loss in [0.8, 0.6, 0.4]:
            a.aggregate([_state("c1", 100, loss)], round_num=1)
        trend = a.loss_trend()
        assert trend[0] > trend[1] > trend[2]

    def test_tc25_is_improving_true(self):
        a = FedAvgAggregator()
        a.aggregate([_state("c1", 100, 0.8)], round_num=1)
        a.aggregate([_state("c1", 100, 0.5)], round_num=2)
        assert a.is_improving()

    def test_tc26_is_improving_false(self):
        a = FedAvgAggregator()
        a.aggregate([_state("c1", 100, 0.4)], round_num=1)
        a.aggregate([_state("c1", 100, 0.9)], round_num=2)
        assert not a.is_improving()

    def test_tc27_is_improving_single_round(self):
        a = FedAvgAggregator()
        a.aggregate([_state("c1", 100, 0.5)], round_num=1)
        assert a.is_improving()  # 하나일 때는 True

    def test_tc28_history_immutable(self):
        a = FedAvgAggregator()
        a.aggregate([_state("c1", 100, 0.5)], round_num=1)
        h = a.history
        h.clear()
        assert len(a.history) == 1

    def test_tc29_adr195_file_exists(self):
        adr_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'docs', 'adr', 'ADR-195.md'
        )
        assert os.path.exists(adr_path)

    def test_tc30_fedavg_importable(self):
        from literary_system.federation.fedavg import FedAvgAggregator as FA
        assert FA is not None
