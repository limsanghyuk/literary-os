"""
V383 — PhysicsAwareRouter
Stage96 LLMNodeRouter + NarrativeFitnessScore 기반 라우팅.

Stage96 멀티어댑터 아키텍처 흡수:
  - ComfyUI 스타일 어댑터 레지스트리 (기존 LLMNodeRouter 상속)
  - NarrativeFitnessScore를 라우팅 결정에 활용
  - QUALITY_PHYSICS: 물리 점수가 높은 어댑터 우선
  - ENSEMBLE: 복수 어댑터 결과를 NarrativeFitnessArbiter로 중재 (V389 선행 구현)
"""
from __future__ import annotations
from enum import Enum
from typing import Any, Dict, List, Optional
from literary_system.llm_bridge.llm_node_router import LLMNodeRouter, RoutingPolicy, _AdapterNode
from literary_system.llm_bridge.llm_bridge_interface import LLMBridgeInterface


class PhysicsRoutingPolicy(str, Enum):
    PRIMARY         = "primary"         # 우선순위 1번 어댑터
    FALLBACK        = "fallback"        # 순서대로 시도
    ROUND_ROBIN     = "round_robin"     # 순환
    QUALITY_PHYSICS = "quality_physics" # NarrativeFitness 최고 어댑터
    ENSEMBLE        = "ensemble"        # 복수 결과 중재 (V389 완전 구현)


class _PhysicsAdapterNode(_AdapterNode):
    """물리 점수를 추가로 보유하는 어댑터 노드."""
    def __init__(self, name: str, adapter: LLMBridgeInterface,
                 priority: int, narrative_fitness_weight: float = 0.5):
        super().__init__(name, adapter, priority)
        self.narrative_fitness_weight = narrative_fitness_weight
        self.last_fitness_score: float = 5.0  # 초기 기본값


class PhysicsAwareRouter(LLMBridgeInterface):
    """
    Stage96 스타일 멀티어댑터 라우터.
    
    기존 LLMNodeRouter 위에 physics-aware 레이어 추가:
      - 어댑터별 NarrativeFitness 이력 추적
      - QUALITY_PHYSICS 전략: 최근 fitness 점수 기반 라우팅
      - ENSEMBLE 전략: 복수 어댑터 호출 후 최고 fitness 선택
    """

    def __init__(
        self,
        policy: PhysicsRoutingPolicy = PhysicsRoutingPolicy.QUALITY_PHYSICS,
        ensemble_top_k: int = 2,
    ) -> None:
        self._policy      = policy
        self._ensemble_k  = ensemble_top_k
        self._nodes: List[_PhysicsAdapterNode] = []
        self._rr_idx      = 0
        self._fitness_history: Dict[str, List[float]] = {}

    @property
    def provider_name(self) -> str:
        return "physics_aware_router"

    def register(
        self,
        name:                    str,
        adapter:                 LLMBridgeInterface,
        priority:                int   = 0,
        narrative_fitness_weight: float = 0.5,
    ) -> "PhysicsAwareRouter":
        node = _PhysicsAdapterNode(name, adapter, priority, narrative_fitness_weight)
        self._nodes.append(node)
        self._nodes.sort(key=lambda n: -n.priority)
        self._fitness_history[name] = []
        return self

    def update_fitness(self, adapter_name: str, fitness_score: float) -> None:
        """어댑터의 NarrativeFitness 점수 업데이트 (Gate 7 결과 반영)."""
        for node in self._nodes:
            if node.name == adapter_name:
                node.last_fitness_score = fitness_score
                hist = self._fitness_history.setdefault(adapter_name, [])
                hist.append(fitness_score)
                if len(hist) > 10:
                    hist.pop(0)
                break

    def generate(self, prompt: str, context=None, **kwargs) -> str:
        # Bug-Fix: added context param to match LLMBridgeInterface.generate(prompt, context)
        if not self._nodes:
            return "[PhysicsAwareRouter] no adapters registered"

        if self._policy == PhysicsRoutingPolicy.ENSEMBLE:
            return self._ensemble_generate(prompt, **kwargs)

        node = self._select_node()
        return self._call(node, prompt, **kwargs)

    def parse_action_packet(self, raw: str):
        try:
            from literary_system.llm_bridge.tool_use_parser import ToolUseParser
            return ToolUseParser().parse(raw)
        except Exception:
            return None

    def _select_node(self) -> _PhysicsAdapterNode:
        if self._policy == PhysicsRoutingPolicy.QUALITY_PHYSICS:
            return max(self._nodes, key=lambda n: n.last_fitness_score)
        elif self._policy == PhysicsRoutingPolicy.ROUND_ROBIN:
            node = self._nodes[self._rr_idx % len(self._nodes)]
            self._rr_idx += 1
            return node
        elif self._policy == PhysicsRoutingPolicy.PRIMARY:
            return self._nodes[0]
        else:  # FALLBACK
            return self._nodes[0]

    def _ensemble_generate(self, prompt: str, **kwargs) -> str:
        """
        복수 어댑터 호출 → last_fitness_score 기반 최고 선택.
        V389에서 NarrativeFitnessArbiter로 교체 예정.
        """
        top_k = min(self._ensemble_k, len(self._nodes))
        candidates = sorted(self._nodes, key=lambda n: -n.last_fitness_score)[:top_k]

        results: List[tuple] = []
        for node in candidates:
            try:
                text = self._call(node, prompt, **kwargs)
                results.append((node.last_fitness_score, node.name, text))
            except Exception:
                pass

        if not results:
            return "[PhysicsAwareRouter:ENSEMBLE] all adapters failed"

        # 현재는 단순 fitness 최고값 선택 (V389에서 MERGE 전략 추가)
        results.sort(key=lambda r: -r[0])
        return results[0][2]

    def _call(self, node: _PhysicsAdapterNode, prompt: str, **kwargs) -> str:
        node.calls += 1
        if 'context' not in kwargs:
            kwargs['context'] = {}
        return node.adapter.generate(prompt, **kwargs)

    def stats(self) -> Dict[str, Any]:
        return {
            "policy": self._policy.value,
            "adapters": {
                n.name: {
                    "calls": n.calls,
                    "errors": n.errors,
                    "last_fitness": n.last_fitness_score,
                    "avg_fitness": (
                        sum(self._fitness_history.get(n.name, [5.0])) /
                        max(len(self._fitness_history.get(n.name, [5.0])), 1)
                    ),
                }
                for n in self._nodes
            }
        }
