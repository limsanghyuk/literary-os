"""
V551 — PNECore: PredictiveNarrativeEngine 핵심 누적기
======================================================
설계도 §5.1 기준:
  - AutoRepair ExecutionResult 스트림을 받아 RepairOutcome 리스트로 정규화
  - PatternLibrary에 카테고리별 성공/실패 카운트·severity 분포 누적
  - 학습 피처 벡터 생성 (DebtPredictor V552 입력)

LLM-0 정책 준수: 외부 LLM 호출 없음
"""

from __future__ import annotations

import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# ─── 도메인 타입 ───────────────────────────────────────────────────────────────

@dataclass
class RepairOutcome:
    """AutoRepair 1건의 정규화된 결과 레코드."""
    scene_id:         str
    recommendation_id: str
    category:         str          # DebtItem.category 값
    severity:         float        # DebtItem.severity 0.0~1.0
    success:          bool         # ExecutionStatus.APPROVED → True
    blast_ratio:      float = 0.0  # SafetyAugmentedAutoRepair blast_ratio (옵션)


@dataclass
class CategoryStats:
    """카테고리별 누적 통계."""
    category:       str
    total:          int   = 0
    success_count:  int   = 0
    fail_count:     int   = 0
    severities:     List[float] = field(default_factory=list)
    blast_ratios:   List[float] = field(default_factory=list)

    def success_rate(self) -> float:
        return round(self.success_count / max(self.total, 1), 4)

    def mean_severity(self) -> float:
        return round(statistics.mean(self.severities), 4) if self.severities else 0.0

    def mean_blast(self) -> float:
        return round(statistics.mean(self.blast_ratios), 4) if self.blast_ratios else 0.0


class PatternLibrary:
    """카테고리별 RepairOutcome 누적 패턴 저장소."""

    def __init__(self) -> None:
        self._stats: Dict[str, CategoryStats] = {}
        self._outcomes: List[RepairOutcome] = []

    # ── 누적 ─────────────────────────────────────────────────────────────────

    def record(self, outcome: RepairOutcome) -> None:
        """단일 RepairOutcome을 패턴 라이브러리에 누적."""
        cat = outcome.category
        if cat not in self._stats:
            self._stats[cat] = CategoryStats(category=cat)

        st = self._stats[cat]
        st.total += 1
        if outcome.success:
            st.success_count += 1
        else:
            st.fail_count += 1
        st.severities.append(outcome.severity)
        st.blast_ratios.append(outcome.blast_ratio)
        self._outcomes.append(outcome)

    def record_batch(self, outcomes: List[RepairOutcome]) -> None:
        for o in outcomes:
            self.record(o)

    # ── 조회 ─────────────────────────────────────────────────────────────────

    def get_stats(self, category: str) -> Optional[CategoryStats]:
        return self._stats.get(category)

    def all_stats(self) -> Dict[str, CategoryStats]:
        return dict(self._stats)

    def total_outcomes(self) -> int:
        return len(self._outcomes)

    def all_outcomes(self) -> List[RepairOutcome]:
        return list(self._outcomes)

    def feature_vector(self, category: str) -> List[float]:
        """DebtPredictor 학습용 피처 벡터 [success_rate, mean_severity, mean_blast, total_log]."""
        import math
        st = self._stats.get(category)
        if st is None or st.total == 0:
            return [0.0, 0.0, 0.0, 0.0]
        return [
            st.success_rate(),
            st.mean_severity(),
            st.mean_blast(),
            round(math.log1p(st.total), 4),
        ]

    def global_feature_vector(self) -> List[float]:
        """전체 카테고리 통합 피처 벡터."""
        import math
        all_outcomes = self._outcomes
        if not all_outcomes:
            return [0.0, 0.0, 0.0, 0.0]
        total = len(all_outcomes)
        success = sum(1 for o in all_outcomes if o.success)
        mean_sev = statistics.mean(o.severity for o in all_outcomes)
        mean_blast = statistics.mean(o.blast_ratio for o in all_outcomes)
        return [
            round(success / total, 4),
            round(mean_sev, 4),
            round(mean_blast, 4),
            round(math.log1p(total), 4),
        ]


# ─── PNECore ──────────────────────────────────────────────────────────────────

class PNECore:
    """
    PredictiveNarrativeEngine 핵심 누적기 (V551).

    AutoRepairExecutor.execute() / execute_batch() 결과를 받아
    PatternLibrary에 누적하고 학습 피처를 제공한다.

    사용 예::

        core = PNECore()
        core.ingest_execution_result(exec_result, debt_item)
        fv = core.feature_vector("unresolved_secret")
    """

    def __init__(self, library: Optional[PatternLibrary] = None) -> None:
        self._library = library if library is not None else PatternLibrary()

    # ── 주입 API ─────────────────────────────────────────────────────────────

    def ingest_execution_result(
        self,
        exec_result,          # ExecutionResult (auto_repair_executor)
        debt_item,            # DebtItem (narrative_debt_detector)
        blast_ratio: float = 0.0,
    ) -> RepairOutcome:
        """
        ExecutionResult + DebtItem 쌍을 RepairOutcome으로 변환 후 누적.

        Parameters
        ----------
        exec_result : ExecutionResult
            AutoRepairExecutor.execute() 반환값
        debt_item : DebtItem
            해당 수리 요청의 원본 DebtItem
        blast_ratio : float
            SafetyAugmentedAutoRepair의 blast_ratio (없으면 0.0)
        """
        outcome = RepairOutcome(
            scene_id=exec_result.scene_id,
            recommendation_id=exec_result.recommendation_id,
            category=str(debt_item.category),
            severity=float(debt_item.severity),
            success=exec_result.ok(),
            blast_ratio=float(blast_ratio),
        )
        self._library.record(outcome)
        return outcome

    def ingest_outcome(self, outcome: RepairOutcome) -> None:
        """직접 생성한 RepairOutcome을 누적 (테스트·외부 주입용)."""
        self._library.record(outcome)

    def ingest_outcomes(self, outcomes: List[RepairOutcome]) -> None:
        self._library.record_batch(outcomes)

    # ── 조회 API ─────────────────────────────────────────────────────────────

    @property
    def library(self) -> PatternLibrary:
        return self._library

    def feature_vector(self, category: str) -> List[float]:
        """카테고리별 4차원 피처 벡터."""
        return self._library.feature_vector(category)

    def global_feature_vector(self) -> List[float]:
        """전체 4차원 피처 벡터."""
        return self._library.global_feature_vector()

    def category_stats(self, category: str) -> Optional[CategoryStats]:
        return self._library.get_stats(category)

    def total_ingested(self) -> int:
        return self._library.total_outcomes()

    def snapshot(self) -> Dict:
        """현재 누적 상태 스냅샷 (직렬화용)."""
        stats = self._library.all_stats()
        return {
            cat: {
                "total": st.total,
                "success_rate": st.success_rate(),
                "mean_severity": st.mean_severity(),
                "mean_blast": st.mean_blast(),
            }
            for cat, st in stats.items()
        }
