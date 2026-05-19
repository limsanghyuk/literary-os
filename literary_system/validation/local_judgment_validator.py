"""
V320: LocalJudgmentValidator
Phase 1B — 로컬 판정 시스템 vs 인간 레이블 Precision/Recall 측정.

핵심 원칙 (최고 프론티어 개발자 지적 반영):
  "GPT critic과 비교하면 안 된다.
   인간 레이블만이 기준."
  
  "Precision >= 0.70, Recall >= 0.65 달성 필수.
   미달 시 임계값 재조정 또는 판정 로직 보정."

구조:
  JudgmentResult      — 단일 씬에 대한 로컬 판정 결과
  ValidationMetrics   — Precision / Recall / F1 / confusion matrix
  LocalJudgmentValidator — 판정 시스템 vs 골드 스탠다드 비교

LLM 0회.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from literary_system.trajectory.reader_simulator import ReaderSimulator
from literary_system.validation.gold_standard_builder import GoldStandardStore, QualityLabel, SceneLabel


@dataclass
class JudgmentResult:
    """로컬 판정 시스템의 단일 씬 판정 결과."""
    scene_id: str
    system_label: QualityLabel      # 시스템이 판정한 레이블
    gold_label: QualityLabel        # 인간이 레이블한 정답
    reader_pull: float
    reader_afterimage: float
    reader_uncertainty: float
    pdi_compliance: bool
    match: bool                     # 시스템 판정 == 골드 레이블
    notes: str = ""


@dataclass
class ValidationMetrics:
    """
    이진 분류 (GOOD vs BAD) 기준 Precision / Recall / F1.
    MARGINAL은 제외.
    """
    total_scenes: int
    true_positives: int     # GOOD이라 판정했고 실제 GOOD
    false_positives: int    # GOOD이라 판정했지만 실제 BAD
    true_negatives: int     # BAD라 판정했고 실제 BAD
    false_negatives: int    # BAD라 판정했지만 실제 GOOD
    precision: float        # TP / (TP + FP)
    recall: float           # TP / (TP + FN)
    f1: float               # 2 * P * R / (P + R)
    accuracy: float         # (TP + TN) / total
    passed_precision: bool  # >= 0.70
    passed_recall: bool     # >= 0.65
    passed: bool            # 둘 다 통과

    PRECISION_THRESHOLD = 0.70
    RECALL_THRESHOLD    = 0.65

    def summary(self) -> dict[str, Any]:
        return {
            "total": self.total_scenes,
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1": round(self.f1, 4),
            "accuracy": round(self.accuracy, 4),
            "passed": self.passed,
            "passed_precision": self.passed_precision,
            "passed_recall": self.passed_recall,
            "tp": self.true_positives,
            "fp": self.false_positives,
            "tn": self.true_negatives,
            "fn": self.false_negatives,
        }


class LocalJudgmentValidator:
    """
    Phase 1B: 로컬 판정 시스템 검증기.

    ReaderSimulator의 3지표(reader_pull, afterimage, uncertainty)와
    임계값 기반으로 씬을 GOOD/BAD로 분류하고,
    골드 스탠다드와 비교하여 Precision/Recall을 측정.
    """

    # 기본 임계값 (Phase 2 실측 후 조정 가능)
    DEFAULT_THRESHOLDS = {
        "reader_pull_min":        0.40,   # 이 이상이면 GOOD 후보
        "reader_afterimage_min":  0.35,
        "reader_uncertainty_max": 0.75,   # 이 이하면 GOOD 후보
        "pdi_required":           True,
    }

    def __init__(
        self,
        reader_simulator: ReaderSimulator | None = None,
        thresholds: dict[str, Any] | None = None,
    ):
        self.reader_simulator = reader_simulator or ReaderSimulator()
        self.thresholds = thresholds or self.DEFAULT_THRESHOLDS.copy()

    def judge_scene(self, scene: SceneLabel) -> JudgmentResult:
        """단일 씬을 로컬 판정 시스템으로 평가."""
        # ReaderSimulator 3지표 측정
        est = self.reader_simulator.estimate(scene.scene_text)
        pull       = est.reader_pull
        afterimage = est.reader_afterimage
        uncertainty= est.reader_uncertainty

        # PDI (간단한 rule-based — V312 엔진 내부 기준과 동일)
        pdi = self._check_pdi(scene.scene_text)

        # 분류 로직
        is_good = (
            pull       >= self.thresholds["reader_pull_min"] and
            afterimage >= self.thresholds["reader_afterimage_min"] and
            uncertainty<= self.thresholds["reader_uncertainty_max"] and
            (not self.thresholds["pdi_required"] or pdi)
        )
        system_label = QualityLabel.GOOD if is_good else QualityLabel.BAD
        match = (system_label == scene.label)

        return JudgmentResult(
            scene_id=scene.scene_id,
            system_label=system_label,
            gold_label=scene.label,
            reader_pull=round(pull, 4),
            reader_afterimage=round(afterimage, 4),
            reader_uncertainty=round(uncertainty, 4),
            pdi_compliance=pdi,
            match=match,
        )

    def validate_store(
        self,
        store: GoldStandardStore,
    ) -> tuple[ValidationMetrics, list[JudgmentResult]]:
        """
        골드 스탠다드 스토어 전체에 대해 검증 실행.
        MARGINAL 레이블은 제외.
        """
        validatable = store.filter_for_validation()
        results: list[JudgmentResult] = []
        for scene in validatable:
            r = self.judge_scene(scene)
            results.append(r)

        metrics = self._compute_metrics(results)
        return metrics, results

    def adjust_thresholds(
        self,
        metrics: ValidationMetrics,
        results: list[JudgmentResult],
    ) -> dict[str, Any]:
        """
        미달 시 임계값 자동 조정 제안.
        실제 조정은 개발자가 확인 후 적용.
        """
        suggestions = {}

        if not metrics.passed_precision:
            # FP 많음 → reader_pull 임계값 높이기
            fp_pulls = [r.reader_pull for r in results
                        if r.system_label == QualityLabel.GOOD and r.gold_label == QualityLabel.BAD]
            if fp_pulls:
                new_threshold = round(max(fp_pulls) + 0.02, 2)
                suggestions["reader_pull_min"] = min(new_threshold, 0.65)
                suggestions["reason_precision"] = (
                    f"FP {metrics.false_positives}건 감소 위해 "
                    f"reader_pull_min을 {self.thresholds['reader_pull_min']} → {suggestions['reader_pull_min']} 상향 제안"
                )

        if not metrics.passed_recall:
            # FN 많음 → reader_pull 임계값 낮추기
            fn_pulls = [r.reader_pull for r in results
                        if r.system_label == QualityLabel.BAD and r.gold_label == QualityLabel.GOOD]
            if fn_pulls:
                new_threshold = round(min(fn_pulls) - 0.02, 2)
                suggestions["reader_pull_min"] = max(new_threshold, 0.20)
                suggestions["reason_recall"] = (
                    f"FN {metrics.false_negatives}건 감소 위해 "
                    f"reader_pull_min을 {self.thresholds['reader_pull_min']} → {suggestions.get('reader_pull_min', '?')} 하향 제안"
                )

        return suggestions

    def apply_threshold_adjustment(self, adjustments: dict[str, Any]) -> None:
        """임계값 조정 적용."""
        for k, v in adjustments.items():
            if k in self.thresholds:
                self.thresholds[k] = v

    # ── 내부 헬퍼 ──────────────────────────────────────────────────

    def _check_pdi(self, text: str) -> bool:
        """PDI 간이 판정 — 직접 감정 표현 비율 검사."""
        direct_emotion = [
            "슬펐다", "화가 났다", "기뻤다", "두려웠다", "놀랐다",
            "그녀는 울었다", "그는 울었다", "깨달았다", "이상하게도",
            "왠지 모르게", "배신의 공기"
        ]
        words = text.split()
        total = max(len(words), 1)
        direct_count = sum(text.count(expr) for expr in direct_emotion)
        direct_ratio = direct_count / total
        return direct_ratio < 0.05  # 5% 미만이면 PDI 준수

    def _compute_metrics(self, results: list[JudgmentResult]) -> ValidationMetrics:
        """Precision / Recall / F1 계산."""
        tp = sum(1 for r in results
                 if r.system_label == QualityLabel.GOOD and r.gold_label == QualityLabel.GOOD)
        fp = sum(1 for r in results
                 if r.system_label == QualityLabel.GOOD and r.gold_label == QualityLabel.BAD)
        tn = sum(1 for r in results
                 if r.system_label == QualityLabel.BAD and r.gold_label == QualityLabel.BAD)
        fn = sum(1 for r in results
                 if r.system_label == QualityLabel.BAD and r.gold_label == QualityLabel.GOOD)

        precision = tp / max(tp + fp, 1)
        recall    = tp / max(tp + fn, 1)
        f1        = 2 * precision * recall / max(precision + recall, 1e-9)
        accuracy  = (tp + tn) / max(len(results), 1)

        return ValidationMetrics(
            total_scenes=len(results),
            true_positives=tp,
            false_positives=fp,
            true_negatives=tn,
            false_negatives=fn,
            precision=round(precision, 4),
            recall=round(recall, 4),
            f1=round(f1, 4),
            accuracy=round(accuracy, 4),
            passed_precision=precision >= ValidationMetrics.PRECISION_THRESHOLD,
            passed_recall=recall >= ValidationMetrics.RECALL_THRESHOLD,
            passed=(precision >= ValidationMetrics.PRECISION_THRESHOLD and
                    recall    >= ValidationMetrics.RECALL_THRESHOLD),
        )
