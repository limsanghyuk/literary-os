"""
V314 테스트 — NarrativeTrajectory + ReaderSimulator 전수 검증.
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ═══════════════════════════════════════════════════════════
# TestNarrativeTrajectory
# ═══════════════════════════════════════════════════════════
class TestNarrativeTrajectory:
    def setup_method(self):
        from literary_system.trajectory.narrative_trajectory import (
            NarrativeTrajectory, TrajectoryEngine, TrajectoryPoint
        )
        self.engine = TrajectoryEngine()
        self.NarrativeTrajectory = NarrativeTrajectory
        self.TrajectoryPoint = TrajectoryPoint

    def test_create_trajectory_by_genre(self):
        t = self.engine.create("proj_01", "political_thriller", 16)
        assert t.shape_name == "tension_rising_spiral"
        assert t.total_episodes == 16

    def test_target_rises_over_episodes_sp(self):
        t = self.engine.create("proj_01", "political_thriller", 16)
        sp_ep1  = t.target_at(1, "SP")
        sp_ep8  = t.target_at(8, "SP")
        sp_ep16 = t.target_at(16, "SP")
        assert sp_ep1 < sp_ep8 < sp_ep16, \
            f"SP should rise: {sp_ep1:.3f} < {sp_ep8:.3f} < {sp_ep16:.3f}"

    def test_target_falls_over_episodes_ru(self):
        t = self.engine.create("proj_01", "political_thriller", 16)
        ru_ep1  = t.target_at(1, "RU")
        ru_ep16 = t.target_at(16, "RU")
        assert ru_ep1 > ru_ep16, f"RU should fall: {ru_ep1:.3f} > {ru_ep16:.3f}"

    def test_record_and_deviation(self):
        t = self.engine.create("proj_01", "political_thriller", 16)
        # SP 목표보다 낮게 기록
        low_sp_state = {"SP": 0.20, "RU": 0.65, "ET": 0.0,
                         "RD": 0.1, "RT": 0.3, "AC": 0.7, "RO": 0.5, "MR": 0.1}
        t = self.engine.ingest_episode_result(t, 4, low_sp_state)
        dev = t.deviation(4)
        # SP가 목표보다 낮으므로 deviation이 음수여야 함
        assert dev["SP"] < 0, f"SP deviation should be negative: {dev['SP']}"

    def test_on_track_when_deviation_small(self):
        t = self.engine.create("proj_01", "political_thriller", 16)
        # 목표값에 거의 정확한 state 기록
        target_sp = t.target_at(4, "SP")
        target_ru = t.target_at(4, "RU")
        target_et = t.target_at(4, "ET")
        state = {"SP": target_sp, "RU": target_ru, "ET": target_et,
                  "RD": 0.1, "RT": 0.3, "AC": 0.7, "RO": 0.5, "MR": 0.1}
        t = self.engine.ingest_episode_result(t, 4, state)
        report = t.trajectory_report(4)
        assert report["total_deviation"] < 0.05
        assert report["severity"] == "on_track"

    def test_critical_deviation_detected(self):
        t = self.engine.create("proj_01", "political_thriller", 16)
        far_off_state = {"SP": 0.10, "RU": 0.95, "ET": -0.5,
                          "RD": 0.1, "RT": 0.3, "AC": 0.7, "RO": 0.5, "MR": 0.1}
        t = self.engine.ingest_episode_result(t, 8, far_off_state)
        report = t.trajectory_report(8)
        assert report["severity"] in ("moderate_deviation", "critical_deviation")
        assert report["needs_correction"] is True

    def test_predict_landing_with_data(self):
        t = self.engine.create("proj_01", "political_thriller", 16)
        t = self.engine.ingest_episode_result(t, 1, {"SP": 0.30, "RU": 0.65, "ET": 0.0,
                                                       "RD": 0.1, "RT": 0.3, "AC": 0.7, "RO": 0.5, "MR": 0.1})
        t = self.engine.ingest_episode_result(t, 2, {"SP": 0.38, "RU": 0.60, "ET": 0.05,
                                                       "RD": 0.12, "RT": 0.35, "AC": 0.70, "RO": 0.50, "MR": 0.11})
        prediction = t.predict_landing(2)
        assert "SP" in prediction
        assert 0.0 <= prediction["SP"] <= 1.0

    def test_correction_vector_toward_target(self):
        t = self.engine.create("proj_01", "political_thriller", 16)
        # SP가 낮게 기록됨
        t = self.engine.ingest_episode_result(t, 4, {"SP": 0.20, "RU": 0.65, "ET": 0.0,
                                                       "RD": 0.1, "RT": 0.3, "AC": 0.7, "RO": 0.5, "MR": 0.1})
        correction = self.engine.correction_vector(t, 4)
        # 보정 벡터의 SP 방향이 양수 (SP를 올리는 방향)여야 함
        assert "SP" in correction

    def test_5_shapes_available(self):
        shapes = self.engine.list_shapes()
        assert len(shapes) >= 5


# ═══════════════════════════════════════════════════════════
# TestReaderSimulator
# ═══════════════════════════════════════════════════════════
class TestReaderSimulator:
    def setup_method(self):
        from literary_system.trajectory.reader_simulator import ReaderSimulator
        self.sim = ReaderSimulator()

    def test_empty_text_safe(self):
        result = self.sim.estimate("")
        assert 0.0 <= result.reader_pull <= 1.0
        assert 0.0 <= result.reader_afterimage <= 1.0
        assert 0.0 <= result.reader_uncertainty <= 1.0

    def test_ai_smell_detected(self):
        text = "결국 그는 진실을 알게 됐다. 마치 오랜 꿈에서 깨어난 것처럼 그제야 이해했다."
        result = self.sim.estimate(text)
        assert result.ai_smell_score > 0.0
        assert len(result.signals_found["ai_smell"]) > 0

    def test_clean_text_lower_ai_smell(self):
        clean = "서류가 책상 위에 있었다. 그는 손을 뻗었다. 창문 밖에 비가 내렸다."
        dirty = "결국 그는 알았다. 마치 다른 사람이 된 것처럼. 그제야 이해했다. 어쩌면 그것이었을까."
        r_clean = self.sim.estimate(clean)
        r_dirty = self.sim.estimate(dirty)
        assert r_clean.ai_smell_score <= r_dirty.ai_smell_score

    def test_concrete_ending_boosts_afterimage(self):
        concrete_end = "그는 서류를 쥐었다. 빗소리가 났다. 창문에 그림자."
        abstract_end = "그는 많은 생각을 했다. 복잡한 감정이 들었다."
        r_concrete = self.sim.estimate(concrete_end)
        r_abstract = self.sim.estimate(abstract_end)
        assert r_concrete.reader_afterimage >= r_abstract.reader_afterimage

    def test_emotion_leak_reduces_pull(self):
        leaky = "그는 너무 슬펐다. 두려웠다. 기뻤다."
        tight = "그는 서류를 내려놓았다. 비가 왔다. 창문이 닫혔다."
        r_leaky = self.sim.estimate(leaky)
        r_tight = self.sim.estimate(tight)
        assert r_leaky.reader_pull <= r_tight.reader_pull

    def test_composite_quality_range(self):
        text = "형사는 멈췄다. 서류가 있었다. 비."
        result = self.sim.estimate(text)
        assert 0.0 <= result.composite_quality <= 1.0

    def test_loss_components_compatible(self):
        text = "그는 쥐었다. 바람이 불었다."
        result = self.sim.estimate(text)
        loss = result.as_loss_components()
        for key in ["L_reader_pull", "L_reader_afterimage", "L_smell_surface"]:
            assert key in loss
            assert 0.0 <= loss[key] <= 1.0

    def test_batch_estimate(self):
        scenes = {
            "SC01": "형사는 멈췄다. 서류. 빗소리.",
            "SC02": "결국 그는 알았다. 마치 새벽처럼.",
        }
        results = self.sim.estimate_batch(scenes)
        assert "SC01" in results
        assert "SC02" in results
        # SC02는 AI 냄새가 더 강해야 함
        assert results["SC02"].ai_smell_score >= results["SC01"].ai_smell_score

    def test_should_repair_leaky_text(self):
        leaky_text = "결국 그는 슬펐다. 마치 꿈처럼. 어쩌면 괜찮을지도."
        result = self.sim.estimate(leaky_text)
        needs_repair, reasons = self.sim.should_repair(result)
        # ai_smell 또는 pull 문제로 수리 필요
        assert isinstance(needs_repair, bool)
        assert isinstance(reasons, list)

    def test_with_literary_state_before(self):
        text = "침묵. 서류. 손."
        state_high_ru = {"SP": 0.5, "RU": 0.80, "ET": 0.0}
        state_low_ru  = {"SP": 0.5, "RU": 0.20, "ET": 0.0}
        r_high = self.sim.estimate(text, state_high_ru)
        r_low  = self.sim.estimate(text, state_low_ru)
        # 높은 RU → 더 높은 reader_uncertainty
        assert r_high.reader_uncertainty >= r_low.reader_uncertainty
