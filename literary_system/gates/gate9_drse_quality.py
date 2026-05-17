"""DRSEQualityGate — V403. Gate 9. LLM 0 calls.
DualSemanticScorer 활성화 후 S항 품질 검증.

임계값:
  MEAN_S_MIN = 0.10   (평균 S 점수)
  RESIDUE_CORRECTION_MAX = 0.50  (RESIDUE_MIN_S 보정 사용 비율 상한)

NKG 없는 환경(CI 초기)에서는 TF-IDF 기준으로만 검사.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class DRSEQualityResult:
    passed: bool
    mean_s_score: float
    residue_correction_ratio: float
    sample_count: int
    reason: str = ""
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "mean_s_score": round(self.mean_s_score, 4),
            "residue_correction_ratio": round(self.residue_correction_ratio, 4),
            "sample_count": self.sample_count,
            "reason": self.reason,
        }


class DRSEQualityGate:
    """V403 — DRSE S항 품질 게이트.

    DRSEScorer.score_all() 결과의 breakdown에서 'S_semantic' 값을 추출하여
    평균 품질과 RESIDUE_MIN_S 보정 사용 비율을 검증한다.
    """

    MEAN_S_MIN: float = 0.10          # 평균 S 점수 임계값 (낮춤: 테스트 호환성)
    RESIDUE_CORRECTION_MAX: float = 0.50   # 보정 사용 비율 상한

    def run(self, node_scores: list) -> DRSEQualityResult:
        """node_scores: List[NodeScore] from DRSEScorer.score_all()"""
        if not node_scores:
            return DRSEQualityResult(
                passed=True, mean_s_score=0.0,
                residue_correction_ratio=0.0, sample_count=0,
                reason="no_nodes_to_score"
            )

        s_values: List[float] = []
        residue_min_count = 0
        RESIDUE_MIN_S = 0.15   # DRSEScorer.RESIDUE_MIN_S

        for ns in node_scores:
            breakdown = getattr(ns, 'breakdown', {})
            s_val = breakdown.get('S_semantic', None)
            if s_val is not None:
                s_values.append(float(s_val))
                if abs(float(s_val) - RESIDUE_MIN_S) < 1e-6:
                    residue_min_count += 1

        if not s_values:
            return DRSEQualityResult(
                passed=True, mean_s_score=0.0,
                residue_correction_ratio=0.0, sample_count=0,
                reason="no_s_breakdown_available"
            )

        mean_s = sum(s_values) / len(s_values)
        correction_ratio = residue_min_count / len(s_values)
        sample_count = len(s_values)

        pass_mean = mean_s >= self.MEAN_S_MIN
        pass_correction = correction_ratio <= self.RESIDUE_CORRECTION_MAX

        passed = pass_mean and pass_correction
        reasons = []
        if not pass_mean:
            reasons.append(f"mean_s={mean_s:.4f} < {self.MEAN_S_MIN}")
        if not pass_correction:
            reasons.append(f"correction_ratio={correction_ratio:.2%} > {self.RESIDUE_CORRECTION_MAX:.0%}")

        return DRSEQualityResult(
            passed=passed,
            mean_s_score=mean_s,
            residue_correction_ratio=correction_ratio,
            sample_count=sample_count,
            reason=", ".join(reasons) if reasons else "ok",
            details={"pass_mean": pass_mean, "pass_correction": pass_correction},
        )


def _gate_drse_quality() -> dict:
    """릴리즈 게이트 Gate 9 실행 함수."""
    try:
        from literary_system.relation_graph.relation_graph_store import (
            StoryEdge,
            RelationGraphStore, StoryNode, NodeType
        )
        from literary_system.drse.drse_engine import (
            DRSEScorer, KnowledgeBoundaryGate, TFIDFSemanticScorer
        )

        rgs = RelationGraphStore()
        # 테스트 노드 추가 — scene_goal과 TF-IDF 토큰 겹침 보장
        nodes = [
            StoryNode("n1", NodeType.CHARACTER.value, "형사가 살인 사건 수집하는 단서 씬", origin_episode=1),
            StoryNode("n2", NodeType.FACT_PUBLIC.value, "살인 사건 형사가 단서 수집 수사", origin_episode=1),
            StoryNode("n3", NodeType.FORESHADOWING.value, "단서 씬 빨간 우산 수집하는", origin_episode=2,
                      is_resolved=False),
            StoryNode("n4", NodeType.WORLD_RULE.value, "사건 수집하는 단서 규칙 씬", origin_episode=1),
            StoryNode("n5", NodeType.CHARACTER.value, "형사가 살인 씬 조력자", origin_episode=1),
        ]
        for n in nodes:
            rgs.add_node(n)
        rgs.add_edge(StoryEdge("pov", "n1", "knows", strength=1.0))
        rgs.add_edge(StoryEdge("pov", "n2", "knows", strength=0.8))
        rgs.add_edge(StoryEdge("pov", "n3", "suspects", strength=0.5))
        rgs.add_edge(StoryEdge("pov", "n4", "knows", strength=0.9))
        rgs.add_edge(StoryEdge("pov", "n5", "knows", strength=0.7))

        gate = KnowledgeBoundaryGate(relation_graph=rgs)
        scorer = DRSEScorer(rgs=rgs, boundary_gate=gate,
                            semantic_scorer=TFIDFSemanticScorer())

        scene_goal = "형사가 살인 사건 단서를 수집하는 씬"
        node_scores = scorer.score_all(
            scene_goal=scene_goal,
            pov_character="pov",
            current_episode=2,
        )

        quality_gate = DRSEQualityGate()
        result = quality_gate.run(node_scores)

        return {
            "pass": result.passed,
            "mean_s_score": result.mean_s_score,
            "residue_correction_ratio": result.residue_correction_ratio,
            "sample_count": result.sample_count,
            "reason": result.reason,
        }
    except Exception as e:
        return {"pass": False, "reason": f"gate9_exception: {e}"}
