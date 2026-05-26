"""
meta_learner_cycle.py — MetaLearnerCycle V642 (ADR-102)

V641 대비 변경사항:
  - CycleReport.augmentation_batch 필드 추가 (Optional[AugmentationBatch])
  - run_cycle() sample_texts 파라미터 추가 → DataAugmentationController.augment() 실 호출
  - AlphaStability 데이터클래스 + alpha_stability() 메서드 추가
  - ALPHA_STABILITY_MAX_VAR 상수 추가

SP-C.1 Constitution v2.0 MetaLearner 4사이클 래퍼.
blueprint v2.0 §2.2 + 목표 A1: R(scene)≥0.78, Krippendorff α≥0.70.

역할:
  1. MetaLearner (nie/) outer-loop 1사이클 실행
  2. Krippendorff α 평가자 간 신뢰도 측정 (1차)
  3. DataAugmentationController 연계: augment_ratio 동적 조정 + 실제 augment() 호출
  4. FeedbackIntegrator 연계: 피드백 신호를 MetaLearner 이득으로 변환
  5. [V642 신규] α 안정성 측정: 다사이클 간 α 분산 추적

설계 원칙:
  - LLM-0 준수 (외부 API 없음)
  - 순수 Python 표준 라이브러리
  - 기존 MetaLearner / DataAugmentationController / FeedbackIntegrator 비침투적 통합
"""
from __future__ import annotations

import logging
import statistics
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

from literary_system.nie.meta_learner import (
    MetaLearner, MetaState, MetaUpdateResult,
    ACTIVATION_WORKS, META_LR,
)
from literary_system.constitution.krippendorff_alpha import (
    KrippendorffAlpha, AlphaResult, ALPHA_MIN_THRESHOLD, METRIC_INTERVAL,
)
from literary_system.constitution.data_augmentation_controller import (
    DataAugmentationController, AugmentationBatch, DEFAULT_AUGMENT_RATIO,
)
from literary_system.constitution.feedback_integrator import (
    FeedbackIntegrator, IntegrationResult,
)

logger = logging.getLogger(__name__)

# ─── 상수 ─────────────────────────────────────────────────────────────────────
CYCLE_COUNT: int = 4          # 총 사이클 수 (V641~V644)
R_SCENE_TARGET: float = 0.78  # Constitution v2.0 §A1 R(scene) 목표
ALPHA_TARGET: float = 0.70    # Krippendorff α 합격 임계값

# augment_ratio 조정 보폭
AUGMENT_RATIO_STEP: float = 0.02
AUGMENT_RATIO_MIN: float = 0.05
AUGMENT_RATIO_MAX: float = 0.40

# α 조건 기반 augment 비율 조정
AUGMENT_RATIO_BOOST_THRESHOLD: float  = 0.65   # α 이하 → 증강 강화
AUGMENT_RATIO_REDUCE_THRESHOLD: float = 0.80   # α 이상 → 증강 완화

# [V642 신규] α 안정성 상수
ALPHA_STABILITY_MAX_VAR: float = 0.01  # α 분산 허용 최대값 (안정 기준)
ALPHA_STABILITY_MIN_CYCLES: int = 2    # 안정성 측정 최소 사이클 수

# DataAugmentationController augment() 호출 기본 파라미터
DEFAULT_AUGMENT_COUNT_PER_CYCLE: int = 3
CYCLE_AUGMENT_DATASET_ID_PREFIX: str = "cycle-aug"


# ─── 결과 데이터 클래스 ───────────────────────────────────────────────────────
@dataclass
class AlphaStability:
    """[V642 신규] 다사이클 간 Krippendorff α 안정성 측정 결과."""
    cycle_count: int          # 측정에 사용된 사이클 수
    alpha_values: List[float] # 각 사이클의 α 값 목록
    mean_alpha: float         # 평균 α
    variance: float           # α 분산
    is_stable: bool           # 분산 < ALPHA_STABILITY_MAX_VAR 여부

    @property
    def summary(self) -> str:
        status = "STABLE" if self.is_stable else "UNSTABLE"
        return (
            f"[AlphaStability] {status} "
            f"cycles={self.cycle_count} "
            f"mean={self.mean_alpha:.4f} "
            f"var={self.variance:.6f} "
            f"threshold={ALPHA_STABILITY_MAX_VAR}"
        )


