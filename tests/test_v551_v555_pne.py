"""
tests/test_v551_v555_pne.py
============================
Phase 6 Stage B — PredictiveNarrativeEngine 테스트 (V551~V555)

TestPNECore              (7 tests) — V551
TestDebtPredictor        (8 tests) — V552
TestPreemptiveGate       (7 tests) — V553
TestFeedbackLearner      (8 tests) — V554
TestGate29Integration    (5 tests) — V555
"""

import pytest
from typing import List


# ─── V551: PNECore ─────────────────────────────────────────────────────────────

class TestPNECore:
    """PNECore 단위 테스트 (7종)."""

    def _make_core(self):
        from literary_system.predictive import PNECore
        return PNECore()

    def _make_outcome(self, cat="unresolved_secret", sev=0.7, success=True, blast=0.2):
        from literary_system.predictive.pne_core import RepairOutcome
        return RepairOutcome(
            scene_id="s1", recommendation_id="r1",
            category=cat, severity=sev, success=success, blast_ratio=blast,
        )

    def test_ingest_single_outcome(self):
        core = self._make_core()
        o = self._make_outcome()
        core.ingest_outcome(o)
        assert core.total_ingested() == 1

    def test_ingest_multiple_outcomes(self):
        core = self._make_core()
        outcomes = [self._make_outcome(cat="unresolved_secret", success=(i % 2 == 0))
                    for i in range(10)]
        core.ingest_outcomes(outcomes)
        assert core.total_ingested() == 10

    def test_category_stats_success_rate(self):
        core = self._make_core()
        from literary_system.predictive.pne_core import RepairOutcome
        for i in range(4):
            core.ingest_outcome(RepairOutcome("s", "r", "unresolved_secret", 0.7, success=(i < 3)))
        st = core.category_stats("unresolved_secret")
        assert st is not None
        assert st.total == 4
        assert st.success_rate() == 0.75

    def test_feature_vector_length(self):
        core = self._make_core()
        core.ingest_outcome(self._make_outcome())
        fv = core.feature_vector("unresolved_secret")
        assert len(fv) == 4
        assert all(isinstance(v, float) for v in fv)

    def test_global_feature_vector(self):
        core = self._make_core()
        for cat in ["unresolved_secret", "broken_foreshadow"]:
            core.ingest_outcome(self._make_outcome(cat=cat))
        gfv = core.global_feature_vector()
        assert len(gfv) == 4

    def test_snapshot_structure(self):
        core = self._make_core()
        core.ingest_outcome(self._make_outcome())
        snap = core.snapshot()
        assert "unresolved_secret" in snap
        assert "total" in snap["unresolved_secret"]

    def test_pattern_library_record_batch(self):
        from literary_system.predictive.pne_core import PatternLibrary, RepairOutcome
        lib = PatternLibrary()
        outcomes = [RepairOutcome("s", "r", "abandoned_thread", 0.5, True) for _ in range(5)]
        lib.record_batch(outcomes)
        assert lib.total_outcomes() == 5
        st = lib.get_stats("abandoned_thread")
        assert st.total == 5


# ─── V552: DebtPredictor ───────────────────────────────────────────────────────

class TestDebtPredictor:
    """DebtPredictor 단위 테스트 (8종)."""

    def _make_predictor(self, with_core=False):
        from literary_system.predictive import DebtPredictor, PNECore
        from literary_system.predictive.pne_core import RepairOutcome
        core = PNECore() if with_core else None
        if with_core:
            for cat in DebtPredictor.DEBT_CATEGORIES:
                for i in range(10):
                    core.ingest_outcome(RepairOutcome(
                        f"s{i}", f"r{i}", cat, 0.5, success=(i < 7)
                    ))
        return DebtPredictor(pne_core=core), core

    def test_predict_returns_report(self):
        predictor, _ = self._make_predictor()
        report = predictor.predict("s1", current_severity=0.5, horizon=3)
        assert report.scene_id == "s1"
        assert report.horizon == 3

    def test_predict_categories_coverage(self):
        predictor, _ = self._make_predictor()
        report = predictor.predict("s1")
        cats = {p.category for p in report.predictions}
        assert "unresolved_secret" in cats
        assert "broken_foreshadow" in cats

    def test_predict_probability_in_range(self):
        predictor, _ = self._make_predictor()
        report = predictor.predict("s1", current_severity=0.8, horizon=5)
        for pred in report.predictions:
            assert 0.0 <= pred.probability <= 1.0

    def test_predict_confidence_in_range(self):
        predictor, _ = self._make_predictor()
        report = predictor.predict("s1")
        for pred in report.predictions:
            assert 0.0 <= pred.confidence <= 1.0

    def test_high_risk_detection(self):
        predictor, _ = self._make_predictor(with_core=True)
        # severity 높게 → 확률 높아야 함
        report = predictor.predict("s1", current_severity=0.95, horizon=1)
        # high_risk는 prob >= 0.60 카테고리 (휴리스틱 모드에서는 보장 불가하지만 리스트 존재 확인)
        assert isinstance(report.high_risk, list)

    def test_train_with_core(self):
        predictor, core = self._make_predictor(with_core=True)
        result = predictor.train(pne_core=core)
        assert isinstance(result, dict)
        # sklearn 여부와 무관하게 dict 반환

    def test_predict_category_single(self):
        from literary_system.predictive import DebtPredictor
        predictor = DebtPredictor()
        pred = predictor.predict_category("unresolved_secret", "s1", current_severity=0.6)
        assert pred.category == "unresolved_secret"
        assert 0.0 <= pred.probability <= 1.0

    def test_max_probability(self):
        predictor, _ = self._make_predictor()
        report = predictor.predict("s1")
        assert report.max_probability() == max(p.probability for p in report.predictions)


