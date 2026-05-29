"""V328 Task17: EmotionalMomentumTracker + SceneDraftOutput 테스트."""
import sys; sys.path.insert(0,"/tmp/literary_os_v328")
import pytest
from dataclasses import dataclass
from literary_system.emotion.emotional_momentum_tracker import EmotionalVector, EmotionalMomentumTracker
from literary_system.schemas.scene_draft_output import SceneDraftOutput, SceneQuality, _quality_from_score

@dataclass
class FakeSeqPlan:
    tension_target:float=0.7; seq_index:int=0; goal:str="충돌"; seq_id:str="s0"
    episode_no:int=1; scene_count:int=2; act_index:int=1; pct_start:float=0.0; pct_end:float=0.5

@dataclass
class FakeRecord:
    scene_id:str="s001"; draft_text:str="위기가 발생했다. 긴장이 고조된다."; mae_score:float=0.72
    tension_actual:float=0.7; seq_id:str="s0"; scene_index:int=0; text:str="위기가 발생했다."
    consensus:bool=True; retries:int=0; llm_calls:int=1; focus_ctx:dict=None
    def __post_init__(self):
        if self.focus_ctx is None: self.focus_ctx={}

# ── EmotionalVector ──────────────────────────────────────────────────
class TestEmotionalVector:
    def test_clamp(self): v=EmotionalVector(2.0,-0.5,0.3,1.5); assert all(0<=getattr(v,a)<=1 for a in ("tension","sympathy","dread","catharsis"))
    def test_dominant(self): assert EmotionalVector(0.9,0.3,0.2,0.1).dominant_dim()=="tension"
    def test_magnitude_positive(self): assert EmotionalVector(0.5,0.5,0.5,0.5).magnitude()>0
    def test_repr(self): assert "EmotionalVector" in repr(EmotionalVector())
    def test_defaults(self): v=EmotionalVector(); assert v.tension==0.5 and v.dread==0.3

# ── EmotionalMomentumTracker ─────────────────────────────────────────
class TestEmotionalMomentumTracker:
    def test_init_default(self): assert isinstance(EmotionalMomentumTracker().current(), EmotionalVector)
    def test_init_custom(self):
        t=EmotionalMomentumTracker(EmotionalVector(tension=0.9,sympathy=0.1,dread=0.8,catharsis=0.0))
        assert t.current().tension==pytest.approx(0.9)
    def test_update_returns_vector(self): assert isinstance(EmotionalMomentumTracker().update(FakeRecord(),FakeSeqPlan()),EmotionalVector)
    def test_update_changes_state(self):
        t=EmotionalMomentumTracker(); before=t.current().tension
        t.update(FakeRecord(draft_text="crisis conflict tension danger explode "*5,mae_score=0.9),FakeSeqPlan(tension_target=0.95))
        assert t.current().tension != before
    def test_history_grows(self):
        t=EmotionalMomentumTracker()
        for i in range(5): t.update(FakeRecord(scene_id=f"s{i}"),FakeSeqPlan())
        assert len(t.history())==5
    def test_history_immutable(self):
        t=EmotionalMomentumTracker(); t.update(FakeRecord(),FakeSeqPlan())
        h=t.history(); h.append(None); assert len(t.history())==1
    def test_reset(self): t=EmotionalMomentumTracker(); t.update(FakeRecord(),FakeSeqPlan()); t.reset(); assert len(t.history())==0
    def test_prompt_hint_format(self):
        h=EmotionalMomentumTracker().to_prompt_hint(); assert "EmotionalMomentum" in h and "dominant=" in h
    def test_ema_decay(self):
        t=EmotionalMomentumTracker(); t.update(FakeRecord(draft_text="",mae_score=0.5),FakeSeqPlan(tension_target=1.0))
        assert 0.5<=t.current().tension<=1.0
    def test_no_seq_plan(self): assert isinstance(EmotionalMomentumTracker().update(FakeRecord(),None),EmotionalVector)
    def test_tension_keyword_signal(self):
        t=EmotionalMomentumTracker()
        v=t.update(FakeRecord(draft_text="crisis conflict tension danger explode "*5),FakeSeqPlan(tension_target=0.9))
        assert v.tension>0.5
    def test_catharsis_keywords(self):
        t=EmotionalMomentumTracker()
        v=t.update(FakeRecord(draft_text="해방 해결 승리 안도 relief resolved victory "*5,mae_score=0.95),FakeSeqPlan(tension_target=0.1))
        assert v.catharsis>0

