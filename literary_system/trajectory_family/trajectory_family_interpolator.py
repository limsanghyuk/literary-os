"""
V317: TrajectoryFamilyInterpolator
GPT v1600 trajectory_family_interpolation (phase48) 흡수 구현.

핵심 이론:
  Literary State는 단일 궤도 형상(SP↑ RU↓ etc.)에 따라 움직이는 것이 아니라,
  여러 원형 패밀리(archetype) 중 어느 것에 가까운가 + 두 패밀리 사이 어디에 있는가로
  더 정확하게 기술된다.

  예: "slow_burn_opening" 40% + "false_opening_deepen" 60% = 이 씬의 궤도 정체성

GPT v1600 패턴 vs 우리 V314:
  V314: 5개 형상 중 1개 선택 → 목표값 보간
  V317: 패밀리 매칭 점수 계산 → 1위/2위 보간 → 복합 궤도 신호 프로파일

LLM 0회. 완전 deterministic.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any


# ── 궤도 패밀리 프로파일 ──────────────────────────────────────
@dataclass
class TrajectoryFamilyProfile:
    """단일 궤도 패밀리의 원형 정의."""
    family_id: str
    name: str
    description: str
    target_curve: str
    archetype_tags: list[str]
    # 기대 Literary State 신호 프로파일 (에피소드 중반 기준)
    expected_signal_profile: dict[str, float]
    # 이탈 시 복귀 방향 (어느 축으로 당겨야 하는가)
    recovery_bias: dict[str, float]
    # 컨텍스트 스티칭 키워드
    stitching_keywords: list[str]


class TrajectoryFamilyRegistry:
    """
    Literary OS 표준 궤도 패밀리 레지스트리.
    GPT v1600의 trajectory_family_profile에 해당.
    """

    def __init__(self):
        self._profiles: dict[str, TrajectoryFamilyProfile] = {}
        self._init_standard_profiles()

    def _init_standard_profiles(self) -> None:
        """표준 5개 패밀리 등록."""

        # ① opening_pressure_seed — 오프닝 압력 씨앗
        self.register(TrajectoryFamilyProfile(
            family_id="opening_pressure_seed",
            name="Opening Pressure Seed",
            description="오프닝에서 질문을 심고 압력을 서서히 올리는 원형. 한국 정치 스릴러/느와르 표준.",
            target_curve="opening_pressure_seed",
            archetype_tags=["opening", "slow_burn", "delayed_reveal", "question_first"],
            expected_signal_profile={"SP": 0.62, "RU": 0.68, "RO": 0.58, "ET": 0.02},
            recovery_bias={"RO": 0.05, "SP": 0.03, "RU": -0.02},
            stitching_keywords=["object", "question", "linger", "silence", "withheld"],
        ))

        # ② pressure_release_then_relock — 압력 해소 후 재잠금
        self.register(TrajectoryFamilyProfile(
            family_id="pressure_release_then_relock",
            name="Pressure Release → Relock",
            description="일시적 해소 후 더 깊은 잠금. 거짓 돌파구 원형.",
            target_curve="pressure_release_then_relock",
            archetype_tags=["false_opening", "relock", "deeper_lock", "twist"],
            expected_signal_profile={"SP": 0.55, "RU": 0.72, "RO": 0.45, "ET": 0.08},
            recovery_bias={"SP": -0.04, "RU": 0.06},
            stitching_keywords=["door", "escape", "trap", "return", "deeper"],
        ))

        # ③ steady_institutional_pressure — 제도적 압력 지속
        self.register(TrajectoryFamilyProfile(
            family_id="steady_institutional_pressure",
            name="Steady Institutional Pressure",
            description="제도/구조의 압력이 일정하게 가해지는 원형. 기업/법정/정치 드라마.",
            target_curve="steady_institutional_pressure",
            archetype_tags=["institutional", "structural", "constant_pressure", "system"],
            expected_signal_profile={"SP": 0.58, "RU": 0.55, "AC": 0.72, "ET": 0.05},
            recovery_bias={"AC": 0.04, "SP": 0.02},
            stitching_keywords=["document", "hierarchy", "rule", "protocol", "decision"],
        ))

        # ④ emotional_escalation_peak — 감정 상승 절정
        self.register(TrajectoryFamilyProfile(
            family_id="emotional_escalation_peak",
            name="Emotional Escalation Peak",
            description="감정이 단계적으로 상승하여 절정에 이르는 원형. 멜로드라마/가족극.",
            target_curve="emotional_escalation_peak",
            archetype_tags=["melodrama", "emotional", "peak", "catharsis"],
            expected_signal_profile={"SP": 0.72, "RU": 0.48, "ET": 0.35, "MR": 0.25},
            recovery_bias={"ET": 0.08, "MR": 0.04},
            stitching_keywords=["confession", "tears", "return", "forgiveness", "memory"],
        ))

        # ⑤ knowledge_asymmetry_escalation — 지식 비대칭 상승
        self.register(TrajectoryFamilyProfile(
            family_id="knowledge_asymmetry_escalation",
            name="Knowledge Asymmetry Escalation",
            description="독자가 아는 것과 인물이 아는 것의 비대칭이 커지는 원형. 스릴러/미스터리.",
            target_curve="knowledge_asymmetry_escalation",
            archetype_tags=["dramatic_irony", "knowledge_gap", "suspense", "secret"],
            expected_signal_profile={"SP": 0.65, "RU": 0.78, "RD": 0.28, "RT": 0.45},
            recovery_bias={"RU": 0.05, "RD": 0.03},
            stitching_keywords=["secret", "hidden", "knows", "unaware", "reveal", "truth"],
        ))

    def register(self, profile: TrajectoryFamilyProfile) -> None:
        self._profiles[profile.family_id] = profile

    def list_profiles(self) -> list[TrajectoryFamilyProfile]:
        return list(self._profiles.values())

    def get(self, family_id: str) -> TrajectoryFamilyProfile | None:
        return self._profiles.get(family_id)


@dataclass
class TrajectoryFamilyMatch:
    """궤도 패밀리 매칭 결과."""
    matched_family_id: str
    similarity_score: float
    matched_tags: list[str]
    recommended_shift_overrides: dict[str, float]
    rationale: list[str]


@dataclass
class TrajectoryFamilyInterpolation:
    """두 패밀리 보간 결과."""
    project_id: str
    interpolation_id: str
    primary_family_id: str
    secondary_family_id: str
    primary_score: float
    secondary_score: float
    blend_ratio: float                          # primary의 비율 [0, 1]
    interpolated_signal_profile: dict[str, float]
    interpolated_shift_profile: dict[str, float]
    stitching_keywords: list[str]
    notes: list[str]


class TrajectoryFamilyMatcher:
    """
    현재 Literary State + 씬 컨텍스트 → 가장 가까운 패밀리 매칭.
    GPT v1600 trajectory_family_matcher 흡수.
    """

    def __init__(self, registry: TrajectoryFamilyRegistry | None = None):
        self.registry = registry or TrajectoryFamilyRegistry()

    def match(
        self,
        current_state: dict[str, float],
        target_curve: str | None = None,
        scene_notes: str = "",
        episode_no: int = 1,
        total_episodes: int = 16,
    ) -> list[tuple[str, float]]:
        """
        현재 상태에 가장 가까운 패밀리를 점수 순으로 반환.
        [(family_id, score), ...]
        """
        scored = []
        for profile in self.registry.list_profiles():
            score = self._score(current_state, profile, target_curve, scene_notes, episode_no, total_episodes)
            scored.append((profile.family_id, score))
        scored.sort(key=lambda x: -x[1])
        return scored

    def build_match(
        self,
        current_state: dict[str, float],
        target_curve: str | None = None,
        scene_notes: str = "",
        project_id: str = "",
    ) -> TrajectoryFamilyMatch:
        """상위 1개 매칭 결과 반환."""
        import uuid
        ranked = self.match(current_state, target_curve, scene_notes)
        best_id, best_score = ranked[0]
        profile = self.registry.get(best_id)

        # 추천 이동 방향: 현재 상태와 기대 프로파일의 차이
        shifts = {}
        if profile:
            for var, target in profile.expected_signal_profile.items():
                actual = current_state.get(var, target)
                diff = target - actual
                if abs(diff) > 0.03:
                    shifts[var] = round(diff * 0.4, 4)  # 40% 방향으로 당김

        matched_tags = profile.archetype_tags[:3] if profile else []
        rationale = []
        if profile:
            rationale.append(f"현재 Literary State가 '{profile.name}' 패밀리와 유사")
            if target_curve and profile.target_curve == target_curve:
                rationale.append(f"목표 커브 '{target_curve}'와 정확히 일치")

        return TrajectoryFamilyMatch(
            matched_family_id=best_id,
            similarity_score=round(best_score, 4),
            matched_tags=matched_tags,
            recommended_shift_overrides=shifts,
            rationale=rationale,
        )

    def _score(
        self,
        state: dict[str, float],
        profile: TrajectoryFamilyProfile,
        target_curve: str | None,
        notes: str,
        episode_no: int,
        total_episodes: int,
    ) -> float:
        score = 0.0

        # ① target_curve 직접 일치
        if target_curve and profile.target_curve == target_curve:
            score += 0.30

        # ② Literary State 유사도 (코사인 근사)
        ep = profile.expected_signal_profile
        vars_ = list(ep.keys())
        dot = sum(ep[v] * state.get(v, 0.0) for v in vars_)
        norm_e = math.sqrt(sum(ep[v] ** 2 for v in vars_)) + 1e-9
        norm_s = math.sqrt(sum(state.get(v, 0.0) ** 2 for v in vars_)) + 1e-9
        cosine = dot / (norm_e * norm_s)
        score += cosine * 0.40

        # ③ 키워드 매칭
        notes_lower = notes.lower()
        keyword_hits = sum(1 for kw in profile.stitching_keywords if kw in notes_lower)
        score += min(keyword_hits / max(len(profile.stitching_keywords), 1), 1.0) * 0.15

        # ④ 에피소드 위치 적합성
        ep_ratio = episode_no / max(total_episodes, 1)
        if "opening" in profile.archetype_tags and ep_ratio < 0.25:
            score += 0.10
        elif "peak" in profile.archetype_tags and 0.6 < ep_ratio < 0.85:
            score += 0.10
        elif "relock" in profile.archetype_tags and 0.2 < ep_ratio < 0.5:
            score += 0.05

        return round(min(1.0, score), 4)


class TrajectoryFamilyInterpolator:
    """
    두 궤도 패밀리 사이를 보간하여 복합 궤도 신호 프로파일 생성.
    GPT v1600 trajectory_family_interpolation (phase48) 흡수.

    핵심 이론: "이 씬은 slow_burn 60% + knowledge_asymmetry 40%"
    → 두 패밀리의 expected_signal_profile을 가중 평균
    → stitching_keywords 합집합
    """

    def __init__(
        self,
        registry: TrajectoryFamilyRegistry | None = None,
        matcher: TrajectoryFamilyMatcher | None = None,
    ):
        self.registry = registry or TrajectoryFamilyRegistry()
        self.matcher = matcher or TrajectoryFamilyMatcher(self.registry)

    def interpolate(
        self,
        project_id: str,
        current_state: dict[str, float],
        target_curve: str | None = None,
        scene_notes: str = "",
        episode_no: int = 1,
        total_episodes: int = 16,
    ) -> TrajectoryFamilyInterpolation:
        """
        현재 상태 → 두 패밀리 매칭 → 보간된 복합 궤도 프로파일.
        """
        import uuid
        interp_id = f"interp_{uuid.uuid4().hex[:8]}"

        ranked = self.matcher.match(
            current_state, target_curve, scene_notes, episode_no, total_episodes
        )

        # 상위 2개 패밀리
        p1_id, p1_score = ranked[0]
        p2_id, p2_score = ranked[1] if len(ranked) > 1 else ranked[0]

        total = max(p1_score + p2_score, 1e-9)
        blend = round(p1_score / total, 4)  # primary 비율

        p1 = self.registry.get(p1_id)
        p2 = self.registry.get(p2_id)

        # 보간된 신호 프로파일
        all_vars = set()
        if p1:
            all_vars.update(p1.expected_signal_profile.keys())
        if p2:
            all_vars.update(p2.expected_signal_profile.keys())

        interpolated_signal = {}
        for var in all_vars:
            v1 = p1.expected_signal_profile.get(var, 0.0) if p1 else 0.0
            v2 = p2.expected_signal_profile.get(var, 0.0) if p2 else 0.0
            interpolated_signal[var] = round(blend * v1 + (1 - blend) * v2, 4)

        # 보간된 이동 방향
        interpolated_shift = {}
        for var in all_vars:
            actual = current_state.get(var, interpolated_signal.get(var, 0.0))
            target_val = interpolated_signal.get(var, actual)
            diff = target_val - actual
            if abs(diff) > 0.02:
                interpolated_shift[var] = round(diff * 0.35, 4)

        # 키워드 합집합
        keywords = list(set(
            (p1.stitching_keywords if p1 else []) +
            (p2.stitching_keywords if p2 else [])
        ))[:8]

        notes = [
            f"Primary: {p1.name if p1 else p1_id} ({round(blend*100)}%)",
            f"Secondary: {p2.name if p2 else p2_id} ({round((1-blend)*100)}%)",
        ]
        if target_curve:
            notes.append(f"Target curve: {target_curve}")

        return TrajectoryFamilyInterpolation(
            project_id=project_id,
            interpolation_id=interp_id,
            primary_family_id=p1_id,
            secondary_family_id=p2_id,
            primary_score=p1_score,
            secondary_score=p2_score,
            blend_ratio=blend,
            interpolated_signal_profile=interpolated_signal,
            interpolated_shift_profile=interpolated_shift,
            stitching_keywords=keywords,
            notes=notes,
        )

    def correction_for_deviation(
        self,
        current_state: dict[str, float],
        interpolation: TrajectoryFamilyInterpolation,
    ) -> dict[str, float]:
        """
        현재 상태와 보간된 목표 사이의 보정 벡터.
        이것이 다음 씬 렌더링 지시에 들어간다.
        """
        correction = {}
        for var, target in interpolation.interpolated_signal_profile.items():
            actual = current_state.get(var, target)
            diff = target - actual
            if abs(diff) > 0.03:
                correction[var] = round(diff * 0.5, 4)
        return correction
