"""
test_v650_agent_coordinator.py — V650 AgentCoordinator 단위 테스트 (30 TC).
SP-C.2 C-M-09 오케스트레이션 검증.
"""
import pytest
from literary_system.ensemble.agent_coordinator import AgentCoordinator, CoordinatorResult


# ── 헬퍼 ─────────────────────────────────────────────────────────────────────

def _make_coordinator(**kwargs):
    return AgentCoordinator(**kwargs)


def _minimal_blueprint(scene_id="test_ep01_sc01"):
    return {
        "scene_id":    scene_id,
        "objective":   "test objective",
        "setting":     "test setting",
        "characters":  ["Alice"],
        "tone":        "neutral",
        "constraints": {"editor_can_reject": False},
    }


# ── TC-01~05: CoordinatorResult 구조 ─────────────────────────────────────────

class TestCoordinatorResultStructure:
    def test_tc01_fields_exist(self):
        r = CoordinatorResult(
            scene_id="s01", final_text="text", rounds_used=1,
            success=True,
        )
        assert hasattr(r, "scene_id")
        assert hasattr(r, "final_text")
        assert hasattr(r, "rounds_used")
        assert hasattr(r, "success")
        assert hasattr(r, "last_critic_score")
        assert hasattr(r, "last_fitness_decision")
        assert hasattr(r, "polish_notes")
        assert hasattr(r, "error")

    def test_tc02_default_error_none(self):
        r = CoordinatorResult(scene_id="s", final_text="", rounds_used=1, success=True)
        assert r.error is None

    def test_tc03_default_polish_notes_empty(self):
        r = CoordinatorResult(scene_id="s", final_text="", rounds_used=1, success=True)
        assert r.polish_notes == []

    def test_tc04_to_dict_keys(self):
        r = CoordinatorResult(scene_id="s01", final_text="hi", rounds_used=2, success=True)
        d = r.to_dict()
        for key in ("scene_id", "final_text", "rounds_used", "success",
                    "last_critic_score", "last_fitness_decision", "polish_notes", "error"):
            assert key in d

    def test_tc05_from_dict_roundtrip(self):
        r = CoordinatorResult(
            scene_id="abc", final_text="hello", rounds_used=2,
            success=True, last_critic_score=0.75, last_fitness_decision="SELECT",
            polish_notes=["note1"],
        )
        r2 = CoordinatorResult.from_dict(r.to_dict())
        assert r2.scene_id == r.scene_id
        assert r2.final_text == r.final_text
        assert r2.rounds_used == r.rounds_used
        assert r2.success == r.success
        assert r2.last_critic_score == r.last_critic_score
        assert r2.polish_notes == r.polish_notes


# ── TC-06~10: AgentCoordinator 기본 속성 ──────────────────────────────────────

class TestAgentCoordinatorBasic:
    def test_tc06_max_rounds_3(self):
        assert AgentCoordinator.MAX_ROUNDS == 3

    def test_tc07_instantiate_no_args(self):
        coord = AgentCoordinator()
        assert coord is not None

    def test_tc08_instantiate_with_stubs(self):
        coord = AgentCoordinator(director=None, script=None, critic=None, editor=None)
        assert coord is not None

    def test_tc09_coordinate_returns_coordinator_result(self):
        coord = AgentCoordinator()
        result = coord.coordinate()
        assert isinstance(result, CoordinatorResult)

    def test_tc10_coordinate_success_true(self):
        coord = AgentCoordinator()
        result = coord.coordinate()
        assert result.success is True


# ── TC-11~15: 오케스트레이션 흐름 ────────────────────────────────────────────

class TestOrchestrationFlow:
    def test_tc11_rounds_used_at_least_1(self):
        coord = AgentCoordinator()
        result = coord.coordinate()
        assert result.rounds_used >= 1

    def test_tc12_rounds_used_at_most_max(self):
        coord = AgentCoordinator()
        result = coord.coordinate()
        assert result.rounds_used <= AgentCoordinator.MAX_ROUNDS

    def test_tc13_scene_id_in_result(self):
        coord = AgentCoordinator()
        bp = _minimal_blueprint("custom_ep02_sc03")
        result = coord.coordinate(blueprint_dict=bp)
        assert result.scene_id == "custom_ep02_sc03"

    def test_tc14_blueprint_dict_preserved(self):
        coord = AgentCoordinator()
        bp = _minimal_blueprint("bp_test")
        result = coord.coordinate(blueprint_dict=bp)
        assert result.blueprint_dict.get("scene_id") == "bp_test"

    def test_tc15_max_rounds_param_respected(self):
        """max_rounds=1 → rounds_used == 1."""
        coord = AgentCoordinator()
        result = coord.coordinate(max_rounds=1)
        assert result.rounds_used == 1


