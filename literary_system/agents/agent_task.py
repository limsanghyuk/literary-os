"""
V697 — AgentTask + TaskQueue (SP-D.2 MultiAgent Coordination Layer)
ADR-159: 에이전트 작업 단위 표준화 및 우선순위 큐.

LLM-0 원칙: 외부 LLM API 직접 호출 없음.
"""
from __future__ import annotations

import uuid
import time
import heapq
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


# ── 열거형 ────────────────────────────────────────────────────────────────────

class TaskStatus(Enum):
    """작업 상태 전이: PENDING → RUNNING → DONE / FAILED / CANCELLED."""
    PENDING    = "pending"
    RUNNING    = "running"
    DONE       = "done"
    FAILED     = "failed"
    CANCELLED  = "cancelled"
    RETRYING   = "retrying"


class TaskPriority(Enum):
    """작업 우선순위 (낮은 숫자 = 높은 우선순위, heapq 호환)."""
    CRITICAL = 0
    HIGH     = 1
    NORMAL   = 2
    LOW      = 3
    BACKGROUND = 4


# ── AgentTask ─────────────────────────────────────────────────────────────────

@dataclass
class AgentTask:
    """에이전트 작업 단위 (ADR-159).

    Attributes:
        task_id: 작업 고유 ID
        name: 작업 이름
        assigned_agent: 담당 에이전트 ID
        payload: 작업 입력 데이터
        priority: 우선순위
        status: 현재 상태
        created_at: 생성 시각
        started_at: 시작 시각
        completed_at: 완료 시각
        result: 작업 결과
        error: 에러 메시지 (실패 시)
        max_retries: 최대 재시도 횟수
        retry_count: 현재 재시도 횟수
        timeout_seconds: 타임아웃 (초)
        dependencies: 선행 작업 ID 목록
        tags: 작업 태그
    """
    name: str
    assigned_agent: str
    payload: Dict[str, Any]
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    max_retries: int = 0
    retry_count: int = 0
    timeout_seconds: Optional[float] = None
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    # ── 상태 전이 ─────────────────────────────────────────────────────

    def start(self) -> None:
        """PENDING → RUNNING 전이."""
        if self.status not in (TaskStatus.PENDING, TaskStatus.RETRYING):
            raise ValueError(f"Cannot start task in status={self.status}")
        self.status = TaskStatus.RUNNING
        self.started_at = time.time()
        logger.debug("[AgentTask] %s → RUNNING", self.task_id)

    def complete(self, result: Any = None) -> None:
        """RUNNING → DONE 전이."""
        if self.status != TaskStatus.RUNNING:
            raise ValueError(f"Cannot complete task in status={self.status}")
        self.status = TaskStatus.DONE
        self.completed_at = time.time()
        self.result = result
        logger.debug("[AgentTask] %s → DONE", self.task_id)

    def fail(self, error: str) -> None:
        """RUNNING → FAILED 전이 (재시도 여부 판단)."""
        if self.status != TaskStatus.RUNNING:
            raise ValueError(f"Cannot fail task in status={self.status}")
        self.error = error
        if self.retry_count < self.max_retries:
            self.retry_count += 1
            self.status = TaskStatus.RETRYING
            logger.warning("[AgentTask] %s → RETRYING (%d/%d)", self.task_id, self.retry_count, self.max_retries)
        else:
            self.status = TaskStatus.FAILED
            self.completed_at = time.time()
            logger.error("[AgentTask] %s → FAILED: %s", self.task_id, error)

    def cancel(self) -> None:
        """작업 취소 (PENDING/RETRYING 상태에서만 가능)."""
        if self.status not in (TaskStatus.PENDING, TaskStatus.RETRYING):
            raise ValueError(f"Cannot cancel task in status={self.status}")
        self.status = TaskStatus.CANCELLED
        self.completed_at = time.time()

    def reset_for_retry(self) -> None:
        """RETRYING → PENDING 재설정."""
        if self.status != TaskStatus.RETRYING:
            raise ValueError(f"Cannot reset task in status={self.status}")
        self.status = TaskStatus.PENDING
        self.started_at = None

    # ── 조회 ──────────────────────────────────────────────────────────

    @property
    def is_terminal(self) -> bool:
        """완료/실패/취소 여부."""
        return self.status in (TaskStatus.DONE, TaskStatus.FAILED, TaskStatus.CANCELLED)

    @property
    def duration_seconds(self) -> Optional[float]:
        """실행 시간 (초). 완료된 경우만."""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        if self.started_at:
            return time.time() - self.started_at
        return None

    def is_timed_out(self) -> bool:
        """타임아웃 초과 여부."""
        if self.timeout_seconds is None or self.started_at is None:
            return False
        return (time.time() - self.started_at) > self.timeout_seconds

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id":         self.task_id,
            "name":            self.name,
            "assigned_agent":  self.assigned_agent,
            "payload":         self.payload,
            "priority":        self.priority.value,
            "status":          self.status.value,
            "created_at":      self.created_at,
            "started_at":      self.started_at,
            "completed_at":    self.completed_at,
            "result":          self.result,
            "error":           self.error,
            "max_retries":     self.max_retries,
            "retry_count":     self.retry_count,
            "timeout_seconds": self.timeout_seconds,
            "dependencies":    list(self.dependencies),
            "tags":            list(self.tags),
        }


