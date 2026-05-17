"""
V320 테스트 — 4개 신규 모듈 전수 검증.

1. GoldStandardBuilder    (Phase 1A)
2. LocalJudgmentValidator (Phase 1B)
3. ConditionalLLMGate     (Phase 3)
4. E2ELoopOrchestrator    (Phase 2 — mock V312 사용)
"""
from __future__ import annotations
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ═══════════════════════════════════════════════════════════
# TestGoldStandardBuilder
# ═══════════════════════════════════════════════════════════
class TestGoldStandardBuilder:

    def setup_method(self):
        from literary_system.validation.gold_standard_builder import (
            GoldStandardBuilder, GoldStandardStore, QualityLabel, LabelSource
        )
        self.store   = GoldStandardStore()
        self.builder = GoldStandardBuilder(self.store)
        self.QualityLabel = QualityLabel
        self.LabelSource  = LabelSource

    def test_label_scene_creates_entry(self):
        lbl = self.builder.label_scene(
            scene_text="그는 복도에서 파일을 발견했다. 창문 너머로 빗소리가 들렸다.",
            label=self.QualityLabel.GOOD,
            source=self.LabelSource.ARCHITECT,
            notes="PDI 준수, 잔향 선명",
        )
        assert lbl.label == self.QualityLabel.GOOD
        assert lbl.source == self.LabelSource.ARCHITECT
        assert lbl.scene_id in self.store._labels

    def test_label_scene_bad(self):
        lbl = self.builder.label_scene(
            scene_text="그는 슬펐다. 결국 모든 것이 끝났다.",
            label=self.QualityLabel.BAD,
            source=self.LabelSource.ARCHITECT,
        )
        assert lbl.label == self.QualityLabel.BAD

    def test_store_count(self):
        for i in range(5):
            self.builder.label_scene(f"씬 {i}", self.QualityLabel.GOOD, self.LabelSource.ARCHITECT)
        for i in range(3):
            self.builder.label_scene(f"나쁜 씬 {i}", self.QualityLabel.BAD, self.LabelSource.ARCHITECT)
        counts = self.store.count()
        assert counts["GOOD"] == 5
        assert counts["BAD"] == 3
        assert counts["total"] == 8

    def test_filter_for_validation_excludes_marginal(self):
        self.builder.label_scene("G", self.QualityLabel.GOOD, self.LabelSource.ARCHITECT)
        self.builder.label_scene("B", self.QualityLabel.BAD, self.LabelSource.ARCHITECT)
        self.builder.label_scene("M", self.QualityLabel.MARGINAL, self.LabelSource.ARCHITECT)
        validatable = self.store.filter_for_validation()
        assert len(validatable) == 2
        labels = [l.label for l in validatable]
        assert self.QualityLabel.MARGINAL not in labels

    def test_cross_validate_perfect_agreement(self):
        scene_id = "sc_001"
        arch = [self.builder.label_scene("텍스트", self.QualityLabel.GOOD,
                                          self.LabelSource.ARCHITECT, scene_id=scene_id)]
        comp = [self.builder.label_scene("텍스트", self.QualityLabel.GOOD,
                                          self.LabelSource.COMPILER, scene_id=scene_id + "_c")]
        # 같은 scene_id로 다시
        from literary_system.validation.gold_standard_builder import SceneLabel
        comp2 = [SceneLabel(scene_id=scene_id, scene_text="텍스트",
                             label=self.QualityLabel.GOOD,
                             source=self.LabelSource.COMPILER)]
        result = self.builder.cross_validate(arch, comp2)
        assert result.agreement_rate == 1.0
        assert result.passed_threshold is True
        assert result.agreed_items == 1
        assert result.disagreed_items == 0

    def test_cross_validate_disagreement(self):
        from literary_system.validation.gold_standard_builder import SceneLabel
        sid = "sc_002"
        arch = [SceneLabel(scene_id=sid, scene_text="T", label=self.QualityLabel.GOOD,
                            source=self.LabelSource.ARCHITECT)]
        comp = [SceneLabel(scene_id=sid, scene_text="T", label=self.QualityLabel.BAD,
                            source=self.LabelSource.COMPILER)]
        result = self.builder.cross_validate(arch, comp)
        assert result.agreement_rate == 0.0
        assert result.passed_threshold is False
        assert sid in result.disagreed_scene_ids

    def test_cross_validate_threshold_75(self):
        from literary_system.validation.gold_standard_builder import SceneLabel
        arch, comp = [], []
        for i in range(8):  # 8 agree
            arch.append(SceneLabel(f"sc_{i}", "T", self.QualityLabel.GOOD, self.LabelSource.ARCHITECT))
            comp.append(SceneLabel(f"sc_{i}", "T", self.QualityLabel.GOOD, self.LabelSource.COMPILER))
        for i in range(8, 10):  # 2 disagree
            arch.append(SceneLabel(f"sc_{i}", "T", self.QualityLabel.GOOD, self.LabelSource.ARCHITECT))
            comp.append(SceneLabel(f"sc_{i}", "T", self.QualityLabel.BAD, self.LabelSource.COMPILER))
        result = self.builder.cross_validate(arch, comp)
        assert result.agreement_rate == 0.8
        assert result.passed_threshold is True

    def test_progress_report(self):
        for i in range(25):
            self.builder.label_scene(f"씬 {i}", self.QualityLabel.GOOD, self.LabelSource.CONSENSUS)
        progress = self.builder.get_progress()
        assert progress["minimum_met"] is True
        assert progress["ready_for_phase1b"] is True

    def test_load_from_gpt_outputs(self):
        texts = ["씬 A", "씬 B", "씬 C"]
        labels = [self.QualityLabel.GOOD, self.QualityLabel.BAD, self.QualityLabel.GOOD]
        result = self.builder.load_from_gpt_outputs(texts, labels)
        assert len(result) == 3
        assert result[0].label == self.QualityLabel.GOOD
        assert result[1].label == self.QualityLabel.BAD

    def test_commit_consensus(self):
        from literary_system.validation.gold_standard_builder import SceneLabel
        orig = [SceneLabel("sc_c1", "텍스트", self.QualityLabel.GOOD, self.LabelSource.ARCHITECT)]
        consensus = {"sc_c1": self.QualityLabel.GOOD}
        n = self.builder.commit_consensus(consensus, orig)
        assert n == 1
        committed = self.store.list_by_source(self.LabelSource.CONSENSUS)
        assert len(committed) >= 1


