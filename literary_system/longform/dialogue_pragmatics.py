"""DialoguePragmaticsEngine — V396.
한국 드라마 대사의 화용론적 구조를 진단하는 검증기(생성기 아님). LLM 0 calls.
Node2가 최종 표면 리듬 생성을 담당한다.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class DialogueProfile:
    """인물별 대사 화용론 프로파일."""
    character_id: str
    honorific_distance: float = 0.5      # 0(반말) ~ 1(극존대)
    speech_level_variance: float = 0.2
    subtext_density: float = 0.5
    silence_ratio: float = 0.1
    withheld_answer_rate: float = 0.2
    expository_ratio: float = 0.1        # 직접 설명 비율 (낮을수록 좋음)


@dataclass
class DialogueForce:
    """단일 대화 교환의 화용론적 힘."""
    scene_id: str
    subtext_gap: float = 0.0
    relation_pressure: float = 0.0
    speech_level_shift: float = 0.0
    withheld_information: float = 0.0
    silence_weight: float = 0.0
    rank_pressure: float = 0.0

    @property
    def total_force(self) -> float:
        return (self.subtext_gap + self.relation_pressure + self.speech_level_shift
                + self.withheld_information + self.silence_weight + self.rank_pressure)


@dataclass
class DialogueReport:
    character_profiles: Dict[str, DialogueProfile] = field(default_factory=dict)
    speech_level_inconsistencies: List[str] = field(default_factory=list)
    expository_dialogue_ratio: float = 0.0
    korean_honorific_pressure_curve: List[float] = field(default_factory=list)
    subtext_gap_scores: List[float] = field(default_factory=list)
    dialogue_forces: List[DialogueForce] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def is_consistent(self) -> bool:
        return (len(self.speech_level_inconsistencies) == 0
                and self.expository_dialogue_ratio < 0.2)

    @property
    def pass_gate(self) -> bool:
        return self.is_consistent


class DialoguePragmaticsEngine:
    """V396 — 한국 드라마 대사 화용론 진단기."""

    EXPOSITORY_THRESHOLD = 0.2
    INCONSISTENCY_THRESHOLD = 0.3  # 말 레벨 변동폭 임계값

    def analyze_profiles(
        self,
        profiles: Dict[str, DialogueProfile],
        dialogue_forces: List[DialogueForce],
    ) -> DialogueReport:
        inconsistencies = []
        for cid, p in profiles.items():
            if p.speech_level_variance > self.INCONSISTENCY_THRESHOLD:
                inconsistencies.append(
                    f"speech_level_inconsistency: {cid} variance={p.speech_level_variance:.2f}"
                )

        all_expository = [p.expository_ratio for p in profiles.values()]
        avg_expository = sum(all_expository) / max(1, len(all_expository))

        honorific_curve = [
            sum(p.honorific_distance for p in profiles.values()) / max(1, len(profiles))
        ] * max(1, len(dialogue_forces) // 4 + 1)

        subtext_scores = [f.subtext_gap for f in dialogue_forces]
        warnings = []
        if avg_expository > self.EXPOSITORY_THRESHOLD:
            warnings.append(f"high_expository_ratio={avg_expository:.2f}")

        return DialogueReport(
            character_profiles=profiles,
            speech_level_inconsistencies=inconsistencies,
            expository_dialogue_ratio=round(avg_expository, 4),
            korean_honorific_pressure_curve=honorific_curve,
            subtext_gap_scores=subtext_scores,
            dialogue_forces=dialogue_forces,
            warnings=warnings,
        )

    @staticmethod
    def build_synthetic_profiles(character_ids: List[str]) -> Dict[str, DialogueProfile]:
        """Synthetic corpus용 프로파일 생성."""
        profiles = {}
        for i, cid in enumerate(character_ids):
            profiles[cid] = DialogueProfile(
                character_id=cid,
                honorific_distance=0.3 + 0.1 * (i % 5),
                speech_level_variance=0.1 + 0.05 * (i % 3),
                subtext_density=0.4 + 0.1 * (i % 4),
                silence_ratio=0.05 + 0.05 * (i % 3),
                withheld_answer_rate=0.15 + 0.05 * (i % 4),
                expository_ratio=0.05 + 0.03 * (i % 4),
            )
        return profiles
