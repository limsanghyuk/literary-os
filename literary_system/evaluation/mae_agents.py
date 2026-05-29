"""
V324 - MAE Agents  (Phase 1)
Alpha(Logic) / Beta(Character) / Gamma(Literary) 3 에이전트.

설계 원칙 (P3 LLM 0회, P4 MAE 앙상블):
  - 각 에이전트는 SceneMetrics만을 입력으로 받는다
  - 자기 가중치를 평가 점수 계산에 사용하지 않는다 (Gemini 결함 방지)
  - 가중치는 MAEOrchestrator가 합의 판정 시 참조
  - LLM 0회. 완전 로컬.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from literary_system.evaluation.scene_metrics_collector import SceneMetrics


@dataclass
class AgentVerdict:
    """단일 에이전트의 씬 평가 결과."""
    agent_name: str       # 'alpha' | 'beta' | 'gamma'
    passed: bool
    score: float          # 0.0 ~ 1.0
    reason: str

    def to_dict(self) -> dict:
        return {
            "agent_name": self.agent_name,
            "passed": self.passed,
            "score": round(self.score, 4),
            "reason": self.reason,
        }


# ── 임계값 상수 ───────────────────────────────────────────────────────────────

_ALPHA_DRSE_MIN = 0.60      # DRSE gate pass rate 최소
_ALPHA_SPATIAL_MAX = 2      # 최대 허용 spatial 위반 수
_BETA_CONSISTENCY_MIN = 0.70
_GAMMA_COMPOSITE_MIN = 0.15  # (pull+afterimage-uncertainty)/3
_GAMMA_UNCERTAINTY_MAX = 0.80


# ════════════════════════════════════════════════════════════════════
# AlphaAgent — 논리성 평가
# ════════════════════════════════════════════════════════════════════

class AlphaAgent:
    """
    논리 일관성 평가.
    DRSE gate pass rate + SpatialConstraint 위반 수를 기반으로 점수 계산.
    """

    def __init__(self, weight: float = 0.5) -> None:
        self.weight = weight

    def evaluate(self, scene_id: str, metrics: SceneMetrics) -> AgentVerdict:
        # DRSE gate pass rate 기여 (60%)
        drse_score = metrics.drse_gate_pass_rate

        # Spatial 위반 페널티 (위반 1건당 -0.1, 최대 -1.0)
        spatial_penalty = min(1.0, metrics.spatial_violation_count * 0.1)
        spatial_score = max(0.0, 1.0 - spatial_penalty)

        # 종합 점수
        score = 0.6 * drse_score + 0.4 * spatial_score

        passed = (
            metrics.drse_gate_pass_rate >= _ALPHA_DRSE_MIN
            and metrics.spatial_violation_count <= _ALPHA_SPATIAL_MAX
        )
        reason = (
            f"drse_pass={metrics.drse_gate_pass_rate:.2f}, "
            f"spatial_violations={metrics.spatial_violation_count}"
        )
        return AgentVerdict(agent_name="alpha", passed=passed, score=score, reason=reason)


# ════════════════════════════════════════════════════════════════════
# BetaAgent — 캐릭터 상태 평가
# ════════════════════════════════════════════════════════════════════

class BetaAgent:
    """
    캐릭터 상태 일관성 평가.
    CharacterStateGate 결과 + 관계 일관성으로 점수 계산.
    """

    def __init__(self, weight: float = 0.5) -> None:
        self.weight = weight

    def evaluate(self, scene_id: str, metrics: SceneMetrics) -> AgentVerdict:
        # 캐릭터 상태 기여 (70%)
        char_score = 1.0 if metrics.character_state_valid else 0.0

        # 관계 일관성 기여 (30%)
        consistency_score = metrics.relation_consistency

        score = 0.7 * char_score + 0.3 * consistency_score

        passed = (
            metrics.character_state_valid
            and metrics.relation_consistency >= _BETA_CONSISTENCY_MIN
        )
        reason = (
            f"char_valid={metrics.character_state_valid}, "
            f"consistency={metrics.relation_consistency:.2f}"
        )
        return AgentVerdict(agent_name="beta", passed=passed, score=score, reason=reason)


# ════════════════════════════════════════════════════════════════════
# GammaAgent — 문학성 평가
# ════════════════════════════════════════════════════════════════════

class GammaAgent:
    """
    독자 경험 / 문학성 평가.
    reader_pull, reader_afterimage, reader_uncertainty 기반 점수 계산.
    """

    def __init__(self, weight: float = 0.5) -> None:
        self.weight = weight

    def evaluate(self, scene_id: str, metrics: SceneMetrics) -> AgentVerdict:
        # composite score: (pull + afterimage - uncertainty) / 3
        composite = metrics.reader_composite_score

        # 정규화 (-1/3 ~ 2/3 범위를 0~1로)
        normalized = (composite + 1.0 / 3.0) / (2.0 / 3.0 + 1.0 / 3.0)
        score = max(0.0, min(1.0, normalized))

        passed = (
            composite >= _GAMMA_COMPOSITE_MIN
            and metrics.reader_uncertainty <= _GAMMA_UNCERTAINTY_MAX
        )
        reason = (
            f"composite={composite:.2f}, "
            f"uncertainty={metrics.reader_uncertainty:.2f}"
        )
        return AgentVerdict(agent_name="gamma", passed=passed, score=score, reason=reason)