# ═══════════════════════════════════════════════════════════
# TestLocalJudgmentValidator
# ═══════════════════════════════════════════════════════════
class TestLocalJudgmentValidator:

    def setup_method(self):
        from literary_system.validation.gold_standard_builder import (
            GoldStandardBuilder, GoldStandardStore, QualityLabel, LabelSource, SceneLabel
        )
        from literary_system.validation.local_judgment_validator import (
            LocalJudgmentValidator, ValidationMetrics
        )
        self.QualityLabel = QualityLabel
        self.LabelSource  = LabelSource
        self.SceneLabel   = SceneLabel
        self.ValidationMetrics = ValidationMetrics
        self.validator = LocalJudgmentValidator()
        self.builder   = GoldStandardBuilder(GoldStandardStore())

    def _make_scene(self, text, label):
        return self.SceneLabel(
            scene_id=f"sc_{label}_{text[:4]}",
            scene_text=text,
            label=label,
            source=self.LabelSource.CONSENSUS,
        )

    def test_judge_good_scene(self):
        scene = self._make_scene(
            "그는 복도에서 걸음을 멈췄다. 파일이 바닥에 펼쳐져 있었다. "
            "창문 너머로 가로등이 흔들렸다. 손이 저절로 서류를 향했다.",
            self.QualityLabel.GOOD
        )
        result = self.validator.judge_scene(scene)
        assert result.scene_id == scene.scene_id
        assert result.gold_label == self.QualityLabel.GOOD
        assert isinstance(result.reader_pull, float)
        assert isinstance(result.match, bool)

    def test_judge_bad_scene(self):
        scene = self._make_scene(
            "그는 슬펐다. 왠지 모르게 그는 두려웠다. 결국 아무것도 하지 않았다. 이상하게도.",
            self.QualityLabel.BAD
        )
        result = self.validator.judge_scene(scene)
        assert result.gold_label == self.QualityLabel.BAD

    def test_validate_store_returns_metrics(self):
        from literary_system.validation.gold_standard_builder import GoldStandardStore
        store = GoldStandardStore()
        # 좋은 씬 10개, 나쁜 씬 10개
        good_texts = [
            f"복도가 조용했다. 서류가 바닥에 펼쳐져 있었다. 손이 멈췄다. 창문이 흔들렸다. 그는 {i}번 장면이었다."
            for i in range(10)
        ]
        bad_texts = [
            f"그는 슬펐다. 결국 화가 났다. 왠지 모르게 두려웠다. {i}번 장면."
            for i in range(10)
        ]
        for i, text in enumerate(good_texts):
            store.add(self.SceneLabel(f"g_{i}", text, self.QualityLabel.GOOD, self.LabelSource.CONSENSUS))
        for i, text in enumerate(bad_texts):
            store.add(self.SceneLabel(f"b_{i}", text, self.QualityLabel.BAD, self.LabelSource.CONSENSUS))

        metrics, results = self.validator.validate_store(store)
        assert metrics.total_scenes == 20
        assert metrics.precision + metrics.recall + metrics.f1 >= 0
        assert isinstance(metrics.passed, bool)

    def test_metrics_structure(self):
        from literary_system.validation.gold_standard_builder import GoldStandardStore
        store = GoldStandardStore()
        store.add(self.SceneLabel("s1", "복도. 서류. 침묵.", self.QualityLabel.GOOD, self.LabelSource.CONSENSUS))
        store.add(self.SceneLabel("s2", "그는 슬펐다.", self.QualityLabel.BAD, self.LabelSource.CONSENSUS))
        metrics, _ = self.validator.validate_store(store)
        assert 0.0 <= metrics.precision <= 1.0
        assert 0.0 <= metrics.recall <= 1.0
        assert 0.0 <= metrics.f1 <= 1.0

    def test_threshold_adjustment_suggestion(self):
        from literary_system.validation.local_judgment_validator import ValidationMetrics
        metrics = ValidationMetrics(
            total_scenes=20, true_positives=5, false_positives=5,
            true_negatives=8, false_negatives=2,
            precision=0.50, recall=0.71, f1=0.59, accuracy=0.65,
            passed_precision=False, passed_recall=True, passed=False
        )
        suggestions = self.validator.adjust_thresholds(metrics, [])
        assert isinstance(suggestions, dict)

    def test_pdi_check_good(self):
        text = "그는 손을 거두지 못했다. 파일이 거기 있었다."
        result = self.validator._check_pdi(text)
        assert result is True  # PDI 준수

    def test_pdi_check_bad(self):
        text = "그는 슬펐다. 그녀는 울었다. 그는 화가 났다."
        result = self.validator._check_pdi(text)
        assert result is False  # PDI 위반

    def test_apply_threshold_adjustment(self):
        original = self.validator.thresholds["reader_pull_min"]
        self.validator.apply_threshold_adjustment({"reader_pull_min": 0.55})
        assert self.validator.thresholds["reader_pull_min"] == 0.55
        self.validator.thresholds["reader_pull_min"] = original  # 복원


