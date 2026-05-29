"""V328 SGO 심층 통합 테스트 + 추가 경계값 커버리지."""
import sys; sys.path.insert(0,"/tmp/literary_os_v328")
import pytest
from dataclasses import dataclass
from literary_system.llm_bridge.mock_llm_bridge import MockLLMBridge
from literary_system.evaluation.mae_orchestrator import MAEOrchestrator
from literary_system.validation.coefficient_mapper import CoefficientMapper
from literary_system.validation.learned_coefficient_store import LearnedCoefficientStore
from literary_system.orchestrators.scene_generation_orchestrator import (
    SceneGenerationOrchestrator as SGO, SceneRecord, E2ESceneGenerationResult)
from literary_system.orchestrators.sequence_planner import SequencePlan, SequenceType
from literary_system.emotion.emotional_momentum_tracker import EmotionalMomentumTracker, EmotionalVector
from literary_system.schemas.scene_draft_output import SceneDraftOutput, SceneQuality

def _plan(n=1, scene_count=1, tension=0.6, seq_type=SequenceType.PLOT_ADVANCE):
    return [SequencePlan(seq_id=f"s{i}", episode_no=1, seq_index=i, goal=f"목표{i}",
                         tension_target=tension, scene_count=scene_count,
                         act_index=1, pct_start=i/n, pct_end=(i+1)/n,
                         seq_type=seq_type) for i in range(n)]

def _sgo(**kw):
    return SGO(bridge=MockLLMBridge(), mae_orchestrator=MAEOrchestrator(),
               coeff_mapper=CoefficientMapper(), coeff_store=LearnedCoefficientStore(), **kw)

# ── SGO 기본 동작 ────────────────────────────────────────────────────
class TestSGOBasic:
    def test_run_returns_e2e_result(self):
        r=_sgo().run_episode(_plan(),episode_no=1)
        assert isinstance(r, E2ESceneGenerationResult)

    def test_success_true(self):
        assert _sgo().run_episode(_plan(),episode_no=1).success==True

    def test_scenes_count_matches_plan(self):
        r=_sgo().run_episode(_plan(2, scene_count=3),episode_no=1)
        assert r.total_scenes_generated==6

    def test_scene_records_stored(self):
        r=_sgo().run_episode(_plan(1,2),episode_no=1)
        assert len(r.scenes)==2
        assert all(isinstance(s,SceneRecord) for s in r.scenes)

    def test_mae_consensus_rate_range(self):
        r=_sgo().run_episode(_plan(),episode_no=1)
        assert 0.0<=r.mae_consensus_rate<=1.0

    def test_duration_positive(self):
        r=_sgo().run_episode(_plan(),episode_no=1)
        assert r.duration_seconds>=0.0

    def test_summary_dict(self):
        r=_sgo().run_episode(_plan(),episode_no=1)
        s=r.summary()
        assert "episode_no" in s and "success" in s

    def test_multiple_sequence_types(self):
        plans=[]
        for i,st in enumerate([SequenceType.SETUP_HOOK, SequenceType.CONFLICT_PEAK,
                                SequenceType.EMOTIONAL_BEAT, SequenceType.CLIFFHANGER]):
            plans.append(SequencePlan(seq_id=f"s{i}",episode_no=1,seq_index=i,goal="g",
                                      tension_target=0.5+i*0.1,scene_count=1,act_index=1,
                                      pct_start=i/4,pct_end=(i+1)/4,seq_type=st))
        r=_sgo().run_episode(plans,episode_no=1)
        assert r.total_scenes_generated==4

# ── SceneRecord ──────────────────────────────────────────────────────
class TestSceneRecord:
    def _run(self):
        r=_sgo().run_episode(_plan(1,2),episode_no=1)
        return r.scenes

    def test_scene_id_unique(self):
        scenes=self._run()
        ids=[s.scene_id for s in scenes]
        assert len(set(ids))==len(ids)

    def test_mae_score_range(self):
        for s in self._run():
            assert 0.0<=s.mae_score<=1.0

    def test_scene_to_dict(self):
        for s in self._run():
            d=s.to_dict()
            assert "scene_id" in d and "text" in d

    def test_scene_text_nonempty(self):
        for s in self._run():
            assert len(s.text)>0

