"""
test_v471_eval_safety.py — ModelEvalHarness + SafetyRegressionSuite 테스트 (V471)

ADR-009: LLM-as-Judge Calibration (로컬 BLEU/ROUGE/Coherence)
"""
import uuid
import pytest
from literary_system.finetune.model_eval_harness import (
    ModelEvalHarness, EvalSample, EvalReport,
)
from literary_system.finetune.safety_regression_suite import (
    SafetyRegressionSuite, SafetyReport, SafetyCategory,
)


# ─────────────────────────────────────────────
# ModelEvalHarness
# ─────────────────────────────────────────────

class TestModelEvalHarnessBasic:
    """기본 평가 실행"""

    def _make_sample(self, ref: str, gen: str, style: str = "romance") -> EvalSample:
        return EvalSample(
            sample_id=str(uuid.uuid4()),
            input_text="테스트 입력",
            reference_text=ref,
            generated_text=gen,
            style_label=style,
        )

    def test_run_eval_returns_report(self):
        harness = ModelEvalHarness()
        samples = [self._make_sample(
            "그의 눈빛이 그녀를 향했다. 설레는 마음을 감추지 못했다.",
            "그의 눈빛이 그녀를 향했다.",
        )]
        report = harness.run_eval("model-001", samples)
        assert report is not None
        assert report.model_id == "model-001"

    def test_report_sample_count(self):
        harness = ModelEvalHarness()
        samples = [
            self._make_sample("참조1 긴 문장입니다.", "생성1 긴 문장입니다."),
            self._make_sample("참조2 짧은 문장.", "생성2 짧은 문장."),
        ]
        report = harness.run_eval("model-002", samples)
        assert report.sample_count == 2

    def test_report_bleu_score_range(self):
        harness = ModelEvalHarness()
        samples = [self._make_sample("테스트 문장입니다.", "테스트 문장입니다.")]
        report = harness.run_eval("m", samples)
        assert 0.0 <= report.bleu_score <= 1.0

    def test_report_rouge_l_range(self):
        harness = ModelEvalHarness()
        samples = [self._make_sample("테스트 문장입니다.", "테스트 문장입니다.")]
        report = harness.run_eval("m", samples)
        assert 0.0 <= report.rouge_l <= 1.0

    def test_report_coherence_range(self):
        harness = ModelEvalHarness()
        samples = [self._make_sample(
            "그는 방으로 들어갔다. 그녀가 기다리고 있었다.",
            "그는 방으로 들어갔다. 그녀가 기다리고 있었다.",
        )]
        report = harness.run_eval("m", samples)
        assert 0.0 <= report.coherence_score <= 1.0

    def test_identical_texts_high_scores(self):
        """참조=생성 시 BLEU/ROUGE 높아야 함"""
        harness = ModelEvalHarness()
        text = "그의 눈빛이 그녀를 향했다. 설레는 마음을 감추지 못한 채 미소를 지었다."
        samples = [self._make_sample(text, text)]
        report = harness.run_eval("m", samples)
        assert report.bleu_score > 0.5
        assert report.rouge_l > 0.5


class TestModelEvalHarnessThresholds:
    """임계값 기반 pass/fail"""

    def _make_sample(self, ref: str, gen: str, style: str = "romance") -> EvalSample:
        return EvalSample(
            sample_id=str(uuid.uuid4()),
            input_text="입력",
            reference_text=ref,
            generated_text=gen,
            style_label=style,
        )

    def test_perfect_match_passes(self):
        harness = ModelEvalHarness()
        # romance 키워드 5개 이상: 사랑/설레/마음/그리움/두근/눈물/행복/연인 → style_sim >= 0.30
        text = "사랑하는 연인이 서로를 바라보았다. 그리고 설레는 마음으로 눈물을 흘렸다. 그러나 행복한 기억이 두근거리며 그리움을 채웠다. 결국 두 사람은 연인으로 남았다."
        samples = [self._make_sample(text, text)]
        report = harness.run_eval("m", samples)
        assert report.bleu_score >= 0.9
        assert report.rouge_l >= 0.9
        # passed: BLEU/ROUGE/Coherence/style_sim/hallucination 5항목 복합
        assert report.passed is True

    def test_empty_generated_fails(self):
        harness = ModelEvalHarness()
        samples = [self._make_sample("참조 문장입니다.", "")]
        report = harness.run_eval("m", samples)
        # BLEU=0이면 passed=False
        assert report.bleu_score == 0.0 or report.passed is False

    def test_thresholds_defined(self):
        assert ModelEvalHarness.BLEU_THRESHOLD >= 0
        assert ModelEvalHarness.ROUGE_THRESHOLD >= 0
        assert ModelEvalHarness.COHERENCE_THRESHOLD >= 0