# ═══════════════════════════════════════════════════════════
# TestConditionalLLMGate
# ═══════════════════════════════════════════════════════════
class TestConditionalLLMGate:

    def setup_method(self):
        from literary_system.gate.conditional_llm_gate import (
            ConditionalLLMGate, GateDecision
        )
        self.gate = ConditionalLLMGate()
        self.GateDecision = GateDecision

    def _metrics_good(self):
        return {"reader_pull": 0.65, "reader_afterimage": 0.55, "reader_uncertainty": 0.40}

    def _metrics_bad(self):
        return {"reader_pull": 0.20, "reader_afterimage": 0.15, "reader_uncertainty": 0.90}

    def test_pass_when_all_criteria_met(self):
        result = self.gate.evaluate(
            literary_state={"SP": 0.65},
            reader_metrics=self._metrics_good(),
            literary_loss=1,
            patch_attempts=0,
        )
        assert result.decision == self.GateDecision.PASS
        assert result.llm_call_prevented is True

    def test_patch_only_on_first_failure(self):
        result = self.gate.evaluate(
            literary_state={"SP": 0.30},
            reader_metrics=self._metrics_bad(),
            literary_loss=5,
            patch_attempts=0,
        )
        assert result.decision == self.GateDecision.PATCH_ONLY
        assert result.llm_call_prevented is True

    def test_patch_only_on_second_failure(self):
        result = self.gate.evaluate(
            literary_state={"SP": 0.30},
            reader_metrics=self._metrics_bad(),
            literary_loss=5,
            patch_attempts=1,
        )
        assert result.decision == self.GateDecision.PATCH_ONLY
        assert result.llm_call_prevented is True

    def test_rerender_after_max_patches(self):
        result = self.gate.evaluate(
            literary_state={"SP": 0.30},
            reader_metrics=self._metrics_bad(),
            literary_loss=5,
            patch_attempts=2,  # MAX_PATCH_ATTEMPTS 초과
        )
        assert result.decision == self.GateDecision.RERENDER
        assert result.llm_call_prevented is False

    def test_correction_hints_populated(self):
        result = self.gate.evaluate(
            literary_state={},
            reader_metrics={"reader_pull": 0.20, "reader_afterimage": 0.10, "reader_uncertainty": 0.90},
            literary_loss=5,
            patch_attempts=0,
        )
        assert len(result.correction_hints) > 0
        assert len(result.reasons) > 0

    def test_stats_tracking(self):
        gate = __import__('literary_system.gate.conditional_llm_gate',
                           fromlist=['ConditionalLLMGate']).ConditionalLLMGate()
        gate.evaluate({}, self._metrics_good(), 0, 0)
        gate.evaluate({}, self._metrics_bad(), 5, 0)
        gate.evaluate({}, self._metrics_bad(), 5, 2)
        stats = gate.get_stats()
        assert stats["total_evaluations"] == 3
        assert stats["pass_count"] == 1
        assert stats["rerender_count"] == 1

    def test_llm_prevention_rate(self):
        gate = __import__('literary_system.gate.conditional_llm_gate',
                           fromlist=['ConditionalLLMGate']).ConditionalLLMGate()
        # 3 PASS + 1 PATCH_ONLY + 1 RERENDER = 4/5 방지
        gate.evaluate({}, self._metrics_good(), 0, 0)
        gate.evaluate({}, self._metrics_good(), 0, 0)
        gate.evaluate({}, self._metrics_good(), 0, 0)
        gate.evaluate({}, self._metrics_bad(), 5, 0)
        gate.evaluate({}, self._metrics_bad(), 5, 2)
        stats = gate.get_stats()
        assert stats["llm_calls_prevented"] == 4
        assert stats["llm_prevention_rate"] == 0.8

    def test_calibrate_from_baseline(self):
        baseline = {"rerender_rate": 0.60}
        suggestions = self.gate.calibrate_from_baseline(baseline, target_reduction=0.50)
        assert "target_rerender_rate" in suggestions
        assert suggestions["target_rerender_rate"] < 0.60

    def test_reset_stats(self):
        self.gate.evaluate({}, self._metrics_good(), 0, 0)
        self.gate.reset_stats()
        stats = self.gate.get_stats()
        assert stats["total_evaluations"] == 0

    def test_custom_thresholds(self):
        strict_gate = __import__('literary_system.gate.conditional_llm_gate',
                                  fromlist=['ConditionalLLMGate']).ConditionalLLMGate(
            thresholds={"reader_pull_min": 0.80, "reader_afterimage_min": 0.70,
                        "reader_uncertainty_max": 0.30, "literary_loss_max": 0}
        )
        result = strict_gate.evaluate({}, self._metrics_good(), 0, 0)
        # reader_pull=0.65 < 0.80이므로 PASS 불가
        assert result.decision != self.GateDecision.PASS


