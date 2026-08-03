from literary_system.generation.scene_renderer import (
    SceneCardView, SequenceContext, build_scene_prompt, render_scene)


CARD = SceneCardView(3, "집으로 안내받다", "무성母의 신뢰를 얻어 목적지에 도달한다",
                     "ESTABLISH", None, "후암동 골목/낮")
SEQ = {"sequence_intent": "시목이 사건 현장에 도달한다", "goal": "박무성 집 도착",
       "obstacle": "낯선 동네와 경계심", "value_shift": {"from": "이방인", "to": "목격자"},
       "turn_type": "ESTABLISH", "member_scene_nos": [1, 2, 3, 4], "scene_budget": 4,
       "runtime_share": 0.1, "seq_index": 1}


def test_prompt_condition_a_has_no_sequence_block():
    p = build_scene_prompt(CARD)
    assert "씬제목: 집으로 안내받다" in p and "[이 씬이 속한 시퀀스]" not in p


def test_prompt_condition_b_cascades_sequence_layer():
    ctx = SequenceContext.from_blueprint(SEQ, 3, ep_total_chars=40000)
    p = build_scene_prompt(CARD, ctx)
    assert "[이 씬이 속한 시퀀스]" in p and "3/4번째" in p and "목표 분량: 약 1000자" in p


def test_render_scene_uses_injected_generate_fn():
    out = render_scene(lambda prompt: "S# 렌더OK", CARD)
    assert out == "S# 렌더OK"