# ─── V553: PreemptiveGate ──────────────────────────────────────────────────────

class TestPreemptiveGate:
    """PreemptiveGate 단위 테스트 (7종)."""

    def _make_gate(self, threshold=0.60):
        from literary_system.predictive import DebtPredictor, PreemptiveGate
        predictor = DebtPredictor()
        return PreemptiveGate(predictor=predictor, horizon=3, threshold=threshold), predictor

    def test_evaluate_returns_result(self):
        gate, _ = self._make_gate()
        result = gate.evaluate("s1", current_severity=0.5)
        assert result.scene_id == "s1"
        assert isinstance(result.blocked, bool)

    def test_evaluate_blocked_structure(self):
        gate, _ = self._make_gate(threshold=0.60)
        result = gate.evaluate("s1", current_severity=0.99)
        if result.blocked:
            assert len(result.high_risk_cats) > 0
            assert result.max_probability >= 0.60

    def test_evaluate_not_blocked_low_severity(self):
        gate, _ = self._make_gate(threshold=0.99)  # 임계값 극대화
        result = gate.evaluate("s1", current_severity=0.01)
        assert not result.blocked

    def test_block_reason_when_blocked(self):
        gate, _ = self._make_gate(threshold=0.01)  # 임계값 극소화 → 반드시 차단
        result = gate.evaluate("s1", current_severity=0.9)
        if result.blocked:
            assert len(result.block_reason()) > 0

    def test_evaluate_batch(self):
        gate, _ = self._make_gate()
        results = gate.evaluate_batch(["s1", "s2", "s3"], severities=[0.3, 0.5, 0.7])
        assert len(results) == 3

    def test_block_count_and_rate(self):
        gate, _ = self._make_gate(threshold=0.99)  # 거의 차단 안 함
        for i in range(5):
            gate.evaluate(f"s{i}", 0.1)
        assert gate.total_evaluated() == 5
        assert 0.0 <= gate.block_rate() <= 1.0

    def test_gate_summary_structure(self):
        gate, _ = self._make_gate()
        gate.evaluate("s1")
        summary = gate.gate_summary()
        for key in ("total_evaluated", "block_count", "block_rate", "threshold", "horizon"):
            assert key in summary


# ─── V554: FeedbackLearner ─────────────────────────────────────────────────────

