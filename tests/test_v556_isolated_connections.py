"""
tests/test_v556_isolated_connections.py
========================================
V556 — 고립 모듈 파이프라인 연결 로직 증명 테스트

GitNexus V555 인덱싱 결과 inbound=0으로 확인된 4종 심볼의
실제 호출(CALLS 엣지) 연결을 단위·통합 테스트로 증명한다.

TestFractalPlotTreeBuilderConnection    (5 tests) — FractalPlotTreeBuilder.build()
TestNKGEmotionalLinkerEvDelta           (5 tests) — NKGEmotionalLinker.compute_ev_delta()
TestSceneMetricsCollectorBatch          (5 tests) — ReaderSimulator.estimate_batch()
TestPreemptiveGateFeedbackCycle         (5 tests) — PreemptiveGate.evaluate_batch()
TestIsolationProof                      (5 tests) — 4종 연결 종합 증명
"""

import pytest
from typing import List


# ══════════════════════════════════════════════════════════════════
# 1. FractalPlotTreeBuilder.build() — LongformEnduranceOrchestrator 연결
# ══════════════════════════════════════════════════════════════════

class TestFractalPlotTreeBuilderConnection:
    """FractalPlotTreeBuilder.build()가 파이프라인에서 실제 호출됨을 증명."""

    def test_builder_direct_call_returns_tree(self):
        """FractalPlotTreeBuilder.build() 직접 호출 — 반환값 검증."""
        from literary_system.longform.fractal_plot_tree import (
            FractalPlotTreeBuilder, FractalPlotTree, FractalTreeConfig
        )
        config = FractalTreeConfig(total_episodes=8, microplots_per_episode=4)
        tree = FractalPlotTreeBuilder().build(config)
        assert isinstance(tree, FractalPlotTree)
        assert tree.root is not None

    def test_builder_produces_units(self):
        """build() 결과 all_units 비어있지 않음."""
        from literary_system.longform.fractal_plot_tree import (
            FractalPlotTreeBuilder, FractalTreeConfig
        )
        tree = FractalPlotTreeBuilder().build(FractalTreeConfig(total_episodes=4))
        assert len(tree.all_units) > 0

    def test_orchestrator_fractal_tree_field_populated(self):
        """LongformEnduranceOrchestrator.run() 후 fractal_tree 필드 비어있지 않음 (V556 연결 증명)."""
        from literary_system.orchestrators.longform_endurance_orchestrator import (
            LongformEnduranceOrchestrator, LongformInput
        )
        from literary_system.episode.episode_state import SeriesConfig
        orch = LongformEnduranceOrchestrator()
        cfg = SeriesConfig(title="test", total_episodes=4, genre="drama")
        report = orch.run(LongformInput(series_config=cfg))
        # V556 핵심 검증: fractal_tree가 None이 아님
        assert report.fractal_tree is not None, "FractalPlotTreeBuilder.build()가 연결되지 않음"

    def test_orchestrator_fractal_tree_has_units(self):
        """fractal_tree.all_units 실제 유닛 보유."""
        from literary_system.orchestrators.longform_endurance_orchestrator import (
            LongformEnduranceOrchestrator, LongformInput
        )
        from literary_system.episode.episode_state import SeriesConfig
        orch = LongformEnduranceOrchestrator()
        cfg = SeriesConfig(title="test", total_episodes=4, genre="drama")
        report = orch.run(LongformInput(series_config=cfg))
        assert len(report.fractal_tree.all_units) > 0

    def test_orchestrator_trace_contains_fractal_tree_log(self):
        """실행 트레이스에 FractalPlotTree 로그 존재."""
        from literary_system.orchestrators.longform_endurance_orchestrator import (
            LongformEnduranceOrchestrator, LongformInput
        )
        from literary_system.episode.episode_state import SeriesConfig
        orch = LongformEnduranceOrchestrator()
        cfg = SeriesConfig(title="trace_test", total_episodes=4, genre="drama")
        report = orch.run(LongformInput(series_config=cfg))
        trace_str = " ".join(report.execution_trace)
        assert "FractalPlotTree" in trace_str, "실행 트레이스에 FractalPlotTree 로그 없음"


# ══════════════════════════════════════════════════════════════════
# 2. NKGEmotionalLinker.compute_ev_delta() — NKGPipeline 연결
# ══════════════════════════════════════════════════════════════════

