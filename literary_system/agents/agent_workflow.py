"""V702 — AgentWorkflow DAG (SP-D.2) ADR-164: DAG 기반 에이전트 작업 흐름."""
from __future__ import annotations
import time, uuid, logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowStatus(Enum):
    DRAFT = "draft"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkflowStep:
    step_id: str
    name: str
    handler: Callable[["WorkflowContext"], Any]
    depends_on: List[str] = field(default_factory=list)  # step_ids
    status: StepStatus = StepStatus.PENDING
    result: Optional[Any] = None
    error: str = ""
    started_at: Optional[float] = None
    finished_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def duration_seconds(self) -> Optional[float]:
        if self.started_at and self.finished_at:
            return self.finished_at - self.started_at
        return None

    def is_terminal(self) -> bool:
        return self.status in (StepStatus.DONE, StepStatus.FAILED, StepStatus.SKIPPED)


@dataclass
class WorkflowContext:
    """실행 컨텍스트 — 단계 간 데이터 공유."""
    workflow_id: str
    data: Dict[str, Any] = field(default_factory=dict)
    step_results: Dict[str, Any] = field(default_factory=dict)  # step_id → result


class AgentWorkflow:
    """DAG 기반 에이전트 워크플로우.

    ADR-164: 단계(WorkflowStep)를 DAG로 연결하고 위상 정렬 순서로 실행한다.
    의존성이 완료된 단계만 실행. 실패 시 다운스트림 단계 스킵.
    """

    def __init__(self, name: str = "") -> None:
        self.workflow_id = str(uuid.uuid4())
        self.name = name
        self._steps: Dict[str, WorkflowStep] = {}
        self.status = WorkflowStatus.DRAFT
        self.context = WorkflowContext(workflow_id=self.workflow_id)
        self._hooks: Dict[str, List[Callable]] = {}
        self.created_at = time.time()
        self.finished_at: Optional[float] = None

    # ── 단계 등록 ────────────────────────────────────────────────────

    def add_step(
        self,
        name: str,
        handler: Callable[[WorkflowContext], Any],
        depends_on: Optional[List[str]] = None,
        step_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> WorkflowStep:
        sid = step_id or str(uuid.uuid4())
        step = WorkflowStep(
            step_id=sid,
            name=name,
            handler=handler,
            depends_on=depends_on or [],
            metadata=metadata or {},
        )
        # 의존성 검증
        for dep in step.depends_on:
            if dep not in self._steps:
                raise ValueError(f"Dependency step_id '{dep}' not registered yet")
        self._steps[sid] = step
        return step

    # ── 실행 ─────────────────────────────────────────────────────────

    def run(self) -> bool:
        """워크플로우 실행. 완료 시 True, 실패 시 False."""
        if self.status != WorkflowStatus.DRAFT:
            return False
        if self._has_cycle():
            raise RuntimeError("Workflow DAG has a cycle")

        self.status = WorkflowStatus.RUNNING
        self._fire("started", self)

        order = self._topological_sort()
        failed_steps: Set[str] = set()

        for sid in order:
            step = self._steps[sid]

            # 의존성 실패 → 스킵
            if any(dep in failed_steps for dep in step.depends_on):
                step.status = StepStatus.SKIPPED
                failed_steps.add(sid)  # 스킵도 다운스트림 차단
                self._fire("step_skipped", step)
                continue

            # 실행
            step.status = StepStatus.RUNNING
            step.started_at = time.time()
            self._fire("step_started", step)
            try:
                result = step.handler(self.context)
                step.result = result
                step.status = StepStatus.DONE
                self.context.step_results[sid] = result
                self._fire("step_done", step)
            except Exception as exc:
                step.error = str(exc)
                step.status = StepStatus.FAILED
                failed_steps.add(sid)
                self._fire("step_failed", step)
                logger.warning("[Workflow] step %s FAILED: %s", step.name, exc)
            finally:
                step.finished_at = time.time()

        if any(s.status == StepStatus.FAILED for s in self._steps.values()):
            self.status = WorkflowStatus.FAILED
            self._fire("failed", self)
            self.finished_at = time.time()
            return False

        self.status = WorkflowStatus.COMPLETED
        self.finished_at = time.time()
        self._fire("completed", self)
        return True

    # ── DAG 유틸리티 ─────────────────────────────────────────────────

    def _topological_sort(self) -> List[str]:
        """Kahn's algorithm 위상 정렬."""
        in_degree: Dict[str, int] = {sid: 0 for sid in self._steps}
        adj: Dict[str, List[str]] = {sid: [] for sid in self._steps}
        for sid, step in self._steps.items():
            for dep in step.depends_on:
                adj[dep].append(sid)
                in_degree[sid] += 1

        queue = [sid for sid, d in in_degree.items() if d == 0]
        order: List[str] = []
        while queue:
            node = queue.pop(0)
            order.append(node)
            for child in adj[node]:
                in_degree[child] -= 1
                if in_degree[child] == 0:
                    queue.append(child)
        return order

    def _has_cycle(self) -> bool:
        visited: Set[str] = set()
        rec_stack: Set[str] = set()

        def dfs(v: str) -> bool:
            visited.add(v)
            rec_stack.add(v)
            for dep in self._steps[v].depends_on:
                if dep not in visited:
                    if dfs(dep):
                        return True
                elif dep in rec_stack:
                    return True
            rec_stack.discard(v)
            return False

        for sid in self._steps:
            if sid not in visited:
                if dfs(sid):
                    return True
        return False

    # ── 훅·조회 ──────────────────────────────────────────────────────

    def on(self, event: str, cb: Callable) -> None:
        self._hooks.setdefault(event, []).append(cb)

    def _fire(self, event: str, payload: Any) -> None:
        for cb in self._hooks.get(event, []):
            try:
                cb(payload)
            except Exception as exc:
                logger.warning("[Workflow] hook error: %s", exc)

    def steps(self) -> List[WorkflowStep]:
        return list(self._steps.values())

    def step_by_id(self, step_id: str) -> Optional[WorkflowStep]:
        return self._steps.get(step_id)

    def stats(self) -> Dict[str, Any]:
        counts: Dict[str, int] = {}
        for s in self._steps.values():
            counts[s.status.value] = counts.get(s.status.value, 0) + 1
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "status": self.status.value,
            "total_steps": len(self._steps),
            "by_status": counts,
        }

    def cancel(self) -> bool:
        if self.status in (WorkflowStatus.COMPLETED, WorkflowStatus.FAILED,
                           WorkflowStatus.CANCELLED):
            return False
        self.status = WorkflowStatus.CANCELLED
        self.finished_at = time.time()
        return True


ADR_164 = {
    "id": "ADR-164",
    "title": "AgentWorkflow DAG",
    "status": "accepted",
    "decision": (
        "WorkflowStep + DAG 위상 정렬 실행. 의존성 실패 시 다운스트림 스킵. "
        "컨텍스트 공유로 단계 간 데이터 전달."
    ),
    "version": "V702",
}
