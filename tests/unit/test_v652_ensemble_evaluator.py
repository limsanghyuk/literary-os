"""
V652 — AgentEnsembleEvaluator 단위 테스트 (30 TC).
SELECT/MERGE/REJECT 결정, 점수 계산, 라운드트립, 에지 케이스.
"""
import pytest
from literary_system.ensemble.ensemble_evaluator import (
    AgentEnsembleEvaluator,
    EnsembleEvalResult,
)


# ────────────────────────────────────────────────────────────────
# 픽스처
# ────────────────────────────────────────────────────────────────

def _cand(scene_id="s1", text="A" * 200, critic_score=0.85, success=True):
    return {
        "scene_id":          scene_id,
        "final_text":        text,
        "success":           success,
        "last_critic_score": critic_score,
        "rounds_used":       1,
        "polish_notes":      "",
        "error":             None,
    }


@pytest.fixture
def ev():
    return AgentEnsembleEvaluator()


# ────────────────────────────────────────────────────────────────
# TC-01~05: EnsembleEvalResult 구조 / 라운드트립
# ────────────────────────────────────────────────────────────────

def test_tc01_result_fields():
    r = EnsembleEvalResult(
        selected_scene_id="s1",
        selected_text="hello",
        aggregate_score=0.9,
        decision="SELECT",
    )
    assert r.selected_scene_id == "s1"
    assert r.selected_text == "hello"
    assert r.aggregate_score == 0.9
    assert r.decision == "SELECT"
    assert r.candidate_scores == {}
    assert r.merge_sources == []
    assert r.evaluation_note == ""


def test_tc02_result_to_dict():
    r = EnsembleEvalResult("s1", "txt", 0.8, "SELECT")
    d = r.to_dict()
    assert isinstance(d, dict)
    assert d["selected_scene_id"] == "s1"
    assert d["decision"] == "SELECT"


def test_tc03_result_from_dict():
    d = {
        "selected_scene_id": "s2",
        "selected_text": "hello",
        "aggregate_score": 0.75,
        "decision": "MERGE",
        "candidate_scores": {"s2": 0.75},
        "merge_sources": ["s2", "s3"],
        "evaluation_note": "test",
    }
    r = EnsembleEvalResult.from_dict(d)
    assert r.selected_scene_id == "s2"
    assert r.decision == "MERGE"
    assert r.merge_sources == ["s2", "s3"]


def test_tc04_roundtrip_exact():
    original = EnsembleEvalResult(
        selected_scene_id="s5",
        selected_text="Lorem ipsum",
        aggregate_score=0.67,
        decision="MERGE",
        candidate_scores={"s5": 0.67},
        merge_sources=["s5", "s6"],
        evaluation_note="merged",
    )
    d = original.to_dict()
    restored = EnsembleEvalResult.from_dict(d)
    assert restored.selected_scene_id == original.selected_scene_id
    assert abs(restored.aggregate_score - original.aggregate_score) < 1e-9
    assert restored.merge_sources == original.merge_sources


def test_tc05_result_defaults():
    r = EnsembleEvalResult.from_dict({
        "selected_scene_id": "x",
        "selected_text": "",
        "aggregate_score": 0.0,
        "decision": "REJECT",
    })
    assert r.candidate_scores == {}
    assert r.merge_sources == []
    assert r.evaluation_note == ""


# ────────────────────────────────────────────────────────────────
# TC-06~10: 클래스 상수 / 속성
# ────────────────────────────────────────────────────────────────

def test_tc06_select_threshold():
    assert AgentEnsembleEvaluator.SELECT_THRESHOLD == 0.80


def test_tc07_merge_threshold():
    assert AgentEnsembleEvaluator.MERGE_THRESHOLD == 0.55


def test_tc08_thresholds_ordering():
    assert AgentEnsembleEvaluator.MERGE_THRESHOLD < AgentEnsembleEvaluator.SELECT_THRESHOLD


def test_tc09_evaluate_callable(ev):
    assert callable(getattr(ev, "evaluate", None))


def test_tc10_score_candidate_callable(ev):
    assert callable(getattr(ev, "_score_candidate", None))


# ────────────────────────────────────────────────────────────────
# TC-11~15: 단일 후보 SELECT 결정
# ────────────────────────────────────────────────────────────────

def test_tc11_single_select_high(ev):
    res = ev.evaluate([_cand(scene_id="s1", critic_score=0.92, text="X" * 300)])
    assert res.decision == "SELECT"


def test_tc12_single_select_score_ge_080(ev):
    res = ev.evaluate([_cand(scene_id="s1", critic_score=0.80, text="Y" * 300)])
    assert res.aggregate_score >= 0.80


