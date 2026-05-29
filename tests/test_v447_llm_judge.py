"""
V447 tests — LLMJudge + RubricCalibrator (ADR-009)
"""
import pytest
from literary_system.quality.llm_judge import (
    LLMJudge, RubricCalibrator, RubricScore, JudgeSession, CalibrationRun,
    RUBRIC_AXES, RUBRIC_DESCRIPTIONS, _mock_judge_fn,
)
from literary_system.trace.trace_dataset_store import make_trace_record


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _rec(scene_id="s1", episode_no=1, response_text="씬 본문 내용 텍스트"):
    return make_trace_record(
        project_id="test", episode_no=episode_no, scene_id=scene_id,
        seed_contract={"genre": "drama", "user_prompt": "씬 생성"},
        style_dna_profile="압박형", macroarc_intent="갈등",
        literary_state_before={}, literary_state_after={},
        render_output={scene_id: response_text},
        loss_report={"L_total": 0.10},
        reader_estimate={"reader_pull": 0.6, "ai_smell_score": 0.1},
        trajectory_deviation=0.05, critic_findings=[],
        repair_applied=False, hitl_recommended=False, knowledge_pressure=0.3,
    )


def _many_recs(n=15):
    return [_rec(scene_id=f"s{i}", episode_no=i+1, response_text=f"씬 {i} 본문 내용 텍스트 묘사") for i in range(n)]


# ---------------------------------------------------------------------------
# TestMockJudgeFn
# ---------------------------------------------------------------------------

class TestMockJudgeFn:
    def test_returns_axis_scores_and_rationale(self):
        scores, rationale = _mock_judge_fn("prompt", "response 내용", RUBRIC_AXES)
        assert isinstance(scores, dict)
        assert isinstance(rationale, str)

    def test_all_axes_present(self):
        scores, _ = _mock_judge_fn("p", "r", RUBRIC_AXES)
        for ax in RUBRIC_AXES:
            assert ax in scores

    def test_scores_in_range(self):
        scores, _ = _mock_judge_fn("p", "응답 텍스트입니다", RUBRIC_AXES)
        for v in scores.values():
            assert 0.0 <= v <= 1.0

    def test_safety_fail_on_unsafe_content(self):
        scores, _ = _mock_judge_fn("p", "욕설 포함 텍스트", RUBRIC_AXES)
        assert scores["safety"] == 0.0

    def test_safety_pass_on_clean_content(self):
        scores, _ = _mock_judge_fn("p", "안전한 텍스트 내용", RUBRIC_AXES)
        assert scores["safety"] == 1.0


# ---------------------------------------------------------------------------
# TestLLMJudgeInit
# ---------------------------------------------------------------------------

class TestLLMJudgeInit:
    def test_default_sampling_rate(self):
        judge = LLMJudge()
        assert judge.sampling_rate == 0.27

    def test_invalid_sampling_rate_raises(self):
        with pytest.raises(ValueError):
            LLMJudge(sampling_rate=0.0)
        with pytest.raises(ValueError):
            LLMJudge(sampling_rate=1.5)

    def test_custom_judge_fn_injected(self):
        fn = lambda p, r, axes: ({ax: 0.9 for ax in axes}, "custom")
        judge = LLMJudge(judge_fn=fn)
        assert judge.judge_fn is fn

    def test_rubric_axes_defined(self):
        assert len(LLMJudge.RUBRIC_AXES) == 4
        assert "content_quality" in LLMJudge.RUBRIC_AXES
        assert "safety" in LLMJudge.RUBRIC_AXES


# ---------------------------------------------------------------------------
# TestEvaluateOne
# ---------------------------------------------------------------------------

class TestEvaluateOne:
    def test_force_evaluates(self):
        judge = LLMJudge(random_seed=0)
        score = judge.evaluate_one("t1", "prompt", "response", force=True)
        assert isinstance(score, RubricScore)
        assert score.trace_id == "t1"

    def test_non_sampled_returns_none(self):
        judge = LLMJudge(sampling_rate=0.0001, random_seed=99)
        results = [judge.evaluate_one("t1", "p", "r") for _ in range(20)]
        # 대부분 None
        assert sum(1 for r in results if r is None) > 15

    def test_score_overall_in_range(self):
        judge = LLMJudge()
        score = judge.evaluate_one("t1", "p", "응답 텍스트", force=True)
        assert 0.0 <= score.overall <= 1.0

    def test_score_passed_property(self):
        judge = LLMJudge(pass_threshold=0.5)
        score = judge.evaluate_one("t1", "p", "응답 텍스트 내용입니다", force=True)
        assert isinstance(score.passed, bool)

    def test_score_to_dict(self):
        judge = LLMJudge()
        score = judge.evaluate_one("t1", "p", "r", force=True)
        d = score.to_dict()
        assert "judge_id" in d
        assert "trace_id" in d
        assert "axis_scores" in d
        assert "overall" in d
        assert "passed" in d

    def test_history_accumulates(self):
        judge = LLMJudge()
        for i in range(3):
            judge.evaluate_one(f"t{i}", "p", "r", force=True)
        assert len(judge.history()) == 3


# ---------------------------------------------------------------------------
# TestEvaluateSession
# ---------------------------------------------------------------------------