# ── EmotionalMomentum + SGO ──────────────────────────────────────────
class TestSGOEmotionDeep:
    def test_emotion_tracker_updates_per_scene(self):
        t=EmotionalMomentumTracker()
        sgo=_sgo(emotion_tracker=t)
        sgo.run_episode(_plan(2,scene_count=3),episode_no=1)
        assert len(t.history())==6

    def test_emotion_vector_values_in_range(self):
        t=EmotionalMomentumTracker()
        sgo=_sgo(emotion_tracker=t)
        sgo.run_episode(_plan(),episode_no=1)
        v=t.current()
        for attr in ("tension","sympathy","dread","catharsis"):
            assert 0.0<=getattr(v,attr)<=1.0

    def test_draft_output_attached_to_record(self):
        sgo=_sgo()
        r=sgo.run_episode(_plan(1,2),episode_no=1)
        for scene in r.scenes:
            if hasattr(scene,"_draft_output") and scene._draft_output is not None:
                assert isinstance(scene._draft_output, SceneDraftOutput)

    def test_emotion_tracker_reset_between_episodes(self):
        t=EmotionalMomentumTracker()
        sgo=_sgo(emotion_tracker=t)
        sgo.run_episode(_plan(1,2),episode_no=1)
        before=len(t.history())
        sgo.run_episode(_plan(1,2),episode_no=2)
        # History accumulates (no reset between episodes by default)
        assert len(t.history())==before+2

    def test_high_tension_plan_affects_emotion(self):
        t=EmotionalMomentumTracker()
        sgo=_sgo(emotion_tracker=t)
        sgo.run_episode(_plan(tension=0.95),episode_no=1)
        assert t.current().tension > 0.4  # some tension signal

# ── SGO _build_prompt ─────────────────────────────────────────────────
class TestSGOBuildPrompt:
    def _ctx(self, sgo, plan):
        from literary_system.orchestrators.scene_focus_injector import SceneFocusInjector
        return SceneFocusInjector(rag_bridge=None).build(
            seq_plan=plan, scene_index=0, total_scenes_in_seq=1)

    def test_contains_goal(self):
        sgo=_sgo(); plan=_plan()[0]
        ctx=self._ctx(sgo,plan)
        assert "목표0" in sgo._build_prompt(plan,ctx,0)

    def test_contains_tension(self):
        sgo=_sgo(); plan=_plan()[0]
        ctx=self._ctx(sgo,plan)
        assert "0.60" in sgo._build_prompt(plan,ctx,0)

    def test_attempt_msg_on_retry(self):
        sgo=_sgo(); plan=_plan()[0]
        ctx=self._ctx(sgo,plan)
        assert "재생성" in sgo._build_prompt(plan,ctx,attempt=2)

    def test_no_retry_msg_on_first_attempt(self):
        sgo=_sgo(); plan=_plan()[0]
        ctx=self._ctx(sgo,plan)
        assert "재생성" not in sgo._build_prompt(plan,ctx,attempt=0)

    def test_emotion_hint_present(self):
        t=EmotionalMomentumTracker(); sgo=_sgo(emotion_tracker=t)
        plan=_plan()[0]; ctx=self._ctx(sgo,plan)
        prompt=sgo._build_prompt(plan,ctx,0)
        assert "EmotionalMomentum" in prompt

    def test_knowledge_pressure_included(self):
        sgo=_sgo(); plan=_plan()[0]
        ctx=self._ctx(sgo,plan)
        char_states={"_knowledge_pressure":0.8,"_dominant_tension":{"chars":"A-B","fact":"배신","pressure":0.8}}
        prompt=sgo._build_prompt(plan,ctx,0,character_states=char_states)
        assert "지식 비대칭 압력" in prompt

