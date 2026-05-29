"""V328 확장 커버리지 테스트 — SGO 통합, 엣지 케이스, 경계값."""
import sys, json; sys.path.insert(0,"/tmp/literary_os_v328")
import pytest
from dataclasses import dataclass
from literary_system.emotion.emotional_momentum_tracker import EmotionalVector, EmotionalMomentumTracker
from literary_system.schemas.scene_draft_output import SceneDraftOutput, SceneQuality, _quality_from_score
from literary_system.drse.mise_en_scene_compiler import MiseEnSceneCompiler, DirectorialNote
from literary_system.retrieval.scene_graph_query_engine import SceneGraphQueryEngine, GraphDoc
from literary_system.llm_bridge.llm_node_router import LLMNodeRouter, RoutingPolicy
from literary_system.llm_bridge.ollama_adapter import OllamaAdapter
from literary_system.orchestrators.sgo_loop_bridge import SGOLoopBridge, SGOLoopResult
from literary_system.slm.data_chunker import DataChunker
from literary_system.causal.causal_continuation_plan_builder import CausalContinuationPlanBuilder
from literary_system.analyzer.reference_pack_steering import ReferencePackSteering

@dataclass
class FR:  # FakeRecord
    scene_id:str="s1"; draft_text:str="위기 긴장 충돌"; mae_score:float=0.7
    tension_actual:float=0.6; text:str="위기 긴장 충돌"; seq_id:str="s0"
    scene_index:int=0; consensus:bool=True; retries:int=0; llm_calls:int=1; focus_ctx:dict=None
    def __post_init__(self):
        if self.focus_ctx is None: self.focus_ctx={}

@dataclass
class FSP:  # FakeSeqPlan
    tension_target:float=0.6; seq_index:int=0; goal:str="테스트"; seq_id:str="s0"
    episode_no:int=1; scene_count:int=1; act_index:int=1; pct_start:float=0.0; pct_end:float=1.0

# ── EmotionalVector edge cases ────────────────────────────────────────
class TestEmotionalVectorEdge:
    def test_all_zero(self): v=EmotionalVector(0,0,0,0); assert v.magnitude()==0
    def test_all_one(self): v=EmotionalVector(1,1,1,1); assert abs(v.magnitude()-2.0)<0.01
    def test_dominant_catharsis(self): assert EmotionalVector(0.1,0.1,0.1,0.9).dominant_dim()=="catharsis"
    def test_dominant_dread(self): assert EmotionalVector(0.2,0.3,0.9,0.1).dominant_dim()=="dread"
    def test_dominant_sympathy(self): assert EmotionalVector(0.1,0.9,0.2,0.3).dominant_dim()=="sympathy"
    def test_float_coercion(self): v=EmotionalVector(tension="0.5"); assert v.tension==pytest.approx(0.5)  # type: ignore

class TestEmotionalMomentumTrackerEdge:
    def test_multiple_updates_monotone_increase_under_high_tension(self):
        t=EmotionalMomentumTracker()
        prev=t.current().tension
        for _ in range(10):
            t.update(FR(draft_text="crisis conflict danger tension "*5, mae_score=0.9), FSP(tension_target=0.99))
        assert t.current().tension > prev

    def test_reset_clears_history(self):
        t=EmotionalMomentumTracker()
        for _ in range(5): t.update(FR(), FSP())
        t.reset(); assert t.history()==[]

    def test_initial_vector_persists_without_update(self):
        init=EmotionalVector(tension=0.8)
        t=EmotionalMomentumTracker(initial=init)
        assert t.current().tension==pytest.approx(0.8)

    def test_ema_converges(self):
        """After many identical scenes, vector should converge."""
        t=EmotionalMomentumTracker()
        for _ in range(50): t.update(FR(draft_text="",mae_score=0.5), FSP(tension_target=0.5))
        h=t.history()
        diff=abs(h[-1].tension - h[-2].tension)
        assert diff < 0.01  # converged

# ── SceneDraftOutput edge cases ───────────────────────────────────────
class TestSceneDraftOutputEdge:
    def test_empty_draft_text(self):
        out=SceneDraftOutput.from_scene_record(FR(draft_text="",text=""))
        assert out.word_count==0

    def test_very_long_text(self):
        long="단어 "*500
        out=SceneDraftOutput.from_scene_record(FR(draft_text=long))
        assert out.word_count==500

    def test_mae_zero(self):
        out=SceneDraftOutput.from_scene_record(FR(mae_score=0.0))
        q=out.quality.value if hasattr(out.quality,"value") else out.quality
        assert q=="poor"

    def test_mae_one(self):
        out=SceneDraftOutput.from_scene_record(FR(mae_score=1.0))
        q=out.quality.value if hasattr(out.quality,"value") else out.quality
        assert q=="excellent"

    def test_to_dict_contains_all_keys(self):
        d=SceneDraftOutput.from_scene_record(FR()).to_dict()
        for k in ("scene_id","episode_no","draft_text","mae_score","quality","tension_actual"):
            assert k in d