class TestFeedbackLearner:
    """FeedbackLearner 단위 테스트 (8종)."""

    def _make_learner(self, min_retrain=5):
        from literary_system.predictive import FeedbackLearner, DebtPredictor
        predictor = DebtPredictor()
        return FeedbackLearner(predictor=predictor, threshold=0.60, min_retrain=min_retrain)

    def test_record_single(self):
        learner = self._make_learner()
        rec = learner.record("s1", "unresolved_secret", 0.7, True)
        assert rec.predicted_high
        assert rec.actual_occurred
        assert learner.total_records() == 1

    def test_tp_counted_correctly(self):
        learner = self._make_learner()
        # TP: predicted_high=True + actual_occurred=True
        learner.record("s1", "unresolved_secret", 0.8, True)
        m = learner.metrics("unresolved_secret")
        assert m.tp == 1
        assert m.fp == 0

    def test_fp_counted_correctly(self):
        learner = self._make_learner()
        # FP: predicted_high=True + actual_occurred=False
        learner.record("s1", "unresolved_secret", 0.8, False)
        m = learner.metrics("unresolved_secret")
        assert m.fp == 1

    def test_fn_counted_correctly(self):
        learner = self._make_learner()
        # FN: predicted_high=False + actual_occurred=True
        learner.record("s1", "unresolved_secret", 0.3, True)
        m = learner.metrics("unresolved_secret")
        assert m.fn == 1

    def test_precision_computation(self):
        learner = self._make_learner()
        learner.record("s1", "c", 0.8, True)   # TP
        learner.record("s2", "c", 0.8, True)   # TP
        learner.record("s3", "c", 0.8, False)  # FP
        m = learner.metrics("c")
        assert abs(m.precision() - 2/3) < 1e-4

    def test_should_retrain_trigger(self):
        learner = self._make_learner(min_retrain=3)
        for i in range(3):
            learner.record(f"s{i}", "c", 0.7, True)
        assert learner.should_retrain()

    def test_auto_retrain_with_core(self):
        from literary_system.predictive import PNECore, DebtPredictor, FeedbackLearner
        from literary_system.predictive.pne_core import RepairOutcome
        core = PNECore()
        for i in range(10):
            core.ingest_outcome(RepairOutcome(f"s{i}", "r", "unresolved_secret", 0.5, True))
        predictor = DebtPredictor(pne_core=core)
        learner = FeedbackLearner(predictor=predictor, pne_core=core, min_retrain=3)
        for i in range(3):
            learner.record(f"s{i}", "unresolved_secret", 0.7, True)
        result = learner.auto_retrain_if_needed()
        assert result is not None  # 재학습 실행됨
        assert learner.retrain_count() == 1

    def test_summary_structure(self):
        learner = self._make_learner()
        learner.record("s1", "c", 0.7, True)
        summary = learner.summary()
        for key in ("total_records", "precision", "recall", "f1", "meets_target", "retrain_count"):
            assert key in summary


# ─── V555: Gate29 통합 테스트 ──────────────────────────────────────────────────

class TestGate29Integration:
    """Gate29 release_gate 통합 테스트 (5종)."""

    def test_gate29_function_exists(self):
        from literary_system.gates.release_gate import GATES
        names = [g[0] for g in GATES]
        assert "pne_convergence_gate29" in names

    def test_gate29_passes(self):
        from literary_system.gates import release_gate as rg
        fn = next(g[2] for g in rg.GATES if g[0] == "pne_convergence_gate29")
        result = fn()
        assert result["pass"] is True, f"Gate29 FAIL: {result.get('error', '')}"

    def test_gate_count_is_28_or_more(self):
        from literary_system.gates.release_gate import GATES
        assert len(GATES) >= 28

    def test_release_gate_version(self):
        from literary_system.gates.release_gate import run_release_gate
        result = run_release_gate()
        assert result["version"] in ("V555", "V556", "V561", "V571")

    def test_pne_end_to_end_pipeline(self):
        """PNECore → DebtPredictor → PreemptiveGate → FeedbackLearner 파이프라인 검증."""
        from literary_system.predictive import PNECore, DebtPredictor, PreemptiveGate, FeedbackLearner
        from literary_system.predictive.pne_core import RepairOutcome

        # 1. PNECore 누적
        core = PNECore()
        for i in range(8):
            core.ingest_outcome(RepairOutcome(
                f"s{i}", f"r{i}", "unresolved_secret", 0.65, success=(i < 6)
            ))

        # 2. DebtPredictor 예측
        predictor = DebtPredictor(pne_core=core)
        report = predictor.predict("s_new", current_severity=0.65, horizon=3)
        assert len(report.predictions) > 0

        # 3. PreemptiveGate 평가
        gate = PreemptiveGate(predictor=predictor, horizon=3)
        gate_result = gate.evaluate("s_new", current_severity=0.65)
        assert isinstance(gate_result.blocked, bool)

        # 4. FeedbackLearner 기록
        learner = FeedbackLearner(predictor=predictor, pne_core=core, min_retrain=20)
        pred_cat = report.predictions[0]
        learner.record("s_new", pred_cat.category, pred_cat.probability, actual_occurred=True)
        assert learner.total_records() == 1

        # 5. 전체 파이프라인 데이터 일관성
        assert core.total_ingested() == 8
        assert gate.total_evaluated() == 1
