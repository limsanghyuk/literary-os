"""VoiceManifold / StyleGenome — V397. LLM 0 calls.
13차원 VoiceVector. 1~3화 Anchor 기반 cosine drift 감지.
character growth driven shift = permitted_drift, 무근거 변화 = blocked_drift.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


@dataclass
class VoiceVector:
    """문체 13차원 벡터."""
    sentence_length_dist: float = 0.5
    dialogue_ratio: float = 0.4
    silence_ratio: float = 0.1
    metaphor_density: float = 0.3
    sensory_channel_pref: float = 0.5
    verb_strength: float = 0.5
    abstraction_ratio: float = 0.3
    rhythm_variance: float = 0.4
    ellipsis_freq: float = 0.2
    subtext_density: float = 0.4
    tactile_density: float = 0.2
    visual_density: float = 0.4
    auditory_density: float = 0.2

    def as_list(self) -> List[float]:
        return [
            self.sentence_length_dist, self.dialogue_ratio, self.silence_ratio,
            self.metaphor_density, self.sensory_channel_pref, self.verb_strength,
            self.abstraction_ratio, self.rhythm_variance, self.ellipsis_freq,
            self.subtext_density, self.tactile_density, self.visual_density,
            self.auditory_density,
        ]

    def cosine_distance(self, other: "VoiceVector") -> float:
        a = self.as_list()
        b = other.as_list()
        dot = sum(x * y for x, y in zip(a, b))
        mag_a = math.sqrt(sum(x**2 for x in a))
        mag_b = math.sqrt(sum(x**2 for x in b))
        if mag_a == 0 or mag_b == 0:
            return 1.0
        return 1.0 - dot / (mag_a * mag_b)

    @classmethod
    def average(cls, vectors: List["VoiceVector"]) -> "VoiceVector":
        if not vectors:
            return cls()
        n = len(vectors)
        lists = [v.as_list() for v in vectors]
        avg = [sum(lists[i][j] for i in range(n)) / n for j in range(13)]
        fields = ["sentence_length_dist","dialogue_ratio","silence_ratio",
                  "metaphor_density","sensory_channel_pref","verb_strength",
                  "abstraction_ratio","rhythm_variance","ellipsis_freq",
                  "subtext_density","tactile_density","visual_density","auditory_density"]
        return cls(**dict(zip(fields, avg)))


class DriftType(str, Enum):
    NONE = "NONE"
    PERMITTED = "PERMITTED"      # character growth 기반
    BLOCKED = "BLOCKED"          # 무근거 변화


@dataclass
class DriftResult:
    episode_idx: int
    cosine_distance: float
    drift_type: DriftType
    reason: str = ""

    @property
    def is_concerning(self) -> bool:
        return self.drift_type == DriftType.BLOCKED


@dataclass
class VoiceDriftReport:
    anchor_vector: Optional[VoiceVector] = None
    episode_vectors: List[VoiceVector] = field(default_factory=list)
    drift_results: List[DriftResult] = field(default_factory=list)
    blocked_drift_count: int = 0
    avg_drift: float = 0.0
    max_drift: float = 0.0

    @property
    def pass_gate(self) -> bool:
        return self.blocked_drift_count == 0 and self.max_drift < 0.4


class VoiceManifold:
    """V397 — 문체 다차원 공간 관리기."""

    DRIFT_THRESHOLD_PERMITTED = 0.15   # 허용 drift
    DRIFT_THRESHOLD_BLOCKED = 0.30     # 차단 drift
    ANCHOR_EPISODES = 3                # 앵커로 사용할 초기 에피소드 수

    def __init__(self) -> None:
        self.anchor_vector: Optional[VoiceVector] = None

    def set_anchor(self, vectors: List[VoiceVector]) -> None:
        self.anchor_vector = VoiceVector.average(vectors[:self.ANCHOR_EPISODES])

    def analyze_drift(
        self,
        episode_vectors: List[VoiceVector],
        growth_episodes: List[int] = None,
    ) -> VoiceDriftReport:
        if growth_episodes is None:
            growth_episodes = []
        if not self.anchor_vector and episode_vectors:
            self.set_anchor(episode_vectors[:self.ANCHOR_EPISODES])

        results: List[DriftResult] = []
        for i, v in enumerate(episode_vectors[self.ANCHOR_EPISODES:], start=self.ANCHOR_EPISODES):
            dist = self.anchor_vector.cosine_distance(v)
            if dist <= self.DRIFT_THRESHOLD_PERMITTED:
                dtype = DriftType.NONE
            elif i in growth_episodes:
                dtype = DriftType.PERMITTED
            elif dist <= self.DRIFT_THRESHOLD_BLOCKED:
                dtype = DriftType.PERMITTED
            else:
                dtype = DriftType.BLOCKED
            results.append(DriftResult(episode_idx=i, cosine_distance=round(dist,4),
                                        drift_type=dtype))

        blocked = sum(1 for r in results if r.drift_type == DriftType.BLOCKED)
        dists = [r.cosine_distance for r in results] or [0.0]
        return VoiceDriftReport(
            anchor_vector=self.anchor_vector,
            episode_vectors=episode_vectors,
            drift_results=results,
            blocked_drift_count=blocked,
            avg_drift=round(sum(dists)/len(dists), 4),
            max_drift=round(max(dists), 4),
        )


class StyleGenome:
    """V397 — 산문 샘플에서 VoiceVector 추출."""

    @staticmethod
    def extract(prose_features: dict) -> VoiceVector:
        """prose_features: prose 분석 결과 dict → VoiceVector."""
        return VoiceVector(
            sentence_length_dist=prose_features.get("avg_sentence_length", 15) / 30.0,
            dialogue_ratio=prose_features.get("dialogue_ratio", 0.4),
            silence_ratio=prose_features.get("silence_ratio", 0.1),
            metaphor_density=prose_features.get("metaphor_density", 0.3),
            sensory_channel_pref=prose_features.get("sensory_density", 0.5),
            verb_strength=prose_features.get("verb_strength", 0.5),
            abstraction_ratio=prose_features.get("abstraction_ratio", 0.3),
            rhythm_variance=prose_features.get("rhythm_variance", 0.4),
            ellipsis_freq=prose_features.get("ellipsis_freq", 0.2),
            subtext_density=prose_features.get("subtext_density", 0.4),
            tactile_density=prose_features.get("tactile_density", 0.2),
            visual_density=prose_features.get("visual_density", 0.4),
            auditory_density=prose_features.get("auditory_density", 0.2),
        )

    @staticmethod
    def build_synthetic(episode_count: int = 16) -> List[VoiceVector]:
        """Synthetic corpus용 VoiceVector 목록."""
        import random
        random.seed(77)
        vectors = []
        base = VoiceVector()
        for i in range(episode_count):
            noise = 0.02 + 0.01 * (i % 5)
            fields = base.as_list()
            perturbed = [max(0.0, min(1.0, f + random.uniform(-noise, noise))) for f in fields]
            fn = ["sentence_length_dist","dialogue_ratio","silence_ratio",
                  "metaphor_density","sensory_channel_pref","verb_strength",
                  "abstraction_ratio","rhythm_variance","ellipsis_freq",
                  "subtext_density","tactile_density","visual_density","auditory_density"]
            vectors.append(VoiceVector(**dict(zip(fn, perturbed))))
        return vectors
