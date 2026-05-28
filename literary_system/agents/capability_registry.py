"""
V698 — AgentCapabilityRegistry (SP-D.2 MultiAgent Coordination Layer)
ADR-160: 에이전트 능력 등록소 — 에이전트별 수행 가능 작업 목록 관리.

LLM-0 원칙: 외부 LLM API 직접 호출 없음.
"""
from __future__ import annotations
import time, logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class AgentCapability:
    """에이전트 단일 능력 항목."""
    name: str                          # 능력 식별자 (예: "scene_write", "critique")
    description: str = ""
    version: str = "1.0"
    tags: List[str] = field(default_factory=list)
    max_concurrent: int = 1            # 동시 처리 가능 작업 수
    avg_latency_ms: float = 0.0       # 평균 처리 시간

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name, "description": self.description,
            "version": self.version, "tags": list(self.tags),
            "max_concurrent": self.max_concurrent, "avg_latency_ms": self.avg_latency_ms,
        }


@dataclass
class AgentProfile:
    """등록된 에이전트 프로필."""
    agent_id: str
    capabilities: List[AgentCapability] = field(default_factory=list)
    registered_at: float = field(default_factory=time.time)
    last_heartbeat: float = field(default_factory=time.time)
    active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def capability_names(self) -> Set[str]:
        return {c.name for c in self.capabilities}

    def has_capability(self, name: str) -> bool:
        return name in self.capability_names()

    def get_capability(self, name: str) -> Optional[AgentCapability]:
        for c in self.capabilities:
            if c.name == name:
                return c
        return None

    def update_heartbeat(self) -> None:
        self.last_heartbeat = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "capabilities": [c.to_dict() for c in self.capabilities],
            "registered_at": self.registered_at,
            "last_heartbeat": self.last_heartbeat,
            "active": self.active,
            "metadata": self.metadata,
        }


class AgentCapabilityRegistry:
    """에이전트 능력 등록소.

    에이전트 등록/해제, 능력별 에이전트 조회, 헬스체크 지원.
    """

    def __init__(self, heartbeat_timeout_seconds: float = 30.0) -> None:
        self._agents: Dict[str, AgentProfile] = {}
        self._heartbeat_timeout = heartbeat_timeout_seconds

    # ── 등록/해제 ──────────────────────────────────────────────────────

    def register(
        self,
        agent_id: str,
        capabilities: List[AgentCapability],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AgentProfile:
        """에이전트 등록 (이미 있으면 갱신)."""
        profile = AgentProfile(
            agent_id=agent_id,
            capabilities=capabilities,
            metadata=metadata or {},
        )
        self._agents[agent_id] = profile
        logger.info("[Registry] registered agent=%s caps=%s", agent_id, [c.name for c in capabilities])
        return profile

    def deregister(self, agent_id: str) -> bool:
        if agent_id in self._agents:
            del self._agents[agent_id]
            logger.info("[Registry] deregistered agent=%s", agent_id)
            return True
        return False

    def heartbeat(self, agent_id: str) -> bool:
        profile = self._agents.get(agent_id)
        if profile:
            profile.update_heartbeat()
            profile.active = True
            return True
        return False

    # ── 조회 ──────────────────────────────────────────────────────────

    def get_agent(self, agent_id: str) -> Optional[AgentProfile]:
        return self._agents.get(agent_id)

    def agents_with_capability(self, capability_name: str) -> List[AgentProfile]:
        """특정 능력을 가진 활성 에이전트 목록."""
        return [
            p for p in self._agents.values()
            if p.active and p.has_capability(capability_name)
        ]

    def all_agents(self) -> List[AgentProfile]:
        return list(self._agents.values())

    def active_agents(self) -> List[AgentProfile]:
        return [p for p in self._agents.values() if p.active]

    def all_capabilities(self) -> Set[str]:
        """등록된 전체 능력 이름 집합."""
        caps: Set[str] = set()
        for p in self._agents.values():
            caps |= p.capability_names()
        return caps

    def agent_count(self) -> int:
        return len(self._agents)

    def active_count(self) -> int:
        return sum(1 for p in self._agents.values() if p.active)

    # ── 헬스체크 ──────────────────────────────────────────────────────

    def check_health(self) -> Dict[str, bool]:
        """타임아웃 초과 에이전트를 inactive로 표시. {agent_id: is_active} 반환."""
        now = time.time()
        result: Dict[str, bool] = {}
        for agent_id, profile in self._agents.items():
            alive = (now - profile.last_heartbeat) <= self._heartbeat_timeout
            profile.active = alive
            result[agent_id] = alive
        return result

    def stats(self) -> Dict[str, int]:
        return {
            "total": self.agent_count(),
            "active": self.active_count(),
            "capabilities": len(self.all_capabilities()),
        }


ADR_160 = {
    "id": "ADR-160",
    "title": "AgentCapabilityRegistry — 에이전트 능력 등록소",
    "status": "accepted",
    "decision": (
        "AgentCapabilityRegistry로 에이전트별 수행 가능 작업(AgentCapability) 관리. "
        "heartbeat 기반 활성 상태 추적. 능력별 에이전트 조회 지원."
    ),
    "version": "V698",
}