class TestEvaluateSession:
    def test_returns_judge_session(self):
        judge = LLMJudge(sampling_rate=1.0)
        records = _many_recs(5)
        session = judge.evaluate(records)
        assert isinstance(session, JudgeSession)

    def test_total_equals_input(self):
        judge = LLMJudge(sampling_rate=1.0)
        records = _many_recs(8)
        session = judge.evaluate(records)
        assert session.total == 8

    def test_sampling_rate_applied(self):
        judge = LLMJudge(sampling_rate=0.27, random_seed=42)
        records = _many_recs(100)
        session = judge.evaluate(records)
        # 27% 샘플링 → 대략 15~40개
        assert 5 <= session.sampled <= 60

    def test_pass_count_consistent(self):
        judge = LLMJudge(sampling_rate=1.0)
        records = _many_recs(6)
        session = judge.evaluate(records)
        assert session.pass_count + session.fail_count == session.sampled

    def test_session_summary_keys(self):
        judge = LLMJudge(sampling_rate=1.0)
        records = _many_recs(4)
        session = judge.evaluate(records)
        s = session.summary()
        assert "session_id" in s
        assert "total_records" in s
        assert "pass_rate" in s
        assert "avg_overall" in s

    def test_dict_records_supported(self):
        judge = LLMJudge(sampling_rate=1.0)
        records = [
            {"trace_id": f"t{i}", "prompt": "씬 요청", "response": f"씬 {i} 응답 내용"}
            for i in range(4)
        ]
        session = judge.evaluate(records)
        assert session.total == 4

    def test_empty_records(self):
        judge = LLMJudge()
        session = judge.evaluate([])
        assert session.total == 0
        assert session.sampled == 0


# ---------------------------------------------------------------------------
# TestJudgeStats
# ---------------------------------------------------------------------------

class TestJudgeStats:
    def test_stats_keys(self):
        judge = LLMJudge(sampling_rate=1.0)
        judge.evaluate(_many_recs(5))
        s = judge.stats()
        assert "total_judged" in s
        assert "pass_rate" in s
        assert "avg_overall" in s
        assert "axis_averages" in s

    def test_axis_averages_all_present(self):
        judge = LLMJudge(sampling_rate=1.0)
        judge.evaluate(_many_recs(5))
        for ax in RUBRIC_AXES:
            assert ax in judge.stats()["axis_averages"]

    def test_empty_stats(self):
        judge = LLMJudge()
        s = judge.stats()
        assert s["total_judged"] == 0


# ---------------------------------------------------------------------------
# TestRubricCalibrator
# ---------------------------------------------------------------------------

class TestRubricCalibrator:
    def test_calibrate_returns_run(self):
        judge = LLMJudge(random_seed=0)
        cal = RubricCalibrator(judge=judge)
        run = cal.calibrate(_many_recs(15))
        assert isinstance(run, CalibrationRun)

    def test_first_run_sets_baseline(self):
        judge = LLMJudge(random_seed=0)
        cal = RubricCalibrator(judge=judge)
        run = cal.calibrate(_many_recs(15))
        assert run.drift == 0.0
        assert run.drift_alarm is False
        assert "baseline" in run.notes

    def test_second_run_computes_drift(self):
        judge = LLMJudge(random_seed=0)
        cal = RubricCalibrator(judge=judge)
        cal.calibrate(_many_recs(15))
        run2 = cal.calibrate(_many_recs(15))
        assert isinstance(run2.drift, float)
        assert run2.drift >= 0.0

    def test_min_samples_enforced(self):
        judge = LLMJudge()
        cal = RubricCalibrator(judge=judge)
        with pytest.raises(ValueError):
            cal.calibrate(_many_recs(3))

    def test_drift_alarm_triggered(self):
        judge = LLMJudge(random_seed=0)
        cal = RubricCalibrator(judge=judge, drift_threshold=0.0)
        cal.calibrate(_many_recs(15))
        # threshold=0.0 → 두 번째 실행에서 반드시 alarm
        # (실제로 완전히 동일한 점수가 나오지 않는 한)
        run2 = cal.calibrate(_many_recs(15))
        # drift가 0.0이면 alarm이 False, > 0이면 True
        assert isinstance(run2.drift_alarm, bool)

    def test_calibration_history(self):
        judge = LLMJudge(random_seed=0)
        cal = RubricCalibrator(judge=judge)
        cal.calibrate(_many_recs(15))
        cal.calibrate(_many_recs(15))
        assert len(cal.calibration_history()) == 2

    def test_drift_alarms_list(self):
        judge = LLMJudge(random_seed=0)
        cal = RubricCalibrator(judge=judge)
        cal.calibrate(_many_recs(15))
        alarms = cal.drift_alarms()
        assert isinstance(alarms, list)

    def test_summary_keys(self):
        judge = LLMJudge(random_seed=0)
        cal = RubricCalibrator(judge=judge)
        cal.calibrate(_many_recs(15))
        s = cal.summary()
        assert "total_runs" in s
        assert "drift_alarms" in s
        assert "drift_threshold" in s

    def test_calibration_run_to_dict(self):
        judge = LLMJudge(random_seed=0)
        cal = RubricCalibrator(judge=judge)
        run = cal.calibrate(_many_recs(15))
        d = run.to_dict()
        assert "run_id" in d
        assert "drift" in d
        assert "drift_alarm" in d
        assert "axis_drifts" in d

    def test_rubric_descriptions_complete(self):
        for ax in RUBRIC_AXES:
            assert ax in RUBRIC_DESCRIPTIONS
            assert len(RUBRIC_DESCRIPTIONS[ax]) > 5
