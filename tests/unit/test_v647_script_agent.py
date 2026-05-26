"""V647 SP-C.2 — ScriptAgent 테스트 (ADR-107).
TC-01~TC-30: ScriptDraft 생성·속성·경계 조건 검증
"""
from __future__ import annotations
import pytest
from literary_system.agents.script_agent import ScriptAgent, ScriptDraft
from literary_system.agents.director_agent import DirectorAgent


@pytest.fixture
def director():
    return DirectorAgent()

@pytest.fixture
def script():
    return ScriptAgent()

@pytest.fixture
def bp(director):
    return director.generate_blueprint(
        manuscript_context="두 인물이 처음으로 솔직하게 마음을 터놓는 장면",
        episode_num=2, scene_num=4, tone="sincere",
        characters=["이수현", "김민준"],
    ).to_dict()


class TestScriptDraft:
    def test_tc01_fields(self, script, bp):
        draft = script.generate(bp)
        assert isinstance(draft.scene_id, str)
        assert isinstance(draft.draft_text, str)
        assert isinstance(draft.attempt_num, int)
        assert isinstance(draft.safety_passed, bool)
        assert isinstance(draft.lora_artifact_id, str)
        assert isinstance(draft.word_count, int)

    def test_tc02_scene_id_matches_blueprint(self, script, bp):
        draft = script.generate(bp)
        assert draft.scene_id == bp["scene_id"]

    def test_tc03_draft_text_nonempty(self, script, bp):
        draft = script.generate(bp)
        assert len(draft.draft_text) > 10

    def test_tc04_word_count_positive(self, script, bp):
        draft = script.generate(bp)
        assert draft.word_count > 0

    def test_tc05_word_count_matches_text(self, script, bp):
        draft = script.generate(bp)
        assert draft.word_count == len(draft.draft_text.split())

    def test_tc06_attempt_num_default_1(self, script, bp):
        draft = script.generate(bp)
        assert draft.attempt_num == 1

    def test_tc07_attempt_num_passed(self, script, bp):
        draft = script.generate(bp, attempt_num=2)
        assert draft.attempt_num == 2

    def test_tc08_attempt_num_3_allowed(self, script, bp):
        draft = script.generate(bp, attempt_num=3)
        assert draft.attempt_num == 3

    def test_tc09_attempt_num_4_raises(self, script, bp):
        with pytest.raises(ValueError, match="MAX_ATTEMPTS"):
            script.generate(bp, attempt_num=4)

    def test_tc10_safety_passed_no_guard(self, script, bp):
        """Guard 없으면 사전 검사 통과."""
        draft = script.generate(bp)
        assert draft.safety_passed is True


class TestScriptAgentStub:
    def test_tc11_stub_artifact_id(self, script, bp):
        draft = script.generate(bp)
        assert draft.lora_artifact_id == "stub"

    def test_tc12_stub_text_contains_scene_id_info(self, script, bp):
        draft = script.generate(bp)
        assert "씬 초안" in draft.draft_text or "배경" in draft.draft_text

    def test_tc13_stub_attempt_in_text(self, script, bp):
        draft = script.generate(bp, attempt_num=2)
        assert "2" in draft.draft_text

    def test_tc14_tone_in_stub_text(self, script, bp):
        draft = script.generate(bp)
        assert "sincere" in draft.draft_text

    def test_tc15_character_in_stub_text(self, script, bp):
        draft = script.generate(bp)
        assert "이수현" in draft.draft_text or "김민준" in draft.draft_text

    def test_tc16_attempt_count_tracks(self, script, bp):
        assert script.attempt_count == 0
        script.generate(bp)
        script.generate(bp, attempt_num=2)
        assert script.attempt_count == 2

    def test_tc17_role_constant(self):
        assert ScriptAgent.ROLE == "script"

    def test_tc18_max_attempts_constant(self):
        assert ScriptAgent.MAX_ATTEMPTS == 3

    def test_tc19_to_dict_roundtrip(self, script, bp):
        draft = script.generate(bp)
        d = draft.to_dict()
        assert d["scene_id"] == draft.scene_id
        assert d["attempt_num"] == draft.attempt_num
        assert d["safety_passed"] == draft.safety_passed

    def test_tc20_max_words_param_accepted(self, script, bp):
        draft = script.generate(bp, max_words=200)
        assert draft is not None


class TestScriptAgentSafetyGuard:
    class PassGuard:
        def pre_check(self, _): return True

    class FailGuard:
        def pre_check(self, _): return False

    class ErrorGuard:
        def pre_check(self, _): raise RuntimeError("guard error")

    def test_tc21_pass_guard_safety_true(self, bp):
        agent = ScriptAgent(safety_guard=self.PassGuard())
        draft = agent.generate(bp)
        assert draft.safety_passed is True

    def test_tc22_fail_guard_safety_false(self, bp):
        agent = ScriptAgent(safety_guard=self.FailGuard())
        draft = agent.generate(bp)
        assert draft.safety_passed is False

    def test_tc23_error_guard_defaults_to_true(self, bp):
        """Guard 예외 → 안전하게 True 반환."""
        agent = ScriptAgent(safety_guard=self.ErrorGuard())
        draft = agent.generate(bp)
        assert draft.safety_passed is True

    def test_tc24_no_guard_safety_true(self, bp):
        agent = ScriptAgent(safety_guard=None)
        draft = agent.generate(bp)
        assert draft.safety_passed is True


class TestScriptAgentGateway:
    class StubGateway:
        active_artifact_id = "lora_test_001"
        def generate(self, prompt, max_new_tokens=100):
            return {"text": f"씬 초안 텍스트 — LoRA gateway 생성 ({max_new_tokens}토큰 제한)"}

    class ErrorGateway:
        active_artifact_id = "lora_err"
        def generate(self, **kwargs): raise RuntimeError("gateway error")

    def test_tc25_gateway_text_used(self, bp):
        agent = ScriptAgent(inference_gateway=self.StubGateway())
        draft = agent.generate(bp)
        assert "LoRA gateway" in draft.draft_text

    def test_tc26_gateway_artifact_id(self, bp):
        agent = ScriptAgent(inference_gateway=self.StubGateway())
        draft = agent.generate(bp)
        assert draft.lora_artifact_id == "lora_test_001"

    def test_tc27_gateway_error_fallback_to_stub(self, bp):
        """Gateway 예외 → stub 로 fallback."""
        agent = ScriptAgent(inference_gateway=self.ErrorGateway())
        draft = agent.generate(bp)
        assert len(draft.draft_text) > 0  # stub 텍스트

    def test_tc28_word_count_from_gateway(self, bp):
        agent = ScriptAgent(inference_gateway=self.StubGateway())
        draft = agent.generate(bp)
        assert draft.word_count == len(draft.draft_text.split())

    def test_tc29_lora0_principle_no_external_api(self):
        """ScriptAgent 코드에 외부 API URL 없음 확인 (LLM-0)."""
        import inspect
        import literary_system.agents.script_agent as m
        src = inspect.getsource(m)
        for forbidden in ["openai.com", "anthropic.com", "api.openai", "api.anthropic"]:
            assert forbidden not in src, f"LLM-0 위반: {forbidden}"

    def test_tc30_multiple_attempts_independent(self, bp):
        agent = ScriptAgent()
        d1 = agent.generate(bp, attempt_num=1)
        d2 = agent.generate(bp, attempt_num=2)
        d3 = agent.generate(bp, attempt_num=3)
        assert d1.attempt_num == 1
        assert d2.attempt_num == 2
        assert d3.attempt_num == 3