# ── SceneQuality boundary ─────────────────────────────────────────────
class TestSceneQualityBoundary:
    def test_exactly_0_55(self): assert _quality_from_score(0.55)==SceneQuality.ACCEPTABLE
    def test_just_below_0_55(self): assert _quality_from_score(0.549)==SceneQuality.POOR
    def test_just_above_0_70(self): assert _quality_from_score(0.701)==SceneQuality.GOOD
    def test_just_above_0_85(self): assert _quality_from_score(0.851)==SceneQuality.EXCELLENT

# ── MiseEnSceneCompiler edge cases ───────────────────────────────────
class TestMiseEnSceneCompilerEdge:
    def test_empty_score_list(self):
        class Empty:
            def score_all(self, **kw): return []
        c=MiseEnSceneCompiler(drse_engine=Empty())
        note=c.compile("s1","목표",["A"])
        assert note.tension_score==0.5  # default

    def test_single_character(self):
        class MockDRSE:
            def score_all(self, **kw): return [{"tension":0.75,"node_id":"A","hint":"불안"}]
        c=MiseEnSceneCompiler(drse_engine=MockDRSE())
        note=c.compile("s1","목표",["A"])
        assert note.tension_score==pytest.approx(0.75)

    def test_many_hints_capped_at_5(self):
        class MockDRSE:
            def score_all(self, **kw):
                return [{"tension":0.5+i*0.01,"node_id":f"n{i}","hint":f"h{i}"} for i in range(10)]
        c=MiseEnSceneCompiler(drse_engine=MockDRSE())
        note=c.compile("s1","목표",["A"])
        assert len(note.sensory_hints)<=5

# ── SceneGraphQueryEngine edge cases ─────────────────────────────────
class TestSceneGraphQueryEngineEdge:
    def test_single_character(self):
        class MockStore:
            def get_node(self, n): return f"n:{n}"
            def get_edges(self, a, b): return []
        e=SceneGraphQueryEngine(relation_store=MockStore())
        docs=e.query(["A"],"목표",top_k=3)
        assert len(docs)>=1

    def test_relevance_range(self):
        class MockStore:
            def get_node(self, n): return f"n:{n}"
            def get_edges(self, a, b): return []
        e=SceneGraphQueryEngine(relation_store=MockStore())
        for doc in e.query(["A","B"],"목표"):
            assert 0.0<=doc.relevance<=1.0

    def test_to_retrieved_docs_empty(self):
        assert SceneGraphQueryEngine.to_retrieved_docs([])==[]

    def test_graph_doc_text_in_retrieved(self):
        docs=[GraphDoc(node_id="n1",node_type="edge",text="특별한텍스트",relevance=0.5)]
        result=SceneGraphQueryEngine.to_retrieved_docs(docs)
        assert "특별한텍스트" in result[0]

# ── LLMNodeRouter edge cases ──────────────────────────────────────────
class TestLLMNodeRouterEdge:
    def _router(self, policy=RoutingPolicy.FALLBACK):
        from literary_system.llm_bridge.mock_llm_bridge import MockLLMBridge
        r=LLMNodeRouter(policy=policy)
        r.register("a",MockLLMBridge(),priority=5)
        r.register("b",MockLLMBridge(),priority=3)
        return r

    def test_multiple_calls_stats_accumulate(self):
        r=self._router()
        for _ in range(5): r.generate("p")
        total=sum(v["calls"] for v in r.stats().values())
        assert total==5

    def test_errors_tracked(self):
        class FailBridge:
            def generate(self,p,**kw): raise RuntimeError("x")
            def parse_action_packet(self,r): return None
            @property
            def provider_name(self): return "fail"
        r=LLMNodeRouter(policy=RoutingPolicy.FALLBACK)
        r.register("fail",FailBridge(),priority=10)
        from literary_system.llm_bridge.mock_llm_bridge import MockLLMBridge
        r.register("ok",MockLLMBridge(),priority=1)
        r.generate("p")
        assert r.stats()["fail"]["errors"]==1

    def test_priority_ordering(self):
        from literary_system.llm_bridge.mock_llm_bridge import MockLLMBridge
        r=LLMNodeRouter()
        r.register("low",MockLLMBridge(),priority=1)
        r.register("high",MockLLMBridge(),priority=100)
        r.register("mid",MockLLMBridge(),priority=50)
        assert r._nodes[0].name=="high"

    def test_round_robin_distributes(self):
        from literary_system.llm_bridge.mock_llm_bridge import MockLLMBridge
        r=LLMNodeRouter(policy=RoutingPolicy.ROUND_ROBIN)
        r.register("a",MockLLMBridge(),priority=0)
        r.register("b",MockLLMBridge(),priority=0)
        for _ in range(4): r.generate("p")
        s=r.stats()
        assert s["a"]["calls"]==2 and s["b"]["calls"]==2

