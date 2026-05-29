"""test_v697_agent_task.py — V697 AgentTask + TaskQueue 단위 테스트 (ADR-159) TC01~TC33"""
from __future__ import annotations
import time, pytest
from literary_system.agents.agent_task import (
    AgentTask, TaskQueue, TaskStatus, TaskPriority, ADR_159
)

def make_task(name="write", agent="agent_a", priority=TaskPriority.NORMAL, max_retries=0):
    return AgentTask(name=name, assigned_agent=agent, payload={"scene": 1},
                     priority=priority, max_retries=max_retries)

class TestAgentTaskCreation:
    def test_tc01_basic_creation(self):
        t = make_task()
        assert t.name == "write"
        assert t.assigned_agent == "agent_a"
        assert t.status == TaskStatus.PENDING

    def test_tc02_auto_task_id(self):
        t1, t2 = make_task(), make_task()
        assert t1.task_id != t2.task_id

    def test_tc03_priority_default(self):
        assert make_task().priority == TaskPriority.NORMAL

    def test_tc04_start_transition(self):
        t = make_task()
        t.start()
        assert t.status == TaskStatus.RUNNING
        assert t.started_at is not None

    def test_tc05_complete_transition(self):
        t = make_task()
        t.start()
        t.complete(result={"text": "done"})
        assert t.status == TaskStatus.DONE
        assert t.result == {"text": "done"}
        assert t.completed_at is not None

    def test_tc06_fail_no_retry(self):
        t = make_task()
        t.start()
        t.fail("network error")
        assert t.status == TaskStatus.FAILED
        assert t.error == "network error"

    def test_tc07_fail_with_retry(self):
        t = make_task(max_retries=2)
        t.start()
        t.fail("timeout")
        assert t.status == TaskStatus.RETRYING
        assert t.retry_count == 1

    def test_tc08_retry_exhausted(self):
        t = make_task(max_retries=1)
        t.start(); t.fail("e1")   # → RETRYING
        t.reset_for_retry()
        t.start(); t.fail("e2")   # → FAILED (max 초과)
        assert t.status == TaskStatus.FAILED

    def test_tc09_cancel(self):
        t = make_task()
        t.cancel()
        assert t.status == TaskStatus.CANCELLED

    def test_tc10_cancel_running_raises(self):
        t = make_task()
        t.start()
        with pytest.raises(ValueError):
            t.cancel()

    def test_tc11_is_terminal(self):
        t = make_task()
        assert t.is_terminal is False
        t.start(); t.complete()
        assert t.is_terminal is True

    def test_tc12_duration(self):
        t = make_task()
        t.start()
        time.sleep(0.01)
        t.complete()
        assert t.duration_seconds is not None
        assert t.duration_seconds > 0

    def test_tc13_timeout(self):
        t = AgentTask(name="t", assigned_agent="a", payload={}, timeout_seconds=0.001)
        t.start()
        time.sleep(0.01)
        assert t.is_timed_out() is True

    def test_tc14_no_timeout(self):
        t = make_task()
        t.start()
        assert t.is_timed_out() is False

class TestAgentTaskSerialization:
    def test_tc15_to_dict(self):
        t = make_task()
        d = t.to_dict()
        assert d["name"] == "write"
        assert d["status"] == "pending"
        assert d["priority"] == TaskPriority.NORMAL.value

    def test_tc16_dependencies(self):
        t = AgentTask(name="t", assigned_agent="a", payload={},
                      dependencies=["dep1", "dep2"])
        assert "dep1" in t.dependencies
        d = t.to_dict()
        assert "dep1" in d["dependencies"]

    def test_tc17_tags(self):
        t = AgentTask(name="t", assigned_agent="a", payload={}, tags=["sp-d2", "v697"])
        assert "sp-d2" in t.tags

class TestTaskQueue:
    def setup_method(self):
        self.q = TaskQueue("test-q")

    def test_tc18_enqueue_dequeue(self):
        t = make_task()
        self.q.enqueue(t)
        out = self.q.dequeue()
        assert out is not None
        assert out.task_id == t.task_id

    def test_tc19_priority_ordering(self):
        t_low = make_task(name="low", priority=TaskPriority.LOW)
        t_high = make_task(name="high", priority=TaskPriority.HIGH)
        t_critical = make_task(name="crit", priority=TaskPriority.CRITICAL)
        for t in [t_low, t_high, t_critical]:
            self.q.enqueue(t)
        out = self.q.dequeue()
        assert out.name == "crit"

    def test_tc20_empty_dequeue(self):
        assert self.q.dequeue() is None

    def test_tc21_pending_count(self):
        for _ in range(3):
            self.q.enqueue(make_task())
        assert self.q.pending_count() == 3

    def test_tc22_cancel_task(self):
        t = make_task()
        self.q.enqueue(t)
        assert self.q.cancel(t.task_id) is True
        assert t.status == TaskStatus.CANCELLED

    def test_tc23_get_task(self):
        t = make_task()
        self.q.enqueue(t)
        found = self.q.get_task(t.task_id)
        assert found is t

    def test_tc24_stats(self):
        for _ in range(4):
            self.q.enqueue(make_task())
        self.q.dequeue(); self.q.dequeue()
        s = self.q.stats()
        assert s["enqueued"] == 4
        assert s["dequeued"] == 2

    def test_tc25_agent_tasks(self):
        for _ in range(3):
            self.q.enqueue(make_task(agent="agent_x"))
        self.q.enqueue(make_task(agent="agent_y"))
        assert len(self.q.agent_tasks("agent_x")) == 3

    def test_tc26_running_count(self):
        t1, t2 = make_task(), make_task()
        self.q.enqueue(t1); self.q.enqueue(t2)
        out1 = self.q.dequeue(); out1.start()
        assert self.q.running_count() == 1

    def test_tc27_peek(self):
        t = make_task()
        self.q.enqueue(t)
        p = self.q.peek()
        assert p is not None
        assert self.q.pending_count() == 1  # peek은 꺼내지 않음

    def test_tc28_duplicate_enqueue_raises(self):
        t = make_task()
        self.q.enqueue(t)
        with pytest.raises(ValueError):
            self.q.enqueue(t)

    def test_tc29_all_tasks(self):
        for _ in range(5):
            self.q.enqueue(make_task())
        assert len(self.q.all_tasks()) == 5

    def test_tc30_skip_cancelled_on_dequeue(self):
        t1, t2 = make_task(name="t1"), make_task(name="t2")
        self.q.enqueue(t1); self.q.enqueue(t2)
        self.q.cancel(t1.task_id)
        out = self.q.dequeue()
        assert out.name == "t2"

    def test_tc31_fifo_same_priority(self):
        t1 = make_task(name="first"); time.sleep(0.001)
        t2 = make_task(name="second")
        self.q.enqueue(t1); self.q.enqueue(t2)
        assert self.q.dequeue().name == "first"

    def test_tc32_task_priority_critical_value(self):
        assert TaskPriority.CRITICAL.value < TaskPriority.HIGH.value
        assert TaskPriority.HIGH.value < TaskPriority.NORMAL.value
        assert TaskPriority.NORMAL.value < TaskPriority.LOW.value

    def test_tc33_adr_159(self):
        assert ADR_159["id"] == "ADR-159"
        assert "TaskQueue" in ADR_159["decision"]
