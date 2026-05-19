"""
V501~V504 - CharacterInfluenceMatrix (CIM)
ADR-018: 비대칭 W[n×n] 행렬 + 구조적 균형 이론 + PageRank + 5티어 + SparseCIM + TopKTriangleFilter.

설계:
  - W[i][j] ∈ [-1, +1]: i → j 영향력 (양수=우호, 음수=적대)
  - 비대칭: W[i][j] ≠ W[j][i]
  - 구조적 균형 (Heider 1946): B(A,B,C) = sign(W_AB)×sign(W_BC)×sign(W_CA)
  - T(A,B,C) = 1 - B(A,B,C) ∈ {0, 2}  → 긴장 삼각형
  - PageRank d=0.85, 양수 W만 사용 (영향 방향)
  - 5티어: 장(PR>0.80) / 차(0.60-0.80) / 포(BC>0.70) / 마·상(mid) / 졸(<0.30)
  - SparseCIM: N>15 시 자동 sparse (|W|<0.1 컬링)
  - TopKTriangleFilter: |T|≥1.5 priority queue top-50
"""
from __future__ import annotations

import heapq
import logging
import math
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ── 상수 ──────────────────────────────────────────────────────────
LR_CIM = 0.02
SPARSE_N_THRESHOLD = 15
SPARSE_W_THRESHOLD = 0.10
PAGERANK_DAMPING = 0.85
PAGERANK_ITER = 50  # [G2-FIX] ADR-018 준수: 30 → 50 (≥50 보장)
PAGERANK_TOL = 1e-6
TOP_K_TRIANGLES = 50
TRIANGLE_MIN_TENSION = 1.5

# 장기판 5티어 기준
TIER_JANG  = 0.80   # 장(將) - 주연
TIER_CHA   = 0.60   # 차(車) - 조연 상위
TIER_PO_BC = 0.70   # 포(包) - 관계 허브 (betweenness centrality)
TIER_MA    = 0.30   # 마·상(馬·象) - 중간
# < 0.30 = 졸(卒)


@dataclass
class CIMTier:
    character_id: str
    tier: str           # "장" | "차" | "포" | "마·상" | "졸"
    pagerank: float
    betweenness: float  # 근사값


@dataclass
class TriangleTension:
    """삼각 긴장 구조."""
    a: str
    b: str
    c: str
    tension: float      # 0 (균형) or 2 (불균형)
    balance: float      # -1 or +1
    signs: Tuple[float, float, float]  # (W_ab, W_bc, W_ca) sign

    def __lt__(self, other: "TriangleTension") -> bool:
        return self.tension > other.tension  # 높은 긴장 우선

    def to_dict(self) -> dict:
        return {
            "triangle": [self.a, self.b, self.c],
            "tension": self.tension,
            "balance": self.balance,
        }


