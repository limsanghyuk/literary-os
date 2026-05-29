"""V732: FLCoordinator + fl_types 테스트 (50 TC)

검증 범위:
  TC01~TC10: FLClientState 기본
  TC11~TC20: FLGlobalModel 기본
  TC21~TC30: FLRound 기본
  TC31~TC45: FLCoordinator 핵심 로직
  TC46~TC50: ADR-194 메타데이터 + federation 패키지 임포트
"""
import sys
import os
import time
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from literary_system.federation.fl_types import FLClientState, FLGlobalModel, FLRound
from literary_system.federation.fl_coordinator import FLCoordinator, InsufficientClientsError


# ─── FLClientState ────────────────────────────────────────────────────────────

class TestFLClientState:
    def _make(self, **kw):
        defaults = dict(client_id="c1", round_num=1, num_samples=100, local_loss=0.5)
        defaults.update(kw)
        return FLClientState(**defaults)

    def test_tc01_create_basic(self):
        s = self._make()
        assert s.client_id == "c1"

    def test_tc02_round_num(self):
        s = self._make(round_num=3)
        assert s.round_num == 3

    def test_tc03_num_samples(self):
        s = self._make(num_samples=50)
        assert s.num_samples == 50

    def test_tc04_local_loss(self):
        s = self._make(local_loss=1.23)
        assert abs(s.local_loss - 1.23) < 1e-9

    def test_tc05_is_valid_true(self):
        assert self._make().is_valid()

    def test_tc06_is_valid_empty_client_id(self):
        assert not self._make(client_id="").is_valid()

    def test_tc07_is_valid_negative_loss(self):
        assert not self._make(local_loss=-0.1).is_valid()

    def test_tc08_is_valid_zero_samples(self):
        assert not self._make(num_samples=0).is_valid()

    def test_tc09_weights_dict(self):
        s = self._make(weights={"layer1": [0.1, 0.2]})
        assert s.weights["layer1"] == [0.1, 0.2]

    def test_tc10_to_dict_keys(self):
        d = self._make().to_dict()
        assert all(k in d for k in ["client_id", "round_num", "num_samples", "local_loss"])


# ─── FLGlobalModel ────────────────────────────────────────────────────────────

class TestFLGlobalModel:
    def test_tc11_create(self):
        m = FLGlobalModel(round_num=1)
        assert m.round_num == 1

    def test_tc12_aggregated_from_default(self):
        assert FLGlobalModel(round_num=0).aggregated_from == 0

    def test_tc13_global_loss_default(self):
        assert FLGlobalModel(round_num=0).global_loss == 0.0

    def test_tc14_converged_default_false(self):
        assert not FLGlobalModel(round_num=0).converged

    def test_tc15_to_dict_has_round_num(self):
        assert FLGlobalModel(round_num=5).to_dict()["round_num"] == 5

    def test_tc16_to_dict_aggregated_from(self):
        m = FLGlobalModel(round_num=1, aggregated_from=3)
        assert m.to_dict()["aggregated_from"] == 3

    def test_tc17_set_converged(self):
        m = FLGlobalModel(round_num=1, converged=True)
        assert m.converged

    def test_tc18_global_weights(self):
        m = FLGlobalModel(round_num=1, global_weights={"w": [0.5]})
        assert "w" in m.global_weights

    def test_tc19_to_dict_converged_field(self):
        m = FLGlobalModel(round_num=1, converged=True)
        assert m.to_dict()["converged"] is True

    def test_tc20_to_dict_weights_keys(self):
        m = FLGlobalModel(round_num=1, global_weights={"a": [1.0]})
        assert "a" in m.to_dict()["weights_keys"]


# ─── FLRound ──────────────────────────────────────────────────────────────────

class TestFLRound:
    def test_tc21_create(self):
        r = FLRound(round_num=1)
        assert r.round_num == 1

    def test_tc22_default_status(self):
        assert FLRound(round_num=1).status == "pending"

    def test_tc23_participants(self):
        r = FLRound(round_num=1, participants=["c1", "c2"])
        assert len(r.participants) == 2

    def test_tc24_summary_keys(self):
        r = FLRound(round_num=1, participants=["c1"])
        s = r.summary()
        assert all(k in s for k in ["round_num", "participants", "status"])

    def test_tc25_summary_participants_count(self):
        r = FLRound(round_num=2, participants=["c1", "c2", "c3"])
        assert r.summary()["participants"] == 3

    def test_tc26_client_states_empty_default(self):
        assert FLRound(round_num=1).client_states == []

    def test_tc27_global_model_none_default(self):
        assert FLRound(round_num=1).global_model is None

    def test_tc28_summary_global_loss_none_when_no_model(self):
        assert FLRound(round_num=1).summary()["global_loss"] is None

    def test_tc29_status_assignment(self):
        r = FLRound(round_num=1, status="done")
        assert r.status == "done"

    def test_tc30_summary_with_global_model(self):
        r = FLRound(round_num=1, global_model=FLGlobalModel(round_num=1, global_loss=0.3))
        assert abs(r.summary()["global_loss"] - 0.3) < 1e-9


# ─── FLCoordinator ────────────────────────────────────────────────────────────

