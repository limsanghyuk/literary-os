"""
ConstitutionEvalV2 — SP-C.1 헌법 멀티축 평가기 (ADR-079)

LLM-0 원칙: 외부 LLM 호출 없음. 순수 Python + LOSDB(JSONL) 영속화.

설계:
- EvalDimension: 평가 차원 정의 (dimension_id, name, weight)
- EvalScore    : 단일 차원 채점 결과 (raw_score 0.0~1.0 + weighted)
- EvalResult   : 전체 평가 결과 (final_score, passed, evaluator_id)
- ConstitutionEvalV2: JSONL append-only 영속화 + batch_evaluate
  - EVAL_THRESHOLD = 0.70 (final_score >= 0.70 -> PASS)
  - DEFAULT_DIMENSIONS: coherence, authenticity, style_adherence,
                         emotional_resonance, narrative_flow (균등 0.2)
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

# -- 상수 --
EVAL_THRESHOLD: float = 0.70
DEFAULT_DIMENSION_NAMES: List[str] = [
    "coherence",
    "authenticity",
    "style_adherence",
    "emotional_resonance",
    "narrative_flow",
]

_DEFAULT_WEIGHT: float = 1.0 / len(DEFAULT_DIMENSION_NAMES)  # 0.2


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_uuid() -> str:
    return str(uuid.uuid4())


@dataclass
class EvalDimension:
    """평가 차원 정의."""

    dimension_id: str
    name: str
    description: str = ""
    weight: float = _DEFAULT_WEIGHT

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "EvalDimension":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class EvalScore:
    """단일 차원 채점 결과."""

    dimension_id: str
    raw_score: float
    weighted_score: float
    evaluator_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "EvalScore":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class ConstitutionEvalResult:
    """전체 평가 결과 스냅샷."""

    result_id: str
    evaluated_at: str
    scene_id: str
    scores: List[EvalScore]
    final_score: float
    passed: bool
    threshold: float = EVAL_THRESHOLD
    evaluator_id: str = ""
    note: str = ""

    def summary(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        return (
            f"ConstitutionEvalResult({status} | scene={self.scene_id} "
            f"| final={self.final_score:.4f} | dims={len(self.scores)})"
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ConstitutionEvalResult":
        scores = [EvalScore.from_dict(s) for s in d.get("scores", [])]
        return cls(
            result_id=d["result_id"],
            evaluated_at=d["evaluated_at"],
            scene_id=d["scene_id"],
            scores=scores,
            final_score=d["final_score"],
            passed=d["passed"],
            threshold=d.get("threshold", EVAL_THRESHOLD),
            evaluator_id=d.get("evaluator_id", ""),
            note=d.get("note", ""),
        )


class ConstitutionEvalV2:
    """
    헌법 멀티축 평가기 V2.

    - 5축 DEFAULT_DIMENSIONS (coherence / authenticity / style_adherence /
      emotional_resonance / narrative_flow) 또는 사용자 정의 차원
    - evaluate(): 차원별 raw_score -> 가중 합산 -> ConstitutionEvalResult
    - batch_evaluate(): 복수 장면 일괄 평가
    - history() / last_result() / pass_rate() / count() / clear()
    - LOSDB JSONL append-only 영속화
    - LLM-0 원칙 준수
    """

    def __init__(
        self,
        dimensions: Optional[Sequence[EvalDimension]] = None,
        db_path: Union[str, Path] = ":memory:",
        threshold: float = EVAL_THRESHOLD,
    ) -> None:
        if dimensions is None:
            self._dimensions: List[EvalDimension] = [
                EvalDimension(
                    dimension_id=name,
                    name=name.replace("_", " ").title(),
                    weight=_DEFAULT_WEIGHT,
                )
                for name in DEFAULT_DIMENSION_NAMES
            ]
        else:
            self._dimensions = list(dimensions)

        self._threshold = threshold
        self._db_path = Path(db_path) if str(db_path) != ":memory:" else None
        self._records: List[ConstitutionEvalResult] = []

        if self._db_path is not None:
            self._load_from_disk()

    @property
    def dimensions(self) -> List[EvalDimension]:
        return list(self._dimensions)

    @property
    def threshold(self) -> float:
        return self._threshold

    def evaluate(
        self,
        scene_id: str,
        raw_scores: Dict[str, float],
        evaluator_id: str = "",
        note: str = "",
        now: Optional[datetime] = None,
    ) -> ConstitutionEvalResult:
        """
        차원별 raw_score(0.0~1.0)를 받아 EvalResult 생성 후 영속화.

        Raises:
            ValueError: raw_score가 [0,1] 범위를 벗어난 경우
        """
        ts = (now or datetime.now(timezone.utc)).isoformat()

        for dim_id, score in raw_scores.items():
            if not (0.0 <= score <= 1.0):
                raise ValueError(
                    f"raw_score for '{dim_id}' must be in [0.0, 1.0], got {score}"
                )

        scores: List[EvalScore] = []
        final = 0.0
        for dim in self._dimensions:
            raw = raw_scores.get(dim.dimension_id, 0.0)
            weighted = raw * dim.weight
            final += weighted
            scores.append(
                EvalScore(
                    dimension_id=dim.dimension_id,
                    raw_score=raw,
                    weighted_score=weighted,
                    evaluator_id=evaluator_id,
                )
            )

        result = ConstitutionEvalResult(
            result_id=_new_uuid(),
            evaluated_at=ts,
            scene_id=scene_id,
            scores=scores,
            final_score=round(final, 10),
            passed=final >= self._threshold,
            threshold=self._threshold,
            evaluator_id=evaluator_id,
            note=note,
        )
        self._records.append(result)
        self._append_to_disk(result)
        return result

    def batch_evaluate(
        self,
        items: Sequence[Tuple[str, Dict[str, float]]],
        evaluator_id: str = "",
        note: str = "",
    ) -> List[ConstitutionEvalResult]:
        """복수 장면 일괄 평가."""
        return [
            self.evaluate(scene_id, raw_scores, evaluator_id=evaluator_id, note=note)
            for scene_id, raw_scores in items
        ]

    def history(self) -> List[ConstitutionEvalResult]:
        """전체 평가 이력 반환 (시간순)."""
        return list(self._records)

    def last_result(self) -> Optional[ConstitutionEvalResult]:
        """가장 최근 평가 결과 반환."""
        return self._records[-1] if self._records else None

    def pass_rate(self) -> float:
        """전체 평가 중 PASS 비율 (0.0~1.0)."""
        if not self._records:
            return 0.0
        passed = sum(1 for r in self._records if r.passed)
        return passed / len(self._records)

    def count(self) -> int:
        """저장된 평가 결과 수."""
        return len(self._records)

    def results_by_scene(self, scene_id: str) -> List[ConstitutionEvalResult]:
        """특정 scene_id의 평가 이력 반환."""
        return [r for r in self._records if r.scene_id == scene_id]

    def clear(self) -> None:
        """메모리 내 이력 초기화 (디스크 파일 유지)."""
        self._records.clear()

    def _append_to_disk(self, result: ConstitutionEvalResult) -> None:
        if self._db_path is None:
            return
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._db_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(result.to_dict(), ensure_ascii=False) + "\n")

    def _load_from_disk(self) -> None:
        if self._db_path is None or not self._db_path.exists():
            return
        with self._db_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        self._records.append(ConstitutionEvalResult.from_dict(json.loads(line)))
                    except Exception:
                        pass
