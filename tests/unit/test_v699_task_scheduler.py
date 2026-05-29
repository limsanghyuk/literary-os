"""test_v699_task_scheduler.py — V699 AgentTaskScheduler TC01~TC33"""
from __future__ import annotations
import time, pytest
from literary_system.agents.agent_task import AgentTask, TaskStatus, TaskPriority
from literary_system.agents.task_scheduler import AgentTaskScheduler, ADR_161

def make_task(name="write", priority=TaskPriority.NORMAL, tags=None, timeout=None):
    return AgentTask(name=name, assigned_agent="a", payload={},
                     priority=priority, tags=tags or [name], timeout_seconds=timeout)

class TestSchedulerBasics:
    def setup_method(self):
        self.sched = AgentTaskScheduler(max_queue_size=10)

    def test_tc01_creation(self):
        assert self.sched.pending_count() == 0

    def test_tc02_schedule(self):
        t = make_task()
        assert self.sched.schedule(t) is True
        assert self.sched.pending_count() == 1

    def test_tc03_queue_full_reject(self):
        sched = AgentTaskScheduler(max_queue_size=2)
        sched.schedule(make_task("a"))
        sched.schedule(make_task("b"))
        result = sched.schedule(make_task("c"))
        assert result is False
        assert sched.stats()["rejected"] == 1

    def test_tc04_register_handler(self):
        self.sched.register_handler("write", lambda t: True)
        # 핸들러 등록 확인 (내부 구현 접근)
        assert "write" in self.sched._handlers

    def test_tc05_tick_dispatches(self):
        self.sched.register_handler("write", lambda t: True)
        t = make_task(tags=["write"])
        self.sched.schedule(t)
        dispatched = self.sched.tick()
        assert dispatched == 1

    def test_tc06_task_completed_after_tick(self):
        self.sched.register_handler("write", lambda t: True)
        t = make_task(tags=["write"])
        self.sched.schedule(t)
        self.sched.tick()
        assert t.status == TaskStatus.DONE

    def test_tc07_task_failed_on_handler_false(self):
        self.sched.register_handler("write", lambda t: False)
        t = make_task(tags=["write"])
        self.sched.schedule(t)
        self.sched.tick()
        assert t.status == TaskStatus.FAILED

    def test_tc08_task_failed_on_exception(self):
        def bad_handler(t): raise RuntimeError("crash")
        self.sched.register_handler("write", bad_handler)
        t = make_task(tags=["write"])
        self.sched.schedule(t)
        self.sched.tick()
        assert t.status == TaskStatus.FAILED

    def test_tc09_wildcard_handler(self):
        self.sched.register_handler("*", lambda t: True)
        t = make_task(tags=["unknown_cap"])
        self.sched.schedule(t)
        dispatched = self.sched.tick()
        assert dispatched == 1

    def test_tc10_no_handler_stays_pending(self):
        t = make_task(tags=["unregistered"])
        self.sched.schedule(t)
        self.sched.tick()
        # 핸들러 없으면 다시 큐로
        assert self.sched.pending_count() == 1

    def test_tc11_multiple_tasks_dispatched(self):
        self.sched.register_handler("write", lambda t: True)
        for i in range(5):
            self.sched.schedule(make_task(f"w{i}", tags=["write"]))
        cnt = self.sched.tick()
        assert cnt == 5

    def test_tc12_priority_ordering(self):
        order = []
        def handler(t):
            order.append(t.name)
            return True
        self.sched.register_handler("write", handler)
        for name, pri in [("low", TaskPriority.LOW), ("high", TaskPriority.HIGH),
                          ("crit", TaskPriority.CRITICAL)]:
            self.sched.schedule(make_task(name, pri, tags=["write"]))
        self.sched.tick()
        assert order[0] == "crit"
        assert order[1] == "high"
        assert order[2] == "low"

    def test_tc13_cancel_task(self):
        t = make_task()
        self.sched.schedule(t)
        assert self.sched.cancel(t.task_id) is True
        assert t.status == TaskStatus.CANCELLED

    def test_tc14_stats_after_dispatch(self):
        self.sched.register_handler("write", lambda t: True)
        for _ in range(3):
            self.sched.schedule(make_task(tags=["write"]))
        self.sched.tick()
        s = self.sched.stats()
        assert s["scheduled"] == 3
        assert s["dispatched"] == 3
        assert s["pending"] == 0

    def test_tc15_timeout_processing(self):
        self.sched.register_handler("slow", lambda t: (time.sleep(0.05) or True))
        t = make_task(tags=["slow"], timeout=0.001)
        t.start()  # 직접 시작 → running 상태
        t.started_at = time.time() - 1.0  # 1초 전 시작으로 설정
        self.sched._running[t.task_id] = t
        self.sched.tick()
        assert t.status in (TaskStatus.FAILED, TaskStatus.RETRYING)
        assert self.sched.stats()["timed_out"] == 1

class TestSchedulerStats:
    def test_tc16_initial_stats(self):
        s = AgentTaskScheduler()
        stats = s.stats()
        assert stats["scheduled"] == 0
        assert stats["dispatched"] == 0
        assert stats["rejected"] == 0

    def test_tc17_scheduled_count(self):
        s = AgentTaskScheduler()
        s.schedule(make_task("a"))
        s.schedule(make_task("b"))
        assert s.stats()["scheduled"] == 2

    def test_tc18_tick_empty_queue(self):
        s = AgentTaskScheduler()
        assert s.tick() == 0