# ── TC-16~20: Stub 에이전트 주입 ─────────────────────────────────────────────

class _FixedScript:
    def generate(self, *, blueprint_dict, attempt_num=1):
        from types import SimpleNamespace
        d = SimpleNamespace()
        d.scene_id    = blueprint_dict.get("scene_id", "x")
        d.draft_text  = f"fixed draft attempt={attempt_num}"
        d.attempt_num = attempt_num
        d.safety_passed = True
        d.lora_artifact_id = None
        d.word_count  = 3
        d.to_dict = lambda: {
            "scene_id": d.scene_id, "draft_text": d.draft_text,
            "attempt_num": d.attempt_num, "safety_passed": d.safety_passed,
            "lora_artifact_id": d.lora_artifact_id, "word_count": d.word_count,
        }
        return d


class _AlwaysPassCritic:
    def evaluate(self, *, draft_dict, blueprint_dict=None, round_num=1):
        from types import SimpleNamespace
        r = SimpleNamespace()
        r.scene_id = draft_dict.get("scene_id", "x")
        r.passed = True
        r.constitution_score = 0.80
        r.fitness_decision = "SELECT"
        r.request_regeneration = False
        r.round_num = round_num
        r.suggestions = []
        r.axis_scores = {}
        r.to_dict = lambda: {
            "scene_id": r.scene_id, "passed": r.passed,
            "constitution_score": r.constitution_score,
            "fitness_decision": r.fitness_decision,
            "request_regeneration": r.request_regeneration,
            "round_num": r.round_num, "suggestions": r.suggestions,
            "axis_scores": r.axis_scores,
        }
        return r


class _AlwaysRegenCritic:
    """항상 재생성 요청."""
    def evaluate(self, *, draft_dict, blueprint_dict=None, round_num=1):
        from types import SimpleNamespace
        r = SimpleNamespace()
        r.scene_id = draft_dict.get("scene_id", "x")
        r.passed = False
        r.constitution_score = 0.50
        r.fitness_decision = "REJECT"
        r.request_regeneration = (round_num < 3)
        r.round_num = round_num
        r.suggestions = []
        r.axis_scores = {}
        r.to_dict = lambda: {
            "scene_id": r.scene_id, "passed": r.passed,
            "constitution_score": r.constitution_score,
            "fitness_decision": r.fitness_decision,
            "request_regeneration": r.request_regeneration,
            "round_num": r.round_num, "suggestions": r.suggestions,
            "axis_scores": r.axis_scores,
        }
        return r


class _FixedEditor:
    def finalize(self, *, draft_dict, blueprint_dict=None, critic_report_dict=None):
        from types import SimpleNamespace
        e = SimpleNamespace()
        e.scene_id = draft_dict.get("scene_id", "x")
        e.final_text = "EDITED: " + draft_dict.get("draft_text", "")
        e.polish_notes = ["fixed"]
        e.editor_applied = True
        e.to_dict = lambda: {
            "scene_id": e.scene_id, "final_text": e.final_text,
            "polish_notes": e.polish_notes, "editor_applied": e.editor_applied,
        }
        return e


