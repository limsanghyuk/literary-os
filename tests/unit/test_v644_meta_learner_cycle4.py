"""
test_v644_meta_learner_cycle4.py — V644 WeightConvergenceReport 테스트 (33 TC)

검증 범위:
  1. 신규 상수 (3 TC)
  2. WeightConvergenceReport 데이터클래스 (6 TC)
  3. MetaLearnerCycle 초기화 — constitution 파라미터 (3 TC)
  4. weight_convergence_check() 메서드 (6 TC)
  5. CycleReport.weight_convergence 및 weight_converged (5 TC)
  6. run_cycle() — constitution 연결 시 수렴 자동 검증 (5 TC)
  7. weight_convergence_history() / latest_weight_convergence() (4 TC)
  8. 수렴 실패 시나리오 (엔트로피 부족 / 합 이탈) (1 TC)
"""
from __future__ import annotations

import math
import pytest
from typing import Dict

from literary_system.constitution.meta_learner_cycle import (
    MetaLearnerCycle,
    WeightConvergenceReport,
    CycleReport,
    WEIGHT_SUM_TOLERANCE,
    WEIGHT_ENTROPY_MIN,
    WEIGHT_CONVERGENCE_MIN_CYCLES,
)
from literary_system.constitution.los_constitution_v2 import LOSConstitutionV2, _shannon_entropy
from literary_system.constitution.los_constitution import ConstitutionWeights
from literary_system.nie.meta_learner import MetaLearner


# ─── 공통 픽스처 ─────────────────────────────────────────────────────────────

@pytest.fixture
def default_weights() -> Dict[str, float]:
    """ADR-054 기본 ConstitutionWeights 딕셔너리."""
    return {"drse": 0.30, "debt": 0.20, "arc": 0.20, "tension": 0.15, "prose": 0.15}


@pytest.fixture
def skewed_weights() -> Dict[str, float]:
    """극단 편중 가중치 (entropy < 1.5)."""
    return {"drse": 0.96, "debt": 0.01, "arc": 0.01, "tension": 0.01, "prose": 0.01}


@pytest.fixture
def bad_sum_weights() -> Dict[str, float]:
    """합이 1.0±0.01을 벗어난 가중치."""
    return {"drse": 0.30, "debt": 0.20, "arc": 0.20, "tension": 0.15, "prose": 0.20}


@pytest.fixture
def mlc_with_constitution() -> MetaLearnerCycle:
    """LOSConstitutionV2가 연결된 MetaLearnerCycle (즉시 활성화)."""
    ml = MetaLearner(activation_works=1)
    ml.force_activate()
    c = LOSConstitutionV2()
    return MetaLearnerCycle(meta_learner=ml, constitution=c)


@pytest.fixture
def mlc_no_constitution() -> MetaLearnerCycle:
    """LOSConstitutionV2 없는 MetaLearnerCycle."""
    ml = MetaLearner(activation_works=1)
    ml.force_activate()
    return MetaLearnerCycle(meta_learner=ml)


# ─── 1. 신규 상수 ─────────────────────────────────────────────────────────────

class TestV644Constants:
    def test_tc01_weight_sum_tolerance(self):
        assert WEIGHT_SUM_TOLERANCE == 0.01

    def test_tc02_weight_entropy_min(self):
        assert WEIGHT_ENTROPY_MIN == 1.5

    def test_tc03_weight_convergence_min_cycles(self):
        assert WEIGHT_CONVERGENCE_MIN_CYCLES == 2


# ─── 2. WeightConvergenceReport 데이터클래스 ──────────────────────────────────

class TestWeightConvergenceReportDataclass:
    def test_tc04_converged_true_default_weights(self, default_weights):
        """기본 가중치(합=1.0, H≈2.27) → converged=True."""
        vals = list(default_weights.values())
        entropy = _shannon_entropy(vals)
        report = WeightConvergenceReport(
            weights_dict=default_weights,
            weights_sum=sum(vals),
            entropy=entropy,
            sum_ok=True,
            entropy_ok=entropy >= WEIGHT_ENTROPY_MIN,
            converged=True,
        )
        assert report.converged is True
        assert report.sum_ok is True
        assert report.entropy_ok is True

    def test_tc05_entropy_ok_false_for_skewed(self, skewed_weights):
        """극단 편중 가중치 → entropy_ok=False."""
        vals = list(skewed_weights.values())
        entropy = _shannon_entropy(vals)
        assert entropy < WEIGHT_ENTROPY_MIN

    def test_tc06_sum_ok_false_bad_sum(self, bad_sum_weights):
        """합 초과 가중치 → sum_ok=False."""
        total = sum(bad_sum_weights.values())
        assert abs(total - 1.0) > WEIGHT_SUM_TOLERANCE

    def test_tc07_summary_converged_string(self, default_weights):
        """summary 문자열에 CONVERGED 포함."""
        vals = list(default_weights.values())
        report = WeightConvergenceReport(
            weights_dict=default_weights,
            weights_sum=sum(vals),
            entropy=_shannon_entropy(vals),
            sum_ok=True,
            entropy_ok=True,
            converged=True,
        )
        assert "CONVERGED" in report.summary

    def test_tc08_summary_diverged_string(self, skewed_weights):
        """수렴 실패 시 summary에 DIVERGED 포함."""
        vals = list(skewed_weights.values())
        report = WeightConvergenceReport(
            weights_dict=skewed_weights,
            weights_sum=sum(vals),
            entropy=_shannon_entropy(vals),
            sum_ok=True,
            entropy_ok=False,
            converged=False,
        )
        assert "DIVERGED" in report.summary

    def test_tc09_weights_dict_field_preserved(self, default_weights):
        """weights_dict 필드가 입력값 그대로 보존."""
        vals = list(default_weights.values())
        report = WeightConvergenceReport(
            weights_dict=default_weights,
            weights_sum=sum(vals),
            entropy=_shannon_entropy(vals),
            sum_ok=True,
            entropy_ok=True,
            converged=True,
        )
        assert report.weights_dict == default_weights


