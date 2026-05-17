"""
V449: Gate9 v2 — DRSE + LLMJudge 통합 품질 게이트
Gate9 v1(DRSE S-score)에 LLMJudge pass_rate + HallucinationDetector 검사를 추가.

기준:
  MEAN_S_MIN              = 0.10   (DRSE 평균 S 점수)
  RESIDUE_CORRECTION_MAX  = 0.50
  JUDGE_PASS_RATE_MIN     = 0.50   (LLMJudge 세션 pass_rate 하한)
  HALLUCINATION_RATE_MAX  = 0.30   (허상 탐지 비율 상한)

LLM 0회.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Gate9v2Result:
    passed:                  bool
    drse_passed:             bool
    judge_passed:            bool
    hallucination_passed:    bool
    mean_s_score:            float
    judge_pass_rate:         float
    hallucination_rate:      float
    sample_count:            int
    reason:                  str = ""
    details:                 Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "passed":               self.passed,
            "drse_passed":          self.drse_passed,
            "judge_passed":         self.judge_passed,
            "hallucination_passed": self.hallucination_passed,
            "mean_s_score":         round(self.mean_s_score, 4),
            "judge_pass_rate":      round(self.judge_pass_rate, 4),
            "hallucination_rate":   round(self.hallucination_rate, 4),
            "sample_count":         self.sample_count,
            "reason":               self.reason,
        }


class Gate9v2:
    """
    Gate 9 v2: DRSE + LLMJudge + HallucinationDetector 통합 게이트.

    judge_session: LLMJudge.evaluate()가 반환한 JudgeSession (없으면 judge 검사 생략)
    hallucination_reports: HallucinationDetector.detect_batch() 결과 (없으면 생략)
    """

    MEAN_S_MIN             = 0.10
    RESIDUE_CORRECTION_MAX = 0.50
    JUDGE_PASS_RATE_MIN    = 0.50
    HALLUCINATION_RATE_MAX = 0.30

    def run(
        self,
        node_scores:           list = None,
        judge_session=None,
        hallucination_reports: list = None,
    ) -> Gate9v2Result:
        reasons  = []
        details  = {}

        # ── DRSE 검사 ─────────────────────────────
        drse_passed = True
        mean_s      = 0.0
        sample_count = 0

        if node_scores:
            s_values        = []
            residue_min_cnt = 0
            RESIDUE_MIN_S   = 0.15
            for ns in node_scores:
                bd    = getattr(ns, "breakdown", {})
                s_val = bd.get("S_semantic")
                if s_val is not None:
                    s_values.append(float(s_val))
                    if abs(float(s_val) - RESIDUE_MIN_S) < 1e-6:
                        residue_min_cnt += 1
            if s_values:
                mean_s       = sum(s_values) / len(s_values)
                corr_ratio   = residue_min_cnt / len(s_values)
                sample_count = len(s_values)
                if mean_s < self.MEAN_S_MIN:
                    drse_passed = False
                    reasons.append(f"mean_s={mean_s:.4f} < {self.MEAN_S_MIN}")
                if corr_ratio > self.RESIDUE_CORRECTION_MAX:
                    drse_passed = False
                    reasons.append(f"correction_ratio={corr_ratio:.2%} > {self.RESIDUE_CORRECTION_MAX:.0%}")
                details["drse"] = {"mean_s": round(mean_s, 4), "correction_ratio": round(corr_ratio, 4)}

        # ── LLMJudge 검사 ─────────────────────────
        judge_passed   = True
        judge_pass_rate = 1.0

        if judge_session is not None:
            summary = judge_session.summary() if hasattr(judge_session, "summary") else {}
            judge_pass_rate = summary.get("pass_rate", 1.0)
            if judge_pass_rate < self.JUDGE_PASS_RATE_MIN:
                judge_passed = False
                reasons.append(f"judge_pass_rate={judge_pass_rate:.2%} < {self.JUDGE_PASS_RATE_MIN:.0%}")
            details["judge"] = {"pass_rate": round(judge_pass_rate, 4)}

        # ── 허상 탐지 검사 ─────────────────────────
        hallucination_passed = True
        hallucination_rate   = 0.0

        if hallucination_reports:
            total    = len(hallucination_reports)
            flagged  = sum(1 for r in hallucination_reports if getattr(r, "flagged", False))
            hallucination_rate = flagged / total if total > 0 else 0.0
            if hallucination_rate > self.HALLUCINATION_RATE_MAX:
                hallucination_passed = False
                reasons.append(
                    f"hallucination_rate={hallucination_rate:.2%} > {self.HALLUCINATION_RATE_MAX:.0%}"
                )
            details["hallucination"] = {
                "total": total, "flagged": flagged,
                "rate": round(hallucination_rate, 4),
            }

        passed = drse_passed and judge_passed and hallucination_passed

        return Gate9v2Result(
            passed=passed,
            drse_passed=drse_passed,
            judge_passed=judge_passed,
            hallucination_passed=hallucination_passed,
            mean_s_score=mean_s,
            judge_pass_rate=judge_pass_rate,
            hallucination_rate=hallucination_rate,
            sample_count=sample_count,
            reason=", ".join(reasons) if reasons else "ok",
            details=details,
        )


def _gate9_v2_fn() -> dict:
    """Release Gate — Gate9 v2 실행 함수."""
    try:
        from literary_system.relation_graph.relation_graph_store import (
            RelationGraphStore, StoryNode, StoryEdge, NodeType,
        )
        from literary_system.drse.drse_engine import (
            DRSEScorer, KnowledgeBoundaryGate, TFIDFSemanticScorer,
        )
        from literary_system.quality.llm_judge import LLMJudge
        from literary_system.quality.hallucination_safety import HallucinationDetector

        # DRSE
        rgs   = RelationGraphStore()
        nodes = [
            StoryNode("n1", NodeType.CHARACTER.value,    "형사가 살인 사건 수집하는 단서 씬", origin_episode=1),
            StoryNode("n2", NodeType.FACT_PUBLIC.value,  "살인 사건 형사가 단서 수집 수사",   origin_episode=1),
            StoryNode("n3", NodeType.FORESHADOWING.value,"단서 씬 빨간 우산 수집하는",        origin_episode=2, is_resolved=False),
            StoryNode("n4", NodeType.WORLD_RULE.value,   "사건 수집하는 단서 규칙 씬",         origin_episode=1),
            StoryNode("n5", NodeType.CHARACTER.value,    "형사가 살인 씬 조력자",              origin_episode=1),
        ]
        for n in nodes:
            rgs.add_node(n)
        for nid, rel, strength in [("n1","knows",1.0),("n2","knows",0.8),
                                   ("n3","suspects",0.5),("n4","knows",0.9),("n5","knows",0.7)]:
            rgs.add_edge(StoryEdge("pov", nid, rel, strength=strength))

        gate    = KnowledgeBoundaryGate(relation_graph=rgs)
        scorer  = DRSEScorer(rgs=rgs, boundary_gate=gate, semantic_scorer=TFIDFSemanticScorer())
        node_scores = scorer.score_all(
            scene_goal="형사가 살인 사건 단서를 수집하는 씬",
            pov_character="pov", current_episode=2,
        )

        # LLMJudge (mock)
        judge   = LLMJudge(sampling_rate=1.0)

        class _MockRec:
            def __init__(self, i):
                self.trace_id      = f"t{i}"
                self.render_output = {"scene": f"형사가 단서를 수집했다. 씬 {i}"}
                self.seed_contract = {"user_prompt": f"형사 씬 {i}을 써라"}

        records = [_MockRec(i) for i in range(5)]
        session = judge.evaluate(records)

        # HallucinationDetector (mock records)
        detector = HallucinationDetector()
        reports  = [detector.detect(f"t{i}", f"형사가 단서를 수집했다. 씬 {i}") for i in range(5)]

        gate9v2  = Gate9v2()
        result   = gate9v2.run(
            node_scores=node_scores,
            judge_session=session,
            hallucination_reports=reports,
        )

        return {
            "pass":   result.passed,
            "reason": result.reason,
            "details": result.to_dict(),
        }
    except Exception as e:
        return {"pass": False, "reason": f"gate9v2_exception: {e}"}