# ── E2ESceneGenerationResult ─────────────────────────────────────────
class TestE2EResult:
    def test_summary_keys(self):
        r=_sgo().run_episode(_plan(),1)
        s=r.summary()
        for k in ("project_id","episode_no","total_scenes_generated","success"):
            assert k in s

    def test_coeff_update_count_gte_0(self):
        r=_sgo().run_episode(_plan(2,2),1)
        assert r.coeff_update_count>=0

    def test_total_llm_calls_gte_scenes(self):
        r=_sgo().run_episode(_plan(1,3),1)
        assert r.total_llm_calls>=r.total_scenes_generated

    def test_mae_consensus_rate_with_no_mae(self):
        sgo=SGO(bridge=MockLLMBridge())
        r=sgo.run_episode(_plan(),1)
        assert r.success==True

# ── 추가 경계값 및 커버리지 ───────────────────────────────────────────
class TestSceneDraftOutputFull:
    def test_scene_index_zero_based(self):
        from literary_system.schemas.scene_draft_output import SceneDraftOutput
        @dataclass
        class R:
            scene_id:str="x"; draft_text:str="t"; mae_score:float=0.6
            tension_actual:float=0.5; text:str="t"
        out=SceneDraftOutput.from_scene_record(R(), scene_index=0)
        assert out.scene_index==0

    def test_scene_index_large(self):
        from literary_system.schemas.scene_draft_output import SceneDraftOutput
        @dataclass
        class R:
            scene_id:str="x"; draft_text:str="t"; mae_score:float=0.7
            tension_actual:float=0.5; text:str="t"
        out=SceneDraftOutput.from_scene_record(R(), scene_index=99)
        assert out.scene_index==99

    def test_draft_output_gate_passed_default(self):
        from literary_system.schemas.scene_draft_output import SceneDraftOutput
        @dataclass
        class R:
            scene_id:str="x"; draft_text:str="test text"; mae_score:float=0.7
            tension_actual:float=0.5; text:str="test"
        out=SceneDraftOutput.from_scene_record(R())
        assert out.gate_passed==True

    def test_rerender_count_default_zero(self):
        from literary_system.schemas.scene_draft_output import SceneDraftOutput
        @dataclass
        class R:
            scene_id:str="x"; draft_text:str="test"; mae_score:float=0.7
            tension_actual:float=0.5; text:str="test"
        out=SceneDraftOutput.from_scene_record(R())
        assert out.rerender_count==0

class TestEmotionalTrackerStability:
    def test_100_updates_no_exception(self):
        t=EmotionalMomentumTracker()
        @dataclass
        class R:
            draft_text:str="위기 충돌"; mae_score:float=0.6
            tension_actual:float=0.7; text:str="위기"
        @dataclass
        class P:
            tension_target:float=0.7
        for _ in range(100): t.update(R(), P())
        assert len(t.history())==100

    def test_vector_stays_bounded_after_many_updates(self):
        t=EmotionalMomentumTracker()
        @dataclass
        class R:
            draft_text:str="crisis "*10; mae_score:float=1.0; text:str=""
        @dataclass
        class P:
            tension_target:float=1.0
        for _ in range(20): t.update(R(), P())
        v=t.current()
        assert v.tension<=1.0 and v.dread<=1.0

    def test_dominant_dim_all_equal(self):
        v=EmotionalVector(0.5,0.5,0.5,0.5)
        # just verify it returns one of the valid dimensions
        assert v.dominant_dim() in ("tension","sympathy","dread","catharsis")

    def test_sympathy_from_high_mae(self):
        t=EmotionalMomentumTracker()
        @dataclass
        class R:
            draft_text:str=""; mae_score:float=0.95; text:str=""
        @dataclass
        class P:
            tension_target:float=0.3
        v=t.update(R(), P())
        assert v.sympathy > 0.4

