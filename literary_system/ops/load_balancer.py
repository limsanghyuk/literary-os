"""
literary_system/ops/load_balancer.py
V476 — WRR-Cost LoadBalancer (ADR-015)

WRR-Cost(Weighted Round Robin Cost) 알고리즘:
  weight = quality² / (cost + ε)
  quality: LLMJudge 마지막 점수 0~1
  cost:    cost_estimate() $/1k tokens

LLM-0 준수: health_fn / cost_fn / score_fn 주입 가능
"""
from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Any, Tuple


# ── 데이터 계약 ─────────────────────────────────────────────

class AdapterRef:
    """어댑터 참조 — 이름 + 주입 가능한 fn 집합."""

    def __init__(
        self,
        name: str,
        health_fn:  Callable[[], bool]       = None,
        cost_fn:    Callable[[Any], float]   = None,
        score_fn:   Callable[[], float]      = None,
        metadata:   Dict[str, Any]           = None,
    ) -> None:
        self.name      = name
        self.health_fn = health_fn  if health_fn  is not None else (lambda: True)
        self.cost_fn   = cost_fn    if cost_fn    is not None else (lambda ctx: 0.01)
        self.score_fn  = score_fn   if score_fn   is not None else (lambda: 1.0)
        self.metadata  = metadata   if metadata   is not None else {}

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, AdapterRef):
            return self.name == other.name
        return NotImplemented

    def __repr__(self) -> str:
        return f"AdapterRef(name={self.name!r})"

    def is_healthy(self) -> bool:
        try:
            return bool(self.health_fn())
        except Exception:
            return False

    def cost_estimate(self, ctx: Any) -> float:
        try:
            v = float(self.cost_fn(ctx))
            return max(v, 0.0)
        except Exception:
            return 999.0

    def last_judge_score(self) -> float:
        try:
            v = float(self.score_fn())
            return max(0.0, min(1.0, v))
        except Exception:
            return 0.0


@dataclass
class RouteResult:
    adapter:   AdapterRef
    weight:    float
    reason:    str = ""


# ── WRR-Cost 알고리즘 ───────────────────────────────────────

def _compute_weight(adapter: AdapterRef, ctx: Any) -> float:
    """quality² / (cost + ε) — 비용 낮을수록, 품질 높을수록 선호."""
    quality = adapter.last_judge_score()
    cost    = adapter.cost_estimate(ctx)
    return (quality ** 2) / (cost + 1e-6)


def weighted_round_robin(named_weights: List[Tuple[str, float]]) -> str:
    """이름-가중치 쌍 리스트에서 최대 가중치 이름 반환."""
    if not named_weights:
        raise ValueError("weighted_round_robin: 가용 어댑터 없음")
    total = sum(w for _, w in named_weights)
    if total <= 0:
        return named_weights[0][0]
    return max(named_weights, key=lambda x: x[1])[0]


# ── LoadBalancer ────────────────────────────────────────────

class LoadBalancer:
    """
    WRR-Cost 로드밸런서.

    사용 예:
        lb = LoadBalancer()
        lb.register(AdapterRef("claude", health_fn=..., cost_fn=..., score_fn=...))
        ref = lb.route(ctx)
    """

    def __init__(self) -> None:
        self._adapters: List[AdapterRef] = []
        self._manual_weights: Dict[str, float] = {}
        self._lock = threading.Lock()
        self._route_count: Dict[str, int] = {}

    # ── 등록 ────────────────────────────────────────────────

    def register(self, adapter: AdapterRef) -> None:
        """어댑터 등록."""
        with self._lock:
            if any(a.name == adapter.name for a in self._adapters):
                raise ValueError(f"이미 등록된 어댑터: {adapter.name}")
            self._adapters.append(adapter)
            self._route_count[adapter.name] = 0

    def deregister(self, name: str) -> bool:
        """어댑터 제거."""
        with self._lock:
            before = len(self._adapters)
            self._adapters = [a for a in self._adapters if a.name != name]
            return len(self._adapters) < before

    # ── 수동 가중치 ──────────────────────────────────────────

    def set_weights(self, weights: Dict[str, float]) -> None:
        """수동 가중치 오버라이드 (0 = 비활성화)."""
        with self._lock:
            self._manual_weights = dict(weights)

    def clear_weights(self) -> None:
        """수동 가중치 초기화 → WRR-Cost 자동 계산으로 복귀."""
        with self._lock:
            self._manual_weights.clear()

    # ── 라우팅 ──────────────────────────────────────────────

    def route(self, ctx: Any = None) -> RouteResult:
        """WRR-Cost 알고리즘으로 어댑터 선택."""
        with self._lock:
            adapters = list(self._adapters)

        if not adapters:
            raise RuntimeError("LoadBalancer: 등록된 어댑터 없음")

        # 건강한 어댑터만 후보
        healthy = [a for a in adapters if a.is_healthy()]
        if not healthy:
            raise RuntimeError("LoadBalancer: 건강한 어댑터 없음")

        # 이름→어댑터 매핑 (hashability 우회: str 키만 사용)
        adapter_by_name: Dict[str, AdapterRef] = {a.name: a for a in healthy}

        # 이름→가중치 매핑 (str 키)
        weight_map: Dict[str, float] = {}
        for a in healthy:
            if a.name in self._manual_weights:
                w = self._manual_weights[a.name]
                if w > 0:
                    weight_map[a.name] = w
            else:
                weight_map[a.name] = _compute_weight(a, ctx)

        if not weight_map:
            raise RuntimeError("LoadBalancer: 가중치 0인 어댑터만 존재")

        # 리스트 기반 선택 (AdapterRef 절대 Dict 키 미사용)
        named_weights: List[Tuple[str, float]] = list(weight_map.items())
        best_name = weighted_round_robin(named_weights)
        selected = adapter_by_name[best_name]

        with self._lock:
            self._route_count[selected.name] = (
                self._route_count.get(selected.name, 0) + 1
            )

        return RouteResult(
            adapter=selected,
            weight=weight_map[selected.name],
            reason="wrr_cost",
        )

    # ── 통계 ────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "adapters":    [a.name for a in self._adapters],
                "healthy":     [a.name for a in self._adapters if a.is_healthy()],
                "route_count": dict(self._route_count),
            }

    def adapter_count(self) -> int:
        with self._lock:
            return len(self._adapters)

    def healthy_count(self) -> int:
        with self._lock:
            return sum(1 for a in self._adapters if a.is_healthy())