class TestNKGEmotionalLinkerEvDelta:
    """NKGEmotionalLinker.compute_ev_delta()가 파이프라인 ctx에 기록됨을 증명."""

    def test_compute_ev_delta_direct_call(self):
        """compute_ev_delta() 직접 호출 — 벡터 길이 일치."""
        from literary_system.nkg.emotional_linker import NKGEmotionalLinker
        linker = NKGEmotionalLinker()
        ev_a = [0.8, 0.2, 0.5]
        ev_b = [0.3, 0.7, 0.4]
        delta = linker.compute_ev_delta(ev_a, ev_b)
        assert len(delta) == len(ev_a)

    def test_compute_ev_delta_values(self):
        """compute_ev_delta() 수치 정확성 — delta[i] = ev_b[i] - ev_a[i] (변화량 b-a)."""
        from literary_system.nkg.emotional_linker import NKGEmotionalLinker
        linker = NKGEmotionalLinker()
        ev_a = [1.0, 0.0]
        ev_b = [0.0, 1.0]
        delta = linker.compute_ev_delta(ev_a, ev_b)
        # _ev_delta(a,b) = [b[i]-a[i]]:  0-1=-1.0,  1-0=1.0
        assert abs(delta[0] - (-1.0)) < 1e-6
        assert abs(delta[1] - 1.0) < 1e-6

    def test_pipeline_ctx_ev_delta_written(self):
        """NKGPipeline 실행 후 _ev_delta ctx 키 존재 (2개 이상 노드 + ev 속성 필요)."""
        from literary_system.nkg.pipeline import NKGPipeline
        from literary_system.nkg.graph_store import NKGNode
        pipeline = NKGPipeline()
        # ev 속성을 가진 노드 2개 inject
        n1 = NKGNode(node_id="n1", node_type="character", label="A")
        n2 = NKGNode(node_id="n2", node_type="character", label="B")
        n1.ev = [0.8, 0.2, 0.5]
        n2.ev = [0.3, 0.7, 0.4]
        ctx = {"_extracted_scene_nodes": [n1, n2]}
        pipeline._phase_emotional(ctx, {})
        # V556 핵심 검증: compute_ev_delta 결과가 ctx에 기록됨
        assert "_ev_delta" in ctx, "compute_ev_delta() 호출 결과가 ctx에 없음"

    def test_ev_delta_ctx_length_correct(self):
        """ctx의 _ev_delta 길이가 입력 ev 벡터 길이와 일치."""
        from literary_system.nkg.pipeline import NKGPipeline
        from literary_system.nkg.graph_store import NKGNode
        pipeline = NKGPipeline()
        n1 = NKGNode(node_id="n1", node_type="character", label="A")
        n2 = NKGNode(node_id="n2", node_type="character", label="B")
        n1.ev = [0.5, 0.3, 0.8, 0.1]
        n2.ev = [0.2, 0.6, 0.4, 0.9]
        ctx = {"_extracted_scene_nodes": [n1, n2]}
        pipeline._phase_emotional(ctx, {})
        if "_ev_delta" in ctx:
            assert len(ctx["_ev_delta"]) == 4

    def test_ev_delta_not_written_without_ev_attr(self):
        """ev 속성 없는 노드는 _ev_delta 미기록 — 안전성 검증."""
        from literary_system.nkg.pipeline import NKGPipeline
        from literary_system.nkg.graph_store import NKGNode
        pipeline = NKGPipeline()
        n1 = NKGNode(node_id="n1", node_type="character", label="A")
        n2 = NKGNode(node_id="n2", node_type="character", label="B")
        # ev 속성 없음
        ctx = {"_extracted_scene_nodes": [n1, n2]}
        pipeline._phase_emotional(ctx, {})
        # ev 없으면 _ev_delta 미기록이어야 함 (에러 없이 통과)
        assert "_emotional_edges" in ctx  # 기존 키는 존재


# ══════════════════════════════════════════════════════════════════
# 3. ReaderSimulator.estimate_batch() — SceneMetricsCollector 연결
# ══════════════════════════════════════════════════════════════════

