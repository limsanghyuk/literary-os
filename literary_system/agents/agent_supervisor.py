"""V705 — AgentSupervisor + AgentHealthMonitor (SP-D.2) ADR-167."""
from __future__ import annotations
import time, logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════
# AgentHealthMonitor
# ══════════════════════════════════════════════════════════════════════

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthRecord:
    agent_id: str
    status: HealthStatus = HealthStatus.UNKNOWN
    last_check: float = field(default_factory=time.time)
    consecutive_failures: int = 0
    total_checks: int = 0
    total_failures: int = 0
    latency_ms: float = 0.0
    message: str = ""

    def failure_rate(self) -> float:
        if self.total_checks == 0:
            return 0.0
        return self.total_failures / self.total_checks

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "status": self.status.value,
            "last_check": self.last_check,
            "consecutive_failures": self.consecutive_failures,
            "failure_rate": self.failure_rate(),
            "latency_ms": self.latency_ms,
            "message": self.message,
        }


class AgentHealthMonitor:
    """에이전트 헬스 모니터.

    ADR-167: 각 에이전트에 대해 헬스체크 함수를 등록하고
    주기적으로 상태를 평가한다. 연속 실패 임계값 초과 시 UNHEALTHY 마킹.
    """

    def __init__(self, failure_threshold: int = 3,
                 degraded_threshold: int = 1) -> None:
        self._records: Dict[str, HealthRecord] = {}
        self._checkers: Dict[str, Callable[[], bool]] = {}
        self._failure_threshold = failure_threshold
        self._degraded_threshold = degraded_threshold
        self._hooks: Dict[str, List[Callable]] = {}

    def register(self, agent_id: str,
                 checker: Optional[Callable[[], bool]] = None) -> HealthRecord:
        """에이전트 등록. checker 없으면 항상 HEALTHY로 간주."""
        record = HealthRecord(agent_id=agent_id)
        self._records[agent_id] = record
        if checker:
            self._checkers[agent_id] = checker
        return record

    def check(self, agent_id: str) -> HealthRecord:
        """단일 에이전트 헬스체크 실행."""
        record = self._records.get(agent_id)
        if not record:
            r = HealthRecord(agent_id=agent_id, status=HealthStatus.UNKNOWN,
                             message="not registered")
            return r

        checker = self._checkers.get(agent_id)
        record.total_checks += 1
        record.last_check = time.time()

        if checker is None:
            record.status = HealthStatus.HEALTHY
            record.consecutive_failures = 0
            return record

        t0 = time.time()
        try:
            ok = checker()
            record.latency_ms = (time.time() - t0) * 1000
            if ok:
                record.consecutive_failures = 0
                record.status = HealthStatus.HEALTHY
                record.message = ""
            else:
                record.total_failures += 1
                record.consecutive_failures += 1
                self._update_status(record)
        except Exception as exc:
            record.latency_ms = (time.time() - t0) * 1000
            record.total_failures += 1
            record.consecutive_failures += 1
            record.message = str(exc)
            self._update_status(record)

        self._fire("checked", record)
        return record

    def check_all(self) -> Dict[str, HealthRecord]:
        for aid in list(self._records):
            self.check(aid)
        return dict(self._records)

    def _update_status(self, record: HealthRecord) -> None:
        old = record.status
        if record.consecutive_failures >= self._failure_threshold:
            record.status = HealthStatus.UNHEALTHY
        elif record.consecutive_failures >= self._degraded_threshold:
            record.status = HealthStatus.DEGRADED
        if old != record.status:
            self._fire("status_changed", record)

    def get_record(self, agent_id: str) -> Optional[HealthRecord]:
        return self._records.get(agent_id)

    def healthy_agents(self) -> List[str]:
        return [aid for aid, r in self._records.items()
                if r.status == HealthStatus.HEALTHY]

    def unhealthy_agents(self) -> List[str]:
        return [aid for aid, r in self._records.items()
                if r.status == HealthStatus.UNHEALTHY]

    def on(self, event: str, cb: Callable) -> None:
        self._hooks.setdefault(event, []).append(cb)

    def _fire(self, event: str, payload: Any) -> None:
        for cb in self._hooks.get(event, []):
            try:
                cb(payload)
            except Exception as exc:
                logger.warning("[HealthMonitor] hook error: %s", exc)

    def stats(self) -> Dict[str, Any]:
        records = self._records.values()
        by_status: Dict[str, int] = {}
        for r in records:
            by_status[r.status.value] = by_status.get(r.status.value, 0) + 1
        return {"total": len(self._records), "by_status": by_status}


