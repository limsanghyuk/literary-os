"""
V327 Phase 3 통합 테스트
P3-A: BOOToSGOAdapter — bundle → character_states / knowledge_tracker 변환
P3-B: SGO knowledge_tracker 배선 — scene_pressure_from_knowledge() 호출 및 주입
"""
from __future__ import annotations
import pytest
from unittest.mock import MagicMock, patch


# ──────────────────────────────────────────────────────────────
# 공통 픽스처
# ──────────────────────────────────────────────────────────────

def _make_boo_bundle(include_episodes=False, include_residues=True):
    """BOOToSGOAdapter 테스트용 최소 BOO bundle."""
    seed = {
        "project_id": "test_project",
        "genre": "사극",
        "tone_keywords": ["비극", "긴장"],
        "format_type": "miniseries",
        "required_objects": ["편지", "독약"] if include_residues else [],
        "pdi_baseline": {},
    }
    bundle = {
        "project_id": "test_project",
        "mode": "quick",
        "seed_contract": seed,
        "style_dna": {"profile_name": "dark_sageuk"},
        "memory_summary": {
            "episodes_completed": 3,
            "residue_phases": {"편지": "active", "독약": "latent"},
            "state_at_ep3": {
                "lead": {"intent": "진실 규명", "location": "서재", "emotion": "결의"},
                "foil": {"intent": "은폐", "location": "별채", "emotion": "두려움"},
            },
        },
        "episodes": [],
    }
    return bundle

def _make_seq_plan():
    from literary_system.orchestrators.sequence_planner import SequencePlan, SequenceType
    return SequencePlan(
        seq_id="seq_p3", episode_no=1, seq_index=0,
        goal="지식 비대칭 씬", tension_target=0.8,
        scene_count=1, act_index=1,
        pct_start=0.0, pct_end=1.0,
        seq_type=SequenceType.CONFLICT_PEAK.value,
    )

def _make_mock_bridge(text="씬 텍스트"):
    b = MagicMock(); b.generate.return_value = text; return b

def _make_mae(consensus=True):
    mae = MagicMock()
    vote = MagicMock(); vote.score = 0.8
    result = MagicMock()
    result.consensus = consensus; result.votes = [vote, vote, vote]
    mae.evaluate.return_value = result
    return mae

def _make_sgo(**kwargs):
    from literary_system.orchestrators.scene_generation_orchestrator import (
        SceneGenerationOrchestrator,
    )
    defaults = dict(bridge=_make_mock_bridge(), mae_orchestrator=_make_mae())
    defaults.update(kwargs)
    return SceneGenerationOrchestrator(**defaults)


# ──────────────────────────────────────────────────────────────
# P3-A: BOOToSGOAdapter 테스트
# ──────────────────────────────────────────────────────────────