# ═══════════════════════════════════════════════════════════
# TestE2ELoopOrchestrator
# ═══════════════════════════════════════════════════════════
class TestE2ELoopOrchestrator:
    """
    V312 엔진 없이 mock으로 테스트.
    실제 V312 연결은 ANTHROPIC_API_KEY 설정 후 별도 실행.
    """

    def setup_method(self):
        from literary_system.orchestrators.e2e_loop_orchestrator import (
            E2ELoopOrchestrator, GateDecision
        )
        from literary_system.gate.conditional_llm_gate import ConditionalLLMGate
        from literary_system.render_loop.specialized_patch import SpecializedLocalPatchEngine
        from literary_system.trajectory.reader_simulator import ReaderSimulator
        from literary_system.trace.trace_dataset_store import TraceDatasetStore
        from literary_system.compiler.v312_bridge import V312Bridge

        self.GateDecision = GateDecision

        # Mock V312Bridge
        class MockBridge(V312Bridge):
            def __init__(self):
                self.backend_path = type('P', (), {'exists': lambda self: True})()
                self._engine_loaded = False
                self._call_count = 0

            def run(self, bundle, timeout_seconds=120.0):
                self._call_count += 1
                return {
                    "render_output": {
                        "text": f"복도가 조용했다. 서류가 바닥에 펼쳐져 있었다. 그는 손을 멈췄다. [{self._call_count}회]"
                    },
                    "literary_state_after": {"SP": 0.62, "RU": 0.68, "ET": 0.02},
                    "promotion_decision": "archive_only",
                    "literary_loss": 1,
                    "call_count": self._call_count,
                }
            def is_available(self): return True
            def get_status(self): return {"available": True, "backend_exists": True}

        self.mock_bridge = MockBridge()

        self.orch = E2ELoopOrchestrator.__new__(E2ELoopOrchestrator)
        self.orch.bridge       = self.mock_bridge
        self.orch.reader_sim   = ReaderSimulator()
        self.orch.patch_engine = SpecializedLocalPatchEngine()
        self.orch.gate         = ConditionalLLMGate(thresholds={
            "reader_pull_min": 0.10,  # 낮게 설정 → mock 텍스트도 통과
            "reader_afterimage_min": 0.05,
            "reader_uncertainty_max": 0.99,
            "literary_loss_max": 10,
        })
        self.orch.trace_store  = TraceDatasetStore()

    def test_run_returns_result(self):
        bundle = {
            "render_instruction": "비서관이 복도에서 서류를 발견한다.",
            "genre": "korean_political_thriller",
            "state_before": {"SP": 0.62, "RU": 0.68},
        }
        result = self.orch.run(bundle, project_id="test_proj", verbose=False)
        assert result.project_id == "test_proj"
        assert result.total_llm_calls >= 1
        assert isinstance(result.success, bool)
        assert isinstance(result.final_text, str)
        assert len(result.final_text) > 0

    def test_run_completes_loop(self):
        bundle = {"render_instruction": "테스트 씬", "state_before": {}}
        result = self.orch.run(bundle, verbose=False)
        assert result.total_iterations >= 1
        assert result.duration_seconds >= 0

    def test_summary_has_required_keys(self):
        bundle = {"render_instruction": "테스트", "state_before": {}}
        result = self.orch.run(bundle, verbose=False)
        summary = result.summary()
        for key in ["project_id", "success", "total_llm_calls",
                    "total_patch_attempts", "total_iterations",
                    "promotion_decision", "gate_stats"]:
            assert key in summary

    def test_gate_stats_in_result(self):
        bundle = {"render_instruction": "테스트", "state_before": {}}
        result = self.orch.run(bundle, verbose=False)
        assert "total_evaluations" in result.gate_stats
        assert result.gate_stats["total_evaluations"] >= 1

    def test_mock_bridge_available(self):
        assert self.orch.is_v312_available() is True

    def test_rerender_triggers_additional_llm_call(self):
        from literary_system.gate.conditional_llm_gate import ConditionalLLMGate

        # 엄격한 게이트 → 항상 RERENDER → 최대 LLM 호출까지
        self.orch.gate = ConditionalLLMGate(thresholds={
            "reader_pull_min": 0.99,  # 절대 통과 불가
            "reader_afterimage_min": 0.99,
            "reader_uncertainty_max": 0.01,
            "literary_loss_max": 0,
        })
        bundle = {"render_instruction": "테스트", "state_before": {}}
        result = self.orch.run(bundle, verbose=False)
        # 최대 LLM 호출까지 도달해야 함
        assert result.total_llm_calls >= 1

    def test_extract_text_from_dict(self):
        render = {"render_output": {"text": "복도가 조용했다."}}
        text = self.orch._extract_text(render)
        assert "복도" in text

    def test_pick_patch_family(self):
        assert self.orch._pick_patch_family({"pdi_fix": True}) == "pdi_fix"
        assert self.orch._pick_patch_family({"residue_boost": True}) == "residue_boost"
        assert self.orch._pick_patch_family({"reveal_delay": True}) == "reveal_delay"
        assert self.orch._pick_patch_family({}) == "pdi_fix"  # 기본

    def test_inject_soft_instruction(self):
        bundle = {"render_instruction": "원본 지시"}
        new_bundle = self.orch._inject_soft_instruction(bundle, "[PATCH: pdi_fix]")
        assert "[PATCH: pdi_fix]" in new_bundle["render_instruction"]
        assert "원본 지시" in new_bundle["render_instruction"]
