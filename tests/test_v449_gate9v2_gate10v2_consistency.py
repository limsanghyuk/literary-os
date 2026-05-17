"""
V449 테스트: Gate9 v2 + Gate10 v2 + ConsistencyChecker
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from literary_system.gates.gate9_quality_v2 import Gate9v2, Gate9v2Result
from literary_system.gates.gate10_quality_v2 import Gate10v2, Gate10v2Result, QualityModuleViolation
from literary_system.quality.consistency_checker import (
    ConsistencyChecker,
    ConsistencyIssue,
    ConsistencyReport,
)


# ──────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────

class MockNodeScore:
    def __init__(self, s_val):
        self.breakdown = {"S_semantic": s_val}


class MockJudgeSession:
    def __init__(self, pass_rate=1.0):
        self._pass_rate = pass_rate

    def summary(self):
        return {"pass_rate": self._pass_rate, "avg_overall": 0.75}


class MockHallucinationReport:
    def __init__(self, flagged=False):
        self.flagged = flagged


class MockRecord:
    def __init__(self, tid, ep=1, text=""):
        self.trace_id      = tid
        self.render_output = {"scene": text or f"씬 텍스트 {tid}"}
        self.metadata      = {"episode_number": ep}
        self.seed_contract = {"user_prompt": f"씬 {tid}을 써라"}


@pytest.fixture
def gate9():
    return Gate9v2()


@pytest.fixture
def gate10():
    return Gate10v2()


@pytest.fixture
def checker():
    return ConsistencyChecker()


@pytest.fixture
def clean_records():
    return [MockRecord(f"t{i}", ep=i+1) for i in range(5)]


# ──────────────────────────────────────────────
# TestGate9v2Init
# ──────────────────────────────────────────────

class TestGate9v2Init:
    def test_default_thresholds(self, gate9):
        assert gate9.MEAN_S_MIN == 0.10
        assert gate9.RESIDUE_CORRECTION_MAX == 0.50
        assert gate9.JUDGE_PASS_RATE_MIN == 0.50
        assert gate9.HALLUCINATION_RATE_MAX == 0.30

    def test_run_no_args_passes(self, gate9):
        result = gate9.run()
        assert result.passed is True

    def test_result_is_gate9v2result(self, gate9):
        result = gate9.run()
        assert isinstance(result, Gate9v2Result)


# ──────────────────────────────────────────────
# TestGate9v2DRSE
# ──────────────────────────────────────────────

class TestGate9v2DRSE:
    def test_good_drse_passes(self, gate9):
        nodes = [MockNodeScore(0.5), MockNodeScore(0.4), MockNodeScore(0.3)]
        result = gate9.run(node_scores=nodes)
        assert result.drse_passed is True

    def test_low_drse_fails(self):
        g = Gate9v2()
        nodes = [MockNodeScore(0.05), MockNodeScore(0.04)]
        result = g.run(node_scores=nodes)
        assert result.drse_passed is False
        assert "mean_s" in result.reason

    def test_mean_s_score_computed(self, gate9):
        nodes = [MockNodeScore(0.3), MockNodeScore(0.5)]
        result = gate9.run(node_scores=nodes)
        assert abs(result.mean_s_score - 0.4) < 0.001

    def test_empty_node_scores_passes(self, gate9):
        result = gate9.run(node_scores=[])
        assert result.drse_passed is True


# ──────────────────────────────────────────────
# TestGate9v2Judge
# ──────────────────────────────────────────────

class TestGate9v2Judge:
    def test_good_judge_passes(self, gate9):
        session = MockJudgeSession(pass_rate=0.9)
        result  = gate9.run(judge_session=session)
        assert result.judge_passed is True

    def test_low_judge_fails(self):
        g       = Gate9v2()
        session = MockJudgeSession(pass_rate=0.2)
        result  = g.run(judge_session=session)
        assert result.judge_passed is False
        assert "judge_pass_rate" in result.reason

    def test_no_session_skips_judge(self, gate9):
        result = gate9.run(judge_session=None)
        assert result.judge_passed is True
        assert result.judge_pass_rate == 1.0

    def test_judge_pass_rate_recorded(self, gate9):
        session = MockJudgeSession(pass_rate=0.75)
        result  = gate9.run(judge_session=session)
        assert result.judge_pass_rate == 0.75


# ──────────────────────────────────────────────
# TestGate9v2Hallucination
# ──────────────────────────────────────────────

class TestGate9v2Hallucination:
    def test_no_hallucination_passes(self, gate9):
        reports = [MockHallucinationReport(False)] * 5
        result  = gate9.run(hallucination_reports=reports)
        assert result.hallucination_passed is True

    def test_high_hallucination_fails(self):
        g       = Gate9v2()
        reports = [MockHallucinationReport(True)] * 4 + [MockHallucinationReport(False)]
        result  = g.run(hallucination_reports=reports)
        assert result.hallucination_passed is False
        assert "hallucination_rate" in result.reason

    def test_hallucination_rate_computed(self, gate9):
        reports = [MockHallucinationReport(True), MockHallucinationReport(False)]
        result  = gate9.run(hallucination_reports=reports)
        assert abs(result.hallucination_rate - 0.5) < 0.001

    def test_no_reports_skips(self, gate9):
        result = gate9.run(hallucination_reports=None)
        assert result.hallucination_passed is True


# ──────────────────────────────────────────────
# TestGate9v2Combined
# ──────────────────────────────────────────────

class TestGate9v2Combined:
    def test_all_good_passes(self, gate9):
        result = gate9.run(
            node_scores=[MockNodeScore(0.4)],
            judge_session=MockJudgeSession(0.9),
            hallucination_reports=[MockHallucinationReport(False)],
        )
        assert result.passed is True

    def test_one_fail_fails_overall(self):
        g = Gate9v2()
        result = g.run(
            node_scores=[MockNodeScore(0.4)],
            judge_session=MockJudgeSession(0.1),  # 낮은 pass_rate
            hallucination_reports=[MockHallucinationReport(False)],
        )
        assert result.passed is False
        assert result.judge_passed is False

    def test_to_dict_keys(self, gate9):
        result = gate9.run()
        d = result.to_dict()
        assert "passed" in d
        assert "drse_passed" in d
        assert "judge_passed" in d
        assert "hallucination_passed" in d
        assert "mean_s_score" in d
        assert "judge_pass_rate" in d
        assert "hallucination_rate" in d
        assert "sample_count" in d


# ──────────────────────────────────────────────
# TestGate10v2Init
# ──────────────────────────────────────────────

class TestGate10v2Init:
    def test_default_init(self, gate10):
        assert gate10 is not None

    def test_run_no_adapters_passes(self, gate10):
        result = gate10.run(adapters=None)
        assert isinstance(result, Gate10v2Result)

    def test_quality_modules_all_checked(self, gate10):
        result = gate10.run(adapters=None)
        assert result.quality_modules_checked == 4

    def test_quality_modules_pass(self, gate10):
        result = gate10.run(adapters=None)
        assert result.quality_modules_passed is True


# ──────────────────────────────────────────────
# TestGate10v2QualityModules
# ──────────────────────────────────────────────

class TestGate10v2QualityModules:
    def test_llm_judge_interface_verified(self, gate10):
        result = gate10.run(adapters=None)
        # LLMJudge: evaluate_one, evaluate, stats が存在
        assert result.quality_modules_passed is True

    def test_no_quality_violations(self, gate10):
        result = gate10.run(adapters=None)
        assert len(result.quality_violations) == 0

    def test_result_to_dict(self, gate10):
        result = gate10.run(adapters=None)
        d = result.to_dict()
        assert "passed" in d
        assert "quality_modules_passed" in d
        assert "quality_modules_checked" in d
        assert "violation_count" in d

    def test_passed_is_true_without_adapters(self, gate10):
        result = gate10.run(adapters=None)
        assert result.passed is True

    def test_adapter_contract_skipped_when_none(self, gate10):
        result = gate10.run(adapters=None)
        assert result.adapter_contract_passed is True
        assert result.adapters_checked == 0


# ──────────────────────────────────────────────
# TestConsistencyCheckerInit
# ──────────────────────────────────────────────

class TestConsistencyCheckerInit:
    def test_default_init(self, checker):
        assert checker.error_threshold == 1

    def test_custom_threshold(self):
        cc = ConsistencyChecker(error_threshold=3)
        assert cc.error_threshold == 3

    def test_custom_check_fn(self):
        custom_fn = lambda recs: []
        cc = ConsistencyChecker(check_fn=custom_fn)
        assert cc.check_fn is custom_fn

    def test_initial_history_empty(self, checker):
        assert checker._history == []


# ──────────────────────────────────────────────
# TestConsistencyCheckerCheck
# ──────────────────────────────────────────────

class TestConsistencyCheckerCheck:
    def test_clean_records_consistent(self, checker, clean_records):
        report = checker.check(clean_records)
        assert report.consistent is True
        assert report.error_count == 0

    def test_duplicate_ids_detected(self, checker):
        recs = [MockRecord("t1", 1), MockRecord("t1", 2)]
        report = checker.check(recs)
        assert any(i.issue_type == "duplicate_id" for i in report.issues)
        assert report.consistent is False

    def test_timeline_regression_detected(self, checker):
        recs = [MockRecord("t1", 3), MockRecord("t2", 1)]
        report = checker.check(recs)
        assert any(i.issue_type == "timeline_regression" for i in report.issues)

    def test_timeline_regression_is_warning(self, checker):
        recs = [MockRecord("t1", 3), MockRecord("t2", 1)]
        report = checker.check(recs)
        timeline_issues = [i for i in report.issues if i.issue_type == "timeline_regression"]
        assert timeline_issues[0].severity == "warning"

    def test_report_scene_count(self, checker, clean_records):
        report = checker.check(clean_records)
        assert report.scene_count == len(clean_records)

    def test_report_is_consistency_report(self, checker, clean_records):
        report = checker.check(clean_records)
        assert isinstance(report, ConsistencyReport)

    def test_issues_are_immutable(self, checker):
        recs = [MockRecord("x", 1), MockRecord("x", 2)]
        report = checker.check(recs)
        for issue in report.issues:
            assert isinstance(issue, ConsistencyIssue)
            with pytest.raises((AttributeError, TypeError)):
                issue.severity = "changed"

    def test_report_stored_in_history(self, checker, clean_records):
        checker.check(clean_records)
        assert len(checker._history) == 1

    def test_to_dict_keys(self, checker, clean_records):
        report = checker.check(clean_records)
        d = report.to_dict()
        assert "scene_count" in d
        assert "consistent" in d
        assert "error_count" in d
        assert "warning_count" in d
        assert "issue_count" in d
        assert "issues" in d

    def test_custom_check_fn_used(self):
        called = []
        def custom_fn(recs):
            called.append(True)
            return []
        cc = ConsistencyChecker(check_fn=custom_fn)
        cc.check([MockRecord("t1")])
        assert len(called) == 1


# ──────────────────────────────────────────────
# TestConsistencyCheckerStats
# ──────────────────────────────────────────────

class TestConsistencyCheckerStats:
    def test_stats_keys(self, checker, clean_records):
        checker.check(clean_records)
        s = checker.stats()
        assert "total_checks" in s
        assert "consistent_count" in s
        assert "inconsistent_count" in s
        assert "total_issues" in s
        assert "consistency_rate" in s

    def test_stats_zero_on_empty(self):
        cc = ConsistencyChecker()
        s  = cc.stats()
        assert s["total_checks"] == 0
        assert s["consistency_rate"] == 1.0

    def test_stats_counts(self, checker):
        checker.check([MockRecord("t1", 1), MockRecord("t2", 2)])
        checker.check([MockRecord("t3", 1), MockRecord("t3", 2)])  # dup
        s = checker.stats()
        assert s["total_checks"] == 2
        assert s["consistent_count"] == 1
        assert s["inconsistent_count"] == 1

    def test_consistency_rate(self, checker):
        checker.check([MockRecord("t1")])
        checker.check([MockRecord("t2")])
        s = checker.stats()
        assert s["consistency_rate"] == 1.0


# ──────────────────────────────────────────────
# TestV449ReleaseFunctions
# ──────────────────────────────────────────────

class TestV449ReleaseFunctions:
    def test_gate9_v2_fn_passes(self):
        from literary_system.gates.gate9_quality_v2 import _gate9_v2_fn
        result = _gate9_v2_fn()
        assert result["pass"] is True

    def test_gate10_v2_fn_passes(self):
        from literary_system.gates.gate10_quality_v2 import _gate10_v2_fn
        result = _gate10_v2_fn()
        assert result["pass"] is True

    def test_gate9_result_has_details(self):
        from literary_system.gates.gate9_quality_v2 import _gate9_v2_fn
        result = _gate9_v2_fn()
        assert "details" in result
        assert "mean_s_score" in result["details"]

    def test_gate10_result_has_details(self):
        from literary_system.gates.gate10_quality_v2 import _gate10_v2_fn
        result = _gate10_v2_fn()
        assert "details" in result
        assert result["details"]["quality_modules_checked"] == 4
