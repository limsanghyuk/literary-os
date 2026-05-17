"""
V323 - LearnedCoefficientStore  (Phase 2)
씬 판단 누적 -> DRSE 계수 자동 갱신.

설계 원칙 (CSA/CSC/CPE 합의):
  - update_interval 씬마다 학습 갱신 (기본 100, 테스트용 최소 1)
  - 학습 대상 계수:
      DRSE: decay_lambda, arc_pressure_boost, residue_boost, residue_min_s
      Validator: reader_pull_min, reader_afterimage_min, reader_uncertainty_max
  - 안전 범위(clamp) 강제 - 수렴 발산 방지
  - to_json() / from_json_inplace() -> SnapshotManager 연동
  - LLM 0회. 완전 로컬.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any


# ================================================================
# CoefficientRecord - 단일 씬 학습 레코드
# ================================================================

@dataclass
class CoefficientRecord:
    """단일 씬 판단 결과 레코드."""
    scene_id: str
    judgment_label: str
    gold_label: str
    reader_pull: float
    reader_afterimage: float
    reader_uncertainty: float
    final_drse_score: float
    metadata: dict = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    @property
    def is_match(self) -> bool:
        return self.judgment_label == self.gold_label

    @property
    def is_good(self) -> bool:
        return self.judgment_label == "GOOD"

    @property
    def is_bad(self) -> bool:
        return self.judgment_label == "BAD"

    def to_dict(self) -> dict:
        return {
            "scene_id": self.scene_id,
            "judgment_label": self.judgment_label,
            "gold_label": self.gold_label,
            "reader_pull": self.reader_pull,
            "reader_afterimage": self.reader_afterimage,
            "reader_uncertainty": self.reader_uncertainty,
            "final_drse_score": self.final_drse_score,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "CoefficientRecord":
        return cls(
            scene_id=d["scene_id"],
            judgment_label=d["judgment_label"],
            gold_label=d["gold_label"],
            reader_pull=d["reader_pull"],
            reader_afterimage=d["reader_afterimage"],
            reader_uncertainty=d["reader_uncertainty"],
            final_drse_score=d["final_drse_score"],
            metadata=d.get("metadata", {}),
            timestamp=d.get("timestamp", time.time()),
        )


# ================================================================
# LearnedCoefficients - 학습된 계수 세트
# ================================================================

@dataclass
class LearnedCoefficients:
    """
    DRSE 엔진 + LocalJudgmentValidator 에 적용할 학습된 계수.

    안전 범위:
      decay_lambda          [0.001, 0.5]
      arc_pressure_boost    [1.0,   2.5]
      residue_boost         [1.0,   3.0]
      residue_min_s         [0.05,  0.40]
      reader_pull_min       [0.20,  0.70]
      reader_afterimage_min [0.10,  0.60]
      reader_uncertainty_max[0.50,  0.95]
    """
    decay_lambda: float = 0.05
    arc_pressure_boost: float = 1.2
    residue_boost: float = 1.5
    residue_min_s: float = 0.15
    reader_pull_min: float = 0.40
    reader_afterimage_min: float = 0.35
    reader_uncertainty_max: float = 0.75
    version: int = 0
    scenes_processed: int = 0
    last_updated: float = field(default_factory=time.time)

    CLAMP_RANGES = {
        "decay_lambda":             (0.001, 0.500),
        "arc_pressure_boost":       (1.000, 2.500),
        "residue_boost":            (1.000, 3.000),
        "residue_min_s":            (0.050, 0.400),
        "reader_pull_min":          (0.200, 0.700),
        "reader_afterimage_min":    (0.100, 0.600),
        "reader_uncertainty_max":   (0.500, 0.950),
    }

    def __post_init__(self) -> None:
        self.clamp_all()

    def clamp_all(self) -> None:
        for attr, (lo, hi) in self.CLAMP_RANGES.items():
            val = getattr(self, attr)
            setattr(self, attr, max(lo, min(hi, val)))

    def to_dict(self) -> dict:
        return {
            "decay_lambda": self.decay_lambda,
            "arc_pressure_boost": self.arc_pressure_boost,
            "residue_boost": self.residue_boost,
            "residue_min_s": self.residue_min_s,
            "reader_pull_min": self.reader_pull_min,
            "reader_afterimage_min": self.reader_afterimage_min,
            "reader_uncertainty_max": self.reader_uncertainty_max,
            "version": self.version,
            "scenes_processed": self.scenes_processed,
            "last_updated": self.last_updated,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "LearnedCoefficients":
        obj = cls.__new__(cls)
        obj.decay_lambda = d.get("decay_lambda", 0.05)
        obj.arc_pressure_boost = d.get("arc_pressure_boost", 1.2)
        obj.residue_boost = d.get("residue_boost", 1.5)
        obj.residue_min_s = d.get("residue_min_s", 0.15)
        obj.reader_pull_min = d.get("reader_pull_min", 0.40)
        obj.reader_afterimage_min = d.get("reader_afterimage_min", 0.35)
        obj.reader_uncertainty_max = d.get("reader_uncertainty_max", 0.75)
        obj.version = d.get("version", 0)
        obj.scenes_processed = d.get("scenes_processed", 0)
        obj.last_updated = d.get("last_updated", time.time())
        obj.clamp_all()
        return obj


# ================================================================
# LearnedCoefficientStore - 누적 학습 스토어
# ================================================================

class LearnedCoefficientStore:
    """
    씬 판단 레코드를 누적하여 DRSE 계수를 자동 갱신.

    갱신 전략 (최소 침습 원칙):
      - precision 낮음 (FP 많음) -> reader_pull_min 상향 (+step)
      - recall 낮음 (FN 많음)   -> reader_pull_min 하향 (-step)
      - GOOD 씬 평균 drse_score 높음 -> residue_boost / arc_pressure_boost 소폭 상향
      - GOOD 씬 평균 drse_score 낮음 -> decay_lambda 소폭 하향 (더 느린 감쇠)
      - 모든 갱신은 step 단위로 점진적으로

    update_interval=1 허용 -> 테스트 환경 지원
    """

    STEP_SMALL = 0.02
    STEP_MID   = 0.05
    PRECISION_TARGET = 0.70
    RECALL_TARGET    = 0.65

    def __init__(self, update_interval: int = 100):
        self._interval = max(1, update_interval)
        self._records = []
        self._coefficients = LearnedCoefficients()
        self._updates_count = 0
        self._last_update_at = 0

    # -- 핵심 API --------------------------------------------------

    def record(self, rec: CoefficientRecord) -> None:
        """씬 레코드 추가. interval 도달 시 자동 갱신."""
        self._records.append(rec)
        if len(self._records) - self._last_update_at >= self._interval:
            self._do_update()

    def maybe_update(self) -> bool:
        """interval 미달이면 False, 달성 시 갱신 후 True."""
        pending = len(self._records) - self._last_update_at
        if pending >= self._interval:
            self._do_update()
            return True
        return False

    def force_update(self) -> None:
        """레코드 수와 무관하게 즉시 갱신."""
        self._do_update()

    def get_coefficients(self) -> LearnedCoefficients:
        return self._coefficients

    def apply_to_validator(self, validator) -> None:
        """LocalJudgmentValidator 임계값 갱신."""
        c = self._coefficients
        validator.thresholds["reader_pull_min"] = c.reader_pull_min
        validator.thresholds["reader_afterimage_min"] = c.reader_afterimage_min
        validator.thresholds["reader_uncertainty_max"] = c.reader_uncertainty_max

    def apply_to_drse_scorer(self, scorer) -> None:
        """DRSEScorer 계수 갱신."""
        c = self._coefficients
        scorer.DECAY_LAMBDA = c.decay_lambda
        scorer.ARC_PRESSURE_BOOST = c.arc_pressure_boost
        scorer.RESIDUE_BOOST = c.residue_boost
        scorer.RESIDUE_MIN_S = c.residue_min_s

    def clear_records(self) -> None:
        """누적 레코드 초기화 (계수는 유지)."""
        self._records = []
        self._last_update_at = 0

    # -- 상태 조회 -------------------------------------------------

    @property
    def total_records(self) -> int:
        return len(self._records)

    @property
    def updates_count(self) -> int:
        return self._updates_count

    def stats(self) -> dict:
        return {
            "total_records": self.total_records,
            "updates_count": self._updates_count,
            "update_interval": self._interval,
            "pending_until_next_update": max(
                0, self._interval - (len(self._records) - self._last_update_at)
            ),
            "current_coefficients": self._coefficients.to_dict(),
        }

    # -- JSON 직렬화 (SnapshotManager 연동) -----------------------

    def to_json(self) -> str:
        data = {
            "update_interval": self._interval,
            "updates_count": self._updates_count,
            "last_update_at": self._last_update_at,
            "coefficients": self._coefficients.to_dict(),
            "records": [r.to_dict() for r in self._records],
        }
        return json.dumps(data, ensure_ascii=False)

    def from_json_inplace(self, json_str: str) -> None:
        data = json.loads(json_str)
        self._interval = data.get("update_interval", self._interval)
        self._updates_count = data.get("updates_count", 0)
        self._last_update_at = data.get("last_update_at", 0)
        coeff_data = data.get("coefficients", {})
        if coeff_data:
            self._coefficients = LearnedCoefficients.from_dict(coeff_data)
        self._records = [
            CoefficientRecord.from_dict(r)
            for r in data.get("records", [])
        ]

    # -- 내부 갱신 로직 -------------------------------------------

    def _do_update(self) -> None:
        """
        최근 interval 레코드 기반으로 계수 점진 조정.
        최소 침습 원칙: step 단위 점진 조정, 안전 범위 clamp.
        레코드가 없어도 version/updates_count는 반드시 갱신한다 (force_update 지원).
        """
        c = self._coefficients
        window = self._records[self._last_update_at:]

        if not window:
            # 레코드 없어도 버전/카운트 갱신
            c.version += 1
            c.last_updated = time.time()
            self._updates_count += 1
            return

        # -- Precision / Recall 근사 계산 --------------------------
        tp = sum(1 for r in window if r.is_good and r.gold_label == "GOOD")
        fp = sum(1 for r in window if r.is_good and r.gold_label == "BAD")
        fn = sum(1 for r in window if r.is_bad and r.gold_label == "GOOD")

        precision = tp / max(tp + fp, 1)
        recall    = tp / max(tp + fn, 1)

        # -- reader_pull_min 조정 ----------------------------------
        if precision < self.PRECISION_TARGET and fp > 0:
            c.reader_pull_min = min(
                c.reader_pull_min + self.STEP_SMALL,
                LearnedCoefficients.CLAMP_RANGES["reader_pull_min"][1]
            )
        elif recall < self.RECALL_TARGET and fn > 0:
            c.reader_pull_min = max(
                c.reader_pull_min - self.STEP_SMALL,
                LearnedCoefficients.CLAMP_RANGES["reader_pull_min"][0]
            )

        # -- DRSE 계수 조정 ----------------------------------------
        good_records = [r for r in window if r.is_good]

        if good_records:
            avg_good_drse = sum(r.final_drse_score for r in good_records) / len(good_records)
            avg_good_pull = sum(r.reader_pull for r in good_records) / len(good_records)

            if avg_good_drse < 0.3:
                c.decay_lambda = max(
                    c.decay_lambda - self.STEP_SMALL * 0.5,
                    LearnedCoefficients.CLAMP_RANGES["decay_lambda"][0]
                )
            elif avg_good_drse > 0.7:
                c.decay_lambda = min(
                    c.decay_lambda + self.STEP_SMALL * 0.5,
                    LearnedCoefficients.CLAMP_RANGES["decay_lambda"][1]
                )

            if avg_good_pull > 0.7:
                c.residue_boost = min(
                    c.residue_boost + self.STEP_SMALL,
                    LearnedCoefficients.CLAMP_RANGES["residue_boost"][1]
                )

        # -- 계수 버전/메타 갱신 -----------------------------------
        c.version += 1
        c.scenes_processed += len(window)
        c.last_updated = time.time()
        c.clamp_all()

        self._last_update_at = len(self._records)
        self._updates_count += 1