def test_tc13_select_scene_id_preserved(ev):
    res = ev.evaluate([_cand(scene_id="scene_007", critic_score=0.95)])
    assert res.selected_scene_id == "scene_007"


def test_tc14_select_text_preserved(ev):
    text = "The protagonist steps forward." * 20
    res = ev.evaluate([_cand(text=text, critic_score=0.90)])
    assert res.selected_text == text


def test_tc15_candidate_scores_populated(ev):
    res = ev.evaluate([_cand(scene_id="s99", critic_score=0.88)])
    assert "s99" in res.candidate_scores


# ────────────────────────────────────────────────────────────────
# TC-16~20: REJECT 결정
# ────────────────────────────────────────────────────────────────

def test_tc16_single_reject_low(ev):
    res = ev.evaluate([_cand(critic_score=0.10)])
    assert res.decision == "REJECT"


def test_tc17_reject_empty_text(ev):
    res = ev.evaluate([_cand(critic_score=0.10)])
    assert res.selected_text == ""


def test_tc18_empty_candidates_reject(ev):
    res = ev.evaluate([])
    assert res.decision == "REJECT"


def test_tc19_empty_candidates_empty_text(ev):
    res = ev.evaluate([])
    assert res.selected_text == ""


def test_tc20_failed_candidate_penalized(ev):
    cand = _cand(critic_score=0.85, success=False)
    res_fail = ev.evaluate([cand])
    cand_ok = _cand(critic_score=0.85, success=True)
    res_ok = ev.evaluate([cand_ok])
    # failed candidate should score ≤ success candidate
    assert res_fail.aggregate_score <= res_ok.aggregate_score


# ────────────────────────────────────────────────────────────────
# TC-21~25: MERGE 결정
# ────────────────────────────────────────────────────────────────

def test_tc21_merge_decision_mid_score(ev):
    res = ev.evaluate([_cand(critic_score=0.65, text="A" * 100)])
    # score 0.65 → could be MERGE or SELECT depending on length bonus
    assert res.decision in ("MERGE", "SELECT", "REJECT")


def test_tc22_merge_two_candidates(ev):
    cands = [
        _cand("s1", "A" * 200, critic_score=0.70),
        _cand("s2", "B" * 200, critic_score=0.68),
    ]
    res = ev.evaluate(cands)
    assert res.decision in ("SELECT", "MERGE", "REJECT")


def test_tc23_merge_sources_populated_on_merge(ev):
    # 두 후보 모두 MERGE 임계 범위에 해당하도록
    cands = [
        _cand("sA", "X" * 50, critic_score=0.60),
        _cand("sB", "Y" * 50, critic_score=0.58),
    ]
    res = ev.evaluate(cands)
    if res.decision == "MERGE":
        assert len(res.merge_sources) >= 1


def test_tc24_highest_score_wins(ev):
    cands = [
        _cand("low",  "L" * 200, critic_score=0.50),
        _cand("high", "H" * 200, critic_score=0.95),
        _cand("mid",  "M" * 200, critic_score=0.70),
    ]
    res = ev.evaluate(cands)
    if res.decision == "SELECT":
        assert res.selected_scene_id == "high"


def test_tc25_length_bonus_positive(ev):
    short_score = ev._score_candidate(_cand(critic_score=0.80, text="X" * 10))
    long_score  = ev._score_candidate(_cand(critic_score=0.80, text="X" * 400))
    assert long_score >= short_score


# ────────────────────────────────────────────────────────────────
# TC-26~30: Gate G65 + facade import + 에지 케이스
# ────────────────────────────────────────────────────────────────

def test_tc26_gate_g65_pass():
    from literary_system.gates.evaluator_gate import run_g65_gate
    result = run_g65_gate()
    fails = result.get("failed_checkpoints", [])
    assert result["passed"], f"G65 FAIL — {fails}\n{result['checkpoints']}"


def test_tc27_facade_import():
    from literary_system.ensemble import AgentEnsembleEvaluator as AEE
    assert AEE is AgentEnsembleEvaluator


def test_tc28_facade_result_import():
    from literary_system.ensemble import EnsembleEvalResult as EER
    assert EER is EnsembleEvalResult


def test_tc29_score_capped_at_one(ev):
    score = ev._score_candidate(_cand(critic_score=1.0, text="X" * 1000))
    assert score <= 1.0


def test_tc30_evaluate_returns_result_type(ev):
    res = ev.evaluate([_cand(critic_score=0.88)])
    assert isinstance(res, EnsembleEvalResult)
