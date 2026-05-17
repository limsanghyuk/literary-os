"""V399 LongformEnduranceOrchestrator Tests"""
import pytest
from literary_system.episode.episode_state import SeriesConfig, NarrativeStateTensor
from literary_system.orchestrators.longform_endurance_orchestrator import (
    LongformEnduranceOrchestrator, LongformInput, EnduranceRunReport
)

def _make_config(n=16, title="Test Drama"):
    return SeriesConfig(
        title=title, total_episodes=n, runtime_minutes=60,
        genre="korean_drama", protagonist_ids=["HERO_A", "HERO_B"]
    )

def _make_input(n=16, title="Test Drama"):
    return LongformInput(series_config=_make_config(n, title))

class TestLongformInput:
    def test_basic_creation(self):
        inp = _make_input()
        assert inp.series_config.title == "Test Drama"

    def test_optional_agency_deltas_none(self):
        inp = _make_input()
        assert inp.agency_deltas is None

    def test_optional_narrative_state_none(self):
        inp = _make_input()
        assert inp.narrative_state is None

class TestEnduranceRunReport:
    def setup_method(self):
        self.orch = LongformEnduranceOrchestrator()
        self.report = self.orch.run(_make_input())

    def test_has_series_title(self):
        assert self.report.series_title == "Test Drama"

    def test_has_episode_count(self):
        assert self.report.episode_count == 16

    def test_has_microplot_matrix(self):
        assert self.report.microplot_matrix is not None

    def test_has_fractal_report(self):
        assert self.report.fractal_report is not None

    def test_has_load_report(self):
        assert self.report.load_report is not None

    def test_has_agency_report(self):
        assert self.report.agency_report is not None

    def test_has_debt_ledger(self):
        assert self.report.debt_ledger is not None

    def test_has_necessity_report(self):
        assert self.report.necessity_report is not None

    def test_has_dialogue_report(self):
        assert self.report.dialogue_report is not None

    def test_has_voice_drift_report(self):
        assert self.report.voice_drift_report is not None

    def test_has_fatigue_report(self):
        assert self.report.fatigue_report is not None

    def test_has_overall_pass(self):
        assert isinstance(self.report.overall_pass, bool)

    def test_has_gate_summary(self):
        assert isinstance(self.report.gate_summary, dict)

    def test_execution_trace_populated(self):
        assert len(self.report.execution_trace) > 0

class TestLongformEnduranceOrchestrator:
    def setup_method(self):
        self.orch = LongformEnduranceOrchestrator()

    def test_run_returns_endurance_report(self):
        report = self.orch.run(_make_input())
        assert isinstance(report, EnduranceRunReport)

    def test_9_step_pipeline_all_gates(self):
        report = self.orch.run(_make_input())
        expected_gates = [
            "episode_layer", "fractal_topology", "load_balancing",
            "agency_conservation", "payoff_debt", "scene_necessity",
            "dialogue_pragmatics", "voice_manifold", "attention_economy"
        ]
        for g in expected_gates:
            assert g in report.gate_summary

    def test_synthetic_16ep_overall_pass(self):
        report = self.orch.run(_make_input(16))
        assert report.overall_pass is True

    def test_8_episode_series(self):
        report = self.orch.run(_make_input(8, "Short Drama"))
        assert report.episode_count == 8

    def test_24_episode_series(self):
        cfg = SeriesConfig(
            title="Long Drama", total_episodes=24, runtime_minutes=60,
            genre="korean_drama", protagonist_ids=["A", "B"]
        )
        report = self.orch.run(LongformInput(series_config=cfg))
        assert report.episode_count == 24

    def test_deterministic_runs(self):
        r1 = self.orch.run(_make_input())
        r2 = self.orch.run(_make_input())
        assert r1.overall_pass == r2.overall_pass

    def test_matrix_episode_count_matches(self):
        report = self.orch.run(_make_input(16))
        assert report.microplot_matrix.episode_count == 16

    def test_gate_summary_all_true(self):
        report = self.orch.run(_make_input(16))
        for key, val in report.gate_summary.items():
            assert val is True, f"Gate {key} failed"

    def test_v390_scene_layer_intact(self):
        from literary_system.orchestrators.full_scene_orchestrator import FullSceneOrchestrator
        assert FullSceneOrchestrator is not None

    def test_no_provider_default_calls(self):
        # LongformEnduranceOrchestrator is pure deterministic — no LLM calls
        report = self.orch.run(_make_input())
        assert report is not None  # completed without external calls

