"""V370: StyleDNA v2 — 장르별 산문 스타일 DNA 프로파일."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class StyleDNAProfile:
    genre_id:           str
    pov:                str           # "1인칭" | "3인칭 제한" | "3인칭 전지"
    scene_rhythm:       str           # "slow" | "medium" | "fast"
    emotional_amp:      float         # 0.0~1.0
    anti_llm_strictness:str           # "strict" | "firm" | "standard" | "relaxed"
    sensory_priority:   List[str]     # ["visual","audio","tactile"] 우선순위
    inner_monologue:    bool = False  # 내적 독백 강조 여부
    metadata:           Dict[str, Any] = field(default_factory=dict)


# ── 장르별 DNA 프로파일 정의 ─────────────────────────────────────────────
_PROFILES: Dict[str, StyleDNAProfile] = {
    "literary": StyleDNAProfile(
        genre_id="literary",
        pov="1인칭",
        scene_rhythm="slow",
        emotional_amp=0.8,
        anti_llm_strictness="strict",
        sensory_priority=["tactile", "audio", "visual"],
        inner_monologue=True,
    ),
    "noir": StyleDNAProfile(
        genre_id="noir",
        pov="1인칭",
        scene_rhythm="fast",
        emotional_amp=0.4,
        anti_llm_strictness="firm",
        sensory_priority=["visual", "audio", "tactile"],
        inner_monologue=False,
    ),
    "fantasy": StyleDNAProfile(
        genre_id="fantasy",
        pov="3인칭 제한",
        scene_rhythm="medium",
        emotional_amp=0.75,
        anti_llm_strictness="standard",
        sensory_priority=["visual", "tactile", "audio"],
        inner_monologue=False,
    ),
    "romance": StyleDNAProfile(
        genre_id="romance",
        pov="3인칭 제한",
        scene_rhythm="medium",
        emotional_amp=0.95,
        anti_llm_strictness="relaxed",
        sensory_priority=["tactile", "visual", "audio"],
        inner_monologue=True,
    ),
    "historical": StyleDNAProfile(
        genre_id="historical",
        pov="3인칭 전지",
        scene_rhythm="slow",
        emotional_amp=0.6,
        anti_llm_strictness="firm",
        sensory_priority=["audio", "visual", "tactile"],
        inner_monologue=False,
    ),
}


class StyleDNA:
    """
    NarrativeScopeResolver 플러그인 아키텍처와 통합된 장르 DNA 관리자.
    KoreanAntiLLMFilter 강도와 SensoryAnchorInjector 우선순위를 제공한다.
    """

    def __init__(self) -> None:
        self._profiles: Dict[str, StyleDNAProfile] = dict(_PROFILES)

    def get(self, genre_id: str) -> StyleDNAProfile:
        if genre_id not in self._profiles:
            raise ValueError(f"알 수 없는 장르: {genre_id}")
        return self._profiles[genre_id]

    def register(self, profile: StyleDNAProfile) -> None:
        self._profiles[profile.genre_id] = profile

    def available_genres(self) -> List[str]:
        return list(self._profiles.keys())

    def anti_llm_strictness(self, genre_id: str) -> str:
        return self.get(genre_id).anti_llm_strictness

    def sensory_priority(self, genre_id: str) -> List[str]:
        return self.get(genre_id).sensory_priority

    def scene_rhythm(self, genre_id: str) -> str:
        return self.get(genre_id).scene_rhythm
