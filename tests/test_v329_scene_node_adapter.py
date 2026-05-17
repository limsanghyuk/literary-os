"""V329 Task2: SceneNodeAdapter 테스트 — V328 SceneDraftOutput 완전 호환 검증."""
import pytest
from unittest.mock import MagicMock
from literary_system.nkg.adapters.scene_node_adapter import SceneNodeAdapter
from literary_system.nkg.schema import NKGSceneNode, NKGNodeType


def _make_draft(**kw):
    """mock SceneDraftOutput 생성."""
    m = MagicMock()
    m.scene_id       = kw.get("scene_id", "s_test")
    m.episode_id     = kw.get("episode_id", None)
    m.episode_no     = kw.get("episode_no", 1)
    m.draft_text     = kw.get("draft_text", "테스트 장면 내용")
    m.mae_score      = kw.get("mae_score", 0.75)
    m.scene_index    = kw.get("scene_index", 0)
    quality_mock = MagicMock()
    quality_mock.value = kw.get("quality_value", "good")
    m.quality        = quality_mock
    # EmotionalVectorSchema mock
    ev = MagicMock()
    ev.tension   = kw.get("tension",   0.8)
    ev.sympathy  = kw.get("sympathy",  0.5)
    ev.dread     = kw.get("dread",     0.3)
    ev.catharsis = kw.get("catharsis", 0.1)
    m.emotional_vector = kw.get("emotional_vector", ev)
    return m


class TestSceneNodeAdapterBasic:
    def test_returns_nkg_scene_node(self):
        node = SceneNodeAdapter.from_draft_output(_make_draft())
        assert isinstance(node, NKGSceneNode)

    def test_scene_id_preserved(self):
        node = SceneNodeAdapter.from_draft_output(_make_draft(scene_id="s99"))
        assert node.scene_id == "s99"

    def test_episode_id_from_draft(self):
        node = SceneNodeAdapter.from_draft_output(_make_draft(episode_id="ep03"))
        assert node.episode_id == "ep03"

    def test_episode_id_fallback_to_episode_no(self):
        m = _make_draft()
        m.episode_id = None
        node = SceneNodeAdapter.from_draft_output(m)
        assert "1" in node.episode_id   # episode_no=1

    def test_episode_id_explicit_override(self):
        node = SceneNodeAdapter.from_draft_output(_make_draft(), episode_id="ep_FORCED")
        assert node.episode_id == "ep_FORCED"

    def test_content_from_draft_text(self):
        node = SceneNodeAdapter.from_draft_output(
            _make_draft(draft_text="장면 본문 텍스트"))
        assert node.content == "장면 본문 텍스트"

    def test_mae_score_preserved(self):
        node = SceneNodeAdapter.from_draft_output(_make_draft(mae_score=0.88))
        assert abs(node.mae_score - 0.88) < 1e-6

    def test_quality_extracted(self):
        node = SceneNodeAdapter.from_draft_output(_make_draft(quality_value="excellent"))
        assert node.quality == "EXCELLENT"

    def test_scene_index_preserved(self):
        node = SceneNodeAdapter.from_draft_output(_make_draft(scene_index=7))
        assert node.scene_index == 7

    def test_node_type_is_scene(self):
        node = SceneNodeAdapter.from_draft_output(_make_draft())
        assert node.node_type == NKGNodeType.SCENE


class TestSceneNodeAdapterEmotionalVector:
    def test_ev_converted_to_list(self):
        node = SceneNodeAdapter.from_draft_output(
            _make_draft(tension=0.9, sympathy=0.6, dread=0.4, catharsis=0.2))
        assert len(node.emotional_vector) == 4

    def test_tension_value(self):
        node = SceneNodeAdapter.from_draft_output(_make_draft(tension=0.9))
        assert abs(node.tension - 0.9) < 1e-6

    def test_sympathy_value(self):
        node = SceneNodeAdapter.from_draft_output(_make_draft(sympathy=0.65))
        assert abs(node.sympathy - 0.65) < 1e-6

    def test_ev_none_gives_defaults(self):
        m = _make_draft()
        m.emotional_vector = None
        node = SceneNodeAdapter.from_draft_output(m)
        assert len(node.emotional_vector) == 4
        assert node.tension == 0.5

    def test_content_hash_auto_set(self):
        node = SceneNodeAdapter.from_draft_output(_make_draft(draft_text="해시테스트"))
        assert len(node.content_hash) == 16


class TestSceneNodeAdapterBatch:
    def test_batch_returns_list(self):
        outputs = [_make_draft(scene_id=f"s{i}") for i in range(3)]
        nodes = SceneNodeAdapter.batch_convert(outputs)
        assert len(nodes) == 3

    def test_batch_skips_none(self):
        outputs = [_make_draft(), None, _make_draft(scene_id="s2")]
        nodes = SceneNodeAdapter.batch_convert(outputs)
        assert len(nodes) == 2

    def test_batch_episode_id_applied(self):
        outputs = [_make_draft(scene_id=f"s{i}") for i in range(2)]
        nodes = SceneNodeAdapter.batch_convert(outputs, episode_id="ep99")
        assert all(n.episode_id == "ep99" for n in nodes)

    def test_batch_empty_input(self):
        assert SceneNodeAdapter.batch_convert([]) == []


class TestSceneNodeAdapterEdgeCases:
    def test_no_scene_id_uses_unknown(self):
        m = MagicMock()
        m.scene_id = None
        m.episode_id = None
        m.episode_no = 1
        m.draft_text = "내용"
        m.mae_score  = 0.5
        m.scene_index = 0
        m.quality = None
        m.emotional_vector = None
        node = SceneNodeAdapter.from_draft_output(m)
        assert "unknown" in node.scene_id

    def test_no_draft_text_empty_string(self):
        m = MagicMock()
        m.scene_id = "s1"; m.episode_id = "ep1"
        m.draft_text = None; m.scene_text = None; m.text = None
        m.mae_score = 0.0; m.scene_index = 0
        m.quality = None; m.emotional_vector = None
        node = SceneNodeAdapter.from_draft_output(m)
        assert node.content == ""
