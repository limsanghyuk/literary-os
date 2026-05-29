"""V703 — AgentLoadBalancer (SP-D.2) ADR-165: 에이전트 부하 분산."""
from __future__ import annotations
import time, logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class BalancingStrategy(Enum):
    ROUND_ROBIN = "round_robin"
    LEAST_LOADED = "least_loaded"
    WEIGHTED = "weighted"
    RANDOM = "random"


@dataclass
class AgentNode:
    agent_id: str
    capacity: int = 10          # 최대 동시 작업 수
    weight: int = 1             # WEIGHTED 전략에서 사용
    active_tasks: int = 0
    total_handled: int = 0
    failed_tasks: int = 0
    last_assigned: float = 0.0
    online: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def load_ratio(self) -> float:
        if self.capacity == 0:
            return 1.0
        return self.active_tasks / self.capacity

    def is_available(self) -> bool:
        return self.online and self.active_tasks < self.capacity

    def assign(self) -> None:
        self.active_tasks += 1
        self.total_handled += 1
        self.last_assigned = time.time()

    def release(self, failed: bool = False) -> None:
        self.active_tasks = max(0, self.active_tasks - 1)
        if failed:
            self.failed_tasks += 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "capacity": self.capacity,
            "active_tasks": self.active_tasks,
            "total_handled": self.total_handled,
            "failed_tasks": self.failed_tasks,
            "load_ratio": self.load_ratio(),
            "online": self.online,
        }


class AgentLoadBalancer:
    """멀티에이전트 부하 분산기.

    ADR-165: RoundRobin/LeastLoaded/Weighted/Random 4가지 전략.
    온라인 노드만 선택. 오프라인 노드 자동 제외.
    """

    def __init__(self, strategy: BalancingStrategy = BalancingStrategy.ROUND_ROBIN) -> None:
        self._strategy = strategy
        self._nodes: Dict[str, AgentNode] = {}
        self._rr_index: int = 0  # round-robin 포인터

    # ── 노드 관리 ──────────────────────────────────────────────────────

    def register(self, agent_id: str, capacity: int = 10, weight: int = 1,
                 metadata: Optional[Dict[str, Any]] = None) -> AgentNode:
        node = AgentNode(agent_id=agent_id, capacity=capacity, weight=weight,
                         metadata=metadata or {})
        self._nodes[agent_id] = node
        logger.debug("[LB] registered agent=%s capacity=%d", agent_id, capacity)
        return node

    def deregister(self, agent_id: str) -> bool:
        if agent_id in self._nodes:
            del self._nodes[agent_id]
            return True
        return False

    def set_online(self, agent_id: str, online: bool) -> bool:
        node = self._nodes.get(agent_id)
        if node:
            node.online = online
            return True
        return False

    # ── 선택 ──────────────────────────────────────────────────────────

    def select(self) -> Optional[AgentNode]:
        """부하 분산 전략에 따라 에이전트 노드 선택."""
        available = [n for n in self._nodes.values() if n.is_available()]
        if not available:
            return None

        s = self._strategy
        if s == BalancingStrategy.ROUND_ROBIN:
            return self._round_robin(available)
        elif s == BalancingStrategy.LEAST_LOADED:
            return min(available, key=lambda n: n.load_ratio())
        elif s == BalancingStrategy.WEIGHTED:
            return self._weighted(available)
        elif s == BalancingStrategy.RANDOM:
            import random
            return random.choice(available)
        return available[0]

    def _round_robin(self, available: List[AgentNode]) -> AgentNode:
        # 전체 노드 리스트 순서로 RR (available 내에서)
        all_ids = list(self._nodes.keys())
        available_ids = {n.agent_id for n in available}
        n = len(all_ids)
        for _ in range(n):
            idx = self._rr_index % n
            self._rr_index += 1
            aid = all_ids[idx]
            if aid in available_ids:
                return self._nodes[aid]
        return available[0]

    def _weighted(self, available: List[AgentNode]) -> AgentNode:
        import random
        total = sum(n.weight for n in available)
        if total == 0:
            return available[0]
        r = random.randint(0, total - 1)
        cumulative = 0
        for node in available:
            cumulative += node.weight
            if r < cumulative:
                return node
        return available[-1]

    # ── 과제 배분 편의 메서드 ─────────────────────────────────────────

    def assign(self) -> Optional[str]:
        """선택 후 active_tasks 증가. agent_id 반환."""
        node = self.select()
        if node:
            node.assign()
            return node.agent_id
        return None

    def release(self, agent_id: str, failed: bool = False) -> bool:
        node = self._nodes.get(agent_id)
        if node:
            node.release(failed=failed)
            return True
        return False

    # ── 조회 ──────────────────────────────────────────────────────────

    def get_node(self, agent_id: str) -> Optional[AgentNode]:
        return self._nodes.get(agent_id)

    def available_nodes(self) -> List[AgentNode]:
        return [n for n in self._nodes.values() if n.is_available()]

    def all_nodes(self) -> List[AgentNode]:
        return list(self._nodes.values())

    def stats(self) -> Dict[str, Any]:
        nodes = self._nodes.values()
        return {
            "strategy": self._strategy.value,
            "total_nodes": len(self._nodes),
            "online_nodes": sum(1 for n in nodes if n.online),
            "available_nodes": len(self.available_nodes()),
            "total_handled": sum(n.total_handled for n in nodes),
            "total_active": sum(n.active_tasks for n in nodes),
        }


ADR_165 = {
    "id": "ADR-165",
    "title": "AgentLoadBalancer",
    "status": "accepted",
    "decision": (
        "RoundRobin/LeastLoaded/Weighted/Random 4전략. "
        "온라인 + capacity 미초과 노드만 선택. assign/release로 부하 추적."
    ),
    "version": "V703",
}
