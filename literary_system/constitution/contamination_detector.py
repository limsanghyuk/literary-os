"""
contamination_detector.py — ContaminationDetector V638 (ADR-080)

SP-C.1 Self-Learning Loop 훈련 데이터 오염 탐지기.

탐지 대상 오염 유형:
  - LABEL_NOISE          : 레이블 불일치 비율 >= LABEL_NOISE_THRESHOLD(0.05)
  - NEAR_DUPLICATE       : 중복 비율 >= NEAR_DUPLICATE_THRESHOLD(0.10)
  - DISTRIBUTION_SHIFT   : 축별 점수 분포 이탈 >= DISTRIBUTION_SHIFT_THRESHOLD(2.0) sigma
  - POISON_PATTERN       : 블랙리스트 패턴 포함 비율 >= POISON_THRESHOLD(0.01)

설계 원칙:
  - LOSDB JSONL append-only 영속화 (':memory:' 모드 지원)
  - LLM-0 원칙 완전 준수 (외부 LLM 호출 없음)
  - 모든 연산은 순수 Python 표준 라이브러리만 사용
"""
from __future__ import annotations

import json
import math
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

# -------------------------------------------------
# 오염 탐지 임계값 상수
# -------------------------------------------------
LABEL_NOISE_THRESHOLD: float = 0.05
NEAR_DUPLICATE_THRESHOLD: float = 0.10
DISTRIBUTION_SHIFT_THRESHOLD: float = 2.0
POISON_THRESHOLD: float = 0.01

# 블랙리스트 패턴 (정규식)
_DEFAULT_POISON_PATTERNS: List[str] = [
    r"ignore.{0,20}previous.{0,20}instruction",
    r"system.{0,10}prompt",
    r"jailbreak",
    r"<\|.*?\|>",
]