class TestFLCoordinator:
    def _coord(self, min_clients=2, max_rounds=5):
        return FLCoordinator(min_clients=min_clients, max_rounds=max_rounds)

    def _state(self, client_id, round_num=1):
        return FLClientState(client_id=client_id, round_num=round_num,
                              num_samples=100, local_loss=0.4)

    def test_tc31_register_client(self):
        c = self._coord()
        c.register_client("c1")
        assert "c1" in c.registered_clients

    def test_tc32_register_duplicate_noop(self):
        c = self._coord()
        c.register_client("c1")
        c.register_client("c1")
        assert c.registered_clients.count("c1") == 1

    def test_tc33_unregister(self):
        c = self._coord()
        c.register_client("c1")
        c.unregister_client("c1")
        assert "c1" not in c.registered_clients

    def test_tc34_start_round_insufficient_clients(self):
        c = self._coord(min_clients=2)
        c.register_client("c1")
        with pytest.raises(InsufficientClientsError):
            c.start_round()

    def test_tc35_start_round_success(self):
        c = self._coord(min_clients=2)
        c.register_client("c1"); c.register_client("c2")
        rnd = c.start_round()
        assert rnd.round_num == 1
        assert rnd.status == "aggregating"

    def test_tc36_start_round_increments(self):
        c = self._coord(min_clients=1)
        c.register_client("c1")
        c.start_round(); c.start_round()
        assert c.rounds[-1].round_num == 2

    def test_tc37_submit_client_state(self):
        c = self._coord(min_clients=1)
        c.register_client("c1")
        c.start_round()
        c.submit_client_state(self._state("c1"))
        assert len(c.rounds[-1].client_states) == 1

    def test_tc38_submit_invalid_state_raises(self):
        c = self._coord(min_clients=1)
        c.register_client("c1")
        c.start_round()
        bad = FLClientState(client_id="", round_num=1, num_samples=0, local_loss=-1)
        with pytest.raises(ValueError):
            c.submit_client_state(bad)

    def test_tc39_submit_no_round_raises(self):
        c = self._coord()
        with pytest.raises(RuntimeError):
            c.submit_client_state(self._state("c1"))

    def test_tc40_finalize_round_sets_done(self):
        c = self._coord(min_clients=1)
        c.register_client("c1")
        c.start_round()
        gm = FLGlobalModel(round_num=1, global_loss=0.3, aggregated_from=1)
        rnd = c.finalize_round(gm)
        assert rnd.status == "done"

    def test_tc41_global_model_set_after_finalize(self):
        c = self._coord(min_clients=1)
        c.register_client("c1")
        c.start_round()
        gm = FLGlobalModel(round_num=1, global_loss=0.3, aggregated_from=1)
        c.finalize_round(gm)
        assert c.global_model is not None
        assert abs(c.global_model.global_loss - 0.3) < 1e-9

    def test_tc42_convergence_detection(self):
        c = self._coord(min_clients=1, max_rounds=10)
        c.register_client("c1")
        # Round 1
        c.start_round()
        c.finalize_round(FLGlobalModel(round_num=1, global_loss=0.5, aggregated_from=1))
        # Round 2 — 거의 동일한 손실
        c.start_round()
        c.finalize_round(FLGlobalModel(round_num=2, global_loss=0.5 + 1e-5, aggregated_from=1))
        assert c.is_converged()

    def test_tc43_should_continue_false_when_converged(self):
        c = self._coord(min_clients=1)
        c.register_client("c1")
        c.start_round()
        c.finalize_round(FLGlobalModel(round_num=1, global_loss=0.5, aggregated_from=1))
        c.start_round()
        c.finalize_round(FLGlobalModel(round_num=2, global_loss=0.5, aggregated_from=1))
        assert not c.should_continue()

    def test_tc44_should_continue_false_max_rounds(self):
        c = self._coord(min_clients=1, max_rounds=2)
        c.register_client("c1")
        for i in range(2):
            c.start_round()
            c.finalize_round(FLGlobalModel(round_num=i+1, global_loss=float(i+1), aggregated_from=1))
        assert not c.should_continue()

    def test_tc45_summary_keys(self):
        c = self._coord(min_clients=1)
        c.register_client("c1")
        c.start_round()
        c.finalize_round(FLGlobalModel(round_num=1, global_loss=0.4, aggregated_from=1))
        s = c.summary()
        assert all(k in s for k in ["clients", "rounds_completed", "converged", "global_loss"])


# ─── ADR-194 메타데이터 + 패키지 임포트 ─────────────────────────────────────

class TestADR194:
    def test_tc46_federation_package_importable(self):
        import literary_system.federation
        assert literary_system.federation is not None

    def test_tc47_fl_types_importable(self):
        from literary_system.federation import fl_types
        assert fl_types is not None

    def test_tc48_fl_coordinator_importable(self):
        from literary_system.federation import fl_coordinator
        assert fl_coordinator is not None

    def test_tc49_adr194_file_exists(self):
        adr_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'docs', 'adr', 'ADR-194.md'
        )
        assert os.path.exists(adr_path)

    def test_tc50_adr194_content_has_fl_coordinator(self):
        adr_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'docs', 'adr', 'ADR-194.md'
        )
        content = open(adr_path).read()
        assert "FLCoordinator" in content
