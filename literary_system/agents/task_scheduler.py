"""V699 — AgentTaskScheduler (SP-D.2) ADR-161: 우선순위 기반 작업 스케줄러."""
from __future__ import annotations
import time, logging
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional
from literary_system.agents.agent_task import AgentTask, TaskQueue, TaskStatus, TaskPriority

logger = logging.getLogger(__name__)

@dataclass
class SchedulerStats:
    scheduled: int = 0
    dispatched: int = 0
    timed_out: int = 0
    rejected: int = 0

class AgentTaskScheduler:
    """멀티에이전트 작업 스케줄러.
    
    AgentCapabilityRegistry와 연동하여 적합한 에이전트에게 작업을 배분한다.
    우선순위 큐 기반. 타임아웃 작업 자동 실패 처리.
    """
    def __init__(self, max_queue_size: int = 1000) -> None:
        self._queue = TaskQueue("scheduler-queue")
        self._max_queue_size = max_queue_size
        self._handlers: Dict[str, Callable[[AgentTask], bool]] = {}
        self._stats = SchedulerStats()
        self._running: Dict[str, AgentTask] = {}  # task_id → task

    def register_handler(self, capability: str, handler: Callable[[AgentTask], bool]) -> None:
        """능력별 작업 처리 핸들러 등록."""
        self._handlers[capability] = handler

    def schedule(self, task: AgentTask) -> bool:
        """작업 스케줄 등록. 큐 용량 초과 시 거부."""
        if self._queue.pending_count() >= self._max_queue_size:
            self._stats.rejected += 1
            logger.warning("[Scheduler] Queue full, rejected task=%s", task.task_id)
            return False
        self._queue.enqueue(task)
        self._stats.scheduled += 1
        logger.debug("[Scheduler] scheduled task=%s pri=%s", task.name, task.priority.name)
        return True

    def tick(self) -> int:
        """스케줄러 1 tick — 대기 작업을 핸들러에 dispatch. 반환값: dispatch 건수."""
        # 1. 타임아웃 작업 처리
        for task in list(self._running.values()):
            if task.is_timed_out():
                task.fail(f"timeout after {task.timeout_seconds}s")
                del self._running[task.task_id]
                self._stats.timed_out += 1

        # 2. 대기 작업 dispatch
        dispatched = 0
        while True:
            task = self._queue.dequeue()
            if task is None:
                break
            # 능력 기반 핸들러 탐색
            cap_tag = task.tags[0] if task.tags else task.name
            handler = self._handlers.get(cap_tag) or self._handlers.get("*")
            if handler:
                task.start()
                self._running[task.task_id] = task
                try:
                    ok = handler(task)
                    if ok:
                        task.complete()
                    else:
                        task.fail("handler returned False")
                except Exception as exc:
                    task.fail(str(exc))
                finally:
                    self._running.pop(task.task_id, None)
                self._stats.dispatched += 1
                dispatched += 1
            else:
                # 핸들러 없음 → 다시 큐에
                task.status = TaskStatus.PENDING
                task.started_at = None
                self._queue.force_requeue(task)
                break
        return dispatched

    def pending_count(self) -> int:
        return self._queue.pending_count()

    def stats(self) -> Dict:
        return {
            "scheduled": self._stats.scheduled,
            "dispatched": self._stats.dispatched,
            "timed_out": self._stats.timed_out,
            "rejected": self._stats.rejected,
            "pending": self.pending_count(),
        }

    def cancel(self, task_id: str) -> bool:
        return self._queue.cancel(task_id)

ADR_161 = {"id": "ADR-161", "title": "AgentTaskScheduler", "status": "accepted",
            "decision": "우선순위 큐 기반 스케줄러. 능력별 핸들러 등록. 타임아웃 자동 처리.",
            "version": "V699"}
