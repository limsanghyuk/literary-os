"""
V565 GenreTransferLearning — 장르 전이 학습

책임:
- 장르별 스타일 파라미터 프로필 관리
- 소스 장르 → 타깃 장르 파라미터 전이 (선형 보간)
- 전이 이력 추적
- 적응 점수(adaptation_score) 계산

전이 수식:
    transferred[k] = (1 - alpha) * target[k] + alpha * source[k]
    여기서 alpha ∈ [0, 1]은 전이 강도

LLM-0: 외부 LLM 호출 없음.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
import math
from collections import Counter
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

# 장르 기본 스타일 파라미터 (전이의 출발점)
_DEFAULT_GENRE_PROFILES: Dict[str, Dict[str, float]] = {
    "drama": {
        "tension_base": 0.55,
        "dialogue_ratio": 0.60,
        "description_density": 0.40,
        "pacing_norm": 0.50,
        "emotional_intensity": 0.70,
        "plot_twist_freq": 0.30,
    },
    "romance": {
        "tension_base": 0.40,
        "dialogue_ratio": 0.65,
        "description_density": 0.45,
        "pacing_norm": 0.40,
        "emotional_intensity": 0.75,
        "plot_twist_freq": 0.20,
    },
    "fantasy": {
        "tension_base": 0.65,
        "dialogue_ratio": 0.45,
        "description_density": 0.70,
        "pacing_norm": 0.60,
        "emotional_intensity": 0.60,
        "plot_twist_freq": 0.50,
    },
    "thriller": {
        "tension_base": 0.80,
        "dialogue_ratio": 0.50,
        "description_density": 0.55,
        "pacing_norm": 0.80,
        "emotional_intensity": 0.65,
        "plot_twist_freq": 0.70,
    },
    "historical": {
        "tension_base": 0.45,
        "dialogue_ratio": 0.40,
        "description_density": 0.75,
        "pacing_norm": 0.35,
        "emotional_intensity": 0.55,
        "plot_twist_freq": 0.25,
    },
    "comedy": {
        "tension_base": 0.25,
        "dialogue_ratio": 0.70,
        "description_density": 0.30,
        "pacing_norm": 0.65,
        "emotional_intensity": 0.50,
        "plot_twist_freq": 0.35,
    },
    "sf": {
        "tension_base": 0.60,
        "dialogue_ratio": 0.45,
        "description_density": 0.65,
        "pacing_norm": 0.55,
        "emotional_intensity": 0.55,
        "plot_twist_freq": 0.45,
    },
}


@dataclass
class GenreProfile:
    """장르 스타일 파라미터 프로필."""
    genre: str
    params: Dict[str, float]            # 파라미터명 → 값 (0.0 ~ 1.0)
    source_genre: Optional[str] = None  # 전이된 경우 소스 장르
    transfer_alpha: float = 0.0         # 전이 강도 (0 = 순수 타깃)
    created_at: float = field(default_factory=time.time)

    def adaptation_score(self) -> float:
        """적응 점수: 파라미터 표준편차의 역수 기반.

        값이 고르게 분포될수록 높은 점수 (균형잡힌 프로필).
        """
        if not self.params:
            return 0.0
        values = list(self.params.values())
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        std = variance ** 0.5
        return round(1.0 - min(std, 1.0), 4)


@dataclass
class TransferRecord:
    """전이 이력 레코드."""
    record_id: str
    source_genre: str
    target_genre: str
    alpha: float
    result_params: Dict[str, float]
    project_id: Optional[str]
    timestamp: float = field(default_factory=time.time)


class GenreTransferLearning:
    """장르 전이 학습 엔진.

    - 장르 프로필 등록·조회
    - 소스 → 타깃 선형 전이 (transfer)
    - 전이 이력 관리
    - 커스텀 파라미터 업데이트 지원
    """

    def __init__(self) -> None:
        # 기본 프로필 초기화
        self._profiles: Dict[str, GenreProfile] = {
            genre: GenreProfile(genre=genre, params=dict(params))
            for genre, params in _DEFAULT_GENRE_PROFILES.items()
        }
        self._transfer_history: List[TransferRecord] = []
        self._counter = 0
        self._lock = threading.RLock()

    # ------------------------------------------------------------------ #
    # 프로필 관리
    # ------------------------------------------------------------------ #

    def get_profile(self, genre: str) -> Optional[GenreProfile]:
        """장르 프로필 조회."""
        return self._profiles.get(genre)

    def register_profile(
        self,
        genre: str,
        params: Dict[str, float],
        overwrite: bool = False,
    ) -> GenreProfile:
        """장르 프로필 등록.

        Args:
            genre:     장르명
            params:    스타일 파라미터 (0.0 ~ 1.0)
            overwrite: True이면 기존 프로필 덮어쓰기

        Raises:
            KeyError: overwrite=False이고 이미 존재하는 장르
        """
        with self._lock:
            if genre in self._profiles and not overwrite:
                raise KeyError(f"Genre profile already exists: {genre}")
            # 파라미터 범위 클램프
            clamped = {k: max(0.0, min(1.0, v)) for k, v in params.items()}
            profile = GenreProfile(genre=genre, params=clamped)
            self._profiles[genre] = profile
            return profile

    def update_params(self, genre: str, updates: Dict[str, float]) -> None:
        """특정 장르 프로필 파라미터 부분 업데이트."""
        with self._lock:
            profile = self._profiles.get(genre)
            if profile is None:
                raise KeyError(f"Genre profile not found: {genre}")
            for k, v in updates.items():
                profile.params[k] = max(0.0, min(1.0, v))

    def list_genres(self) -> List[str]:
        """등록된 장르 목록."""
        return list(self._profiles.keys())

    # ------------------------------------------------------------------ #
    # 전이
    # ------------------------------------------------------------------ #

    def transfer(
        self,
        source_genre: str,
        target_genre: str,
        alpha: float = 0.3,
        project_id: Optional[str] = None,
    ) -> GenreProfile:
        """소스 장르 → 타깃 장르 선형 전이.

        transferred[k] = (1 - alpha) * target[k] + alpha * source[k]

        Args:
            source_genre: 전이 소스 장르
            target_genre: 전이 타깃 장르
            alpha:        전이 강도 (0.0 = 순수 타깃, 1.0 = 순수 소스)
            project_id:   연결할 프로젝트 ID (선택)

        Returns:
            전이된 GenreProfile (새 인스턴스)

        Raises:
            KeyError:   소스 또는 타깃 장르 미존재
            ValueError: alpha 범위 오류
        """
        if not 0.0 <= alpha <= 1.0:
            raise ValueError(f"alpha must be in [0, 1], got {alpha}")

        with self._lock:
            src = self._profiles.get(source_genre)
            tgt = self._profiles.get(target_genre)
            if src is None:
                raise KeyError(f"Source genre not found: {source_genre}")
            if tgt is None:
                raise KeyError(f"Target genre not found: {target_genre}")

            # 공통 파라미터 키만 전이 (소스에만 있는 키는 제외)
            common_keys = set(src.params.keys()) & set(tgt.params.keys())
            transferred: Dict[str, float] = {}
            for k in common_keys:
                transferred[k] = round(
                    (1.0 - alpha) * tgt.params[k] + alpha * src.params[k], 6
                )
            # 타깃 전용 키는 그대로 유지
            for k in tgt.params:
                if k not in common_keys:
                    transferred[k] = tgt.params[k]

            result_profile = GenreProfile(
                genre=target_genre,
                params=transferred,
                source_genre=source_genre,
                transfer_alpha=alpha,
            )

            # 이력 기록
            self._counter += 1
            record = TransferRecord(
                record_id=f"tr-{self._counter:04d}",
                source_genre=source_genre,
                target_genre=target_genre,
                alpha=alpha,
                result_params=dict(transferred),
                project_id=project_id,
            )
            self._transfer_history.append(record)

            return result_profile

    def transfer_history(
        self,
        project_id: Optional[str] = None,
        source_genre: Optional[str] = None,
    ) -> List[TransferRecord]:
        """전이 이력 조회 (필터 옵션)."""
        with self._lock:
            result = list(self._transfer_history)
            if project_id:
                result = [r for r in result if r.project_id == project_id]
            if source_genre:
                result = [r for r in result if r.source_genre == source_genre]
            return result

    # ------------------------------------------------------------------ #
    # 유사도
    # ------------------------------------------------------------------ #

    def genre_distance(self, genre_a: str, genre_b: str) -> float:
        """두 장르 프로필 간 유클리드 거리.

        Returns:
            거리 (0.0 = 동일, 최대 √N ≈ 2.45 for N=6 params)
        """
        with self._lock:
            pa = self._profiles.get(genre_a)
            pb = self._profiles.get(genre_b)
            if pa is None or pb is None:
                raise KeyError("One or both genres not found")
            common = set(pa.params) & set(pb.params)
            if not common:
                return 1.0
            sq_sum = sum(
                (pa.params[k] - pb.params[k]) ** 2 for k in common
            )
            return round(sq_sum ** 0.5, 6)

    def most_similar_genre(self, genre: str) -> Tuple[str, float]:
        """주어진 장르와 가장 유사한 장르 반환.

        Returns:
            (genre_name, distance) 튜플
        """
        with self._lock:
            genres = [g for g in self._profiles if g != genre]
            if not genres:
                raise KeyError("No other genres registered")
            distances = [(g, self.genre_distance(genre, g)) for g in genres]
            return min(distances, key=lambda x: x[1])

    # ------------------------------------------------------------------ #
    # 통계
    # ------------------------------------------------------------------ #

    def stats(self) -> Dict[str, Any]:
        return {
            "registered_genres": len(self._profiles),
            "transfer_history_count": len(self._transfer_history),
            "genres": self.list_genres(),
        }


# ======================================================================
# V611: GenreTransferV2 — MultiWork v2 통합 장르 전이 엔진
# ======================================================================

if TYPE_CHECKING:
    from .shared_character_db_v2 import SharedCharacterDBV2
    from .shared_world_db_v2 import SharedWorldDBV2
    from .multi_work_cim_v2 import MultiWorkCIMV2


@dataclass
class GenreAdaptationReport:
    """장르 적응 보고서."""
    project_id: str
    source_genre: str
    target_genre: str
    alpha: float
    adapted_profile: GenreProfile
    cim_weight_boost: float          # CIM reward_weighted_weight 기반 보정 강도
    char_reward_mean: float          # SharedCharacterDBV2 평균 보상
    world_consistency: float         # SharedWorldDBV2 일관성 점수
    coherence_score: float           # 프로젝트 간 장르 일관성 (0~1)
    timestamp: float = field(default_factory=time.time)


class GenreTransferV2(GenreTransferLearning):
    """MultiWork v2 통합 장르 전이 엔진 (V611).

    기존 GenreTransferLearning 위에:
    - SharedCharacterDBV2 캐릭터 보상 평균 → alpha 보정
    - SharedWorldDBV2 세계관 일관성 점수 → tension_base 조정
    - MultiWorkCIMV2 reward_weighted_global_weight → 파라미터 가중치
    - 프로젝트 간 장르 일관성 점수 (coherence_score)
    - 프로젝트별 적응 보고서 이력

    LLM-0: 외부 LLM 호출 없음.
    """

    VERSION = "2.0.0"

    def __init__(
        self,
        char_db: Optional["SharedCharacterDBV2"] = None,
        world_db: Optional["SharedWorldDBV2"] = None,
        cim_v2: Optional["MultiWorkCIMV2"] = None,
    ) -> None:
        super().__init__()
        self._char_db = char_db
        self._world_db = world_db
        self._cim_v2 = cim_v2
        self._reports: List[GenreAdaptationReport] = []

    # ------------------------------------------------------------------ #
    # 의존성 주입 (지연 주입 지원)
    # ------------------------------------------------------------------ #

    def set_char_db(self, char_db: "SharedCharacterDBV2") -> None:
        with self._lock:
            self._char_db = char_db

    def set_world_db(self, world_db: "SharedWorldDBV2") -> None:
        with self._lock:
            self._world_db = world_db

    def set_cim_v2(self, cim_v2: "MultiWorkCIMV2") -> None:
        with self._lock:
            self._cim_v2 = cim_v2

    # ------------------------------------------------------------------ #
    # 핵심: weighted_transfer (CIM v2 보상 반영 전이)
    # ------------------------------------------------------------------ #

    def weighted_transfer(
        self,
        source_genre: str,
        target_genre: str,
        project_id: str,
        alpha: float = 0.3,
        boost_factor: float = 0.15,
    ) -> "GenreAdaptationReport":
        """CIM v2 보상 가중치 반영 장르 전이.

        1. 기본 alpha를 CIM reward_weighted_global_weight로 보정
           adjusted_alpha = clamp(alpha + boost_factor * cim_weight, 0, 1)
        2. 캐릭터 보상 평균이 높으면 emotional_intensity 소폭 상향
        3. 세계관 일관성이 낮으면 description_density 소폭 상향
        4. 기본 transfer() 실행 후 보정 파라미터 적용

        Args:
            source_genre: 소스 장르
            target_genre: 타깃 장르
            project_id:   프로젝트 식별자
            alpha:        기본 전이 강도 (0~1)
            boost_factor: CIM 가중치 반영 계수 (기본 0.15)

        Returns:
            GenreAdaptationReport
        """
        # Step 1: CIM v2 가중치 조회
        cim_weight = 0.0
        if self._cim_v2 is not None:
            try:
                cim_weight = self._cim_v2.reward_weighted_global_weight(project_id)
            except Exception:
                cim_weight = 0.0

        adjusted_alpha = max(0.0, min(1.0, alpha + boost_factor * cim_weight))

        # Step 2: 기본 transfer 실행
        profile = self.transfer(
            source_genre=source_genre,
            target_genre=target_genre,
            alpha=adjusted_alpha,
            project_id=project_id,
        )

        # Step 3: 캐릭터 보상 평균 → emotional_intensity 보정
        char_reward_mean = 0.0
        if self._char_db is not None and "emotional_intensity" in profile.params:
            char_ids = list(getattr(self._char_db, "_characters", {}).keys())
            rewards = []
            for cid in char_ids:
                rt = self._char_db.get_reward_trace(cid)
                if rt is not None:
                    m = rt.mean()
                    if not math.isnan(m):
                        rewards.append(m)
            if rewards:
                char_reward_mean = sum(rewards) / len(rewards)
                # 보상 평균 > 0.7이면 emotional_intensity 최대 +0.05
                delta = min(0.05, max(0.0, (char_reward_mean - 0.7) * 0.25))
                profile.params["emotional_intensity"] = min(
                    1.0, profile.params["emotional_intensity"] + delta
                )

        # Step 4: 세계관 일관성 → description_density 보정
        world_consistency = 1.0
        if self._world_db is not None and "description_density" in profile.params:
            try:
                world_consistency = self._world_db.consistency_score()
            except Exception:
                world_consistency = 1.0
            # 일관성 < 0.7이면 description_density 최대 +0.08 (세계관 묘사 강화)
            if world_consistency < 0.7:
                delta = min(0.08, (0.7 - world_consistency) * 0.4)
                profile.params["description_density"] = min(
                    1.0, profile.params["description_density"] + delta
                )

        # Step 5: 프로젝트 간 장르 일관성 점수
        coherence = self._compute_coherence(project_id, target_genre)

        report = GenreAdaptationReport(
            project_id=project_id,
            source_genre=source_genre,
            target_genre=target_genre,
            alpha=adjusted_alpha,
            adapted_profile=profile,
            cim_weight_boost=cim_weight * boost_factor,
            char_reward_mean=char_reward_mean,
            world_consistency=world_consistency,
            coherence_score=coherence,
        )
        with self._lock:
            self._reports.append(report)
        return report

    # ------------------------------------------------------------------ #
    # 프로젝트 간 장르 일관성
    # ------------------------------------------------------------------ #

    def _compute_coherence(self, project_id: str, genre: str) -> float:
        """전이 이력에서 project_id의 genre 일관성 점수 계산.

        같은 project_id에서 같은 target_genre로의 전이 비율.

        Returns:
            coherence ∈ [0, 1]
        """
        history = self.transfer_history(project_id=project_id)
        if not history:
            return 1.0  # 이력 없음 → 기본값 최대
        same_genre = sum(1 for r in history if r.target_genre == genre)
        return round(same_genre / len(history), 4)

    def project_genre_coherence(self, project_id: str) -> float:
        """프로젝트의 전체 장르 일관성 점수.

        타깃 장르가 한 종류이면 1.0, 분산될수록 낮아짐.
        """
        history = self.transfer_history(project_id=project_id)
        if not history:
            return 1.0
        counts = Counter(r.target_genre for r in history)
        dominant_ratio = max(counts.values()) / len(history)
        return round(dominant_ratio, 4)

    # ------------------------------------------------------------------ #
    # 추천
    # ------------------------------------------------------------------ #

    def recommend_genre(
        self,
        current_genre: str,
        project_id: Optional[str] = None,
    ) -> Tuple[str, float]:
        """현재 장르에서 가장 자연스럽게 전이 가능한 장르 추천.

        CIM 보상이 낮으면 (< 0.5) 가장 가까운 장르 추천 (안전한 전이),
        CIM 보상이 높으면 (>= 0.5) 가장 먼 장르 추천 (도전적 전이).

        Returns:
            (recommended_genre, distance) 튜플
        """
        cim_weight = 0.5  # 기본값
        if self._cim_v2 is not None and project_id:
            try:
                cim_weight = self._cim_v2.reward_weighted_global_weight(project_id)
            except Exception:
                pass

        genres = [g for g in self._profiles if g != current_genre]
        if not genres:
            raise KeyError("No other genres registered")

        distances = [(g, self.genre_distance(current_genre, g)) for g in genres]
        if cim_weight >= 0.5:
            # 보상 높음 → 도전적 전이 (먼 장르)
            return max(distances, key=lambda x: x[1])
        else:
            # 보상 낮음 → 안전한 전이 (가까운 장르)
            return min(distances, key=lambda x: x[1])

    # ------------------------------------------------------------------ #
    # 이력·통계
    # ------------------------------------------------------------------ #

    def adaptation_reports(
        self,
        project_id: Optional[str] = None,
    ) -> List["GenreAdaptationReport"]:
        """적응 보고서 이력 조회."""
        with self._lock:
            if project_id:
                return [r for r in self._reports if r.project_id == project_id]
            return list(self._reports)

    def stats_v2(self) -> Dict[str, Any]:
        """v2 통합 통계."""
        base = self.stats()
        return {
            **base,
            "version": self.VERSION,
            "has_char_db": self._char_db is not None,
            "has_world_db": self._world_db is not None,
            "has_cim_v2": self._cim_v2 is not None,
            "adaptation_report_count": len(self._reports),
        }
