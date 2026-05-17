"""V370: ProseRenderContract — 산문 렌더링 필수 진입 계약."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict


class ProseContractViolationError(Exception):
    """산문 렌더링 계약 위반 기본 예외."""
    def __init__(self, rule: str, msg: str = "") -> None:
        self.rule = rule
        super().__init__(f"[{rule}] {msg}")

class SurfaceOnlyViolationError(ProseContractViolationError):
    """NKG 서사 구조 변경 시도 예외."""
    def __init__(self, msg: str = "") -> None:
        super().__init__("SURFACE_ONLY", msg or "NKG 구조 변경은 ProseRenderContract에서 금지됩니다.")

class NewFactViolationError(ProseContractViolationError):
    """새 사실(노드) 생성 시도 예외."""
    def __init__(self, msg: str = "") -> None:
        super().__init__("NEW_FACT", msg or "렌더링 중 새 사실 생성은 금지됩니다.")

class ReaderScoreBelowThresholdError(ProseContractViolationError):
    """ReaderSurfaceScorer 점수 미달 예외."""
    def __init__(self, score: float, threshold: float) -> None:
        self.score = score
        self.threshold = threshold
        super().__init__("READER_SCORE", f"reader_surface_avg {score:.3f} < {threshold:.3f}")


@dataclass
class ProseRenderContract:
    """
    CLRO v2가 렌더링을 시작하기 전 반드시 assert_valid()를 통과해야 하는 계약.
    V360 PlanBuildGate와 동등한 필수 진입 게이트.
    """
    surface_only:          bool  = True
    allow_new_facts:       bool  = False
    allow_reveal_change:   bool  = False
    allow_causal_change:   bool  = False
    min_surface_score:     float = 9.0
    genre_plugin_required: bool  = True
    cluster_weight_enabled:bool  = True
    metadata:              Dict[str, Any] = field(default_factory=dict)

    def assert_valid(self) -> None:
        """계약 내부 일관성 검증. 위반 시 ProseContractViolationError 발생."""
        if not self.surface_only:
            raise SurfaceOnlyViolationError("surface_only는 항상 True여야 합니다.")
        if self.allow_new_facts:
            raise NewFactViolationError("allow_new_facts는 항상 False여야 합니다.")
        if self.allow_reveal_change:
            raise ProseContractViolationError("REVEAL_CHANGE", "allow_reveal_change는 False여야 합니다.")
        if self.allow_causal_change:
            raise ProseContractViolationError("CAUSAL_CHANGE", "allow_causal_change는 False여야 합니다.")
        if not (0.0 < self.min_surface_score <= 10.0):
            raise ProseContractViolationError("SCORE_RANGE", f"min_surface_score 범위 오류: {self.min_surface_score}")

    def assert_score(self, score: float) -> None:
        """실측 점수가 최저 기준을 넘는지 검증."""
        if score < self.min_surface_score:
            raise ReaderScoreBelowThresholdError(score, self.min_surface_score)

    @classmethod
    def default(cls) -> "ProseRenderContract":
        return cls()

    @classmethod
    def strict(cls) -> "ProseRenderContract":
        return cls(min_surface_score=9.5)

    @classmethod
    def relaxed(cls) -> "ProseRenderContract":
        return cls(min_surface_score=7.0)
