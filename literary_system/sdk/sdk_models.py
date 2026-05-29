"""PublicSDK — 요청/응답 데이터 모델 (ADR-116)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ── 공통 ────────────────────────────────────────────────────────────────────

@dataclass
class QualityScore:
    """씬 품질 5축 점수."""
    coherence: float = 0.0          # 이야기 일관성 (0~1)
    emotion: float = 0.0            # 감정 몰입도 (0~1)
    style: float = 0.0              # 문체 완성도 (0~1)
    character: float = 0.0          # 캐릭터 일관성 (0~1)
    tension: float = 0.0            # 극적 긴장감 (0~1)

    @property
    def overall(self) -> float:
        """5축 단순 평균."""
        vals = [self.coherence, self.emotion, self.style, self.character, self.tension]
        return round(sum(vals) / len(vals), 4)


# ── analyze() ───────────────────────────────────────────────────────────────

@dataclass
class AnalyzeRequest:
    """analyze() 입력."""
    text: str
    context: str = ""
    lang: str = "ko"


@dataclass
class AnalyzeResult:
    """analyze() 출력."""
    quality: QualityScore
    issues: list[str] = field(default_factory=list)
    patterns: list[str] = field(default_factory=list)
    word_count: int = 0
    sentence_count: int = 0
    passed: bool = True
    meta: dict[str, Any] = field(default_factory=dict)


# ── repair() ────────────────────────────────────────────────────────────────

@dataclass
class RepairRequest:
    """repair() 입력."""
    text: str
    issues: list[str]
    target_score: float = 0.75
    lang: str = "ko"


@dataclass
class RepairResult:
    """repair() 출력."""
    original_text: str
    repaired_text: str
    applied_fixes: list[str] = field(default_factory=list)
    score_before: float = 0.0
    score_after: float = 0.0
    improved: bool = False
    meta: dict[str, Any] = field(default_factory=dict)


# ── predict() ───────────────────────────────────────────────────────────────

@dataclass
class PredictRequest:
    """predict() 입력."""
    context: str
    n: int = 3
    style_hint: str = ""
    lang: str = "ko"


@dataclass
class ScenePrediction:
    """단일 씬 예측 후보."""
    rank: int
    synopsis: str
    emotion_arc: str
    probability: float


@dataclass
class PredictResult:
    """predict() 출력."""
    predictions: list[ScenePrediction] = field(default_factory=list)
    context_tokens: int = 0
    meta: dict[str, Any] = field(default_factory=dict)


# ── generate() ──────────────────────────────────────────────────────────────

@dataclass
class GenerateRequest:
    """generate() 입력."""
    title: str
    characters: list[str]
    setting: str
    conflict: str
    tone: str = "dramatic"
    max_rounds: int = 3
    lang: str = "ko"


@dataclass
class GenerateResult:
    """generate() 출력."""
    scene_text: str
    quality: QualityScore
    rounds_used: int = 0
    director_blueprint: dict[str, Any] = field(default_factory=dict)
    passed_critic: bool = True
    meta: dict[str, Any] = field(default_factory=dict)