class CharacterInfluenceMatrix:
    """
    NIL Step 1+2 — 인물 영향력 행렬.
    비대칭 W[n×n] + 구조적 균형 + PageRank + SparseCIM + TopK 삼각 필터.
    """

    def __init__(
        self,
        character_ids: Optional[List[str]] = None,
        stability_module=None,
    ) -> None:
        self._ids: List[str] = list(character_ids or [])
        self._id_idx: Dict[str, int] = {c: i for i, c in enumerate(self._ids)}
        self._W: Dict[Tuple[str, str], float] = {}  # sparse dict 표현
        self._stability = stability_module
        self._pagerank: Dict[str, float] = {}
        self._betweenness: Dict[str, float] = {}
        self._update_count = 0

    # ── 인물 관리 ──────────────────────────────────────────────────

    def add_character(self, char_id: str) -> None:
        if char_id not in self._id_idx:
            self._id_idx[char_id] = len(self._ids)
            self._ids.append(char_id)

    def remove_character(self, char_id: str) -> None:
        if char_id in self._id_idx:
            self._ids.remove(char_id)
            self._id_idx = {c: i for i, c in enumerate(self._ids)}
            # 관련 엣지 제거
            self._W = {
                (i, j): w for (i, j), w in self._W.items()
                if i != char_id and j != char_id
            }

    @property
    def n(self) -> int:
        return len(self._ids)

    # ── W 업데이트 ─────────────────────────────────────────────────

    def update(
        self,
        i: str,
        j: str,
        delta: float,
        lr: Optional[float] = None,
    ) -> None:
        """
        W[i][j] ← W[i][j] + lr × delta.
        NILStabilityModule 연동으로 lr 동적 조정 가능.
        """
        if i not in self._id_idx:
            self.add_character(i)
        if j not in self._id_idx:
            self.add_character(j)

        effective_lr = lr or LR_CIM
        if self._stability is not None:
            effective_lr = self._stability.get_effective_lr("cim", effective_lr)

        old = self._W.get((i, j), 0.0)
        new = max(-1.0, min(1.0, old + effective_lr * delta))

        # SparseCIM: N>15 시 |W|<threshold 컬링
        if self.n > SPARSE_N_THRESHOLD and abs(new) < SPARSE_W_THRESHOLD:
            self._W.pop((i, j), None)
        else:
            self._W[(i, j)] = new

        self._update_count += 1

    def get(self, i: str, j: str) -> float:
        return self._W.get((i, j), 0.0)

    def set_direct(self, i: str, j: str, value: float) -> None:
        """직접 설정 (시나리오 초기화 등)."""
        self.add_character(i)
        self.add_character(j)
        clamped = max(-1.0, min(1.0, value))
        if abs(clamped) >= SPARSE_W_THRESHOLD or self.n <= SPARSE_N_THRESHOLD:
            self._W[(i, j)] = clamped

    def prune_sparse(self) -> int:
        """|W|<threshold인 엣지 제거. 제거 수 반환."""
        before = len(self._W)
        self._W = {
            k: v for k, v in self._W.items()
            if abs(v) >= SPARSE_W_THRESHOLD
        }
        removed = before - len(self._W)
        if removed:
            logger.debug("CIM sparse prune: removed %d edges", removed)
        return removed

    # ── 구조적 균형 이론 ───────────────────────────────────────────

    @staticmethod
    def _sign(v: float) -> float:
        if v > 0: return 1.0
        if v < 0: return -1.0
        return 0.0

    def balance(self, a: str, b: str, c: str) -> float:
        """
        B(A,B,C) = sign(W_AB) × sign(W_BC) × sign(W_CA).
        +1 = 균형 삼각형, -1 = 불균형 삼각형.
        """
        return (
            self._sign(self.get(a, b)) *
            self._sign(self.get(b, c)) *
            self._sign(self.get(c, a))
        )

    def tension(self, a: str, b: str, c: str) -> float:
        """T(A,B,C) = 1 - B(A,B,C) ∈ {0, 2}."""
        return 1.0 - self.balance(a, b, c)

    # ── TopK 삼각 필터 ─────────────────────────────────────────────

    def top_k_triangles(self, k: int = TOP_K_TRIANGLES) -> List[TriangleTension]:
        """
        |T| ≥ TRIANGLE_MIN_TENSION인 삼각형 중 상위 k개 반환.
        N=20 → C(20,3)=1140, heap으로 O(n³ log k) 처리.
        """
        heap: List[TriangleTension] = []
        chars = self._ids

        for i in range(len(chars)):
            for j in range(i + 1, len(chars)):
                for k_idx in range(j + 1, len(chars)):
                    a, b, c = chars[i], chars[j], chars[k_idx]
                    t = self.tension(a, b, c)
                    if t >= TRIANGLE_MIN_TENSION:
                        tri = TriangleTension(
                            a=a, b=b, c=c,
                            tension=t,
                            balance=self.balance(a, b, c),
                            signs=(
                                self._sign(self.get(a, b)),
                                self._sign(self.get(b, c)),
                                self._sign(self.get(c, a)),
                            ),
                        )
                        if len(heap) < k:
                            heapq.heappush(heap, tri)
                        elif tri.tension > heap[0].tension:
                            heapq.heapreplace(heap, tri)

        return sorted(heap, key=lambda x: -x.tension)

    # ── PageRank ──────────────────────────────────────────────────

    def compute_pagerank(self) -> Dict[str, float]:
        """
        PageRank d=0.85, 양수 W만 사용 (영향 방향).
        수렴 기준: max delta < TOL 또는 ITER 도달.
        """
        chars = self._ids
        n = len(chars)
        if n == 0:
            return {}

        pr = {c: 1.0 / n for c in chars}
        d = PAGERANK_DAMPING

        for _ in range(PAGERANK_ITER):
            new_pr: Dict[str, float] = {}
            for c in chars:
                # c에 대한 incoming positive influence 합산
                incoming = sum(
                    pr[src] * self._W[(src, c)]
                    for src in chars
                    if (src, c) in self._W and self._W[(src, c)] > 0
                )
                # out-degree (positive only)
                out_sum = sum(
                    self._W[(c, dst)]
                    for dst in chars
                    if (c, dst) in self._W and self._W[(c, dst)] > 0
                )
                # dangling node 처리
                teleport = (1.0 - d) / n
                new_pr[c] = teleport + d * incoming

            # 정규화
            total = sum(new_pr.values()) or 1.0
            new_pr = {c: v / total for c, v in new_pr.items()}

            # 수렴 확인
            delta = max(abs(new_pr[c] - pr[c]) for c in chars)
            pr = new_pr
            if delta < PAGERANK_TOL:
                break

        self._pagerank = pr
        return pr

    # ── 근사 betweenness centrality ───────────────────────────────

    def compute_betweenness_approx(self) -> Dict[str, float]:
        """
        근사 BC: 각 노드의 삼각형 참여 비율.
        (완전 BC는 O(n³), NIE 실시간에 불필요)
        """
        triangle_count: Dict[str, int] = defaultdict(int)
        chars = self._ids
        total = 0
        for i in range(len(chars)):
            for j in range(i + 1, len(chars)):
                for k in range(j + 1, len(chars)):
                    a, b, c = chars[i], chars[j], chars[k]
                    if self.tension(a, b, c) >= TRIANGLE_MIN_TENSION:
                        triangle_count[a] += 1
                        triangle_count[b] += 1
                        triangle_count[c] += 1
                        total += 1
        if total == 0:
            self._betweenness = {c: 0.0 for c in chars}
        else:
            self._betweenness = {c: triangle_count[c] / total for c in chars}
        return self._betweenness

    # ── 5티어 분류 ────────────────────────────────────────────────

    def classify_tiers(self) -> Dict[str, CIMTier]:
        """
        PageRank + BC 기반 장기판 5티어 분류.
        캐시된 pagerank/betweenness 사용 (없으면 계산).
        """
        if not self._pagerank:
            self.compute_pagerank()
        if not self._betweenness:
            self.compute_betweenness_approx()

        tiers: Dict[str, CIMTier] = {}
        for char_id in self._ids:
            pr = self._pagerank.get(char_id, 0.0)
            bc = self._betweenness.get(char_id, 0.0)

            if pr >= TIER_JANG:
                tier = "장"
            elif pr >= TIER_CHA:
                tier = "차"
            elif bc >= TIER_PO_BC:
                tier = "포"
            elif pr >= TIER_MA:
                tier = "마·상"
            else:
                tier = "졸"

            tiers[char_id] = CIMTier(
                character_id=char_id,
                tier=tier,
                pagerank=pr,
                betweenness=bc,
            )
        return tiers

    # ── 조회 / 직렬화 ─────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "characters": self._ids,
            "n": self.n,
            "edges": {f"{i}→{j}": round(w, 4) for (i, j), w in self._W.items()},
            "update_count": self._update_count,
        }

    def edge_count(self) -> int:
        return len(self._W)

    def density(self) -> float:
        max_edges = self.n * (self.n - 1)
        return self.edge_count() / max_edges if max_edges > 0 else 0.0
