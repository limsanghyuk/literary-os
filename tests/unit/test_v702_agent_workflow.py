"""V702 — AgentWorkflow DAG 테스트 (33 TC)."""
import pytest
from literary_system.agents.agent_workflow import (
    AgentWorkflow, WorkflowStep, WorkflowStatus, StepStatus,
    WorkflowContext, ADR_164,
)


def make_wf(name: str = "wf") -> AgentWorkflow:
    return AgentWorkflow(name=name)


def ok_handler(ctx: WorkflowContext) -> str:
    return "ok"


def fail_handler(ctx: WorkflowContext) -> None:
    raise RuntimeError("step failed")


# ══════════════════════════════════════════════════════════════════════
class TestWorkflowBasics:
    def test_tc01_create_workflow(self):
        wf = make_wf("test")
        assert wf.name == "test"
        assert wf.status == WorkflowStatus.DRAFT

    def test_tc02_add_step(self):
        wf = make_wf()
        s = wf.add_step("step1", ok_handler)
        assert s.name == "step1"
        assert s.status == StepStatus.PENDING

    def test_tc03_run_single_step(self):
        wf = make_wf()
        wf.add_step("step1", ok_handler, step_id="s1")
        ok = wf.run()
        assert ok
        assert wf.status == WorkflowStatus.COMPLETED
        assert wf.context.step_results["s1"] == "ok"

    def test_tc04_run_sequential(self):
        wf = make_wf()
        order = []
        wf.add_step("s1", lambda ctx: order.append(1), step_id="s1")
        wf.add_step("s2", lambda ctx: order.append(2), step_id="s2", depends_on=["s1"])
        wf.add_step("s3", lambda ctx: order.append(3), step_id="s3", depends_on=["s2"])
        ok = wf.run()
        assert ok
        assert order == [1, 2, 3]

    def test_tc05_parallel_steps(self):
        wf = make_wf()
        results = []
        wf.add_step("s1", lambda ctx: results.append("s1"), step_id="s1")
        wf.add_step("s2", lambda ctx: results.append("s2"), step_id="s2")
        wf.add_step("s3", lambda ctx: results.append("s3"), step_id="s3",
                    depends_on=["s1", "s2"])
        ok = wf.run()
        assert ok
        assert "s3" in results
        assert wf.status == WorkflowStatus.COMPLETED

    def test_tc06_step_failure_causes_workflow_failure(self):
        wf = make_wf()
        wf.add_step("s1", fail_handler, step_id="s1")
        ok = wf.run()
        assert not ok
        assert wf.status == WorkflowStatus.FAILED

    def test_tc07_downstream_skipped_on_failure(self):
        wf = make_wf()
        wf.add_step("s1", fail_handler, step_id="s1")
        wf.add_step("s2", ok_handler, step_id="s2", depends_on=["s1"])
        wf.run()
        assert wf._steps["s1"].status == StepStatus.FAILED
        assert wf._steps["s2"].status == StepStatus.SKIPPED

    def test_tc08_context_shared_between_steps(self):
        wf = make_wf()
        def writer(ctx): ctx.data["key"] = "value"; return "written"
        def reader(ctx): return ctx.data.get("key")
        wf.add_step("write", writer, step_id="w")
        wf.add_step("read", reader, step_id="r", depends_on=["w"])
        wf.run()
        assert wf.context.step_results["r"] == "value"

    def test_tc09_step_result_in_context(self):
        wf = make_wf()
        wf.add_step("s1", lambda ctx: 42, step_id="s1")
        wf.run()
        assert wf.context.step_results["s1"] == 42

    def test_tc10_invalid_dependency_raises(self):
        wf = make_wf()
        with pytest.raises(ValueError):
            wf.add_step("s1", ok_handler, depends_on=["nonexistent"])

    def test_tc11_step_done_status(self):
        wf = make_wf()
        wf.add_step("s1", ok_handler, step_id="s1")
        wf.run()
        assert wf._steps["s1"].status == StepStatus.DONE

    def test_tc12_step_failed_status(self):
        wf = make_wf()
        wf.add_step("s1", fail_handler, step_id="s1")
        wf.run()
        assert wf._steps["s1"].status == StepStatus.FAILED
        assert "step failed" in wf._steps["s1"].error

    def test_tc13_step_duration(self):
        wf = make_wf()
        wf.add_step("s1", ok_handler, step_id="s1")
        wf.run()
        d = wf._steps["s1"].duration_seconds()
        assert d is not None and d >= 0

    def test_tc14_workflow_finished_at(self):
        wf = make_wf()
        wf.add_step("s1", ok_handler)
        assert wf.finished_at is None
        wf.run()
        assert wf.finished_at is not None

    def test_tc15_stats(self):
        wf = make_wf()
        wf.add_step("s1", ok_handler, step_id="s1")
        wf.add_step("s2", fail_handler, step_id="s2")
        wf.add_step("s3", ok_handler, step_id="s3", depends_on=["s2"])
        wf.run()
        st = wf.stats()
        assert st["total_steps"] == 3
        assert st["by_status"].get("done", 0) == 1
        assert st["by_status"].get("failed", 0) == 1
        assert st["by_status"].get("skipped", 0) == 1


