"""
V323 - CriticComparisonGate  (Phase 3)
audit_mode 전용: V312 단독 vs V323 풀 파이프라인 비교.

설계 원칙 (CSA/CSC/CPE 합의):
  - audit_mode=False (기본): 제로 오버헤드, 프로덕션 안전
  - audit_mode=True:  AuditResult 반환, 히스토리 누적
  - LLM 0회. 완전 로컬.
"""
from __future__ import annotations
import logging

from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


# ================================================================
# PipelineOutput - 파이프라인 단일 출력
# ================================================================

@dataclass
class PipelineOutput:
    """V312 또는 V323 파이프라인의 단일 씬 출력."""
    scene_text: str
    drse_score: float
    judgment_label: str   # GOOD / BAD / MARGINAL
    passed: bool
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "scene_text": self.scene_text[:80],  # 미리보기 80자
            "drse_score": self.drse_score,
            "judgment_label": self.judgment_label,
            "passed": self.passed,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "PipelineOutput":
        return cls(
            scene_text=d.get("scene_text", ""),
            drse_score=d.get("drse_score", 0.0),
            judgment_label=d.get("judgment_label", "BAD"),
            passed=d.get("passed", False),
            metadata=d.get("metadata", {}),
        )


# ================================================================
# AuditResult - 비교 결과
# ================================================================

@dataclass
class AuditResult:
    """V312 vs V323 단일 씬 비교 결과."""
    scene_id: str
    v312_output: PipelineOutput
    v323_output: PipelineOutput

    @property
    def delta_score(self) -> float:
        """V323 - V312 스코어 차이. 양수 = V323 개선."""
        return round(self.v323_output.drse_score - self.v312_output.drse_score, 6)

    @property
    def agreement(self) -> bool:
        """두 파이프라인의 판정(passed) 일치 여부."""
        return self.v312_output.passed == self.v323_output.passed

    def to_dict(self) -> dict:
        return {
            "scene_id": self.scene_id,
            "delta_score": self.delta_score,
            "agreement": self.agreement,
            "v312_output": self.v312_output.to_dict(),
            "v323_output": self.v323_output.to_dict(),
        }


# ================================================================
# CriticComparisonGate
# ================================================================

class CriticComparisonGate:
    """
    V323 Phase 3 감사 게이트.

    audit_mode=False (기본): compare() 호출 시 None 반환 (무비용).
    audit_mode=True:  AuditResult 반환 + 히스토리 누적 + 통계.

    사용 예:
        gate = CriticComparisonGate(audit_mode=True)
        result = gate.compare("scene_01", v312_out, v323_out)
        logger.debug(gate.stats())
    """

    def __init__(self, audit_mode: bool = False):
        self._audit_mode = audit_mode
        self._history: list[AuditResult] = []

    @property
    def audit_mode(self) -> bool:
        return self._audit_mode

    @property
    def audit_count(self) -> int:
        return len(self._history)

    @property
    def history(self) -> list[AuditResult]:
        return list(self._history)

    def compare(
        self,
        scene_id: str,
        v312_output: PipelineOutput,
        v323_output: PipelineOutput,
    ) -> AuditResult | None:
        """
        두 파이프라인 출력 비교.
        audit_mode=False 시 즉시 None 반환 (프로덕션 안전).
        """
        if not self._audit_mode:
            return None

        result = AuditResult(
            scene_id=scene_id,
            v312_output=v312_output,
            v323_output=v323_output,
        )
        self._history.append(result)
        return result

    def clear_history(self) -> None:
        self._history.clear()

    def stats(self) -> dict[str, Any]:
        if not self._history:
            return {
                "audit_mode": self._audit_mode,
                "audit_count": 0,
                "agreement_rate": 0.0,
                "avg_delta_score": 0.0,
            }

        agreements = sum(1 for r in self._history if r.agreement)
        avg_delta = sum(r.delta_score for r in self._history) / len(self._history)

        return {
            "audit_mode": self._audit_mode,
            "audit_count": len(self._history),
            "agreement_rate": round(agreements / len(self._history), 4),
            "avg_delta_score": round(avg_delta, 6),
            "disagreement_count": len(self._history) - agreements,
        }
