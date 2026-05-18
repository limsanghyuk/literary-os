"""
literary_system/corpus/cim_bootstrap.py  — V560
CIMBootstrap: 코퍼스 공기어 통계로 CIM W[i][j] 웜스타트
LLM-0 정책(ADR-015/031): 외부 LLM 호출 없음
"""
from __future__ import annotations
import math
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Tuple
from .corpus_ingestor import ScenarioEntry


@dataclass
class BootstrapReport:
    total_scenes: int
    unique_characters: int
    total_pairs: int          # 유니크 (i,j) 공기어 쌍 수
    top_pairs: List[Tuple[str, str, int]]  # (char_a, char_b, count) 상위 10


class CIMBootstrap:
    """
    코퍼스 ScenarioEntry 목록에서 캐릭터 공기어(co-occurrence) 통계를 추출하여
    CIM 가중치 행렬 W[i][j] 초기값(웜스타트)을 제공한다.

    decay: 공기어 횟수를 W[i][j]로 변환할 때 사용하는 감쇠 계수.
           W[i][j] = 1 - exp(-decay * count) ∈ (0, 1)
    """

    def __init__(self, decay: float = 0.95) -> None:
        self._decay = decay
        self._cooccur: Dict[Tuple[str, str], int] = defaultdict(int)
        self._characters: set = set()
        self._scenes_seen: int = 0

    # ── 공개 API ─────────────────────────────────────────────────────────────

    def fit(self, entries: List[ScenarioEntry]) -> BootstrapReport:
        """ScenarioEntry 목록을 학습하여 공기어 행렬을 구축한다."""
        self._cooccur.clear()
        self._characters.clear()
        self._scenes_seen = 0

        for entry in entries:
            chars = entry.characters
            self._characters.update(chars)
            self._scenes_seen += 1
            # 씬 내 모든 캐릭터 쌍 공기어 +1 (순서 정규화: 알파벳 순)
            for i in range(len(chars)):
                for j in range(i + 1, len(chars)):
                    a, b = sorted((chars[i], chars[j]))
                    self._cooccur[(a, b)] += 1

        top = sorted(self._cooccur.items(), key=lambda x: x[1], reverse=True)[:10]
        top_list = [(k[0], k[1], v) for k, v in top]

        return BootstrapReport(
            total_scenes      = self._scenes_seen,
            unique_characters = len(self._characters),
            total_pairs       = len(self._cooccur),
            top_pairs         = top_list,
        )

    def warm_start_weights(
        self, characters: List[str]
    ) -> Dict[str, Dict[str, float]]:
        """
        주어진 캐릭터 목록에 대한 W[i][j] 초기값 딕셔너리 반환.
        W[i][j] = 1 - exp(-decay * count(i,j))
        """
        result: Dict[str, Dict[str, float]] = {c: {} for c in characters}
        for i, a in enumerate(characters):
            for j, b in enumerate(characters):
                if i == j:
                    result[a][b] = 1.0
                    continue
                key = tuple(sorted((a, b)))
                count = self._cooccur.get(key, 0)
                w = 1.0 - math.exp(-self._decay * count)
                result[a][b] = w
        return result

    def warm_start_matrix(
        self, characters: List[str]
    ) -> List[List[float]]:
        """warm_start_weights를 2D 행렬(리스트의 리스트)로 반환."""
        wd = self.warm_start_weights(characters)
        return [[wd[a][b] for b in characters] for a in characters]
