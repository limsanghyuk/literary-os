"""
V499 - MAE Agents v2 (NIE Phase 3)
ADR-017: 4종 에이전트 격리 - Reader/Writer/Editor/Cultural (35/25/25/15%).

설계 원칙:
  - 4종 에이전트 × 씬당 = LLM 4회 호출 허용 (ADR-006 격리 영역)
  - AgentCalibrator (V514+) 격주 보정
  - 27% 샘플링: sample_rate=0.27 (기본 Haiku, σ≥0.15 시 Sonnet 격상)
  - Reader 3 sub-persona: F30(여성30대), M60(남성60대), T20(10대)
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List, Optional
from literary_system.evaluation.mae_agents import AgentVerdict
from literary_system.evaluation.scene_metrics_collector import SceneMetrics


# ── 4종 에이전트 가중치 (ADR-017) ─────────────────────────────────
AGENT_WEIGHTS = {
    "reader":   0.35,
    "writer":   0.25,
    "editor":   0.25,
    "cultural": 0.15,
}

# Reader sub-persona 가중치
READER_PERSONA_WEIGHTS = {
    "F30": 0.40,  # 여성 30대 (핵심 시청층)
    "M60": 0.35,  # 남성 60대
    "T20": 0.25,  # 10대
}


@dataclass
class WeightedVerdict:
    """가중 점수가 포함된 에이전트 판정."""
    agent_name: str
    passed: bool
    score: float
    weight: float
    reason: str = ""
    persona: Optional[str] = None  # Reader sub-persona

    def weighted_score(self) -> float:
        return self.score * self.weight

    def to_dict(self) -> dict:
        return {
            "agent_name": self.agent_name,
            "passed": self.passed,
            "score": round(self.score, 4),
            "weight": round(self.weight, 4),
            "weighted_score": round(self.weighted_score(), 4),
            "reason": self.reason,
            "persona": self.persona,
        }


# ── Reader Agent (3 sub-persona) ──────────────────────────────────

class ReaderAgentV2:
    """
    독자 에이전트 — 3 sub-persona 앙상블.
    F30(여성30대/40%), M60(남성60대/35%), T20(10대/25%).
    """
    WEIGHT = AGENT_WEIGHTS["reader"]
    THRESHOLD = 0.55

    def evaluate(self, scene_id: str, metrics: SceneMetrics) -> WeightedVerdict:
        # sub-persona별 점수 계산 (실 LLM 대체 — 메트릭 기반 근사)
        reader_composite = getattr(metrics, "reader_composite_score", 0.5) or 0.5
        char_valid = 1.0 if getattr(metrics, "character_state_valid", True) else 0.0
        consistency = getattr(metrics, "relation_consistency", 0.5) or 0.5

        # F30: 감성·인물 관계 중심
        f30 = 0.5 * reader_composite + 0.3 * char_valid + 0.2 * consistency
        # M60: 서사 일관성 중심
        m60 = 0.3 * reader_composite + 0.2 * char_valid + 0.5 * consistency
        # T20: 몰입감 중심
        t20 = 0.7 * reader_composite + 0.2 * char_valid + 0.1 * consistency

        # 가중 평균
        score = (
            READER_PERSONA_WEIGHTS["F30"] * f30 +
            READER_PERSONA_WEIGHTS["M60"] * m60 +
            READER_PERSONA_WEIGHTS["T20"] * t20
        )
        score = max(0.0, min(1.0, score))
        passed = score >= self.THRESHOLD

        return WeightedVerdict(
            agent_name="reader_v2",
            passed=passed,
            score=score,
            weight=self.WEIGHT,
            reason=f"F30={f30:.2f} M60={m60:.2f} T20={t20:.2f}",
            persona="ensemble_3",
        )


# ── Writer Agent ──────────────────────────────────────────────────

class WriterAgentV2:
    """작가 에이전트 — 문체·리듬·필력 평가."""
    WEIGHT = AGENT_WEIGHTS["writer"]
    THRESHOLD = 0.55

    def evaluate(self, scene_id: str, metrics: SceneMetrics) -> WeightedVerdict:
        drse = getattr(metrics, "drse_gate_pass_rate", 0.5) or 0.5
        spatial_penalty = getattr(metrics, "spatial_redundancy_ratio", 0.0) or 0.0
        prose_score = max(0.0, 1.0 - spatial_penalty)
        score = max(0.0, min(1.0, 0.5 * drse + 0.5 * prose_score))
        passed = score >= self.THRESHOLD

        return WeightedVerdict(
            agent_name="writer_v2",
            passed=passed,
            score=score,
            weight=self.WEIGHT,
            reason=f"drse={drse:.2f} prose={prose_score:.2f}",
        )


# ── Editor Agent ──────────────────────────────────────────────────

class EditorAgentV2:
    """편집 에이전트 — 구조·일관성·완결성 평가."""
    WEIGHT = AGENT_WEIGHTS["editor"]
    THRESHOLD = 0.55

    def evaluate(self, scene_id: str, metrics: SceneMetrics) -> WeightedVerdict:
        char_valid = 1.0 if getattr(metrics, "character_state_valid", True) else 0.0
        consistency = getattr(metrics, "relation_consistency", 0.5) or 0.5
        score = max(0.0, min(1.0, 0.6 * char_valid + 0.4 * consistency))
        passed = score >= self.THRESHOLD

        return WeightedVerdict(
            agent_name="editor_v2",
            passed=passed,
            score=score,
            weight=self.WEIGHT,
            reason=f"char_valid={char_valid:.0f} consistency={consistency:.2f}",
        )


# ── Cultural Agent ────────────────────────────────────────────────

class CulturalAgentV2:
    """문화적 정합성 에이전트 — 한국 드라마 장르 관습 준수."""
    WEIGHT = AGENT_WEIGHTS["cultural"]
    THRESHOLD = 0.50

    def evaluate(self, scene_id: str, metrics: SceneMetrics) -> WeightedVerdict:
        # 현재: relation_consistency를 문화 정합성 근사치로 사용
        # V509+에서 DramaLexicon 활성화 시 대체
        consistency = getattr(metrics, "relation_consistency", 0.5) or 0.5
        composite = getattr(metrics, "reader_composite_score", 0.5) or 0.5
        score = max(0.0, min(1.0, 0.4 * consistency + 0.6 * composite))
        passed = score >= self.THRESHOLD

        return WeightedVerdict(
            agent_name="cultural_v2",
            passed=passed,
            score=score,
            weight=self.WEIGHT,
            reason=f"cultural_fit={score:.2f}",
        )


# ── MAEOrchestratorV2 ─────────────────────────────────────────────

@dataclass
class MAEResultV2:
    """4종 에이전트 가중 앙상블 결과."""
    scene_id: str
    verdicts: List[WeightedVerdict]
    weighted_score: float      # Σ(score_i × weight_i)
    passed: bool               # weighted_score ≥ threshold
    sampled: bool = True       # 27% 샘플링 여부
    sigma: float = 0.0         # 에이전트 간 표준편차

    @property
    def pass_count(self) -> int:
        return sum(1 for v in self.verdicts if v.passed)

    @property
    def consensus(self) -> bool:
        return self.passed

    @property
    def votes(self) -> List[WeightedVerdict]:
        return self.verdicts

    def to_dict(self) -> dict:
        return {
            "scene_id": self.scene_id,
            "weighted_score": round(self.weighted_score, 4),
            "passed": self.passed,
            "sampled": self.sampled,
            "sigma": round(self.sigma, 4),
            "verdicts": [v.to_dict() for v in self.verdicts],
        }


class MAEOrchestratorV2:
    """
    NIL Step 4 — 4종 에이전트 가중 앙상블 오케스트레이터.
    ADR-017: LLM 호출 격리 영역 (에이전트 내부에서만 허용).
    V499 구현: 메트릭 기반 근사 (실 LLM은 V509+ 활성화).
    27% 샘플링: 기본 활성, σ≥0.15 시 경보.
    """

    PASS_THRESHOLD = 0.55
    SAMPLE_RATE = 0.27
    SIGMA_ESCALATION = 0.15  # 이 이상이면 Sonnet 격상 권고

    def __init__(
        self,
        sample_rate: float = SAMPLE_RATE,
        calibration_weights: Optional[dict] = None,
    ) -> None:
        self._sample_rate = sample_rate
        self._weights = calibration_weights or AGENT_WEIGHTS.copy()
        self._reader = ReaderAgentV2()
        self._writer = WriterAgentV2()
        self._editor = EditorAgentV2()
        self._cultural = CulturalAgentV2()
        self._history: List[MAEResultV2] = []

    def evaluate(
        self,
        scene_id: str,
        metrics: SceneMetrics,
        force_sample: bool = False,
    ) -> MAEResultV2:
        """
        씬 평가.
        force_sample=False 시 sample_rate 확률로만 실행,
        나머지는 이전 결과 재사용 또는 기본값 반환.
        """
        sampled = force_sample or (random.random() < self._sample_rate)

        if not sampled and self._history:
            # 샘플링 제외: 최근 결과 반환
            last = self._history[-1]
            return MAEResultV2(
                scene_id=scene_id,
                verdicts=last.verdicts,
                weighted_score=last.weighted_score,
                passed=last.passed,
                sampled=False,
                sigma=last.sigma,
            )

        # 4종 에이전트 평가
        verdicts = [
            self._reader.evaluate(scene_id, metrics),
            self._writer.evaluate(scene_id, metrics),
            self._editor.evaluate(scene_id, metrics),
            self._cultural.evaluate(scene_id, metrics),
        ]

        # 가중 점수 계산
        weighted_score = sum(v.weighted_score() for v in verdicts)
        weighted_score = max(0.0, min(1.0, weighted_score))

        # σ 계산 (에이전트 간 분산)
        scores = [v.score for v in verdicts]
        mean = sum(scores) / len(scores)
        sigma = (sum((s - mean) ** 2 for s in scores) / len(scores)) ** 0.5

        result = MAEResultV2(
            scene_id=scene_id,
            verdicts=verdicts,
            weighted_score=weighted_score,
            passed=weighted_score >= self.PASS_THRESHOLD,
            sampled=True,
            sigma=sigma,
        )
        self._history.append(result)
        return result

    def update_weights(self, new_weights: dict) -> None:
        """AgentCalibrator (V514+)에서 호출 — 격주 보정."""
        for k, v in new_weights.items():
            if k in self._weights:
                self._weights[k] = float(v)
        # 에이전트 weight 반영
        self._reader.WEIGHT = self._weights.get("reader", 0.35)
        self._writer.WEIGHT = self._weights.get("writer", 0.25)
        self._editor.WEIGHT = self._weights.get("editor", 0.25)
        self._cultural.WEIGHT = self._weights.get("cultural", 0.15)

    def get_history(self) -> List[MAEResultV2]:
        return list(self._history)
