"""V394 Agency Conservation Tests"""
import pytest
from literary_system.longform.agency_conservation import (
    AgencyEventType, AgencyDelta, AgencyConservationChecker, AgencyReport
)

class TestAgencyEventType:
    def test_all_event_types_exist(self):
        for et in [AgencyEventType.CHOICE, AgencyEventType.REFUSAL, AgencyEventType.LIE,
                   AgencyEventType.CONFESSION, AgencyEventType.SACRIFICE, AgencyEventType.BETRAYAL,
                   AgencyEventType.RESISTANCE, AgencyEventType.SILENCE]:
            assert et is not None

    def test_event_type_is_string_enum(self):
        assert isinstance(AgencyEventType.CHOICE, str)

class TestAgencyDelta:
    def _make(self, **kw):
        defaults = dict(
            character_id="A", episode_idx=0, scene_id="ep0_sc0",
            event_type=AgencyEventType.CHOICE,
            decision_weight=1.0, consequence_weight=1.0,
            risk_weight=1.0, irreversibility_weight=1.0, belief_shift_weight=1.0
        )
        defaults.update(kw)
        return AgencyDelta(**defaults)

    def test_basic_creation(self):
        d = self._make()
        assert d.episode_idx == 0
        assert d.character_id == "A"

    def test_score_positive(self):
        d = self._make()
        assert d.score > 0

    def test_score_formula(self):
        d = self._make(
            decision_weight=1.0, consequence_weight=1.0,
            risk_weight=1.0, irreversibility_weight=1.0, belief_shift_weight=0.0
        )
        # 0.3 + 0.25 + 0.2 + 0.15 + 0 = 0.9
        assert abs(d.score - 0.9) < 1e-9

    def test_passive_class_method(self):
        d = AgencyDelta.passive("HERO", 3, "ep3_sc5")
        assert d.score == 0.0
        assert d.event_type == AgencyEventType.SILENCE

    def test_low_score_passive_action(self):
        d = self._make(
            decision_weight=0.0, consequence_weight=0.0,
            risk_weight=0.0, irreversibility_weight=0.0, belief_shift_weight=0.0
        )
        assert d.score == 0.0

class TestAgencyConservationChecker:
    def setup_method(self):
        self.checker = AgencyConservationChecker()
        self.protagonist_ids = ["HERO_A", "HERO_B"]

    def test_synthetic_deltas_builds(self):
        deltas = AgencyConservationChecker.build_synthetic_deltas(self.protagonist_ids, 16)
        assert len(deltas) > 0

    def test_synthetic_deltas_cover_all_episodes(self):
        deltas = AgencyConservationChecker.build_synthetic_deltas(self.protagonist_ids, 16)
        ep_idxs = {d.episode_idx for d in deltas}
        assert len(ep_idxs) == 16

    def test_check_returns_agency_report(self):
        deltas = AgencyConservationChecker.build_synthetic_deltas(self.protagonist_ids, 16)
        report = self.checker.check(deltas, self.protagonist_ids, 16)
        assert isinstance(report, AgencyReport)

    def test_agency_floor_constant(self):
        assert AgencyConservationChecker.AGENCY_FLOOR == 0.15

    def test_max_passive_episodes_constant(self):
        assert AgencyConservationChecker.MAX_PASSIVE_EPISODES == 3

    def test_report_has_required_fields(self):
        deltas = AgencyConservationChecker.build_synthetic_deltas(self.protagonist_ids, 16)
        report = self.checker.check(deltas, self.protagonist_ids, 16)
        assert hasattr(report, 'agency_floor_violations')
        assert hasattr(report, 'protagonist_floor_pass')
        assert hasattr(report, 'pass_gate')

    def test_pass_gate_is_bool(self):
        deltas = AgencyConservationChecker.build_synthetic_deltas(self.protagonist_ids, 16)
        report = self.checker.check(deltas, self.protagonist_ids, 16)
        assert isinstance(report.pass_gate, bool)

    def test_synthetic_16ep_passes(self):
        deltas = AgencyConservationChecker.build_synthetic_deltas(self.protagonist_ids, 16)
        report = self.checker.check(deltas, self.protagonist_ids, 16)
        assert report.pass_gate is True

    def test_single_protagonist(self):
        deltas = AgencyConservationChecker.build_synthetic_deltas(["HERO"], 8)
        report = self.checker.check(deltas, ["HERO"], 8)
        assert isinstance(report, AgencyReport)

    def test_character_agency_curves_in_report(self):
        deltas = AgencyConservationChecker.build_synthetic_deltas(self.protagonist_ids, 16)
        report = self.checker.check(deltas, self.protagonist_ids, 16)
        assert hasattr(report, 'character_agency_curves')
        for pid in self.protagonist_ids:
            assert pid in report.character_agency_curves

    def test_passive_episode_counts_in_report(self):
        deltas = AgencyConservationChecker.build_synthetic_deltas(self.protagonist_ids, 16)
        report = self.checker.check(deltas, self.protagonist_ids, 16)
        assert hasattr(report, 'passive_episode_counts')

    def test_all_passive_fails_gate(self):
        # All passive deltas for protagonist
        deltas = [AgencyDelta.passive("HERO", i, f"sc{i}") for i in range(16)]
        report = self.checker.check(deltas, ["HERO"], 16)
        assert report.pass_gate is False

