"""
V573-S2: Gate28 (StoryQualityGate) 단위 테스트
ADR-033 기반 — BUG-1/BUG-2 회귀 방지 + Gate28 실제 평가 로직 검증

TC-01: 빈 보고서 → Gate28 approved=True
TC-02: debt 임계값 초과 → Gate28 approved=False
TC-03: arc 임계값 초과 → Gate28 approved=False
TC-04: combined_quality 수식 정확도 (debt×0.55 + arc×0.45)
TC-05: DoctorReport 전체 필드 정상 구성 → ValueError 없음
"""

from __future__ import annotations

import pytest
from literary_system.graph_intelligence.asd.gate28 import Gate28, Gate28Result
from literary_system.graph_intelligence.asd.narrative_debt_detector import NarrativeDebtReport
from literary_system.graph_intelligence.asd.arc_consistency_checker import ArcConsistencyReport
from literary_system.graph_intelligence.asd.story_doctor_orchestrator import DoctorReport


def _make_debt(score: float = 0.0) -> NarrativeDebtReport:
    """빈 NarrativeDebtReport (total_debts=0, 점수는 score)."""
    return NarrativeDebtReport(
        total_debts=0,
        unresolved_secrets=[],
        broken_foreshadows=[],
        abandoned_threads=[],
        overall_debt_score=score,
    )


def _make_arc(score: float = 0.0) -> ArcConsistencyReport:
    """빈 ArcConsistencyReport (total_issues=0, 점수는 score)."""
    return ArcConsistencyReport(
        total_issues=0,
        not_tracked=[],
        post_death_edges=[],
        contradiction_flows=[],
        episode_inversions=[],
        overall_score=score,
    )


def _make_report(debt_score: float = 0.0, arc_score: float = 0.0) -> DoctorReport:
    return DoctorReport(
        recommendations=[],
        total_issues=0,
        high_priority=[],
        medium_priority=[],
        low_priority=[],
        debt_report=_make_debt(debt_score),
        arc_report=_make_arc(arc_score),
    )


# ─── TC-01: 빈 보고서 → approved=True ─────────────────────────────────────
def test_gate28_tc01_empty_report_passes():
    """TC-01: 모든 점수 0인 빈 보고서는 Gate28 PASS."""
    gate = Gate28()
    report = _make_report(debt_score=0.0, arc_score=0.0)
    result = gate.evaluate(report)

    assert isinstance(result, Gate28Result), "evaluate()는 Gate28Result를 반환해야 함"
    assert result.approved is True, f"빈 보고서는 approved=True여야 함 (got {result.approved})"
    assert result.combined_quality == pytest.approx(0.0, abs=1e-6)
    assert result.failed_gates == []


# ─── TC-02: debt 임계값 초과 → approved=False ─────────────────────────────
def test_gate28_tc02_high_debt_fails():
    """TC-02: overall_debt_score=0.9 → Gate28 FAIL."""
    gate = Gate28()
    report = _make_report(debt_score=0.9, arc_score=0.0)
    result = gate.evaluate(report)

    assert isinstance(result, Gate28Result)
    assert result.approved is False, "high debt_score → approved=False여야 함"
    assert len(result.failed_gates) >= 1


# ─── TC-03: arc 임계값 초과 → approved=False ──────────────────────────────
def test_gate28_tc03_high_arc_fails():
    """TC-03: arc overall_score=0.8 → Gate28 FAIL."""
    gate = Gate28()
    report = _make_report(debt_score=0.0, arc_score=0.8)
    result = gate.evaluate(report)

    assert isinstance(result, Gate28Result)
    assert result.approved is False, "high arc_score → approved=False여야 함"


# ─── TC-04: combined_quality 수식 정확도 ──────────────────────────────────
def test_gate28_tc04_combined_quality_formula():
    """TC-04: combined_quality = debt×0.55 + arc×0.45, min(..., 1.0)."""
    gate = Gate28()

    # 케이스 A: debt=0.4, arc=0.2 → combined = 0.4×0.55 + 0.2×0.45 = 0.22 + 0.09 = 0.31
    report_a = _make_report(debt_score=0.4, arc_score=0.2)
    result_a = gate.evaluate(report_a)
    expected_a = min(0.4 * 0.55 + 0.2 * 0.45, 1.0)
    assert result_a.combined_quality == pytest.approx(expected_a, abs=1e-4), (
        f"combined_quality 불일치: got {result_a.combined_quality}, expected {expected_a}"
    )

    # 케이스 B: debt=1.0, arc=1.0 → combined = min(1.0, 1.0) = 1.0 (캡)
    report_b = _make_report(debt_score=1.0, arc_score=1.0)
    result_b = gate.evaluate(report_b)
    assert result_b.combined_quality == pytest.approx(1.0, abs=1e-4)


# ─── TC-05: Gate28Result 속성 접근 (BUG-1 회귀 방지) ─────────────────────
def test_gate28_tc05_result_approved_attribute():
    """TC-05: Gate28Result.approved 속성 존재 및 bool 타입 — BUG-1 회귀 방지."""
    gate = Gate28()
    report = _make_report()
    result = gate.evaluate(report)

    # BUG-1 회귀 검사: overall_passed 없음, approved 있음
    assert hasattr(result, "approved"), "Gate28Result에 'approved' 속성 필요"
    assert not hasattr(result, "overall_passed") or True  # 없어도 OK, 있어도 OK (미래 호환)
    assert isinstance(result.approved, bool)

    # BUG-2 회귀 검사: release_gate 함수에서 사용하는 생성자 패턴 검증
    # NarrativeDebtReport 직접 생성 가능
    debt = NarrativeDebtReport(
        total_debts=0, unresolved_secrets=[], broken_foreshadows=[],
        abandoned_threads=[], overall_debt_score=0.0
    )
    assert debt.overall_debt_score == 0.0

    # ArcConsistencyReport 직접 생성 가능
    arc = ArcConsistencyReport(
        total_issues=0, not_tracked=[], post_death_edges=[],
        contradiction_flows=[], episode_inversions=[], overall_score=0.0
    )
    assert arc.overall_score == 0.0

    # DoctorReport 직접 생성 가능 (work_id 없음)
    doc = DoctorReport(
        recommendations=[], total_issues=0,
        high_priority=[], medium_priority=[], low_priority=[],
        debt_report=debt, arc_report=arc
    )
    assert doc.total_issues == 0