# ── SceneQuality ─────────────────────────────────────────────────────
class TestSceneQuality:
    def test_excellent(self): assert _quality_from_score(0.90)==SceneQuality.EXCELLENT
    def test_good(self): assert _quality_from_score(0.75)==SceneQuality.GOOD
    def test_acceptable(self): assert _quality_from_score(0.60)==SceneQuality.ACCEPTABLE
    def test_poor(self): assert _quality_from_score(0.40)==SceneQuality.POOR
    def test_boundary_excellent(self): assert _quality_from_score(0.85)==SceneQuality.EXCELLENT
    def test_boundary_good(self): assert _quality_from_score(0.70)==SceneQuality.GOOD

# ── SceneDraftOutput ─────────────────────────────────────────────────
class TestSceneDraftOutput:
    def test_basic(self):
        out=SceneDraftOutput.from_scene_record(FakeRecord(),episode_no=1,seq_index=0,scene_index=0)
        assert out.scene_id=="s001" and abs(out.mae_score-0.72)<0.01
    def test_word_count(self):
        out=SceneDraftOutput.from_scene_record(FakeRecord(draft_text="one two three four five"))
        assert out.word_count==5
    def test_quality_auto(self):
        out=SceneDraftOutput.from_scene_record(FakeRecord(mae_score=0.88))
        q=out.quality.value if hasattr(out.quality,"value") else out.quality
        assert q=="excellent"
    def test_to_dict(self):
        d=SceneDraftOutput.from_scene_record(FakeRecord()).to_dict()
        assert "scene_id" in d and "mae_score" in d
    def test_with_ev(self):
        ev=EmotionalVector(tension=0.8,sympathy=0.4,dread=0.6,catharsis=0.1)
        out=SceneDraftOutput.from_scene_record(FakeRecord(),emotional_vector=ev)
        assert out.emotional_vector is not None
        assert abs(out.emotional_vector.tension-0.8)<0.01
    def test_episode_no(self): assert SceneDraftOutput.from_scene_record(FakeRecord(),episode_no=5).episode_no==5
    def test_seq_index(self): assert SceneDraftOutput.from_scene_record(FakeRecord(),seq_index=3).seq_index==3
    def test_no_ev(self): assert SceneDraftOutput.from_scene_record(FakeRecord(),emotional_vector=None).emotional_vector is None
    def test_tension_actual(self): assert abs(SceneDraftOutput.from_scene_record(FakeRecord(tension_actual=0.88)).tension_actual-0.88)<0.01

# ── SGO Integration ──────────────────────────────────────────────────
class TestSGOEmotionIntegration:
    def _make_sgo(self, tracker=None):
        from literary_system.orchestrators.scene_generation_orchestrator import SceneGenerationOrchestrator as SGO
        from literary_system.llm_bridge.mock_llm_bridge import MockLLMBridge
        from literary_system.evaluation.mae_orchestrator import MAEOrchestrator
        from literary_system.validation.coefficient_mapper import CoefficientMapper
        from literary_system.validation.learned_coefficient_store import LearnedCoefficientStore
        return SGO(bridge=MockLLMBridge(), mae_orchestrator=MAEOrchestrator(),
                   coeff_mapper=CoefficientMapper(), coeff_store=LearnedCoefficientStore(),
                   emotion_tracker=tracker)

    def test_accepts_tracker_param(self):
        t=EmotionalMomentumTracker(); sgo=self._make_sgo(tracker=t)
        assert sgo._emotion_tracker is t

    def test_auto_creates_tracker(self):
        sgo=self._make_sgo(); assert sgo._emotion_tracker is not None

    def test_tracker_updated_after_run(self):
        from literary_system.orchestrators.sequence_planner import SequencePlan, SequenceType
        t=EmotionalMomentumTracker(); sgo=self._make_sgo(tracker=t)
        plans=[SequencePlan(seq_id="s1",episode_no=1,seq_index=0,goal="테스트",tension_target=0.7,
                            scene_count=2,act_index=1,pct_start=0.0,pct_end=0.5,seq_type=SequenceType.PLOT_ADVANCE)]
        sgo.run_episode(plans, episode_no=1)
        assert len(t.history())==2

    def test_build_prompt_includes_emotion_hint(self):
        from literary_system.orchestrators.sequence_planner import SequencePlan, SequenceType
        from literary_system.orchestrators.scene_focus_injector import SceneFocusInjector
        t=EmotionalMomentumTracker(); sgo=self._make_sgo(tracker=t)
        plan=SequencePlan(seq_id="s1",episode_no=1,seq_index=0,goal="테스트",tension_target=0.7,
                          scene_count=1,act_index=1,pct_start=0.0,pct_end=1.0,seq_type=SequenceType.PLOT_ADVANCE)
        ctx=SceneFocusInjector(rag_bridge=None).build(
            seq_plan=plan, scene_index=0, total_scenes_in_seq=1)
        prompt=sgo._build_prompt(plan,ctx,attempt=0)
        assert "EmotionalMomentum" in prompt