@dataclass
class CycleReport:
    """1 MetaLearner 사이클 실행 결과."""
    cycle_number: int          # 1~4
    meta_update: Optional[MetaUpdateResult]
    alpha_result: Optional[AlphaResult]
    feedback_result: Optional[IntegrationResult]
    augment_ratio_before: float
    augment_ratio_after: float
    r_scene_trend: str         # "improving" | "stable" | "declining"
    notes: List[str] = field(default_factory=list)
    # [V642 신규] DataAugmentationController.augment() 결과
    augmentation_batch: Optional[AugmentationBatch] = None

    @property
    def alpha_passed(self) -> bool:
        return self.alpha_result is not None and self.alpha_result.passed

    @property
    def r_trend_positive(self) -> bool:
        return self.r_scene_trend in ("improving", "stable")

    @property
    def passed(self) -> bool:
        """사이클 합격 조건: α PASS + R 추세 양수."""
        return self.alpha_passed and self.r_trend_positive

    @property
    def augmentation_performed(self) -> bool:
        """[V642 신규] 이번 사이클에 실제 증강이 수행되었는지 여부."""
        return self.augmentation_batch is not None and self.augmentation_batch.augmented_count > 0

    @property
    def summary(self) -> str:
        alpha_str = (
            f"α={self.alpha_result.alpha:.4f}[{'PASS' if self.alpha_passed else 'FAIL'}]"
            if self.alpha_result else "α=N/A"
        )
        meta_str = (
            f"advantage={self.meta_update.advantage:+.4f}"
            if self.meta_update else "meta=N/A"
        )
        aug_str = f"aug_ratio:{self.augment_ratio_before:.3f}→{self.augment_ratio_after:.3f}"
        aug_batch_str = (
            f"aug_batch={self.augmentation_batch.augmented_count}samples"
            if self.augmentation_batch else "aug_batch=none"
        )
        status = "CYCLE_PASS" if self.passed else "CYCLE_FAIL"
        return (
            f"[Cycle {self.cycle_number}] {status} | "
            f"{alpha_str} | {meta_str} | R_trend={self.r_scene_trend} | "
            f"{aug_str} | {aug_batch_str}"
        )


