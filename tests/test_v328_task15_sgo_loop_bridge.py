"""V328 Task15: SGOLoopBridge 테스트."""
import sys; sys.path.insert(0,"/tmp/literary_os_v328")
import pytest
from literary_system.orchestrators.sgo_loop_bridge import SGOLoopBridge, SGOLoopResult, MAX_RERENDERS
from literary_system.llm_bridge.mock_llm_bridge import MockLLMBridge
from literary_system.evaluation.mae_orchestrator import MAEOrchestrator
from literary_system.validation.coefficient_mapper import CoefficientMapper
from literary_system.validation.learned_coefficient_store import LearnedCoefficientStore
from literary_system.orchestrators.scene_generation_orchestrator import SceneGenerationOrchestrator as SGO
from literary_system.orchestrators.sequence_planner import SequencePlan, SequenceType

def _make_sgo():
    return SGO(bridge=MockLLMBridge(), mae_orchestrator=MAEOrchestrator(),
               coeff_mapper=CoefficientMapper(), coeff_store=LearnedCoefficientStore())

def _make_plans(n=2):
    return [SequencePlan(seq_id=f"s{i}", episode_no=1, seq_index=i,
                         goal="테스트", tension_target=0.6, scene_count=1,
                         act_index=1, pct_start=i/n, pct_end=(i+1)/n,
                         seq_type=SequenceType.PLOT_ADVANCE)
            for i in range(n)]

class TestSGOLoopResult:
    def test_defaults(self):
        r = SGOLoopResult(project_id="p1", episode_no=1)
        assert r.success == True
        assert r.rerenders == 0

    def test_fields(self):
        r = SGOLoopResult(project_id="p1", episode_no=2, final_text="텍스트",
                          scenes_generated=3, gate_decision="commit")
        assert r.scenes_generated == 3
        assert r.gate_decision == "commit"

class TestSGOLoopBridge:
    def test_no_sgo_returns_error_result(self):
        b = SGOLoopBridge()
        r = b.run_episode([], "proj1", episode_no=1)
        assert r.success == False
        assert r.error != ""

    def test_run_episode_success(self):
        b = SGOLoopBridge(sgo=_make_sgo())
        r = b.run_episode(_make_plans(), "proj1", episode_no=1)
        assert r.success == True
        assert r.project_id == "proj1"

    def test_episode_no_stored(self):
        b = SGOLoopBridge(sgo=_make_sgo())
        r = b.run_episode(_make_plans(), "proj1", episode_no=5)
        assert r.episode_no == 5

    def test_commit_gate_passes(self):
        class AlwaysCommit:
            def should_commit(self, text): return True
        b = SGOLoopBridge(sgo=_make_sgo(), conditional_gate=AlwaysCommit())
        r = b.run_episode(_make_plans(), "proj1")
        assert r.gate_decision == "commit"
        assert r.rerenders == 0

    def test_rerender_gate_limited_to_max(self):
        class NeverCommit:
            def should_commit(self, text): return False
        b = SGOLoopBridge(sgo=_make_sgo(), conditional_gate=NeverCommit())
        r = b.run_episode(_make_plans(), "proj1")
        assert r.rerenders <= MAX_RERENDERS

    def test_max_rerenders_constant(self):
        assert MAX_RERENDERS == 2

    def test_character_states_passed_through(self):
        b = SGOLoopBridge(sgo=_make_sgo())
        r = b.run_episode(_make_plans(), "proj1",
                          character_states={"홍길동":{"intent":"도주"}})
        assert r.success == True

    def test_sgo_exception_handled(self):
        class FailSGO:
            def run_episode(self, *a, **kw): raise RuntimeError("crash")
        b = SGOLoopBridge(sgo=FailSGO())
        r = b.run_episode([], "proj1")
        assert r.success == False