# ══════════════════════════════════════════════════════════════════════
# AgentSupervisor
# ══════════════════════════════════════════════════════════════════════

class RestartPolicy(Enum):
    NEVER = "never"
    ON_FAILURE = "on_failure"
    ALWAYS = "always"


@dataclass
class SupervisedAgent:
    agent_id: str
    restart_policy: RestartPolicy = RestartPolicy.ON_FAILURE
    max_restarts: int = 3
    restart_count: int = 0
    running: bool = False
    last_restart: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def can_restart(self) -> bool:
        return (self.restart_policy != RestartPolicy.NEVER and
                self.restart_count < self.max_restarts)


class AgentSupervisor:
    """에이전트 수퍼바이저.

    ADR-167: 에이전트 등록/시작/중지/재시작 수명주기 관리.
    AgentHealthMonitor와 연동하여 비정상 에이전트 자동 재시작.
    """

    def __init__(self, health_monitor: Optional[AgentHealthMonitor] = None) -> None:
        self._agents: Dict[str, SupervisedAgent] = {}
        self._starters: Dict[str, Callable[[], bool]] = {}
        self._stoppers: Dict[str, Callable[[], None]] = {}
        self._health = health_monitor or AgentHealthMonitor()
        self._hooks: Dict[str, List[Callable]] = {}

    def register(self, agent_id: str,
                 start_fn: Optional[Callable[[], bool]] = None,
                 stop_fn: Optional[Callable[[], None]] = None,
                 health_checker: Optional[Callable[[], bool]] = None,
                 restart_policy: RestartPolicy = RestartPolicy.ON_FAILURE,
                 max_restarts: int = 3,
                 metadata: Optional[Dict[str, Any]] = None) -> SupervisedAgent:
        sa = SupervisedAgent(
            agent_id=agent_id,
            restart_policy=restart_policy,
            max_restarts=max_restarts,
            metadata=metadata or {},
        )
        self._agents[agent_id] = sa
        if start_fn:
            self._starters[agent_id] = start_fn
        if stop_fn:
            self._stoppers[agent_id] = stop_fn
        self._health.register(agent_id, health_checker)
        return sa

    def start(self, agent_id: str) -> bool:
        sa = self._agents.get(agent_id)
        if not sa or sa.running:
            return False
        fn = self._starters.get(agent_id, lambda: True)
        ok = fn()
        if ok:
            sa.running = True
            self._fire("started", sa)
        return ok

    def stop(self, agent_id: str) -> bool:
        sa = self._agents.get(agent_id)
        if not sa or not sa.running:
            return False
        fn = self._stoppers.get(agent_id, lambda: None)
        fn()
        sa.running = False
        self._fire("stopped", sa)
        return True

    def restart(self, agent_id: str) -> bool:
        sa = self._agents.get(agent_id)
        if not sa or not sa.can_restart():
            return False
        self.stop(agent_id)
        sa.restart_count += 1
        sa.last_restart = time.time()
        ok = self.start(agent_id)
        if ok:
            self._fire("restarted", sa)
        return ok

    def supervise(self) -> List[str]:
        """헬스체크 후 비정상 에이전트 자동 재시작. 재시작된 agent_ids 반환."""
        self._health.check_all()
        restarted: List[str] = []
        for aid in self._health.unhealthy_agents():
            sa = self._agents.get(aid)
            if sa and sa.running and sa.can_restart():
                ok = self.restart(aid)
                if ok:
                    restarted.append(aid)
        return restarted

    def get_agent(self, agent_id: str) -> Optional[SupervisedAgent]:
        return self._agents.get(agent_id)

    def running_agents(self) -> List[str]:
        return [aid for aid, sa in self._agents.items() if sa.running]

    def stats(self) -> Dict[str, Any]:
        return {
            "total": len(self._agents),
            "running": len(self.running_agents()),
            "health": self._health.stats(),
        }

    def on(self, event: str, cb: Callable) -> None:
        self._hooks.setdefault(event, []).append(cb)

    def _fire(self, event: str, payload: Any) -> None:
        for cb in self._hooks.get(event, []):
            try:
                cb(payload)
            except Exception as exc:
                logger.warning("[Supervisor] hook error: %s", exc)


ADR_167 = {
    "id": "ADR-167",
    "title": "AgentSupervisor + AgentHealthMonitor",
    "status": "accepted",
    "decision": (
        "AgentHealthMonitor: 연속 실패 임계값 기반 HEALTHY/DEGRADED/UNHEALTHY. "
        "AgentSupervisor: NEVER/ON_FAILURE/ALWAYS 재시작 정책 + supervise() 자동 복구."
    ),
    "version": "V705",
}