class TestBOOToSGOAdapter:
    """BOOToSGOAdapter — bundle 변환 정확성 검증."""

    def test_adapter_instantiates(self):
        """어댑터 생성 가능."""
        from literary_system.adapters.boo_to_sgo_adapter import BOOToSGOAdapter
        adapter = BOOToSGOAdapter(_make_boo_bundle())
        assert adapter is not None

    def test_project_id_extracted(self):
        """project_id 올바르게 추출."""
        from literary_system.adapters.boo_to_sgo_adapter import BOOToSGOAdapter
        adapter = BOOToSGOAdapter(_make_boo_bundle())
        assert adapter.project_id == "test_project"

    def test_character_states_has_lead_and_foil(self):
        """character_states에 lead, foil 포함."""
        from literary_system.adapters.boo_to_sgo_adapter import BOOToSGOAdapter
        adapter = BOOToSGOAdapter(_make_boo_bundle())
        states = adapter.character_states
        assert "lead" in states
        assert "foil" in states

    def test_character_state_has_required_keys(self):
        """각 인물 상태에 intent, location, emotion, role 키 포함."""
        from literary_system.adapters.boo_to_sgo_adapter import BOOToSGOAdapter
        adapter = BOOToSGOAdapter(_make_boo_bundle())
        for char_id, state in adapter.character_states.items():
            assert "intent"   in state, f"{char_id}: intent 없음"
            assert "location" in state, f"{char_id}: location 없음"
            assert "emotion"  in state, f"{char_id}: emotion 없음"
            assert "role"     in state, f"{char_id}: role 없음"

    def test_literary_state_applied_to_character_states(self):
        """memory_summary의 state_at_ep3가 character_states에 반영됨."""
        from literary_system.adapters.boo_to_sgo_adapter import BOOToSGOAdapter
        adapter = BOOToSGOAdapter(_make_boo_bundle())
        assert adapter.character_states["lead"]["intent"]   == "진실 규명"
        assert adapter.character_states["lead"]["location"] == "서재"
        assert adapter.character_states["foil"]["emotion"]  == "두려움"

    def test_knowledge_tracker_returns_instance_or_none(self):
        """knowledge_tracker가 KnowledgeStateTracker 인스턴스 또는 None."""
        from literary_system.adapters.boo_to_sgo_adapter import BOOToSGOAdapter
        adapter = BOOToSGOAdapter(_make_boo_bundle())
        tracker = adapter.knowledge_tracker
        # 환경에 따라 None 또는 KnowledgeStateTracker 인스턴스
        if tracker is not None:
            from literary_system.world.knowledge_state_tracker import KnowledgeStateTracker
            assert isinstance(tracker, KnowledgeStateTracker)

    def test_knowledge_tracker_facts_registered(self):
        """required_objects가 KnowledgeStateTracker facts로 등록됨."""
        from literary_system.adapters.boo_to_sgo_adapter import BOOToSGOAdapter
        adapter = BOOToSGOAdapter(_make_boo_bundle(include_residues=True))
        tracker = adapter.knowledge_tracker
        if tracker is None:
            pytest.skip("KnowledgeStateTracker 미설치")
        assert "object_편지" in tracker.facts
        assert "object_독약" in tracker.facts

    def test_empty_bundle_handled_gracefully(self):
        """빈 bundle 입력 시 크래시 없음."""
        from literary_system.adapters.boo_to_sgo_adapter import BOOToSGOAdapter
        adapter = BOOToSGOAdapter({})
        assert adapter.project_id == "unknown_project"
        assert isinstance(adapter.character_states, dict)


# ──────────────────────────────────────────────────────────────
# P3-B: SGO knowledge_tracker 배선 테스트
# ──────────────────────────────────────────────────────────────

