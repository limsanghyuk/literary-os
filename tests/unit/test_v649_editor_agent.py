"""V649 — EditorAgent 단위 테스트 (30 TC)."""
import pytest
from literary_system.agents.editor_agent import EditorAgent, EditedScene


@pytest.fixture
def agent():
    return EditorAgent()


@pytest.fixture
def draft_dict():
    return {
        "scene_id": "ep_ep01_sc01",
        "draft_text": "오늘은  서울이다.\n\n\n\n비가  내린다.",
        "attempt_num": 1,
    }


@pytest.fixture
def blueprint_dict():
    return {
        "scene_id": "ep_ep01_sc01",
        "constraints": {"editor_can_reject": False},
    }


@pytest.fixture
def critic_report_dict():
    return {
        "scene_id": "ep_ep01_sc01",
        "passed": False,
        "suggestions": ["narrative_coherence 개선 필요 (현재=0.50)"],
    }


# ── EditedScene 구조 ──────────────────────────────────────────────────
class TestEditedSceneStructure:
    def test_tc01_has_scene_id(self, agent, draft_dict):
        es = agent.finalize(draft_dict)
        assert es.scene_id == "ep_ep01_sc01"

    def test_tc02_has_final_text(self, agent, draft_dict):
        es = agent.finalize(draft_dict)
        assert isinstance(es.final_text, str)
        assert len(es.final_text) > 0

    def test_tc03_has_cadence_applied(self, agent, draft_dict):
        es = agent.finalize(draft_dict)
        assert isinstance(es.cadence_applied, bool)

    def test_tc04_has_polish_notes(self, agent, draft_dict):
        es = agent.finalize(draft_dict)
        assert isinstance(es.polish_notes, list)

    def test_tc05_source_draft_attempt(self, agent, draft_dict):
        es = agent.finalize(draft_dict)
        assert es.source_draft_attempt == 1

    def test_tc06_source_draft_attempt_3(self, agent):
        d = {"scene_id": "x", "draft_text": "text", "attempt_num": 3}
        es = agent.finalize(d)
        assert es.source_draft_attempt == 3


# ── C-M-09: 거부권 없음 ───────────────────────────────────────────────
class TestNoRejectRight:
    def test_tc07_always_returns_edited_scene(self, agent, draft_dict):
        """editor_can_reject=False: 반드시 EditedScene 반환."""
        es = agent.finalize(draft_dict)
        assert isinstance(es, EditedScene)

    def test_tc08_blueprint_reject_constraint_ignored(self, agent, draft_dict, blueprint_dict):
        blueprint_dict["constraints"]["editor_can_reject"] = True
        es = agent.finalize(draft_dict, blueprint_dict=blueprint_dict)
        # 여전히 편집본 반환 (거부 없음)
        assert isinstance(es, EditedScene)

    def test_tc09_empty_draft_still_finalized(self, agent):
        es = agent.finalize({"scene_id": "x", "draft_text": ""})
        assert isinstance(es, EditedScene)

    def test_tc10_role_constant(self):
        assert EditorAgent.ROLE == "editor"


# ── 기본 공백 교정 ────────────────────────────────────────────────────
class TestBasicPolish:
    def test_tc11_trailing_whitespace_removed(self, agent):
        d = {"scene_id": "x", "draft_text": "hello   \n world   "}
        es = agent.finalize(d)
        for line in es.final_text.split("\n"):
            assert line == line.rstrip()

    def test_tc12_consecutive_blank_lines_condensed(self, agent):
        d = {"scene_id": "x", "draft_text": "A\n\n\n\nB"}
        es = agent.finalize(d)
        assert "\n\n\n" not in es.final_text

    def test_tc13_cadence_applied_false_no_planner(self, agent, draft_dict):
        es = agent.finalize(draft_dict)
        assert es.cadence_applied is False

    def test_tc14_polish_note_added(self, agent, draft_dict):
        es = agent.finalize(draft_dict)
        assert any("교정" in n for n in es.polish_notes)