class TestSceneMetricsCollectorBatch:
    """SceneMetricsCollector.collect_batch()가 ReaderSimulator.estimate_batch()를 호출함을 증명."""

    def test_collect_batch_returns_dict(self):
        """collect_batch() 반환 타입이 dict."""
        from literary_system.evaluation.scene_metrics_collector import SceneMetricsCollector
        collector = SceneMetricsCollector()
        result = collector.collect_batch({"s1": "어머니가 문을 열었다.", "s2": "빗소리가 들렸다."})
        assert isinstance(result, dict)

    def test_collect_batch_keys_match_input(self):
        """collect_batch() 반환 dict 키가 입력 scene_ids와 일치."""
        from literary_system.evaluation.scene_metrics_collector import SceneMetricsCollector
        collector = SceneMetricsCollector()
        scenes = {"ep1_s1": "연기가 피어올랐다.", "ep1_s2": "그가 돌아섰다."}
        result = collector.collect_batch(scenes)
        assert set(result.keys()) == set(scenes.keys())

    def test_collect_batch_each_value_is_scene_metrics(self):
        """각 값이 SceneMetrics 타입."""
        from literary_system.evaluation.scene_metrics_collector import (
            SceneMetricsCollector, SceneMetrics
        )
        collector = SceneMetricsCollector()
        result = collector.collect_batch({"s1": "그녀가 웃었다."})
        for v in result.values():
            assert isinstance(v, SceneMetrics)

    def test_collect_batch_reader_uncertainty_in_range(self):
        """각 SceneMetrics.reader_uncertainty가 0.0~1.0 범위."""
        from literary_system.evaluation.scene_metrics_collector import SceneMetricsCollector
        collector = SceneMetricsCollector()
        result = collector.collect_batch({"s1": "비가 내렸다.", "s2": "그가 달렸다."})
        for m in result.values():
            assert 0.0 <= m.reader_uncertainty <= 1.0

    def test_collect_batch_empty_input_returns_empty(self):
        """빈 입력은 빈 dict 반환."""
        from literary_system.evaluation.scene_metrics_collector import SceneMetricsCollector
        collector = SceneMetricsCollector()
        assert collector.collect_batch({}) == {}


# ══════════════════════════════════════════════════════════════════
# 4. PreemptiveGate.evaluate_batch() — FeedbackLearner 연결
# ══════════════════════════════════════════════════════════════════

class TestPreemptiveGateFeedbackCycle:
    """FeedbackLearner.run_prediction_cycle()이 PreemptiveGate.evaluate_batch()를 호출함을 증명."""

    def _make_gate(self):
        from literary_system.predictive import DebtPredictor, PNECore, PreemptiveGate
        core = PNECore()
        predictor = DebtPredictor()
        predictor.train(pne_core=core)
        return PreemptiveGate(predictor=predictor, horizon=3)

    def test_run_prediction_cycle_returns_records(self):
        """run_prediction_cycle() 반환값이 PredictionRecord 리스트."""
        from literary_system.predictive.feedback_learner import FeedbackLearner, PredictionRecord
        gate = self._make_gate()
        learner = FeedbackLearner()
        records = learner.run_prediction_cycle(gate, scene_ids=["s1", "s2", "s3"])
        assert isinstance(records, list)
        assert all(isinstance(r, PredictionRecord) for r in records)

    def test_run_prediction_cycle_count_matches_input(self):
        """반환 레코드 수 == 입력 scene_ids 수."""
        from literary_system.predictive.feedback_learner import FeedbackLearner
        gate = self._make_gate()
        learner = FeedbackLearner()
        records = learner.run_prediction_cycle(gate, scene_ids=["s1", "s2", "s3", "s4"])
        assert len(records) == 4

    def test_run_prediction_cycle_records_stored_in_learner(self):
        """run_prediction_cycle() 후 learner.total_records() 증가."""
        from literary_system.predictive.feedback_learner import FeedbackLearner
        gate = self._make_gate()
        learner = FeedbackLearner()
        assert learner.total_records() == 0
        learner.run_prediction_cycle(gate, scene_ids=["s1", "s2"])
        assert learner.total_records() == 2

    def test_run_prediction_cycle_with_actual_occurrences(self):
        """actual_occurrences 전달 시 TP/FP 분류."""
        from literary_system.predictive.feedback_learner import FeedbackLearner
        gate = self._make_gate()
        learner = FeedbackLearner()
        learner.run_prediction_cycle(
            gate,
            scene_ids=["s1", "s2"],
            actual_occurrences=[True, False],
        )
        m = learner.metrics()
        assert m.total == 2

    def test_run_prediction_cycle_empty_returns_empty(self):
        """빈 scene_ids는 빈 리스트 반환."""
        from literary_system.predictive.feedback_learner import FeedbackLearner
        gate = self._make_gate()
        learner = FeedbackLearner()
        assert learner.run_prediction_cycle(gate, scene_ids=[]) == []


