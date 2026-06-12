"""
tests/gates/test_v749_pairwise_gates.py — G_PAIRWISE_REGRESSION + G_TRANSITIVITY (V749, ADR-211)

DoD 6:
  1. test_regression_pairs_count_is_11
  2. test_regression_gate_passes_with_9_of_11_wins
  3. test_regression_gate_fails_with_8_of_11_wins
  4. test_transitivity_gate_passes_clean_graph
  5. test_transitivity_gate_fails_over_threshold
  6. test_release_gate_includes_both_new_gates
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import List

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from literary_system.validation.pairwise import PairwiseJudgment, transitivity_check
from literary_system.validation.pairwise_fixtures import (
    REGRESSION_MIN_WIN_RATE,
    REGRESSION_PAIRS,
)
from tools.run_release_gate import (
    _check_pairwise_regression,
    _check_transitivity,
)


# ── 헬퍼 ──────────────────────────────────────────────────────────────────────

def _make_judgment(left: str, right: str, winner: str, idx: int = 0) -> PairwiseJudgment:
    return {
        "pair_id": f"{left}_vs_{right}_{idx}",
        "left_id": left,
        "right_id": right,
        "winner": winner,
        "mode": "preference",
        "trait": None,
        "rationale": "test",
        "judge_id": "test_judge",
        "position_seed": idx,
    }


def _build_regression_judgments(n_wins: int) -> List[PairwiseJudgment]:
    """canonical(left)이 n_wins 번 이기는 판정 리스트 생성."""
    judgments = []
    for i, (canonical, degraded) in enumerate(REGRESSION_PAIRS):
        winner = "left" if i < n_wins else "right"
        judgments.append(_make_judgment(canonical, degraded, winner, i))
    return judgments


# ── TC-1: 픽스처 쌍 수 ────────────────────────────────────────────────────────

class TestRegressionPairsCount:
    def test_regression_pairs_count_is_11(self):
        """REGRESSION_PAIRS must have exactly 11 pairs."""
        assert len(REGRESSION_PAIRS) == 11

    def test_regression_min_win_rate(self):
        """REGRESSION_MIN_WIN_RATE == 9/11."""
        assert abs(REGRESSION_MIN_WIN_RATE - 9 / 11) < 1e-9

    def test_each_pair_has_canonical_and_degraded(self):
        """각 쌍은 (str, str) 형태이고 degraded는 _deg 접미사를 가짐."""
        for canonical, degraded in REGRESSION_PAIRS:
            assert isinstance(canonical, str) and len(canonical) > 0
            assert degraded.endswith("_deg"), f"degraded must end with _deg: {degraded}"


# ── TC-2: 9/11 승 → PASS ──────────────────────────────────────────────────────

class TestRegressionGatePasses:
    def test_regression_gate_passes_with_9_of_11_wins(self):
        """9/11 승 → G_PAIRWISE_REGRESSION PASS."""
        judgments = _build_regression_judgments(n_wins=9)
        result = _check_pairwise_regression(judgments=judgments)
        assert result["pass"] is True, f"Expected PASS, got: {result}"
        assert result["wins"] == 9
        assert result["win_rate"] == pytest.approx(9 / 11, abs=1e-4)

    def test_regression_gate_passes_with_11_of_11_wins(self):
        """11/11 승 → PASS."""
        judgments = _build_regression_judgments(n_wins=11)
        result = _check_pairwise_regression(judgments=judgments)
        assert result["pass"] is True
        assert result["wins"] == 11


# ── TC-3: 8/11 승 → FAIL ─────────────────────────────────────────────────────

class TestRegressionGateFails:
    def test_regression_gate_fails_with_8_of_11_wins(self):
        """8/11 승 → G_PAIRWISE_REGRESSION FAIL."""
        judgments = _build_regression_judgments(n_wins=8)
        result = _check_pairwise_regression(judgments=judgments)
        assert result["pass"] is False, f"Expected FAIL, got: {result}"
        assert result["wins"] == 8

    def test_regression_gate_fails_with_0_wins(self):
        """0/11 승 → FAIL."""
        judgments = _build_regression_judgments(n_wins=0)
        result = _check_pairwise_regression(judgments=judgments)
        assert result["pass"] is False


# ── TC-4: 깨끗한 그래프 → G_TRANSITIVITY PASS ─────────────────────────────────

class TestTransitivityGatePasses:
    def test_transitivity_gate_passes_clean_graph(self):
        """A>B>C (비순환) → cycle_rate=0 → PASS."""
        judgments = [
            _make_judgment("A", "B", "left",  0),
            _make_judgment("B", "C", "left",  1),
            _make_judgment("A", "C", "left",  2),
        ]
        result = _check_transitivity(judgments=judgments)
        assert result["pass"] is True
        assert result["cycle_rate"] == pytest.approx(0.0, abs=1e-4)

    def test_transitivity_gate_passes_empty(self):
        """판정 없음 → trivially PASS."""
        result = _check_transitivity(judgments=[])
        assert result["pass"] is True


# ── TC-5: 순환 그래프 → G_TRANSITIVITY FAIL ──────────────────────────────────

class TestTransitivityGateFails:
    def test_transitivity_gate_fails_over_threshold(self):
        """A>B>C>A (완전 순환) → cycle_rate > 0 → FAIL (임계 0.05)."""
        # 3-cycle 생성: A>B, B>C, C>A
        # transitivity_check: 3-cycle = 1 / (total 3-combos)
        # 3개 노드 → C(3,3)=1 combo → cycle_rate = 1.0 → FAIL
        judgments = [
            _make_judgment("A", "B", "left",  0),
            _make_judgment("B", "C", "left",  1),
            _make_judgment("C", "A", "left",  2),
        ]
        cycle_rate = transitivity_check(judgments)
        assert cycle_rate > 0.0, "3-cycle should produce cycle_rate > 0"

        result = _check_transitivity(judgments=judgments)
        assert result["pass"] is False, f"Expected FAIL for 3-cycle, got: {result}"
        assert result["cycle_rate"] > 0.0


# ── TC-6: run_release_gate 통합 ───────────────────────────────────────────────

class TestReleaseGateIntegration:
    def test_release_gate_includes_both_new_gates(self):
        """run_release_gate.py에 G_PAIRWISE_REGRESSION + G_TRANSITIVITY 함수 존재."""
        from tools import run_release_gate as rg
        assert hasattr(rg, "_check_pairwise_regression"), \
            "_check_pairwise_regression missing from run_release_gate"
        assert hasattr(rg, "_check_transitivity"), \
            "_check_transitivity missing from run_release_gate"

    def test_release_gate_output_has_both_keys(self, tmp_path, monkeypatch):
        """run_release_gate final dict에 두 키가 존재."""
        import json
        from tools.run_release_gate import _check_pairwise_regression, _check_transitivity
        r1 = _check_pairwise_regression()
        r2 = _check_transitivity()
        assert "gate" in r1 and r1["gate"] == "G_PAIRWISE_REGRESSION"
        assert "gate" in r2 and r2["gate"] == "G_TRANSITIVITY"
        assert "pass" in r1 and "pass" in r2