class TestSchedulerScenarios:
    def test_tc19_parallel_capability_handlers(self):
        sched = AgentTaskScheduler()
        written, critiqued = [], []
        sched.register_handler("write", lambda t: written.append(t) or True)
        sched.register_handler("critique", lambda t: critiqued.append(t) or True)
        sched.schedule(make_task("w1", tags=["write"]))
        sched.schedule(make_task("c1", tags=["critique"]))
        sched.tick()
        assert len(written) == 1 and len(critiqued) == 1

    def test_tc20_handler_override(self):
        sched = AgentTaskScheduler()
        results = []
        sched.register_handler("write", lambda t: results.append("v1") or True)
        sched.register_handler("write", lambda t: results.append("v2") or True)
        sched.schedule(make_task(tags=["write"]))
        sched.tick()
        assert results == ["v2"]  # 후 등록이 우선

    def test_tc21_task_with_retry(self):
        sched = AgentTaskScheduler()
        call_count = [0]
        def handler(t):
            call_count[0] += 1
            return call_count[0] > 1  # 첫 번째 실패, 두 번째 성공
        sched.register_handler("w", handler)
        t = AgentTask(name="retry", assigned_agent="a", payload={}, max_retries=1, tags=["w"])
        sched.schedule(t)
        sched.tick()  # fail → RETRYING
        if t.status == TaskStatus.RETRYING:
            t.reset_for_retry()
            sched._queue.force_requeue(t)
            sched.tick()  # success
        assert t.status == TaskStatus.DONE

    def test_tc22_large_batch(self):
        sched = AgentTaskScheduler(max_queue_size=500)
        sched.register_handler("bulk", lambda t: True)
        for i in range(100):
            sched.schedule(make_task(f"t{i}", tags=["bulk"]))
        cnt = sched.tick()
        assert cnt == 100

    def test_tc23_pending_after_partial(self):
        sched = AgentTaskScheduler()
        sched.register_handler("w", lambda t: True)
        for _ in range(3):
            sched.schedule(make_task(tags=["w"]))
        # tick 1번에 모두 처리
        sched.tick()
        assert sched.pending_count() == 0

    def test_tc24_task_payload_preserved(self):
        sched = AgentTaskScheduler()
        payload_seen = {}
        def handler(t):
            payload_seen.update(t.payload)
            return True
        sched.register_handler("w", handler)
        t = make_task(tags=["w"])
        t.payload = {"scene_id": "s42", "tone": "dramatic"}
        sched.schedule(t)
        sched.tick()
        assert payload_seen["scene_id"] == "s42"

    def test_tc25_schedule_after_cancel(self):
        sched = AgentTaskScheduler()
        sched.register_handler("w", lambda t: True)
        t = make_task(tags=["w"])
        sched.schedule(t)
        sched.cancel(t.task_id)
        # 취소된 작업은 새 작업으로 대체
        t2 = make_task("w2", tags=["w"])
        sched.schedule(t2)
        cnt = sched.tick()
        assert cnt == 1
        assert t2.status == TaskStatus.DONE

    def test_tc26_adr_161(self):
        assert ADR_161["id"] == "ADR-161"
        assert "스케줄러" in ADR_161["decision"]

    # TC27~TC33 — 엣지 케이스
    def test_tc27_schedule_high_priority_processed_first(self):
        sched = AgentTaskScheduler()
        order = []
        sched.register_handler("x", lambda t: order.append(t.name) or True)
        sched.schedule(make_task("normal", TaskPriority.NORMAL, ["x"]))
        sched.schedule(make_task("critical", TaskPriority.CRITICAL, ["x"]))
        sched.tick()
        assert order[0] == "critical"

    def test_tc28_empty_tick_returns_zero(self):
        sched = AgentTaskScheduler()
        assert sched.tick() == 0

    def test_tc29_max_queue_size_one(self):
        sched = AgentTaskScheduler(max_queue_size=1)
        assert sched.schedule(make_task("a")) is True
        assert sched.schedule(make_task("b")) is False

    def test_tc30_stats_timed_out_initial(self):
        assert AgentTaskScheduler().stats()["timed_out"] == 0

    def test_tc31_cancel_nonexistent(self):
        assert AgentTaskScheduler().cancel("ghost-id") is False

    def test_tc32_handler_receives_task(self):
        sched = AgentTaskScheduler()
        received = []
        sched.register_handler("w", lambda t: received.append(t) or True)
        t = make_task(tags=["w"])
        sched.schedule(t)
        sched.tick()
        assert received[0] is t

    def test_tc33_background_priority(self):
        sched = AgentTaskScheduler()
        order = []
        sched.register_handler("x", lambda t: order.append(t.priority.name) or True)
        for pri in [TaskPriority.BACKGROUND, TaskPriority.NORMAL, TaskPriority.HIGH]:
            sched.schedule(make_task(priority=pri, tags=["x"]))
        sched.tick()
        assert order == ["HIGH", "NORMAL", "BACKGROUND"]
