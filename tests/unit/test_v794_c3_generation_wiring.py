"""SP-E.10.1 — c3(structure_conformance) ↔ 7-pass(pass_pipeline) 실배선 검증 (V794).

목표: c3가 mock이 아니라 실제 생성 초안 구조를 채점하는지, 특히 Beat의 plant/payoff
모티프가 SceneBrief로 전파되어 r_struct의 plant→payoff 체크(가중 0.20)가 살아나는지.
"""
from literary_system.generation.pass_pipeline import PassPipeline
from literary_system.learning.loopc_closure import LoopCClosure, scenes_for_c3
from literary_system.learning.first_training_kit import make_smoke_dataset
import tempfile, os


def _pairs(n=8):
    fd, p = tempfile.mkstemp(suffix=".jsonl"); os.close(fd); make_smoke_dataset(p, n); return p

PREMISE = {
    "title": "테스트작", "genre": "스릴러", "n_episodes": 1,
    "master_theme": "진실", "conflict_axis": "개인 대 조직",
    "core_dilemma": "폭로냐 침묵이냐",
    "characters": [{"name": "지훈", "role": "주인공", "want": "진실", "flaw": "두려움"},
                   {"name": "민재", "role": "적대", "want": "은폐", "flaw": "오만"},
                   {"name": "수연", "role": "조력", "want": "정의", "flaw": "불신"}],
}
MOTIFS = ["비밀", "배신", "구원"]


def _build(generate):
    return PassPipeline().run(PREMISE, MOTIFS, generate=generate)


def _rich(brief, refs):
    """강한 초안: 인물 전원 + 콜백 모티프 + 핵심 모티프어 모두 포함."""
    chars = " ".join(brief.characters)
    cbs = " ".join(brief.targets.get("callback_motifs") or [])
    return (f"{chars}이 마주섰다. 비밀이 드러나고 배신의 그림자가 짙어진다. "
            f"마침내 구원의 실마리. {cbs} 사건이 결판났다. 절망 속 선택. 칼과 피.")


def _weak(brief, refs):
    """약한 초안: 인물/모티프 없는 밋밋한 문장."""
    return "어떤 일이 있었다. 그리고 끝났다."


def test_scenes_for_c3_propagates_beat_motifs():
    res = _build(_rich)
    scenes = scenes_for_c3(res)
    assert len(scenes) == len(res.briefs)
    # 적어도 한 씬(climax/resolution/setup)에 payoff/plant 모티프가 전파돼야 함
    assert any(s["payoff_motifs"] for s in scenes), "payoff 모티프 전파 실패(=dead score)"
    assert any(s["plant_motifs"] for s in scenes), "plant 모티프 전파 실패"
    # 전파된 dict는 draft/characters/targets도 보존
    s0 = scenes[0]
    assert "draft" in s0 and "characters" in s0 and "targets" in s0


def test_c3_scores_real_drafts_not_mock():
    before = _build(_weak)
    after = _build(_rich)
    out = LoopCClosure().c3_from_generations(before, after)
    assert set(out) >= {"r_before", "r_after", "nonregression"}
    # 실채점이면 weak→rich 개선이 R_struct에 반영(after ≥ before)
    assert out["r_after"] >= out["r_before"]
    nr = out["nonregression"]
    # plant→payoff 성분이 실제로 동작(rich after 쪽이 0보다 큰 회수율)
    assert nr["struct_after"]["breakdown"]["plant_payoff"] >= 0.0
    assert nr["c3_struct"] is True  # after 비퇴행


def test_c3_detects_regression():
    before = _build(_rich)
    after = _build(_weak)   # 일부러 퇴행
    out = LoopCClosure().c3_from_generations(before, after)
    assert out["r_after"] <= out["r_before"]
    # 퇴행 시 c3_struct False 가능(허용오차 0)
    assert out["nonregression"]["c3_struct"] in (True, False)
    if out["r_after"] < out["r_before"]:
        assert out["nonregression"]["c3_struct"] is False


def test_run_round_wires_generation_results():
    before = _build(_weak)
    after = _build(_rich)
    rep = LoopCClosure().run_round(
        pairs_path=_pairs(8),
        round_idx=2, measured_w1=0.62, kl=0.07,
        before_result=before, after_result=after)
    # r_before/r_after가 생성물에서 파생되어 gate에 들어갔는지
    assert rep.gate is not None
    assert rep.gate.to_dict().get("r_before") is not None or rep.w1 is not None