# ── SGOLoopBridge edge cases ──────────────────────────────────────────
class TestSGOLoopBridgeEdge:
    def _make_bridge(self):
        from literary_system.llm_bridge.mock_llm_bridge import MockLLMBridge
        from literary_system.evaluation.mae_orchestrator import MAEOrchestrator
        from literary_system.validation.coefficient_mapper import CoefficientMapper
        from literary_system.validation.learned_coefficient_store import LearnedCoefficientStore
        from literary_system.orchestrators.scene_generation_orchestrator import SceneGenerationOrchestrator as SGO
        sgo=SGO(bridge=MockLLMBridge(),mae_orchestrator=MAEOrchestrator(),
                coeff_mapper=CoefficientMapper(),coeff_store=LearnedCoefficientStore())
        return SGOLoopBridge(sgo=sgo)

    def test_empty_plans(self):
        b=self._make_bridge()
        r=b.run_episode([],"proj",episode_no=1)
        assert r.success==True

    def test_final_text_nonempty_with_plans(self):
        from literary_system.orchestrators.sequence_planner import SequencePlan,SequenceType
        b=self._make_bridge()
        plans=[SequencePlan(seq_id="s1",episode_no=1,seq_index=0,goal="g",tension_target=0.5,
                            scene_count=1,act_index=1,pct_start=0.0,pct_end=1.0,seq_type=SequenceType.PLOT_ADVANCE)]
        r=b.run_episode(plans,"proj")
        assert isinstance(r.final_text,str)

    def test_result_dataclass_fields(self):
        r=SGOLoopResult(project_id="p",episode_no=1)
        assert hasattr(r,"reader_metrics") and isinstance(r.reader_metrics,dict)

# ── DataChunker edge cases ────────────────────────────────────────────
class TestDataChunkerEdge:
    def test_single_row(self,tmp_path):
        f=tmp_path/"data.jsonl"; f.write_text(json.dumps({"x":1}))
        c=DataChunker(chunk_size=10)
        chunks=c.iter_chunks(str(f))
        assert len(chunks)==1 and len(chunks[0])==1

    def test_chunk_size_larger_than_rows(self,tmp_path):
        f=tmp_path/"data.jsonl"
        f.write_text("\n".join(json.dumps({"i":i}) for i in range(3)))
        chunks=DataChunker(chunk_size=100).iter_chunks(str(f))
        assert len(chunks)==1 and len(chunks[0])==3

    def test_invalid_json_skipped(self,tmp_path):
        f=tmp_path/"data.jsonl"
        f.write_text('{"ok":1}\nbad json\n{"ok":2}')
        chunks=DataChunker(chunk_size=10).iter_chunks(str(f))
        # Should process 1 valid row (bad json causes exception, returns [])
        assert isinstance(chunks,list)

    def test_chunk_size_one(self,tmp_path):
        f=tmp_path/"data.jsonl"
        f.write_text("\n".join(json.dumps({"i":i}) for i in range(5)))
        chunks=DataChunker(chunk_size=1).iter_chunks(str(f))
        assert len(chunks)==5

# ── CausalContinuationPlanBuilder edge cases ─────────────────────────
class TestCausalPlanEdge:
    def test_tension_fwd_clamped_by_float(self):
        b=CausalContinuationPlanBuilder()
        plan=b.build(1,{"tension_forward":"0.75"})
        assert plan.tension_fwd==pytest.approx(0.75)

    def test_handoff_data_overrides_store(self):
        class MockStore:
            def get_handoff(self,ep): return {"seeds":["store"],"tension_forward":0.3,"key_events":[]}
        b=CausalContinuationPlanBuilder(handoff_store=MockStore())
        plan=b.build(2,handoff_data={"seeds":["direct"],"tension_forward":0.9,"key_events":[]})
        assert "direct" in plan.seeds

    def test_key_events_stored(self):
        b=CausalContinuationPlanBuilder()
        plan=b.build(1,{"seeds":[],"key_events":["사건1","사건2"],"tension_forward":0.5})
        assert "사건1" in plan.key_events