class TestV327P3KnowledgeTrackerWiring:
    """SGO knowledge_tracker 파라미터 수용 및 호출 검증."""

    def test_knowledge_tracker_param_accepted(self):
        """SGO __init__이 knowledge_tracker 파라미터를 받아들임."""
        tracker = MagicMock()
        sgo = _make_sgo(knowledge_tracker=tracker)
        assert sgo._knowledge_tracker is tracker

    def test_knowledge_tracker_none_by_default(self):
        """기본값 None — 기존 파이프라인 영향 없음."""
        sgo = _make_sgo()
        assert sgo._knowledge_tracker is None

    def test_pipeline_works_without_knowledge_tracker(self):
        """knowledge_tracker 없이 정상 동작."""
        sgo = _make_sgo()
        result = sgo.run_episode([_make_seq_plan()])
        assert result.success
        assert result.total_scenes_generated == 1

    def test_scene_pressure_called_per_scene(self):
        """씬마다 tracker.scene_pressure_from_knowledge() 호출됨."""
        tracker = MagicMock()
        tracker.scene_pressure_from_knowledge.return_value = {
            "total_pressure": 0.0, "asymmetries": [], "dominant_tension": None
        }
        char_states = {"lead": {"intent": "목표", "location": "서재", "emotion": "결의"}}
        sgo = _make_sgo(knowledge_tracker=tracker)
        sgo.run_episode([_make_seq_plan()], character_states=char_states)
        tracker.scene_pressure_from_knowledge.assert_called_once()

    def test_scene_pressure_receives_character_ids(self):
        """scene_pressure_from_knowledge에 character_states 키 목록이 전달됨."""
        tracker = MagicMock()
        tracker.scene_pressure_from_knowledge.return_value = {
            "total_pressure": 0.0, "asymmetries": [], "dominant_tension": None
        }
        char_states = {
            "lead": {"intent": "목표", "location": "서재", "emotion": "결의"},
            "foil": {"intent": "은폐", "location": "별채", "emotion": "공포"},
        }
        sgo = _make_sgo(knowledge_tracker=tracker)
        sgo.run_episode([_make_seq_plan()], character_states=char_states)
        call_args = tracker.scene_pressure_from_knowledge.call_args
        chars_passed = (
            call_args.kwargs.get("characters_in_scene") or
            (call_args.args[0] if call_args.args else [])
        )
        # _로 시작하는 메타키 제외한 실제 캐릭터 ID만 전달
        assert set(chars_passed) == {"lead", "foil"}

    def test_knowledge_pressure_high_injected_to_prompt(self):
        """지식 압력 > 0.3 시 프롬프트에 힌트 포함."""
        tracker = MagicMock()
        tracker.scene_pressure_from_knowledge.return_value = {
            "total_pressure": 0.75,
            "dominant_tension": {
                "chars": "lead↔foil", "fact": "object_편지", "pressure": 0.75,
                "dramatic": "정보 격차"
            },
            "asymmetries": [],
        }
        sgo = _make_sgo(knowledge_tracker=tracker)
        prompts_captured = []
        original_generate = sgo.bridge.generate
        def capture_generate(prompt, *a, **kw):
            prompts_captured.append(prompt)
            return "씬 텍스트"
        sgo.bridge.generate = capture_generate

        char_states = {"lead": {"intent": "규명", "location": "서재", "emotion": "결의"}}
        sgo.run_episode([_make_seq_plan()], character_states=char_states)

        assert prompts_captured, "generate 미호출"
        prompt = prompts_captured[0]
        assert "지식 비대칭 압력" in prompt or "핵심 긴장축" in prompt

    def test_knowledge_tracker_error_doesnt_break_pipeline(self):
        """tracker 오류가 씬 생성을 중단시키지 않음."""
        tracker = MagicMock()
        tracker.scene_pressure_from_knowledge.side_effect = RuntimeError("추적기 오류")
        sgo = _make_sgo(knowledge_tracker=tracker)
        result = sgo.run_episode([_make_seq_plan()])
        assert result.success

    def test_real_knowledge_tracker_integration(self):
        """실제 KnowledgeStateTracker 인스턴스로 end-to-end 동작."""
        try:
            from literary_system.world.knowledge_state_tracker import (
                KnowledgeStateTracker, InformationType
            )
        except ImportError:
            pytest.skip("KnowledgeStateTracker 미설치")

        tracker = KnowledgeStateTracker("integration_test")
        tracker.register_fact(
            fact_id="secret_letter",
            fact_type=InformationType.OBJECT,
            description="비밀 편지의 존재",
            true_value="고씨 가문의 음모 증거",
            reader_knows=True,
        )
        tracker.set_knowledge("lead", "secret_letter", "suspects", episode_no=1)
        tracker.set_knowledge("foil", "secret_letter", "unaware", episode_no=1)

        char_states = {
            "lead": {"intent": "편지 찾기", "location": "서재", "emotion": "초조"},
            "foil": {"intent": "감시", "location": "복도", "emotion": "경계"},
        }
        sgo = _make_sgo(knowledge_tracker=tracker)
        result = sgo.run_episode([_make_seq_plan()], character_states=char_states)
        assert result.success
        assert result.total_scenes_generated == 1