_DEFAULT_STORE = "data/losdb/contamination_detector.jsonl"
_MEMORY_SENTINEL = ":memory:"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _mean(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _stddev(values: Sequence[float]) -> float:
    if len(values) < 2:
        return 0.0
    mu = _mean(values)
    variance = sum((x - mu) ** 2 for x in values) / len(values)
    return math.sqrt(variance)


# -------------------------------------------------
# 데이터 클래스
# -------------------------------------------------
@dataclass
class ContaminationFlag:
    """개별 오염 플래그."""
    flag_id: str
    severity: float
    detail: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "flag_id": self.flag_id,
            "severity": self.severity,
            "detail": self.detail,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ContaminationFlag":
        return cls(
            flag_id=d["flag_id"],
            severity=float(d["severity"]),
            detail=d["detail"],
        )


@dataclass
class ContaminationReport:
    """오염 탐지 보고서."""
    report_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    detected_at: str = field(default_factory=_now_iso)
    dataset_id: str = ""
    sample_count: int = 0
    flags: List[ContaminationFlag] = field(default_factory=list)
    contaminated: bool = False
    contamination_rate: float = 0.0
    detector_id: str = ""
    note: str = ""

    def summary(self) -> str:
        status = "CONTAMINATED" if self.contaminated else "CLEAN"
        flag_ids = [f.flag_id for f in self.flags]
        return (
            f"[{status}] dataset={self.dataset_id} "
            f"samples={self.sample_count} "
            f"rate={self.contamination_rate:.3f} "
            f"flags={flag_ids}"
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "detected_at": self.detected_at,
            "dataset_id": self.dataset_id,
            "sample_count": self.sample_count,
            "flags": [f.to_dict() for f in self.flags],
            "contaminated": self.contaminated,
            "contamination_rate": self.contamination_rate,
            "detector_id": self.detector_id,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ContaminationReport":
        return cls(
            report_id=d["report_id"],
            detected_at=d["detected_at"],
            dataset_id=d.get("dataset_id", ""),
            sample_count=d.get("sample_count", 0),
            flags=[ContaminationFlag.from_dict(f) for f in d.get("flags", [])],
            contaminated=d.get("contaminated", False),
            contamination_rate=float(d.get("contamination_rate", 0.0)),
            detector_id=d.get("detector_id", ""),
            note=d.get("note", ""),
        )


# -------------------------------------------------
# ContaminationDetector 본체
# -------------------------------------------------
class ContaminationDetector:
    """
    훈련 데이터 오염 탐지기 -- SP-C.1 V638 (ADR-080).

    사용법::

        detector = ContaminationDetector()                  # 메모리 모드
        detector = ContaminationDetector("path/to.jsonl")  # 파일 영속화

        report = detector.scan(
            dataset_id="ds-2026-q2",
            sample_count=1000,
            label_mismatch_count=30,
            near_duplicate_count=120,
            score_vectors=[[0.8, 0.7, 0.6, 0.9, 0.8], ...],
            raw_texts=["sample text..."],
            detector_id="human-1",
            note="Q2 weekly scan",
        )
    """

    def __init__(
        self,
        store_path: str = _MEMORY_SENTINEL,
        poison_patterns: Optional[List[str]] = None,
    ) -> None:
        self._store_path = store_path
        self._memory: List[ContaminationReport] = []
        self._poison_patterns: List[re.Pattern] = [
            re.compile(p, re.IGNORECASE)
            for p in (poison_patterns or _DEFAULT_POISON_PATTERNS)
        ]
        if store_path != _MEMORY_SENTINEL:
            self._load_from_disk()

    # -- 오염 탐지 ----------------------------
    def scan(
        self,
        dataset_id: str,
        sample_count: int,
        label_mismatch_count: int = 0,
        near_duplicate_count: int = 0,
        score_vectors: Optional[List[List[float]]] = None,
        raw_texts: Optional[List[str]] = None,
        detector_id: str = "",
        note: str = "",
        now: Optional[str] = None,
    ) -> ContaminationReport:
        """단일 데이터셋 오염 스캔."""
        flags: List[ContaminationFlag] = []

        if sample_count > 0:
            # LABEL_NOISE
            label_ratio = label_mismatch_count / sample_count
            if label_ratio >= LABEL_NOISE_THRESHOLD:
                flags.append(ContaminationFlag(
                    flag_id="LABEL_NOISE",
                    severity=min(label_ratio, 1.0),
                    detail=(
                        f"레이블 불일치 {label_mismatch_count}/{sample_count} "
                        f"({label_ratio:.1%}) >= {LABEL_NOISE_THRESHOLD:.1%}"
                    ),
                ))

            # NEAR_DUPLICATE
            dup_ratio = near_duplicate_count / sample_count
            if dup_ratio >= NEAR_DUPLICATE_THRESHOLD:
                flags.append(ContaminationFlag(
                    flag_id="NEAR_DUPLICATE",
                    severity=min(dup_ratio, 1.0),
                    detail=(
                        f"중복 {near_duplicate_count}/{sample_count} "
                        f"({dup_ratio:.1%}) >= {NEAR_DUPLICATE_THRESHOLD:.1%}"
                    ),
                ))

            # DISTRIBUTION_SHIFT
            if score_vectors:
                shift_flag = self._detect_distribution_shift(score_vectors, sample_count)
                if shift_flag:
                    flags.append(shift_flag)

            # POISON_PATTERN
            if raw_texts:
                poison_flag = self._detect_poison(raw_texts, sample_count)
                if poison_flag:
                    flags.append(poison_flag)

        contaminated = len(flags) > 0
        contamination_rate = max((f.severity for f in flags), default=0.0)

        report = ContaminationReport(
            detected_at=now or _now_iso(),
            dataset_id=dataset_id,
            sample_count=sample_count,
            flags=flags,
            contaminated=contaminated,
            contamination_rate=contamination_rate,
            detector_id=detector_id,
            note=note,
        )
        self._memory.append(report)
        if self._store_path != _MEMORY_SENTINEL:
            self._append_to_disk(report)
        return report

    def batch_scan(
        self,
        items: List[Dict[str, Any]],
        detector_id: str = "",
        note: str = "",
    ) -> List[ContaminationReport]:
        """여러 데이터셋 배치 스캔."""
        results = []
        for item in items:
            results.append(self.scan(
                dataset_id=item.get("dataset_id", ""),
                sample_count=item.get("sample_count", 0),
                label_mismatch_count=item.get("label_mismatch_count", 0),
                near_duplicate_count=item.get("near_duplicate_count", 0),
                score_vectors=item.get("score_vectors"),
                raw_texts=item.get("raw_texts"),
                detector_id=item.get("detector_id", detector_id),
                note=item.get("note", note),
            ))
        return results

    # -- 내부 탐지 로직 -----------------------
    def _detect_distribution_shift(
        self,
        score_vectors: List[List[float]],
        sample_count: int,
    ) -> Optional[ContaminationFlag]:
        """축별 점수 분포 이탈 탐지 (z-score 기반)."""
        if len(score_vectors) < 2:
            return None
        n_axes = len(score_vectors[0]) if score_vectors else 0
        if n_axes == 0:
            return None

        shifted_axes = []
        for axis_idx in range(n_axes):
            axis_vals = [
                v[axis_idx] for v in score_vectors
                if axis_idx < len(v)
            ]
            if len(axis_vals) < 2:
                continue
            mu = _mean(axis_vals)
            sigma = _stddev(axis_vals)
            if sigma == 0.0:
                continue
            z = abs(mu - 0.5) / sigma
            if z >= DISTRIBUTION_SHIFT_THRESHOLD:
                shifted_axes.append((axis_idx, z))

        if not shifted_axes:
            return None

        max_z = max(z for _, z in shifted_axes)
        severity = min(max_z / (DISTRIBUTION_SHIFT_THRESHOLD * 2), 1.0)
        detail = (
            f"분포 이탈 축: {['axis' + str(i) + '(z=' + str(round(z, 2)) + ')' for i, z in shifted_axes]} "
            f">= {DISTRIBUTION_SHIFT_THRESHOLD}sigma"
        )
        return ContaminationFlag(
            flag_id="DISTRIBUTION_SHIFT",
            severity=severity,
            detail=detail,
        )

    def _detect_poison(
        self,
        raw_texts: List[str],
        sample_count: int,
    ) -> Optional[ContaminationFlag]:
        """블랙리스트 패턴 포함 텍스트 탐지."""
        matched = 0
        matched_samples: List[str] = []
        for text in raw_texts:
            for pattern in self._poison_patterns:
                if pattern.search(text):
                    matched += 1
                    if len(matched_samples) < 3:
                        matched_samples.append(text[:60])
                    break

        total = max(sample_count, len(raw_texts))
        if total == 0:
            return None
        poison_ratio = matched / total
        if poison_ratio < POISON_THRESHOLD:
            return None

        severity = min(poison_ratio * 10, 1.0)
        detail = (
            f"독성 패턴 {matched}/{total} ({poison_ratio:.1%}) "
            f">= {POISON_THRESHOLD:.1%}. 예: {matched_samples}"
        )
        return ContaminationFlag(
            flag_id="POISON_PATTERN",
            severity=severity,
            detail=detail,
        )

    # -- 조회 API -----------------------------
    def history(self) -> List[ContaminationReport]:
        """모든 보고서 반환 (시간순)."""
        return list(self._memory)

    def last_report(self) -> Optional[ContaminationReport]:
        """가장 최근 보고서."""
        return self._memory[-1] if self._memory else None

    def contaminated_reports(self) -> List[ContaminationReport]:
        """오염 탐지된 보고서만 반환."""
        return [r for r in self._memory if r.contaminated]

    def contamination_rate(self) -> float:
        """전체 스캔 중 오염 탐지 비율."""
        if not self._memory:
            return 0.0
        return len(self.contaminated_reports()) / len(self._memory)

    def reports_by_dataset(self, dataset_id: str) -> List[ContaminationReport]:
        """특정 데이터셋 ID의 보고서 목록."""
        return [r for r in self._memory if r.dataset_id == dataset_id]

    def count(self) -> int:
        """누적 스캔 수."""
        return len(self._memory)

    def clear(self) -> None:
        """메모리 및 디스크 데이터 초기화."""
        self._memory.clear()
        if self._store_path != _MEMORY_SENTINEL:
            Path(self._store_path).write_text("", encoding="utf-8")

    # -- 영속화 -------------------------------
    def _append_to_disk(self, report: ContaminationReport) -> None:
        """JSONL append-only 영속화."""
        path = Path(self._store_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(report.to_dict(), ensure_ascii=False) + "\n")

    def _load_from_disk(self) -> None:
        """디스크에서 JSONL 로드."""
        path = Path(self._store_path)
        if not path.exists():
            return
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                self._memory.append(
                    ContaminationReport.from_dict(json.loads(line))
                )
            except (json.JSONDecodeError, KeyError):
                continue