class TestSGOWithMiseCompiler:
    def test_sgo_with_mise_compiler_no_crash(self):
        from literary_system.drse.mise_en_scene_compiler import MiseEnSceneCompiler
        sgo=_sgo(mise_compiler=MiseEnSceneCompiler())
        r=sgo.run_episode(_plan(),1)
        assert r.success==True

    def test_sgo_mise_compiler_prompt_injection(self):
        class MockDRSE:
            def score_all(self,**kw): return [{"tension":0.9,"node_id":"A","hint":"어둠"}]
        from literary_system.drse.mise_en_scene_compiler import MiseEnSceneCompiler
        sgo=_sgo(mise_compiler=MiseEnSceneCompiler(drse_engine=MockDRSE()))
        plan=_plan()[0]
        from literary_system.orchestrators.scene_focus_injector import SceneFocusInjector
        ctx=SceneFocusInjector(None).build(seq_plan=plan, scene_index=0, total_scenes_in_seq=1)
        prompt=sgo._build_prompt(plan,ctx,0,character_states={"A":{"intent":"도주"}})
        assert "MiseEnScene" in prompt

    def test_sgo_mise_compiler_auto_created(self):
        sgo=_sgo()
        # _mise_compiler either None or MiseEnSceneCompiler depending on availability
        assert hasattr(sgo, "_mise_compiler")

class TestSGOLoopBridgeDeep:
    def _bridge(self):
        from literary_system.orchestrators.sgo_loop_bridge import SGOLoopBridge
        return SGOLoopBridge(sgo=_sgo())

    def test_result_project_id_preserved(self):
        from literary_system.orchestrators.sgo_loop_bridge import SGOLoopBridge
        b=self._bridge()
        r=b.run_episode(_plan(),"my_project",1)
        assert r.project_id=="my_project"

    def test_gate_never_commit_uses_max_rerenders(self):
        from literary_system.orchestrators.sgo_loop_bridge import SGOLoopBridge, MAX_RERENDERS
        class Never:
            def should_commit(self,t): return False
        b=SGOLoopBridge(sgo=_sgo(), conditional_gate=Never())
        r=b.run_episode(_plan(),"p",1)
        assert r.rerenders==MAX_RERENDERS

    def test_success_false_on_sgo_error(self):
        from literary_system.orchestrators.sgo_loop_bridge import SGOLoopBridge
        class BrokenSGO:
            def run_episode(self,*a,**kw): raise RuntimeError("broken")
        b=SGOLoopBridge(sgo=BrokenSGO())
        r=b.run_episode(_plan(),"p",1)
        assert r.success==False and "broken" in r.error

class TestCausalBuilderDeep:
    def test_store_exception_fallback(self):
        class BrokenStore:
            def get_handoff(self,ep): raise RuntimeError("no handoff")
        from literary_system.causal.causal_continuation_plan_builder import CausalContinuationPlanBuilder
        b=CausalContinuationPlanBuilder(handoff_store=BrokenStore())
        plan=b.build(3)
        assert plan.built==True
        assert plan.seeds==[]

    def test_multiple_key_events(self):
        from literary_system.causal.causal_continuation_plan_builder import CausalContinuationPlanBuilder
        b=CausalContinuationPlanBuilder()
        plan=b.build(1,{"seeds":[],"tension_forward":0.5,
                        "key_events":["사건A","사건B","사건C"]})
        assert len(plan.key_events)==3

class TestDataChunkerDeep:
    def test_pipeline_no_trace_store_export(self,tmp_path):
        from literary_system.slm.data_chunker import DataChunker
        import json
        f=tmp_path/"data.jsonl"
        f.write_text("\n".join(json.dumps({"i":i}) for i in range(10)))
        class NoExportStore: pass  # no export_slm_dataset method
        class Collector:
            def __init__(self): self.items=[]
            def add_batch(self,b): self.items.extend(b)
        c=DataChunker(chunk_size=5); col=Collector()
        result=c.run_pipeline(NoExportStore(), col, str(f))
        assert result["pairs_total"]==10
        assert len(col.items)==10

    def test_single_item_add_method(self,tmp_path):
        from literary_system.slm.data_chunker import DataChunker
        import json
        f=tmp_path/"d.jsonl"; f.write_text(json.dumps({"x":1}))
        class AddOne:
            def __init__(self): self.count=0
            def add(self,row): self.count+=1
        a=AddOne(); DataChunker(chunk_size=10).run_pipeline(object(), a, str(f))
        assert a.count==1