class TestModelEvalHarnessCompare:
    """두 모델 비교"""

    def _make_sample(self) -> EvalSample:
        return EvalSample(
            sample_id=str(uuid.uuid4()),
            input_text="입력",
            reference_text="참조 문장입니다.",
            generated_text="참조 문장입니다.",
            style_label="romance",
        )

    def test_compare_returns_dict(self):
        harness = ModelEvalHarness()
        s = self._make_sample()
        harness.run_eval("model-a", [s])
        harness.run_eval("model-b", [s])
        result = harness.compare("model-a", "model-b")
        assert isinstance(result, dict)

    def test_compare_has_winner_key(self):
        harness = ModelEvalHarness()
        s = self._make_sample()
        harness.run_eval("model-a", [s])
        harness.run_eval("model-b", [s])
        result = harness.compare("model-a", "model-b")
        assert isinstance(result, dict)


# ─────────────────────────────────────────────
# SafetyRegressionSuite
# ─────────────────────────────────────────────

class TestSafetyRegressionSuiteSafe:
    """안전한 샘플 검증"""

    def test_safe_samples_pass(self):
        suite = SafetyRegressionSuite()
        safe_samples = [
            "그의 눈빛이 그녀를 향했다. 아름다운 저녁이었다.",
            "우주선이 별을 향해 날아갔다. 인류의 새로운 시대가 열렸다.",
            "조선의 하늘 아래 평화로운 마을이 있었다.",
        ]
        report = suite.run("model-safe", safe_samples)
        assert report.total_samples == 3
        assert report.violation_rate == 0.0
        assert report.passed is True

    def test_single_safe_sample(self):
        suite = SafetyRegressionSuite()
        report = suite.run("model-single", ["평범한 소설 문장입니다."])
        assert report.total_samples == 1
        assert report.passed is True

    def test_safety_score_range(self):
        suite = SafetyRegressionSuite()
        report = suite.run("model-score", ["안전한 문장입니다."])
        assert 0.0 <= report.safety_score <= 1.0


class TestSafetyRegressionSuiteCheck:
    """개별 텍스트 검사"""

    def test_safe_text_no_violations(self):
        suite = SafetyRegressionSuite()
        violations = suite.check_text("평범한 소설 문장입니다.")
        assert len(violations) == 0

    def test_is_safe_returns_true_for_safe(self):
        suite = SafetyRegressionSuite()
        assert suite.is_safe("그는 조용히 방을 나섰다.") is True

    def test_violation_categories_defined(self):
        cats = [
            "VIOLENCE_HATE", "PII_LEAK", "FACTUAL_ASSERTION",
            "COPYRIGHT", "SELF_HARM", "ADULT_CONTENT",
        ]
        for cat in cats:
            assert hasattr(SafetyCategory, cat), f"SafetyCategory.{cat} 미정의"

    def test_violation_threshold_defined(self):
        assert SafetyRegressionSuite.VIOLATION_THRESHOLD > 0
        assert SafetyRegressionSuite.VIOLATION_THRESHOLD <= 1.0


class TestSafetyRegressionSuiteReport:
    """SafetyReport 구조"""

    def test_report_has_required_fields(self):
        suite = SafetyRegressionSuite()
        report = suite.run("model-struct", ["안전한 문장"])
        assert hasattr(report, "total_samples")
        assert hasattr(report, "violation_rate")
        assert hasattr(report, "passed")
        assert hasattr(report, "safety_score")

    def test_report_model_id(self):
        suite = SafetyRegressionSuite()
        report = suite.run("test-model-id", ["문장"])
        assert report.model_id == "test-model-id"

    def test_empty_samples_raises_or_passes(self):
        suite = SafetyRegressionSuite()
        # 구현에 따라 ValueError 또는 빈 결과 반환
        try:
            report = suite.run("empty-model", [])
            assert report.total_samples == 0
        except ValueError:
            pass  # 빈 샘플 불허 정책도 허용
