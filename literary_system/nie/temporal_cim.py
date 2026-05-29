"""
V505~V508 - TemporalCIM
ADR-021: W[t][i][j] 시간 차원 + memory decay η=0.92 + 회상 신 비교.

설계:
  - W[t][i][j]: t=episode_idx 시점의 i→j 영향력
  - memory decay: W[t] = η·W[t-1] + (1-η)·delta_W[t]
  - windowed view: 최근 window(=5화) 평균
  - flashback_compare: W[current] vs W[flashback_t] → 인물 변화 감지
  - Sparse 처리: |W|<threshold 컬링 (N>15 자동 강제)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from literary_system.nie.character_influence_matrix import (
    SPARSE_N_THRESHOLD,
    SPARSE_W_THRESHOLD,
    CharacterInfluenceMatrix,
)

logger = logging.getLogger(__name__)

ETA = 0.92          # memory decay 계수
WINDOW = 5          # 최근 화수 windowed view
MAX_EPISODES = 24   # 최대 에피소드 수 (16부작 + 여유)


@dataclass
class RelationChange:
    """회상 신 비교 결과."""
    char_i: str
    char_j: str
    delta: float      # current - flashback (양수=강화, 음수=약화)
    direction: str    # "강화" | "약화" | "유지"

    def to_dict(self) -> dict:
        return {
            "pair": f"{self.char_i}→{self.char_j}",
            "delta": round(self.delta, 4),
            "direction": self.direction,
        }


class TemporalCIM:
    """
    NIL Step 1 (시간 차원) — 에피소드별 관계 진화 추적.
    ADR-021: W[t][i][j] tensor with memory decay.
    """

    def __init__(
        self,
        character_ids: Optional[List[str]] = None,
        eta: float = ETA,
        window: int = WINDOW,
        max_episodes: int = MAX_EPISODES,
        stability_module=None,
    ) -> None:
        self._eta = eta
        self._window = window
        self._max_episodes = max_episodes
        self._stability = stability_module

        # t별 CIM 저장: _cim_history[t] = CharacterInfluenceMatrix
        self._cim_history: List[Optional[CharacterInfluenceMatrix]] = [
            None for _ in range(max_episodes)
        ]
        self._current_t: int = 0
        self._char_ids: List[str] = list(character_ids or [])

        # t=0 초기화
        self._cim_history[0] = CharacterInfluenceMatrix(
            list(self._char_ids), stability_module
        )

    def _get_or_create(self, t: int) -> CharacterInfluenceMatrix:
        if t < 0 or t >= self._max_episodes:
            raise IndexError(f"Episode index {t} out of range [0, {self._max_episodes})")
        if self._cim_history[t] is None:
            self._cim_history[t] = CharacterInfluenceMatrix(
                list(self._char_ids), self._stability
            )
        return self._cim_history[t]

    # ── 인물 추가 ─────────────────────────────────────────────────

    def add_character(self, char_id: str) -> None:
        if char_id not in self._char_ids:
            self._char_ids.append(char_id)
            for t, cim in enumerate(self._cim_history):
                if cim is not None:
                    cim.add_character(char_id)

    # ── 업데이트 (memory decay 포함) ──────────────────────────────

    def update(
        self,
        t: int,
        i: str,
        j: str,
        delta: float,
        lr: float = 0.02,
    ) -> None:
        """
        W[t][i][j] 업데이트 with memory decay.

        W[t][i][j] = η·W[t-1][i][j] + (1-η)·(W[t-1][i][j] + lr·delta)
                   = W[t-1] + (1-η)·lr·delta
        """
        self.add_character(i)
        self.add_character(j)

        cim_t = self._get_or_create(t)

        # 이전 값 가져오기 (t-1 또는 t가 첫 에피소드이면 0)
        prev = 0.0
        if t > 0 and self._cim_history[t - 1] is not None:
            prev = self._cim_history[t - 1].get(i, j)
        elif t == 0:
            prev = cim_t.get(i, j)

        # memory decay 적용
        decayed_prev = self._eta * prev
        new_val = decayed_prev + (1.0 - self._eta) * (prev + lr * delta)
        new_val = max(-1.0, min(1.0, new_val))

        # Sparse 처리
        n = len(self._char_ids)
        if n > SPARSE_N_THRESHOLD and abs(new_val) < SPARSE_W_THRESHOLD:
            cim_t._W.pop((i, j), None)
        else:
            cim_t._W[(i, j)] = new_val

        self._current_t = max(self._current_t, t)

    def set_episode(self, t: int) -> None:
        """현재 에피소드 인덱스 설정 + 이전 에피소드 decay 전파."""
        if t >= self._max_episodes:
            raise IndexError(f"Episode {t} >= max {self._max_episodes}")

        if t > 0:
            prev_cim = self._get_or_create(t - 1)
            curr_cim = self._get_or_create(t)
            # 이전 에피소드 모든 엣지에 decay 적용
            for (ci, cj), w in prev_cim._W.items():
                decayed = self._eta * w
                if abs(decayed) >= SPARSE_W_THRESHOLD:
                    curr_cim._W[(ci, cj)] = decayed

        self._current_t = t

    # ── windowed view ─────────────────────────────────────────────

    def get_recent_window(self, current_t: Optional[int] = None) -> CharacterInfluenceMatrix:
        """
        현재 t 기준 최근 window화 평균 W를 담은 CIM 반환.
        """
        t = current_t if current_t is not None else self._current_t
        start = max(0, t - self._window + 1)
        window_cims = [
            self._cim_history[ti]
            for ti in range(start, t + 1)
            if self._cim_history[ti] is not None
        ]
        if not window_cims:
            return CharacterInfluenceMatrix(list(self._char_ids))

        # 평균 CIM 구성
        avg_cim = CharacterInfluenceMatrix(list(self._char_ids))
        all_pairs: set = set()
        for cim in window_cims:
            all_pairs.update(cim._W.keys())

        for (ci, cj) in all_pairs:
            vals = [cim._W.get((ci, cj), 0.0) for cim in window_cims]
            avg = sum(vals) / len(vals)
            if abs(avg) >= SPARSE_W_THRESHOLD:
                avg_cim._W[(ci, cj)] = avg

        return avg_cim

    # ── 회상 신 비교 (flashback_compare) ─────────────────────────

    def flashback_compare(
        self,
        current_t: int,
        flashback_t: int,
        threshold: float = 0.05,
    ) -> List[RelationChange]:
        """
        W[current_t] vs W[flashback_t] 비교 → 인물 관계 변화 감지.

        Args:
            current_t:   현재 에피소드 인덱스
            flashback_t: 회상 에피소드 인덱스 (< current_t)
            threshold:   변화 감지 최소 delta

        Returns:
            변화가 있는 RelationChange 목록
        """
        curr_cim = self._get_or_create(current_t)
        flash_cim = self._get_or_create(flashback_t)

        all_pairs: set = set()
        all_pairs.update(curr_cim._W.keys())
        all_pairs.update(flash_cim._W.keys())

        changes: List[RelationChange] = []
        for (ci, cj) in all_pairs:
            w_curr = curr_cim._W.get((ci, cj), 0.0)
            w_flash = flash_cim._W.get((ci, cj), 0.0)
            delta = w_curr - w_flash

            if abs(delta) >= threshold:
                direction = "강화" if delta > 0 else "약화"
                changes.append(RelationChange(
                    char_i=ci,
                    char_j=cj,
                    delta=delta,
                    direction=direction,
                ))

        return sorted(changes, key=lambda x: -abs(x.delta))

    # ── 조회 ──────────────────────────────────────────────────────

    def get_cim_at(self, t: int) -> CharacterInfluenceMatrix:
        return self._get_or_create(t)

    def get_current(self) -> CharacterInfluenceMatrix:
        return self._get_or_create(self._current_t)

    @property
    def current_t(self) -> int:
        return self._current_t

    def snapshot(self) -> dict:
        return {
            "current_t": self._current_t,
            "characters": self._char_ids,
            "eta": self._eta,
            "window": self._window,
            "episode_count": sum(1 for c in self._cim_history if c is not None),
        }