# ─── MetaLearnerCycle ─────────────────────────────────────────────────────────
class MetaLearnerCycle:
    """
    Constitution v2.0 MetaLearner 4사이클 래퍼 (V641→V642, ADR-101/102).

    V642 추가 기능:
      - run_cycle() sample_texts 파라미터: DataAugmentationController.augment() 실 호출
      - alpha_stability(): 다사이클 간 α 분산 측정
      - CycleReport.augmentation_batch: 실제 증강 배치 결과 포함

    4개 V버전(V641~V644)에서 각각 1사이클씩 호출된다.
    각 사이클은:
      1. MetaLearner outer-loop 갱신
      2. Krippendorff α 측정
      3. DataAugmentationController augment_ratio 조정 + 실제 augment() 호출 [V642]
      4. FeedbackIntegrator 신호를 MetaLearner 이득으로 반영
    """

    def __init__(
        self,
        meta_learner: Optional[MetaLearner] = None,
        augmentation_controller: Optional[DataAugmentationController] = None,
        feedback_integrator: Optional[FeedbackIntegrator] = None,
        alpha_metric: str = METRIC_INTERVAL,
    ) -> None:
        self._meta = meta_learner or MetaLearner()
        self._augmentor = augmentation_controller or DataAugmentationController()
        self._feedback = feedback_integrator or FeedbackIntegrator()
        self._alpha_calc = KrippendorffAlpha(metric=alpha_metric)
        self._cycle_history: List[CycleReport] = []
        self._r_scene_history: List[float] = []
        self._current_augment_ratio: float = 0.15  # DEFAULT_AUGMENT_RATIO

    # ── 공개 API ───────────────────────────────────────────────────────────────
    @property
    def current_cycle(self) -> int:
        return len(self._cycle_history) + 1

    @property
    def cycle_history(self) -> List[CycleReport]:
        return list(self._cycle_history)

    @property
    def meta_state(self) -> MetaState:
        return self._meta.state

    def run_cycle(
        self,
        l_final: float,
        rater_data: Optional[Dict[str, Dict[str, Optional[float]]]] = None,
        r_scene: Optional[float] = None,
        *,
        cycle_number: Optional[int] = None,
        sample_texts: Optional[List[str]] = None,
    ) -> CycleReport:
        """
        1 MetaLearner 사이클 실행.

        Args:
            l_final: 이번 사이클의 최종 손실값 (MetaLearner outer-loop 입력)
            rater_data: Krippendorff α 계산용 평가자 데이터
                        {rater_id: {unit_id: score}} — None이면 α 측정 스킵
            r_scene: 씬 품질 점수 (R(scene)) — 추세 판단용
            cycle_number: 강제 지정 (없으면 auto-increment)
            sample_texts: [V642 신규] 증강 대상 텍스트 목록.
                          제공 시 DataAugmentationController.augment() 실제 호출.
        """
        cyc = cycle_number if cycle_number is not None else self.current_cycle
        aug_before = self._current_augment_ratio  # 현재 비율 스냅샷

        # 1. MetaLearner outer-loop
        self._meta.record_work_loss(l_final)
        meta_result = self._meta.maybe_meta_update()

        # 2. Krippendorff α 측정
        alpha_result: Optional[AlphaResult] = None
        if rater_data is not None:
            alpha_result = self._alpha_calc.compute(rater_data)
            logger.info(alpha_result.summary)

        # 3. R(scene) 추세 판단
        if r_scene is not None:
            self._r_scene_history.append(r_scene)
        r_trend = self._compute_r_trend()

        # 4. augment_ratio 조정 (α 결과 기반)
        aug_after = self._adjust_augment_ratio(alpha_result, aug_before)

        # 5. [V642 신규] DataAugmentationController.augment() 실제 호출
        augmentation_batch: Optional[AugmentationBatch] = None
        if sample_texts:
            dataset_id = f"{CYCLE_AUGMENT_DATASET_ID_PREFIX}-{cyc}"
            augmentation_batch = self._augmentor.augment(
                dataset_id=dataset_id,
                texts=sample_texts,
                augment_count=DEFAULT_AUGMENT_COUNT_PER_CYCLE,
                augment_ratio=aug_after,
                controller_id=f"meta_learner_cycle_{cyc}",
                note=f"V642 cycle {cyc} auto-augment",
            )
            logger.info(
                f"[Cycle {cyc}] DataAugmentationController.augment() 호출 완료: "
                f"{augmentation_batch.summary()}"
            )

        # 6. FeedbackIntegrator → MetaLearner 이득 반영
        feedback_result: Optional[IntegrationResult] = None
        if self._feedback.feedbacks:
            feedback_result = self._feedback.integrate()
            # 피드백 보정 신호가 있으면 MetaLearner 손실에 반영
            if feedback_result and feedback_result.avg_correction_delta != 0.0:
                adjusted_loss = l_final + feedback_result.avg_correction_delta * 0.1
                self._meta.record_work_loss(adjusted_loss)
                logger.debug(
                    f"FeedbackIntegrator 보정: {feedback_result.avg_correction_delta:+.4f} "
                    f"→ adjusted_loss={adjusted_loss:.4f}"
                )

        # 7. CycleReport 생성
        notes: List[str] = []
        if meta_result is not None:
            notes.append(f"MetaUpdate: {meta_result.updates}")
        if alpha_result and not alpha_result.passed:
            notes.append(f"α={alpha_result.alpha:.4f} < 임계값 {ALPHA_TARGET} — 증강 강화")
        if r_trend == "declining":
            notes.append("R(scene) 하락 추세 감지")
        if augmentation_batch is not None:
            notes.append(
                f"증강 완료: {augmentation_batch.augmented_count}개 샘플 "
                f"(ratio={aug_after:.3f})"
            )

        report = CycleReport(
            cycle_number=cyc,
            meta_update=meta_result,
            alpha_result=alpha_result,
            feedback_result=feedback_result,
            augment_ratio_before=aug_before,
            augment_ratio_after=aug_after,
            r_scene_trend=r_trend,
            notes=notes,
            augmentation_batch=augmentation_batch,
        )
        self._cycle_history.append(report)
        logger.info(report.summary)
        return report

    def run_n_cycles(
        self,
        l_finals: Sequence[float],
        rater_data_list: Optional[Sequence[Optional[Dict[str, Dict[str, Optional[float]]]]]] = None,
        r_scenes: Optional[Sequence[Optional[float]]] = None,
        sample_texts_list: Optional[Sequence[Optional[List[str]]]] = None,
    ) -> List[CycleReport]:
        """여러 사이클 순차 실행 (V645 통합 검증용).
        
        [V642 신규] sample_texts_list 파라미터 추가 — 사이클별 증강 텍스트 지정.
        """
        reports = []
        for i, lf in enumerate(l_finals):
            rd = rater_data_list[i] if rater_data_list and i < len(rater_data_list) else None
            rs = r_scenes[i] if r_scenes and i < len(r_scenes) else None
            st = sample_texts_list[i] if sample_texts_list and i < len(sample_texts_list) else None
            reports.append(
                self.run_cycle(lf, rd, rs, cycle_number=i + 1, sample_texts=st)
            )
        return reports

    def alpha_history(self) -> List[AlphaResult]:
        """기록된 모든 α 결과 반환."""
        return [r.alpha_result for r in self._cycle_history if r.alpha_result is not None]

    def latest_alpha(self) -> Optional[AlphaResult]:
        history = self.alpha_history()
        return history[-1] if history else None

    def alpha_stability(self) -> Optional[AlphaStability]:
        """[V642 신규] 다사이클 간 Krippendorff α 안정성 측정.
        
        Returns:
            AlphaStability 객체 (α 기록이 ALPHA_STABILITY_MIN_CYCLES 미만이면 None).
        """
        history = self.alpha_history()
        if len(history) < ALPHA_STABILITY_MIN_CYCLES:
            return None

        alpha_values = [r.alpha for r in history]
        mean_alpha = statistics.mean(alpha_values)
        # 분산: 편차 제곱의 평균 (population variance)
        variance = statistics.pvariance(alpha_values)
        is_stable = variance < ALPHA_STABILITY_MAX_VAR

        result = AlphaStability(
            cycle_count=len(history),
            alpha_values=alpha_values,
            mean_alpha=mean_alpha,
            variance=variance,
            is_stable=is_stable,
        )
        logger.info(result.summary)
        return result

    def latest_augmentation_batch(self) -> Optional[AugmentationBatch]:
        """[V642 신규] 가장 최근 사이클의 AugmentationBatch 반환."""
        for report in reversed(self._cycle_history):
            if report.augmentation_batch is not None:
                return report.augmentation_batch
        return None

    def augmentation_batch_history(self) -> List[AugmentationBatch]:
        """[V642 신규] 증강이 수행된 모든 사이클의 AugmentationBatch 목록."""
        return [
            r.augmentation_batch
            for r in self._cycle_history
            if r.augmentation_batch is not None
        ]

    # ── 내부 헬퍼 ─────────────────────────────────────────────────────────────
    def _compute_r_trend(self) -> str:
        h = self._r_scene_history
        if len(h) < 2:
            return "stable"
        recent = h[-1]
        prev = h[-2]
        diff = recent - prev
        if diff > 0.01:
            return "improving"
        if diff < -0.01:
            return "declining"
        return "stable"

    def _adjust_augment_ratio(
        self, alpha_result: Optional[AlphaResult], current_ratio: float
    ) -> float:
        """α 결과에 따라 DataAugmentationController의 augment_ratio를 조정."""
        if alpha_result is None:
            return current_ratio

        if alpha_result.alpha < AUGMENT_RATIO_BOOST_THRESHOLD:
            # α 낮음 → 증강 강화 (더 많은 훈련 데이터 필요)
            new_ratio = min(current_ratio + AUGMENT_RATIO_STEP, AUGMENT_RATIO_MAX)
        elif alpha_result.alpha >= AUGMENT_RATIO_REDUCE_THRESHOLD:
            # α 충분히 높음 → 증강 완화 (과적합 방지)
            new_ratio = max(current_ratio - AUGMENT_RATIO_STEP, AUGMENT_RATIO_MIN)
        else:
            # α 허용 범위 → 유지
            new_ratio = current_ratio

        if abs(new_ratio - current_ratio) > 1e-9:
            self._current_augment_ratio = new_ratio
            logger.debug(
                f"augment_ratio 조정: {current_ratio:.3f} → {new_ratio:.3f} "
                f"(α={alpha_result.alpha:.4f})"
            )
        return new_ratio
