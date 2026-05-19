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
from typing import Any, Dict, List, Optional, Tuple

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