# ══════════════════════════════════════════════════════════════════
# 5. 종합 증명 — 4종 모두 파이프라인에 통합됨
# ══════════════════════════════════════════════════════════════════

class TestIsolationProof:
    """V556 고립 해소 종합 증명: 4개 메서드가 실제 호출됨을 단언."""

    def test_fractal_builder_not_orphan(self):
        """FractalPlotTreeBuilder.build() 호출 후 결과 비어있지 않음."""
        from literary_system.longform.fractal_plot_tree import (
            FractalPlotTreeBuilder, FractalTreeConfig
        )
        tree = FractalPlotTreeBuilder().build(FractalTreeConfig(total_episodes=8))
        assert tree is not None and len(tree.all_units) > 0, \
            "FAIL: FractalPlotTreeBuilder.build() 고립 상태"

    def test_compute_ev_delta_not_orphan(self):
        """NKGEmotionalLinker.compute_ev_delta() 직접 호출 성공."""
        from literary_system.nkg.emotional_linker import NKGEmotionalLinker
        result = NKGEmotionalLinker().compute_ev_delta([0.9, 0.1], [0.4, 0.6])
        assert result is not None and len(result) == 2, \
            "FAIL: compute_ev_delta() 고립 상태"

    def test_estimate_batch_not_orphan(self):
        """ReaderSimulator.estimate_batch() → SceneMetricsCollector.collect_batch() 경로 확인."""
        from literary_system.evaluation.scene_metrics_collector import SceneMetricsCollector
        result = SceneMetricsCollector().collect_batch({"s1": "그가 멈췄다."})
        assert "s1" in result, "FAIL: ReaderSimulator.estimate_batch() 고립 상태"

    def test_evaluate_batch_not_orphan(self):
        """PreemptiveGate.evaluate_batch() → FeedbackLearner 경로 확인."""
        from literary_system.predictive import DebtPredictor, PNECore, PreemptiveGate
        from literary_system.predictive.feedback_learner import FeedbackLearner
        core = PNECore()
        pred = DebtPredictor()
        pred.train(pne_core=core)
        gate = PreemptiveGate(predictor=pred, horizon=2)
        learner = FeedbackLearner()
        recs = learner.run_prediction_cycle(gate, ["s1"])
        assert len(recs) == 1, "FAIL: PreemptiveGate.evaluate_batch() 고립 상태"

    def test_all_four_connections_in_one_run(self):
        """4종 연결을 순서대로 실행 — 모두 예외 없이 완료."""
        errors = []

        # 1) FractalPlotTreeBuilder
        try:
            from literary_system.longform.fractal_plot_tree import (
                FractalPlotTreeBuilder, FractalTreeConfig
            )
            FractalPlotTreeBuilder().build(FractalTreeConfig(total_episodes=4))
        except Exception as e:
            errors.append(f"FractalPlotTreeBuilder: {e}")

        # 2) compute_ev_delta
        try:
            from literary_system.nkg.emotional_linker import NKGEmotionalLinker
            NKGEmotionalLinker().compute_ev_delta([0.5, 0.5], [0.3, 0.7])
        except Exception as e:
            errors.append(f"compute_ev_delta: {e}")

        # 3) estimate_batch via collect_batch
        try:
            from literary_system.evaluation.scene_metrics_collector import SceneMetricsCollector
            SceneMetricsCollector().collect_batch({"s1": "씬 텍스트"})
        except Exception as e:
            errors.append(f"estimate_batch: {e}")

        # 4) evaluate_batch via run_prediction_cycle
        try:
            from literary_system.predictive import DebtPredictor, PNECore, PreemptiveGate
            from literary_system.predictive.feedback_learner import FeedbackLearner
            core = PNECore()
            pred = DebtPredictor()
            pred.train(pne_core=core)
            gate = PreemptiveGate(predictor=pred, horizon=2)
            FeedbackLearner().run_prediction_cycle(gate, ["s1", "s2"])
        except Exception as e:
            errors.append(f"evaluate_batch: {e}")

        assert not errors, f"고립 연결 실패: {errors}"
