"""
literary_system/audit/atia_metadata_auditor.py

V629: ATIAMetadataAuditor — AI 투명성·해석가능성·책임성 메타데이터 외부 감사 패키지
ADR-096 §3: ATIA (Transparency / Interpretability / Accountability) 감사

Literary OS의 각 모듈에 대해 3축(투명성·해석가능성·책임성) 점수를 산정하고
외부 감사 패키지(JSON + 요약 리포트)를 생성한다.
LLM-0 원칙: 외부 LLM 호출 없음.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class ATIADimension(str, Enum):
    """ATIA 3축 평가 차원."""
    TRANSPARENCY = "transparency"        # 투명성: 로그·버전·변경이력 공개
    INTERPRETABILITY = "interpretability"  # 해석가능성: 의사결정 설명 가능성
    ACCOUNTABILITY = "accountability"    # 책임성: 감사 추적·권한·오류 귀속


class ATIARiskLevel(str, Enum):
    """위험 등급."""
    LOW = "low"           # score >= 0.80
    MEDIUM = "medium"     # 0.60 <= score < 0.80
    HIGH = "high"         # 0.40 <= score < 0.60
    CRITICAL = "critical" # score < 0.40


def _risk_from_score(score: float) -> ATIARiskLevel:
    if score >= 0.80:
        return ATIARiskLevel.LOW
    if score >= 0.60:
        return ATIARiskLevel.MEDIUM
    if score >= 0.40:
        return ATIARiskLevel.HIGH
    return ATIARiskLevel.CRITICAL


@dataclass
class ATIAMetadataRecord:
    """단일 모듈에 대한 ATIA 평가 레코드."""
    module_name: str
    version: str
    transparency_score: float   # 0.0 ~ 1.0
    interpretability_score: float
    accountability_score: float
    notes: str = ""
    evidence: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        for attr in ("transparency_score", "interpretability_score", "accountability_score"):
            v = getattr(self, attr)
            if not (0.0 <= v <= 1.0):
                raise ValueError(f"{attr}={v} 는 [0.0, 1.0] 범위여야 합니다.")

    @property
    def overall_score(self) -> float:
        """3축 가중 평균 (T:0.3, I:0.3, A:0.4)."""
        return (
            0.30 * self.transparency_score
            + 0.30 * self.interpretability_score
            + 0.40 * self.accountability_score
        )

    @property
    def risk_level(self) -> ATIARiskLevel:
        return _risk_from_score(self.overall_score)

    @property
    def passed(self) -> bool:
        """전체 점수 0.60 이상 + 각 축 0.40 이상이면 통과."""
        return (
            self.overall_score >= 0.60
            and self.transparency_score >= 0.40
            and self.interpretability_score >= 0.40
            and self.accountability_score >= 0.40
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "module_name": self.module_name,
            "version": self.version,
            "scores": {
                "transparency": round(self.transparency_score, 4),
                "interpretability": round(self.interpretability_score, 4),
                "accountability": round(self.accountability_score, 4),
                "overall": round(self.overall_score, 4),
            },
            "risk_level": self.risk_level.value,
            "passed": self.passed,
            "notes": self.notes,
            "evidence": self.evidence,
        }


@dataclass
class ATIAAuditReport:
    """전체 감사 보고서."""
    system_name: str
    system_version: str
    records: List[ATIAMetadataRecord]
    audited_at: str
    overall_score: float
    passed: bool
    critical_modules: List[str]
    high_risk_modules: List[str]

    @property
    def total_modules(self) -> int:
        return len(self.records)

    @property
    def passed_modules(self) -> int:
        return sum(1 for r in self.records if r.passed)

    @property
    def failed_modules(self) -> int:
        return self.total_modules - self.passed_modules

    def to_dict(self) -> Dict[str, Any]:
        return {
            "system_name": self.system_name,
            "system_version": self.system_version,
            "audited_at": self.audited_at,
            "summary": {
                "overall_score": round(self.overall_score, 4),
                "passed": self.passed,
                "total_modules": self.total_modules,
                "passed_modules": self.passed_modules,
                "failed_modules": self.failed_modules,
                "critical_modules": self.critical_modules,
                "high_risk_modules": self.high_risk_modules,
            },
            "records": [r.to_dict() for r in self.records],
        }

    def to_markdown_summary(self) -> str:
        """감사 요약 Markdown 리포트."""
        status = "✅ PASS" if self.passed else "❌ FAIL"
        lines = [
            f"# ATIA 외부 감사 리포트 — {self.system_name} v{self.system_version}",
            f"",
            f"**감사 일시**: {self.audited_at}  ",
            f"**전체 점수**: {self.overall_score:.4f}  ",
            f"**최종 결과**: {status}",
            f"",
            f"| 항목 | 값 |",
            f"|------|-----|",
            f"| 총 모듈 수 | {self.total_modules} |",
            f"| 통과 모듈 | {self.passed_modules} |",
            f"| 실패 모듈 | {self.failed_modules} |",
            f"| Critical 모듈 | {len(self.critical_modules)} |",
            f"| High Risk 모듈 | {len(self.high_risk_modules)} |",
            f"",
        ]
        if self.critical_modules:
            lines.append("## ❗ Critical 모듈")
            for m in self.critical_modules:
                lines.append(f"- `{m}`")
            lines.append("")
        if self.high_risk_modules:
            lines.append("## ⚠️ High Risk 모듈")
            for m in self.high_risk_modules:
                lines.append(f"- `{m}`")
            lines.append("")
        lines.append("## 모듈별 점수")
        lines.append("")
        lines.append("| 모듈 | 투명성 | 해석가능성 | 책임성 | 종합 | 위험 |")
        lines.append("|------|--------|------------|--------|------|------|")
        for r in sorted(self.records, key=lambda x: x.overall_score):
            lines.append(
                f"| `{r.module_name}` "
                f"| {r.transparency_score:.2f} "
                f"| {r.interpretability_score:.2f} "
                f"| {r.accountability_score:.2f} "
                f"| **{r.overall_score:.2f}** "
                f"| {r.risk_level.value} |"
            )
        return "\n".join(lines)


class ATIAMetadataAuditor:
    """
    ATIA 메타데이터 외부 감사 관리자.

    모듈별 ATIAMetadataRecord를 수집하고 시스템 전체 감사 보고서를 생성한다.
    """

    PASS_THRESHOLD = 0.60    # 시스템 전체 통과 기준

    def __init__(self, system_name: str = "Literary OS", system_version: str = "unknown") -> None:
        self.system_name = system_name
        self.system_version = system_version
        self._records: List[ATIAMetadataRecord] = []

    # ------------------------------------------------------------------ #
    # 등록                                                                  #
    # ------------------------------------------------------------------ #

    def register(self, record: ATIAMetadataRecord) -> "ATIAMetadataAuditor":
        """레코드 등록 (체이닝 지원)."""
        self._records.append(record)
        return self

    def register_many(self, records: List[ATIAMetadataRecord]) -> "ATIAMetadataAuditor":
        for r in records:
            self.register(r)
        return self

    def collect_records(self) -> List[ATIAMetadataRecord]:
        return list(self._records)

    def record_count(self) -> int:
        return len(self._records)

    # ------------------------------------------------------------------ #
    # 점수 계산                                                             #
    # ------------------------------------------------------------------ #

    def compute_scores(self) -> Tuple[float, float, float]:
        """
        시스템 전체 3축 평균 점수 반환.
        Returns: (mean_transparency, mean_interpretability, mean_accountability)
        """
        if not self._records:
            return (0.0, 0.0, 0.0)
        n = len(self._records)
        t = sum(r.transparency_score for r in self._records) / n
        i = sum(r.interpretability_score for r in self._records) / n
        a = sum(r.accountability_score for r in self._records) / n
        return (t, i, a)

    def compute_overall_score(self) -> float:
        t, i, a = self.compute_scores()
        return 0.30 * t + 0.30 * i + 0.40 * a

    # ------------------------------------------------------------------ #
    # 감사 보고서                                                           #
    # ------------------------------------------------------------------ #

    def audit(self) -> ATIAAuditReport:
        """전체 감사 수행 — ATIAAuditReport 반환."""
        overall = self.compute_overall_score()
        critical = [r.module_name for r in self._records if r.risk_level == ATIARiskLevel.CRITICAL]
        high_risk = [r.module_name for r in self._records if r.risk_level == ATIARiskLevel.HIGH]
        return ATIAAuditReport(
            system_name=self.system_name,
            system_version=self.system_version,
            records=list(self._records),
            audited_at=datetime.now(timezone.utc).isoformat(),
            overall_score=overall,
            passed=(overall >= self.PASS_THRESHOLD and len(critical) == 0),
            critical_modules=critical,
            high_risk_modules=high_risk,
        )

    # ------------------------------------------------------------------ #
    # 패키지 내보내기                                                       #
    # ------------------------------------------------------------------ #

    def export_package(self) -> Dict[str, str]:
        """
        외부 감사 패키지 생성.
        Returns: {
            "audit_report.json": JSON 문자열,
            "audit_summary.md": Markdown 문자열,
        }
        """
        report = self.audit()
        return {
            "audit_report.json": json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
            "audit_summary.md": report.to_markdown_summary(),
        }

    # ------------------------------------------------------------------ #
    # 유틸                                                                  #
    # ------------------------------------------------------------------ #

    def dimension_stats(self, dim: ATIADimension) -> Dict[str, float]:
        """특정 차원의 min/max/mean/std 반환."""
        if not self._records:
            return {"min": 0.0, "max": 0.0, "mean": 0.0, "std": 0.0}
        attr_map = {
            ATIADimension.TRANSPARENCY: "transparency_score",
            ATIADimension.INTERPRETABILITY: "interpretability_score",
            ATIADimension.ACCOUNTABILITY: "accountability_score",
        }
        attr = attr_map[dim]
        vals = [getattr(r, attr) for r in self._records]
        mean = sum(vals) / len(vals)
        std = math.sqrt(sum((v - mean) ** 2 for v in vals) / len(vals))
        return {
            "min": min(vals),
            "max": max(vals),
            "mean": mean,
            "std": std,
        }

    def lowest_scored_modules(self, n: int = 5) -> List[ATIAMetadataRecord]:
        """전체 점수 기준 하위 n개 모듈 반환."""
        return sorted(self._records, key=lambda r: r.overall_score)[:n]