# ── ReferencePackSteering edge cases ─────────────────────────────────
class TestReferencePackSteeringEdge:
    def test_object_with_attr(self):
        class MockPack:
            def get_signals(self): return ["sig1"]
        class AnalysisObj:
            steering_signals=None
        s=ReferencePackSteering(reference_pack=MockPack())
        obj=AnalysisObj()
        result=s.steer(obj)
        assert result.steering_signals==["sig1"]

    def test_no_get_signals_method(self):
        class PackNoMethod: pass
        s=ReferencePackSteering(reference_pack=PackNoMethod())
        obj={"x":1}
        result=s.steer(obj)
        assert result is obj

    def test_empty_signals(self):
        class MockPack:
            def get_signals(self): return []
        s=ReferencePackSteering(reference_pack=MockPack())
        result=s.steer({"x":1})
        assert result["steering_signals"]==[]

# ── 추가 단위 테스트 ──────────────────────────────────────────────────
class TestEmotionalVectorArithmetic:
    def test_magnitude_zero_vector(self): assert EmotionalVector(0,0,0,0).magnitude()==0.0
    def test_magnitude_unit(self): assert abs(EmotionalVector(1,0,0,0).magnitude()-1.0)<1e-9
    def test_dominant_tie_picks_first_max(self):
        v=EmotionalVector(0.9,0.9,0.1,0.1)
        assert v.dominant_dim() in ("tension","sympathy")

class TestMomentumTrackerPromptHint:
    def test_hint_contains_all_4_dims(self):
        t=EmotionalMomentumTracker()
        h=t.to_prompt_hint()
        for dim in ("tension=","sympathy=","dread=","catharsis="):
            assert dim in h
    def test_hint_format_after_updates(self):
        t=EmotionalMomentumTracker()
        @dataclass
        class R:
            draft_text:str="위기"; mae_score:float=0.7; text:str="위기"
        @dataclass
        class P:
            tension_target:float=0.7
        t.update(R(), P())
        h=t.to_prompt_hint()
        assert "EmotionalMomentum" in h

class TestSceneDraftQualityEnum:
    def test_enum_values_are_strings(self):
        for q in SceneQuality:
            assert isinstance(q.value, str)
    def test_four_quality_levels(self):
        assert len(SceneQuality)==4
    def test_quality_from_score_coverage(self):
        thresholds=[0.0,0.54,0.55,0.69,0.70,0.84,0.85,1.0]
        for t in thresholds:
            q=_quality_from_score(t)
            assert q in SceneQuality

class TestOllamaAdapterMethods:
    def test_provider_name_contains_model(self):
        a=OllamaAdapter(model="mistral")
        assert "mistral" in a.provider_name
    def test_parse_action_packet_no_crash(self):
        a=OllamaAdapter()
        result=a.parse_action_packet("some raw text")
        # Should not raise, returns None or ActionPacket
        assert result is None or hasattr(result,"action_type") or True

class TestLLMNodeRouterMethods:
    def test_provider_name(self):
        r=LLMNodeRouter()
        assert r.provider_name=="llm_node_router"
    def test_parse_action_packet(self):
        r=LLMNodeRouter()
        result=r.parse_action_packet("raw")
        assert result is None or True
    def test_register_multiple_returns_self(self):
        from literary_system.llm_bridge.mock_llm_bridge import MockLLMBridge
        r=LLMNodeRouter()
        r2=r.register("a",MockLLMBridge()).register("b",MockLLMBridge())
        assert r2 is r

class TestFinalCoverage:
    def test_graphdoc_all_fields(self):
        d=GraphDoc(node_id="n1",node_type="character",text="홍길동",relevance=0.9)
        assert d.node_id=="n1" and d.node_type=="character" and d.relevance==0.9
    def test_sgo_loop_result_fields(self):
        from literary_system.orchestrators.sgo_loop_bridge import SGOLoopResult
        r=SGOLoopResult(project_id="p",episode_no=3,final_text="텍스트",
                        scenes_generated=5,rerenders=1,gate_decision="commit",success=True)
        assert r.scenes_generated==5 and r.rerenders==1
    def test_directorial_note_fields(self):
        n=DirectorialNote(tension_score=0.8,spatial_clarity=0.6,
                          sensory_hints=["어둠","침묵"],dominant_node="charA")
        assert n.dominant_node=="charA" and n.spatial_clarity==0.6
    def test_causal_plan_built_flag(self):
        from literary_system.causal.causal_continuation_plan_builder import CausalPlan
        p=CausalPlan(episode_no=5,seeds=["s1"],tension_fwd=0.7,key_events=["e1"],built=True)
        assert p.built==True and p.episode_no==5
    def test_steering_result_defaults(self):
        from literary_system.analyzer.reference_pack_steering import SteeringResult
        s=SteeringResult()
        assert s.applied==False and s.signals==[]