# ─── 3. MetaLearnerCycle 초기화 — constitution 파라미터 ───────────────────────

class TestMetaLearnerCycleInit:
    def test_tc10_init_without_constitution(self, mlc_no_constitution):
        """constitution 없이 초기화해도 오류 없음."""
        assert mlc_no_constitution._constitution is None

    def test_tc11_init_with_constitution(self, mlc_with_constitution):
        """constitution 연결 시 _constitution 저장."""
        assert mlc_with_constitution._constitution is not None
        assert isinstance(mlc_with_constitution._constitution, LOSConstitutionV2)

    def test_tc12_weight_convergence_history_empty_on_init(self, mlc_with_constitution):
        """초기화 직후 _weight_convergence_history 빈 리스트."""
        assert mlc_with_constitution.weight_convergence_history() == []


# ─── 4. weight_convergence_check() ───────────────────────────────────────────

class TestWeightConvergenceCheck:
    def test_tc13_default_weights_converged(self, mlc_no_constitution, default_weights):
        """기본 가중치 → converged=True."""
        report = mlc_no_constitution.weight_convergence_check(default_weights)
        assert report.converged is True

    def test_tc14_skewed_weights_not_converged(self, mlc_no_constitution, skewed_weights):
        """극단 편중 가중치 → converged=False (entropy_ok=False)."""
        report = mlc_no_constitution.weight_convergence_check(skewed_weights)
        assert report.entropy_ok is False
        assert report.converged is False

    def test_tc15_bad_sum_not_converged(self, mlc_no_constitution, bad_sum_weights):
        """합 이탈 가중치 → converged=False (sum_ok=False)."""
        report = mlc_no_constitution.weight_convergence_check(bad_sum_weights)
        assert report.sum_ok is False
        assert report.converged is False

    def test_tc16_entropy_calculation_correct(self, mlc_no_constitution, default_weights):
        """entropy 값이 _shannon_entropy() 결과와 일치."""
        report = mlc_no_constitution.weight_convergence_check(default_weights)
        expected = _shannon_entropy(list(default_weights.values()))
        assert abs(report.entropy - expected) < 1e-9

    def test_tc17_weights_sum_correct(self, mlc_no_constitution, default_weights):
        """weights_sum 값이 sum() 결과와 일치."""
        report = mlc_no_constitution.weight_convergence_check(default_weights)
        assert abs(report.weights_sum - sum(default_weights.values())) < 1e-9

    def test_tc18_returns_weight_convergence_report_type(self, mlc_no_constitution, default_weights):
        """반환 타입이 WeightConvergenceReport."""
        report = mlc_no_constitution.weight_convergence_check(default_weights)
        assert isinstance(report, WeightConvergenceReport)


# ─── 5. CycleReport.weight_convergence 및 weight_converged ──────────────────

class TestCycleReportWeightConvergence:
    def test_tc19_weight_convergence_none_without_constitution(self, mlc_no_constitution):
        """constitution 없는 사이클 → weight_convergence=None."""
        report = mlc_no_constitution.run_cycle(0.40, r_scene=0.80)
        assert report.weight_convergence is None

    def test_tc20_weight_converged_true_when_none(self, mlc_no_constitution):
        """weight_convergence=None → weight_converged=True (기본)."""
        report = mlc_no_constitution.run_cycle(0.40)
        assert report.weight_converged is True

    def test_tc21_weight_convergence_set_with_constitution(self, mlc_with_constitution):
        """constitution 연결 사이클 → weight_convergence 필드 설정."""
        report = mlc_with_constitution.run_cycle(0.40, r_scene=0.80)
        assert report.weight_convergence is not None
        assert isinstance(report.weight_convergence, WeightConvergenceReport)

    def test_tc22_weight_converged_true_default_constitution(self, mlc_with_constitution):
        """기본 LOSConstitutionV2 가중치는 수렴 조건 충족."""
        report = mlc_with_constitution.run_cycle(0.40, r_scene=0.80)
        assert report.weight_converged is True

    def test_tc23_weight_convergence_in_notes(self, mlc_with_constitution):
        """수렴 결과가 CycleReport.notes에 기록."""
        report = mlc_with_constitution.run_cycle(0.40, r_scene=0.80)
        assert any("수렴" in n or "CONVERGED" in n for n in report.notes)