class TestWorkflowHooks:
    def test_tc16_started_hook(self):
        wf = make_wf()
        fired = []
        wf.on("started", lambda w: fired.append("started"))
        wf.add_step("s1", ok_handler)
        wf.run()
        assert "started" in fired

    def test_tc17_completed_hook(self):
        wf = make_wf()
        fired = []
        wf.on("completed", lambda w: fired.append("completed"))
        wf.add_step("s1", ok_handler)
        wf.run()
        assert "completed" in fired

    def test_tc18_failed_hook(self):
        wf = make_wf()
        fired = []
        wf.on("failed", lambda w: fired.append("failed"))
        wf.add_step("s1", fail_handler)
        wf.run()
        assert "failed" in fired

    def test_tc19_step_done_hook(self):
        wf = make_wf()
        done_steps = []
        wf.on("step_done", lambda s: done_steps.append(s.name))
        wf.add_step("alpha", ok_handler)
        wf.run()
        assert "alpha" in done_steps

    def test_tc20_step_failed_hook(self):
        wf = make_wf()
        failed_steps = []
        wf.on("step_failed", lambda s: failed_steps.append(s.name))
        wf.add_step("bad", fail_handler)
        wf.run()
        assert "bad" in failed_steps

    def test_tc21_step_skipped_hook(self):
        wf = make_wf()
        skipped = []
        wf.on("step_skipped", lambda s: skipped.append(s.name))
        wf.add_step("fail", fail_handler, step_id="f")
        wf.add_step("skip_me", ok_handler, depends_on=["f"])
        wf.run()
        assert "skip_me" in skipped


class TestWorkflowAdvanced:
    def test_tc22_cancel_draft(self):
        wf = make_wf()
        ok = wf.cancel()
        assert ok
        assert wf.status == WorkflowStatus.CANCELLED

    def test_tc23_cannot_cancel_completed(self):
        wf = make_wf()
        wf.add_step("s1", ok_handler)
        wf.run()
        ok = wf.cancel()
        assert not ok

    def test_tc24_cannot_run_twice(self):
        wf = make_wf()
        wf.add_step("s1", ok_handler)
        wf.run()
        ok2 = wf.run()
        assert not ok2

    def test_tc25_steps_accessor(self):
        wf = make_wf()
        wf.add_step("s1", ok_handler, step_id="s1")
        wf.add_step("s2", ok_handler, step_id="s2")
        assert len(wf.steps()) == 2

    def test_tc26_step_by_id(self):
        wf = make_wf()
        s = wf.add_step("s1", ok_handler, step_id="s1")
        assert wf.step_by_id("s1") is s
        assert wf.step_by_id("nope") is None

    def test_tc27_diamond_dag(self):
        """A → B, A → C, B → D, C → D (diamond)."""
        wf = make_wf()
        order = []
        wf.add_step("A", lambda ctx: order.append("A"), step_id="A")
        wf.add_step("B", lambda ctx: order.append("B"), step_id="B", depends_on=["A"])
        wf.add_step("C", lambda ctx: order.append("C"), step_id="C", depends_on=["A"])
        wf.add_step("D", lambda ctx: order.append("D"), step_id="D", depends_on=["B", "C"])
        ok = wf.run()
        assert ok
        assert order[0] == "A"
        assert order[-1] == "D"

    def test_tc28_step_metadata(self):
        wf = make_wf()
        s = wf.add_step("s1", ok_handler, metadata={"owner": "agent-A"})
        assert s.metadata["owner"] == "agent-A"

    def test_tc29_workflow_context_initial(self):
        wf = make_wf()
        assert wf.context.workflow_id == wf.workflow_id
        assert wf.context.data == {}

    def test_tc30_is_terminal_step(self):
        s = WorkflowStep(step_id="x", name="x", handler=ok_handler)
        assert not s.is_terminal()
        s.status = StepStatus.DONE
        assert s.is_terminal()

    def test_tc31_multiple_failures_reported_in_stats(self):
        wf = make_wf()
        wf.add_step("f1", fail_handler, step_id="f1")
        wf.add_step("f2", fail_handler, step_id="f2")
        wf.run()
        st = wf.stats()
        assert st["by_status"].get("failed", 0) == 2

    def test_tc32_long_chain(self):
        wf = make_wf()
        prev = None
        for i in range(10):
            sid = f"s{i}"
            wf.add_step(sid, ok_handler, step_id=sid,
                        depends_on=[f"s{i-1}"] if i > 0 else [])
            prev = sid
        ok = wf.run()
        assert ok
        assert all(s.status == StepStatus.DONE for s in wf.steps())

    def test_tc33_adr_164(self):
        assert ADR_164["id"] == "ADR-164"
        assert ADR_164["status"] == "accepted"
        assert "DAG" in ADR_164["title"]