# ── TaskQueue ─────────────────────────────────────────────────────────────────

class TaskQueue:
    """우선순위 기반 작업 큐 (heapq).

    낮은 priority.value = 높은 우선순위로 처리.
    동일 우선순위에서는 FIFO (created_at 순).
    """

    def __init__(self, name: str = "default-queue") -> None:
        self.name = name
        self._heap: List = []          # (priority_val, created_at, task_id, AgentTask)
        self._tasks: Dict[str, AgentTask] = {}
        self._done: List[AgentTask] = []
        self._stats = {"enqueued": 0, "dequeued": 0, "cancelled": 0, "failed": 0}

    def enqueue(self, task: AgentTask) -> None:
        """작업 큐에 추가."""
        if task.task_id in self._tasks:
            raise ValueError(f"Task {task.task_id} already in queue")
        entry = (task.priority.value, task.created_at, task.task_id, task)
        heapq.heappush(self._heap, entry)
        self._tasks[task.task_id] = task
        self._stats["enqueued"] += 1
        logger.debug("[TaskQueue:%s] enqueued %s (pri=%s)", self.name, task.name, task.priority.name)

    def force_requeue(self, task: AgentTask) -> None:
        """이미 dequeue된 작업을 다시 큐에 추가 (재시도/핸들러없음용)."""
        # _tasks에서 제거 후 재등록
        self._tasks.pop(task.task_id, None)
        self.enqueue(task)

    def dequeue(self) -> Optional[AgentTask]:
        """가장 우선순위 높은 작업 꺼내기 (PENDING 상태만)."""
        while self._heap:
            _, _, task_id, task = heapq.heappop(self._heap)
            if task.status in (TaskStatus.CANCELLED, TaskStatus.DONE, TaskStatus.FAILED):
                self._done.append(task)
                continue
            if task.status == TaskStatus.PENDING:
                self._stats["dequeued"] += 1
                return task
        return None

    def peek(self) -> Optional[AgentTask]:
        """꺼내지 않고 다음 작업 확인."""
        for _, _, _, task in self._heap:
            if task.status == TaskStatus.PENDING:
                return task
        return None

    def cancel(self, task_id: str) -> bool:
        """특정 작업 취소."""
        task = self._tasks.get(task_id)
        if task and task.status in (TaskStatus.PENDING, TaskStatus.RETRYING):
            task.cancel()
            self._stats["cancelled"] += 1
            return True
        return False

    def get_task(self, task_id: str) -> Optional[AgentTask]:
        return self._tasks.get(task_id)

    def pending_count(self) -> int:
        return sum(1 for t in self._tasks.values() if t.status == TaskStatus.PENDING)

    def running_count(self) -> int:
        return sum(1 for t in self._tasks.values() if t.status == TaskStatus.RUNNING)

    def stats(self) -> Dict[str, int]:
        return dict(self._stats)

    def all_tasks(self) -> List[AgentTask]:
        return list(self._tasks.values())

    def agent_tasks(self, agent_id: str) -> List[AgentTask]:
        """특정 에이전트에 배정된 작업 목록."""
        return [t for t in self._tasks.values() if t.assigned_agent == agent_id]


# ── ADR-159 문서 상수 ─────────────────────────────────────────────────────────

ADR_159 = {
    "id": "ADR-159",
    "title": "AgentTask + TaskQueue — 에이전트 작업 단위 표준화",
    "status": "accepted",
    "context": "SP-D.2: 에이전트 간 협조를 위한 작업 단위 표준 및 우선순위 큐 필요",
    "decision": (
        "AgentTask dataclass로 작업 단위 표준화. "
        "TaskStatus 6종 상태 기계(PENDING/RUNNING/DONE/FAILED/CANCELLED/RETRYING). "
        "TaskQueue로 heapq 기반 우선순위 큐 구현."
    ),
    "consequences": [
        "작업 상태 추적 가능 (감사 로그)",
        "재시도 로직 내장 (max_retries)",
        "의존성 그래프 기반 실행 준비 (dependencies)",
    ],
    "version": "V697",
}
