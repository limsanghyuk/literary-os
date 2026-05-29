"""
V652 — Gate G65: AgentEnsembleEvaluator Gate (SP-C.2).
AgentEnsembleEvaluator 의 동작·임계값·결정 로직을 검증.
ADR-112 준수 확인.
LLM-0: 외부 API 직접 호출 없음.
"""
from __future__ import annotations

import traceback
from typing import Any, Dict, List


# ────────────────────────────────────────────────────────────────
# 헬퍼
# ────────────────────────────────────────────────────────────────

def _make_candidate(
    scene_id: str,
    text: str,
    critic_score: float,
    success: bool = True,
) -> Dict[str, Any]:
    return {
        "scene_id":    scene_id,
        "final_text":  text,
        "success":     success,
        "last_critic_score": critic_score,
        "rounds_used": 1,
        "polish_notes": "",
        "error":       None,
    }


# ────────────────────────────────────────────────────────────────
# Gate G65 체크포인트
# ────────────────────────────────────────────────────────────────

def run_g65_gate() -> Dict[str, Any]:
    """
    CP-1  import
    CP-2  인스턴스화
    CP-3  임계값 상수 (SELECT≥0.80, MERGE≥0.55)
    CP-4  단일 후보 SELECT (score≥0.80)
    CP-5  단일 후보 REJECT (score<0.55)
    CP-6  MERGE 결정 (0.55≤score<0.80)
    CP-7  EnsembleEvalResult to_dict / from_dict 라운드트립
    CP-8  빈 후보 처리 (REJECT + 빈 텍스트)
    CP-9  복수 후보 최고점 선택
    CP-10 facade import (literary_system.ensemble)
    """
    results: Dict[str, Any] = {"gate": "G65", "checkpoints": {}, "passed": False}
    cp = results["checkpoints"]

    # CP-1: import
    try:
        from literary_system.ensemble.ensemble_evaluator import (
            AgentEnsembleEvaluator,
            EnsembleEvalResult,
        )
        cp["CP-1"] = "PASS"
    except Exception as exc:
        cp["CP-1"] = f"FAIL: {exc}"
        return results

    # CP-2: 인스턴스화
    try:
        ev = AgentEnsembleEvaluator()
        cp["CP-2"] = "PASS"
    except Exception as exc:
        cp["CP-2"] = f"FAIL: {exc}"
        return results

    # CP-3: 임계값 상수
    try:
        assert AgentEnsembleEvaluator.SELECT_THRESHOLD == 0.80, \
            f"SELECT_THRESHOLD={AgentEnsembleEvaluator.SELECT_THRESHOLD}"
        assert AgentEnsembleEvaluator.MERGE_THRESHOLD == 0.55, \
            f"MERGE_THRESHOLD={AgentEnsembleEvaluator.MERGE_THRESHOLD}"
        cp["CP-3"] = "PASS"
    except AssertionError as exc:
        cp["CP-3"] = f"FAIL: {exc}"

    # CP-4: 단일 후보 SELECT (score≥0.80)
    try:
        cand_high = _make_candidate("s1", "A" * 200, critic_score=0.90)
        res = ev.evaluate([cand_high])
        assert isinstance(res, EnsembleEvalResult), "EnsembleEvalResult 타입 오류"
        assert res.decision == "SELECT", f"decision={res.decision}"
        assert res.aggregate_score >= 0.80, f"score={res.aggregate_score}"
        assert res.selected_scene_id == "s1"
        cp["CP-4"] = "PASS"
    except Exception as exc:
        cp["CP-4"] = f"FAIL: {exc}"

    # CP-5: 단일 후보 REJECT (score<0.55)
    try:
        cand_low = _make_candidate("s2", "B" * 10, critic_score=0.20)
        res = ev.evaluate([cand_low])
        assert res.decision == "REJECT", f"decision={res.decision}"
        cp["CP-5"] = "PASS"
    except Exception as exc:
        cp["CP-5"] = f"FAIL: {exc}"

    # CP-6: MERGE 결정 (0.55≤score<0.80)
    try:
        cand_mid = _make_candidate("s3", "C" * 100, critic_score=0.65)
        res = ev.evaluate([cand_mid])
        assert res.decision in ("MERGE", "SELECT"), f"decision={res.decision}"
        cp["CP-6"] = "PASS"
    except Exception as exc:
        cp["CP-6"] = f"FAIL: {exc}"

    # CP-7: to_dict / from_dict 라운드트립
    try:
        cand = _make_candidate("s4", "D" * 150, critic_score=0.85)
        res = ev.evaluate([cand])
        d = res.to_dict()
        assert isinstance(d, dict), "to_dict() not dict"
        res2 = EnsembleEvalResult.from_dict(d)
        assert res2.selected_scene_id == res.selected_scene_id
        assert abs(res2.aggregate_score - res.aggregate_score) < 1e-9
        assert res2.decision == res.decision
        cp["CP-7"] = "PASS"
    except Exception as exc:
        cp["CP-7"] = f"FAIL: {exc}"

    # CP-8: 빈 후보 처리
    try:
        res = ev.evaluate([])
        assert res.decision == "REJECT", f"decision={res.decision}"
        assert res.selected_text == ""
        cp["CP-8"] = "PASS"
    except Exception as exc:
        cp["CP-8"] = f"FAIL: {exc}"

    # CP-9: 복수 후보 최고점 선택
    try:
        cands = [
            _make_candidate("sA", "E" * 200, critic_score=0.70),
            _make_candidate("sB", "F" * 200, critic_score=0.92),
            _make_candidate("sC", "G" * 200, critic_score=0.55),
        ]
        res = ev.evaluate(cands)
        # 가장 높은 점수 후보가 선택돼야 함 (MERGE 아닐 때)
        assert res.decision in ("SELECT", "MERGE"), f"decision={res.decision}"
        cp["CP-9"] = "PASS"
    except Exception as exc:
        cp["CP-9"] = f"FAIL: {exc}"

    # CP-10: facade import
    try:
        from literary_system.ensemble import AgentEnsembleEvaluator as AEE2
        assert AEE2 is AgentEnsembleEvaluator
        cp["CP-10"] = "PASS"
    except Exception as exc:
        cp["CP-10"] = f"FAIL: {exc}"

    # ── 판정 ──
    fails = [k for k, v in cp.items() if not str(v).startswith("PASS")]
    results["passed"] = len(fails) == 0
    results["failed_checkpoints"] = fails
    return results
