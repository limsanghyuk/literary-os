"""V646 SP-C.2 — DirectorAgent + ensemble facade 테스트 (ADR-106).

TC-01~TC-20: DirectorAgent SceneBlueprint 5요소 검증
TC-21~TC-30: ensemble facade legacy 양립 확인
"""
from __future__ import annotations

import pytest
from literary_system.agents.director_agent import DirectorAgent, SceneBlueprint
from literary_system.ensemble import (
    DirectorAgent as EnsembleDirectorAgent,
    SceneBlueprint as EnsembleBlueprint,
    EnsembleGate,
    NarrativeFitnessArbiter,
)


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def director():
    return DirectorAgent(scene_id_prefix="test")


@pytest.fixture
def sample_blueprint(director):
    return director.generate_blueprint(
        manuscript_context="주인공이 상대역과 카페에서 재회한다. 서로 어색한 침묵.",
        episode_num=1,
        scene_num=3,
        tone="melancholy",
        characters=["주인공(이수현)", "상대역(김민준)"],
    )


# ─── TC-01~TC-10: SceneBlueprint 기본 ────────────────────────────────────────

class TestSceneBlueprint:
    def test_tc01_dataclass_fields(self, sample_blueprint):
        bp = sample_blueprint
        assert isinstance(bp.scene_id, str)
        assert isinstance(bp.objective, str)
        assert isinstance(bp.setting, str)
        assert isinstance(bp.characters, list)
        assert isinstance(bp.tone, str)
        assert isinstance(bp.constraints, dict)

    def test_tc02_scene_id_format(self, sample_blueprint):
        assert sample_blueprint.scene_id == "test_ep01_sc03"

    def test_tc03_characters_passed(self, sample_blueprint):
        assert "주인공(이수현)" in sample_blueprint.characters
        assert "김민준" in sample_blueprint.characters[1]

    def test_tc04_tone_set(self, sample_blueprint):
        assert sample_blueprint.tone == "melancholy"

    def test_tc05_objective_nonempty(self, sample_blueprint):
        assert len(sample_blueprint.objective) > 5

    def test_tc06_setting_nonempty(self, sample_blueprint):
        assert len(sample_blueprint.setting) > 5

    def test_tc07_editor_cannot_reject(self, sample_blueprint):
        """C-M-09: Editor 거부 권한 없음."""
        assert sample_blueprint.constraints.get("editor_can_reject") is False

    def test_tc08_to_dict_roundtrip(self, sample_blueprint):
        d = sample_blueprint.to_dict()
        bp2 = SceneBlueprint.from_dict(d)
        assert bp2.scene_id == sample_blueprint.scene_id
        assert bp2.tone == sample_blueprint.tone

    def test_tc09_default_characters(self, director):
        bp = director.generate_blueprint(episode_num=2, scene_num=1)
        assert len(bp.characters) == 2  # 기본값

    def test_tc10_extra_constraints_merged(self, director):
        bp = director.generate_blueprint(
            extra_constraints={"max_words": 500},
        )
        assert bp.constraints.get("max_words") == 500
        assert bp.constraints.get("editor_can_reject") is False


# ─── TC-11~TC-20: DirectorAgent 규칙 ─────────────────────────────────────────

class TestDirectorAgent:
    def test_tc11_call_count_increments(self, director):
        assert director.call_count == 0
        director.generate_blueprint()
        director.generate_blueprint()
        assert director.call_count == 2

    def test_tc12_role_constant(self):
        assert DirectorAgent.ROLE == "director"

    def test_tc13_no_context_blueprint(self, director):
        bp = director.generate_blueprint()
        assert bp.scene_id.startswith("test_")
        assert "씬" in bp.objective

    def test_tc14_context_influences_objective(self, director):
        ctx = "거대한 폭풍이 밀려오는 바닷가에서 두 사람이 마주친다."
        bp = director.generate_blueprint(manuscript_context=ctx, scene_num=5)
        assert "거대한 폭풍" in bp.objective or "씬 5" in bp.objective

    def test_tc15_episode_in_setting(self, director):
        bp = director.generate_blueprint(episode_num=7, scene_num=1)
        assert "7" in bp.setting

    def test_tc16_different_scenes_different_ids(self, director):
        bp1 = director.generate_blueprint(episode_num=1, scene_num=1)
        bp2 = director.generate_blueprint(episode_num=1, scene_num=2)
        assert bp1.scene_id != bp2.scene_id

    def test_tc17_different_episodes_different_ids(self, director):
        bp1 = director.generate_blueprint(episode_num=1, scene_num=1)
        bp2 = director.generate_blueprint(episode_num=2, scene_num=1)
        assert bp1.scene_id != bp2.scene_id

    def test_tc18_tone_neutral_default(self, director):
        bp = director.generate_blueprint()
        assert bp.tone == "neutral"

    def test_tc19_tone_custom(self, director):
        bp = director.generate_blueprint(tone="romantic")
        assert bp.tone == "romantic"

    def test_tc20_prefix_in_scene_id(self):
        d = DirectorAgent(scene_id_prefix="drama_ep1")
        bp = d.generate_blueprint(episode_num=1, scene_num=1)
        assert bp.scene_id.startswith("drama_ep1_")


# ─── TC-21~TC-30: ensemble facade 양립 ───────────────────────────────────────

class TestEnsembleFacade:
    def test_tc21_director_importable_from_ensemble(self):
        """Step 2: ensemble/__init__.py에서 DirectorAgent 노출."""
        assert EnsembleDirectorAgent is DirectorAgent

    def test_tc22_blueprint_importable_from_ensemble(self):
        assert EnsembleBlueprint is SceneBlueprint

    def test_tc23_legacy_ensemble_gate_still_importable(self):
        assert EnsembleGate is not None

    def test_tc24_legacy_fitness_arbiter_still_importable(self):
        assert NarrativeFitnessArbiter is not None

    def test_tc25_ensemble_gate_instantiable(self):
        gate = EnsembleGate()
        assert gate is not None

    def test_tc26_fitness_arbiter_instantiable(self):
        arb = NarrativeFitnessArbiter()
        assert arb is not None

    def test_tc27_director_via_ensemble_works(self):
        d = EnsembleDirectorAgent()
        bp = d.generate_blueprint()
        assert isinstance(bp, EnsembleBlueprint)

    def test_tc28_from_dict_via_ensemble(self):
        d = {"scene_id": "x", "objective": "o", "setting": "s"}
        bp = EnsembleBlueprint.from_dict(d)
        assert bp.scene_id == "x"

    def test_tc29_blueprint_editor_cannot_reject_via_ensemble(self):
        d = EnsembleDirectorAgent()
        bp = d.generate_blueprint()
        assert bp.constraints.get("editor_can_reject") is False

    def test_tc30_legacy_candidate_score_importable(self):
        from literary_system.ensemble import CandidateScore
        assert CandidateScore is not None