# ── KoreanCadencePlanner 통합 ─────────────────────────────────────────
class TestCadencePlanner:
    def test_tc15_planner_applied(self, draft_dict):
        class MockPlanner:
            def apply(self, text, bp): return "[cadence]" + text
        agent = EditorAgent(cadence_planner=MockPlanner())
        es = agent.finalize(draft_dict)
        assert es.cadence_applied is True
        assert es.final_text.startswith("[cadence]")

    def test_tc16_planner_note_added(self, draft_dict):
        class MockPlanner:
            def apply(self, text, bp): return text
        agent = EditorAgent(cadence_planner=MockPlanner())
        es = agent.finalize(draft_dict)
        assert any("KoreanCadencePlanner" in n for n in es.polish_notes)

    def test_tc17_planner_exception_fallback(self, draft_dict):
        class BadPlanner:
            def apply(self, text, bp): raise RuntimeError("planner error")
        agent = EditorAgent(cadence_planner=BadPlanner())
        es = agent.finalize(draft_dict)
        assert es.cadence_applied is False  # fallback
        assert any("예외" in n or "교정" in n for n in es.polish_notes)

    def test_tc18_no_planner_cadence_false(self, agent, draft_dict):
        es = agent.finalize(draft_dict)
        assert es.cadence_applied is False


# ── Critic 제안 반영 ──────────────────────────────────────────────────
class TestCriticIntegration:
    def test_tc19_critic_suggestions_in_polish_notes(self, agent, draft_dict, critic_report_dict):
        es = agent.finalize(draft_dict, critic_report_dict=critic_report_dict)
        combined = " ".join(es.polish_notes)
        assert "narrative_coherence" in combined

    def test_tc20_no_critic_no_suggestion_notes(self, agent, draft_dict):
        es = agent.finalize(draft_dict)
        assert not any("[편집 반영]" in n for n in es.polish_notes)

    def test_tc21_empty_critic_suggestions(self, agent, draft_dict):
        cr = {"scene_id": "x", "passed": True, "suggestions": []}
        es = agent.finalize(draft_dict, critic_report_dict=cr)
        assert isinstance(es, EditedScene)

    def test_tc22_multiple_suggestions_all_reflected(self, agent, draft_dict):
        cr = {"suggestions": ["A 개선", "B 개선", "C 개선"]}
        es = agent.finalize(draft_dict, critic_report_dict=cr)
        combined = " ".join(es.polish_notes)
        assert "A 개선" in combined
        assert "B 개선" in combined
        assert "C 개선" in combined


# ── 엣지 케이스 ──────────────────────────────────────────────────────
class TestEdgeCases:
    def test_tc23_missing_scene_id_in_draft(self, agent):
        es = agent.finalize({"draft_text": "hello"})
        assert es.scene_id == "unknown"

    def test_tc24_missing_attempt_num_defaults_to_1(self, agent):
        es = agent.finalize({"scene_id": "x", "draft_text": "text"})
        assert es.source_draft_attempt == 1

    def test_tc25_final_text_not_none(self, agent, draft_dict):
        es = agent.finalize(draft_dict)
        assert es.final_text is not None

    def test_tc26_none_blueprint_dict_ok(self, agent, draft_dict):
        es = agent.finalize(draft_dict, blueprint_dict=None)
        assert isinstance(es, EditedScene)

    def test_tc27_none_critic_report_ok(self, agent, draft_dict):
        es = agent.finalize(draft_dict, critic_report_dict=None)
        assert isinstance(es, EditedScene)

    def test_tc28_unicode_text_preserved(self, agent):
        text = "한국어 테스트 — 서울 봄날"
        es = agent.finalize({"scene_id": "x", "draft_text": text})
        assert "한국어" in es.final_text

    def test_tc29_loras_lmm0_no_external_api_in_source(self):
        import inspect
        from literary_system.agents import editor_agent
        src = inspect.getsource(editor_agent)
        assert "anthropic.com" not in src
        assert "openai.com" not in src

    def test_tc30_multiple_finalizations_independent(self, agent):
        d1 = {"scene_id": "sc1", "draft_text": "텍스트 A"}
        d2 = {"scene_id": "sc2", "draft_text": "텍스트 B"}
        es1 = agent.finalize(d1)
        es2 = agent.finalize(d2)
        assert es1.scene_id != es2.scene_id
