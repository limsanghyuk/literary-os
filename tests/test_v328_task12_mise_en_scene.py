"""V328 Task12: MiseEnSceneCompiler 테스트."""
import sys; sys.path.insert(0,"/tmp/literary_os_v328")
import pytest
from literary_system.drse.mise_en_scene_compiler import MiseEnSceneCompiler, DirectorialNote

class TestDirectorialNote:
    def test_default(self):
        n = DirectorialNote()
        assert 0.0 <= n.tension_score <= 1.0

    def test_to_prompt_hint_contains_key_fields(self):
        n = DirectorialNote(tension_score=0.8, dominant_node="char_A", sensory_hints=["어둠","침묵"])
        h = n.to_prompt_hint()
        assert "MiseEnScene" in h
        assert "0.80" in h
        assert "char_A" in h

    def test_sensory_hints_truncated_to_3(self):
        n = DirectorialNote(sensory_hints=["hint_alpha","hint_beta","hint_gamma","hint_delta","hint_epsilon"])
        h = n.to_prompt_hint()
        assert "hint_delta" not in h  # only first 3 shown

class TestMiseEnSceneCompiler:
    def test_no_drse_returns_default(self):
        c = MiseEnSceneCompiler()
        note = c.compile("s1","목표",["A","B"])
        assert isinstance(note, DirectorialNote)
        assert note.tension_score == 0.5

    def test_with_mock_drse(self):
        class MockDRSE:
            def score_all(self, scene_id, characters):
                return [{"tension":0.9,"node_id":"A","hint":"어둠"},
                        {"tension":0.6,"node_id":"B","hint":"침묵"}]
        c = MiseEnSceneCompiler(drse_engine=MockDRSE())
        note = c.compile("s1","목표",["A","B"])
        assert note.tension_score == pytest.approx(0.9)
        assert note.dominant_node == "A"
        assert "어둠" in note.sensory_hints

    def test_drse_exception_returns_default(self):
        class BrokenDRSE:
            def score_all(self, **kw): raise RuntimeError("fail")
        c = MiseEnSceneCompiler(drse_engine=BrokenDRSE())
        note = c.compile("s1","목표",["A"])
        assert note.tension_score == 0.5

    def test_empty_characters(self):
        class MockDRSE:
            def score_all(self, **kw): return []
        c = MiseEnSceneCompiler(drse_engine=MockDRSE())
        note = c.compile("s1","목표",[])
        assert isinstance(note, DirectorialNote)

    def test_prompt_hint_empty_hints(self):
        n = DirectorialNote(tension_score=0.5, dominant_node="", sensory_hints=[])
        h = n.to_prompt_hint()
        assert "MiseEnScene" in h