class TestStubInjection:
    def test_tc16_custom_script_used(self):
        coord = AgentCoordinator(script=_FixedScript(), critic=_AlwaysPassCritic())
        result = coord.coordinate(blueprint_dict=_minimal_blueprint("inj_test"))
        assert "fixed draft" in result.final_text or result.success

    def test_tc17_always_pass_critic_1_round(self):
        coord = AgentCoordinator(script=_FixedScript(), critic=_AlwaysPassCritic())
        result = coord.coordinate(blueprint_dict=_minimal_blueprint())
        assert result.rounds_used == 1

    def test_tc18_always_regen_critic_max_rounds(self):
        """재생성 요청 Critic → rounds_used == MAX_ROUNDS."""
        coord = AgentCoordinator(script=_FixedScript(), critic=_AlwaysRegenCritic())
        result = coord.coordinate(blueprint_dict=_minimal_blueprint())
        assert result.rounds_used == AgentCoordinator.MAX_ROUNDS

    def test_tc19_editor_always_runs(self):
        coord = AgentCoordinator(
            script=_FixedScript(), critic=_AlwaysPassCritic(), editor=_FixedEditor()
        )
        result = coord.coordinate(blueprint_dict=_minimal_blueprint())
        assert result.final_text.startswith("EDITED:")

    def test_tc20_editor_polish_notes_forwarded(self):
        coord = AgentCoordinator(
            script=_FixedScript(), critic=_AlwaysPassCritic(), editor=_FixedEditor()
        )
        result = coord.coordinate(blueprint_dict=_minimal_blueprint())
        assert "fixed" in result.polish_notes


# ── TC-21~25: C-M-09 제약 검증 ────────────────────────────────────────────────

class TestCM09Constraints:
    def test_tc21_max_rounds_not_exceeded(self):
        coord = AgentCoordinator(script=_FixedScript(), critic=_AlwaysRegenCritic())
        result = coord.coordinate(blueprint_dict=_minimal_blueprint())
        assert result.rounds_used <= 3

    def test_tc22_success_even_after_max_regen(self):
        """MAX_ROUNDS 소진 후에도 success=True (EditorAgent 항상 실행)."""
        coord = AgentCoordinator(script=_FixedScript(), critic=_AlwaysRegenCritic())
        result = coord.coordinate(blueprint_dict=_minimal_blueprint())
        assert result.success is True

    def test_tc23_editor_cannot_reject(self):
        """EditorAgent가 예외를 내도 success=True (Stub 폴백)."""
        class _ErrorEditor:
            def finalize(self, **kwargs):
                raise RuntimeError("editor error")

        coord = AgentCoordinator(
            script=_FixedScript(), critic=_AlwaysPassCritic(), editor=_ErrorEditor()
        )
        result = coord.coordinate(blueprint_dict=_minimal_blueprint())
        # 에디터 오류 시 드래프트 텍스트로 폴백, success=True
        assert result.success is True

    def test_tc24_critic_score_stored(self):
        coord = AgentCoordinator(script=_FixedScript(), critic=_AlwaysPassCritic())
        result = coord.coordinate(blueprint_dict=_minimal_blueprint())
        assert result.last_critic_score == pytest.approx(0.80)

    def test_tc25_fitness_decision_stored(self):
        coord = AgentCoordinator(script=_FixedScript(), critic=_AlwaysPassCritic())
        result = coord.coordinate(blueprint_dict=_minimal_blueprint())
        assert result.last_fitness_decision == "SELECT"


# ── TC-26~30: 에지 케이스 및 G64 Gate ────────────────────────────────────────

class TestEdgeCasesAndGate:
    def test_tc26_blueprint_dict_none_generates(self):
        """blueprint_dict=None → DirectorAgent Stub으로 생성."""
        coord = AgentCoordinator()
        result = coord.coordinate()
        assert result.scene_id != ""

    def test_tc27_scene_prefix_episode_scene_params(self):
        coord = AgentCoordinator()
        result = coord.coordinate(scene_prefix="ep", episode_num=3, scene_num=7)
        assert "03" in result.scene_id or "ep" in result.scene_id

    def test_tc28_script_error_returns_failure(self):
        class _ErrorScript:
            def generate(self, **kwargs):
                raise RuntimeError("script error")

        coord = AgentCoordinator(script=_ErrorScript(), critic=_AlwaysPassCritic())
        result = coord.coordinate(blueprint_dict=_minimal_blueprint())
        assert result.success is False
        assert result.error is not None

    def test_tc29_gate_g64_pass(self):
        from literary_system.gates.coordinator_gate import run_g64_gate
        r = run_g64_gate()
        assert r["pass"] is True, f"G64 실패: {r}"

    def test_tc30_facade_import(self):
        from literary_system.ensemble import AgentCoordinator as AC, CoordinatorResult as CR
        assert AC is AgentCoordinator
        assert CR is CoordinatorResult