# ─── 6. run_cycle() — constitution 연결 시 수렴 자동 검증 ─────────────────────

class TestRunCycleWithConstitution:
    def test_tc24_first_cycle_creates_history(self, mlc_with_constitution):
        """첫 사이클 후 weight_convergence_history 길이 = 1."""
        mlc_with_constitution.run_cycle(0.40, r_scene=0.80)
        assert len(mlc_with_constitution.weight_convergence_history()) == 1

    def test_tc25_two_cycles_accumulate_history(self, mlc_with_constitution):
        """2사이클 → history 길이 = 2."""
        mlc_with_constitution.run_cycle(0.40, r_scene=0.80)
        mlc_with_constitution.run_cycle(0.38, r_scene=0.81)
        assert len(mlc_with_constitution.weight_convergence_history()) == 2

    def test_tc26_four_cycles_accumulate_history(self, mlc_with_constitution):
        """4사이클 → history 길이 = 4 (MetaLearnerCycle 전체 사이클)."""
        for loss in [0.45, 0.42, 0.40, 0.38]:
            mlc_with_constitution.run_cycle(loss, r_scene=0.80)
        assert len(mlc_with_constitution.weight_convergence_history()) == 4

    def test_tc27_convergence_entropy_above_min(self, mlc_with_constitution):
        """기본 constitution 가중치 엔트로피 ≥ WEIGHT_ENTROPY_MIN."""
        mlc_with_constitution.run_cycle(0.40, r_scene=0.80)
        history = mlc_with_constitution.weight_convergence_history()
        assert history[0].entropy >= WEIGHT_ENTROPY_MIN

    def test_tc28_convergence_sum_within_tolerance(self, mlc_with_constitution):
        """기본 constitution 가중치 합 1.0 ± WEIGHT_SUM_TOLERANCE."""
        mlc_with_constitution.run_cycle(0.40, r_scene=0.80)
        history = mlc_with_constitution.weight_convergence_history()
        assert abs(history[0].weights_sum - 1.0) <= WEIGHT_SUM_TOLERANCE


# ─── 7. weight_convergence_history() / latest_weight_convergence() ───────────

class TestWeightConvergenceHistoryMethods:
    def test_tc29_empty_history_before_cycles(self, mlc_with_constitution):
        """사이클 실행 전 history 빈 리스트."""
        assert mlc_with_constitution.weight_convergence_history() == []

    def test_tc30_latest_returns_none_before_cycles(self, mlc_with_constitution):
        """사이클 실행 전 latest_weight_convergence() = None."""
        assert mlc_with_constitution.latest_weight_convergence() is None

    def test_tc31_latest_matches_last_history(self, mlc_with_constitution):
        """latest_weight_convergence() == history[-1]."""
        mlc_with_constitution.run_cycle(0.40, r_scene=0.80)
        mlc_with_constitution.run_cycle(0.38, r_scene=0.82)
        latest = mlc_with_constitution.latest_weight_convergence()
        history = mlc_with_constitution.weight_convergence_history()
        assert latest is history[-1]

    def test_tc32_history_returns_copy(self, mlc_with_constitution):
        """weight_convergence_history()가 복사본 반환 (외부 수정 격리)."""
        mlc_with_constitution.run_cycle(0.40, r_scene=0.80)
        h1 = mlc_with_constitution.weight_convergence_history()
        h1.clear()
        h2 = mlc_with_constitution.weight_convergence_history()
        assert len(h2) == 1


# ─── 8. 수렴 실패 시나리오 ────────────────────────────────────────────────────

class TestConvergenceFailureScenario:
    def test_tc33_skewed_constitution_diverged(self):
        """극단 편중 가중치 LOSConstitution → diverged 감지."""
        # 극단 편중 ConstitutionWeights 는 __post_init__ 에서 ValueError
        # weight_convergence_check() 직접 호출로 검증
        mlc = MetaLearnerCycle()
        skewed = {"drse": 0.96, "debt": 0.01, "arc": 0.01, "tension": 0.01, "prose": 0.01}
        report = mlc.weight_convergence_check(skewed)
        assert report.converged is False
        assert report.entropy_ok is False
        assert report.sum_ok is True  # 합은 1.0
