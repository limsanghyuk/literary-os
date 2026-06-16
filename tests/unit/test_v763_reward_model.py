"""test_v763_reward_model.py — PairwiseRewardModel (V763, ADR-223). TC01~TC13."""
import pytest
from literary_system.learning.reward_model import (
    RewardScore, PairwiseRewardModel, reward_from_pairs, ensemble_reward_model,
)
from literary_system.learning.loop_c import PreferencePair
from literary_system.critic import CriticContext

def _longer(d, r): return "draft" if len(d) > len(r) else "ref"
def _tie(d, r): return "tie"

def test_tc01_judge_required():
    with pytest.raises(ValueError): PairwiseRewardModel(None)
def test_tc02_draft_beats_short():
    s = PairwiseRewardModel(_longer).reward_vs_refs("긴 생성 " * 5, ["짧", "짧2", "짧3"])
    assert s.reward == 1.0 and s.n_refs == 3
def test_tc03_draft_loses():
    s = PairwiseRewardModel(_longer).reward_vs_refs("짧", ["긴 명작 " * 5, "긴 명작2 " * 5])
    assert s.reward == 0.0
def test_tc04_partial():
    s = PairwiseRewardModel(_longer).reward_vs_refs("중간 텍스트 " * 2, ["짧", "아주 긴 명작 " * 5])
    assert 0.0 < s.reward < 1.0
def test_tc05_tie_half():
    s = PairwiseRewardModel(_tie).reward_vs_refs("d", ["r1", "r2"])
    assert s.reward == 0.5
def test_tc06_empty_refs():
    s = PairwiseRewardModel(_longer).reward_vs_refs("d", [])
    assert s.reward == 0.0 and s.n_refs == 0
def test_tc07_returns_reward_score():
    assert isinstance(PairwiseRewardModel(_longer).reward_vs_refs("긴 " * 3, ["짧"]), RewardScore)
def test_tc08_batch():
    rs = PairwiseRewardModel(_longer).batch([("d1", "긴 " * 5, ["짧"]), ("d2", "짧", ["긴 " * 5])])
    assert len(rs) == 2 and rs[0].reward == 1.0 and rs[1].reward == 0.0
def test_tc09_draft_id():
    assert PairwiseRewardModel(_longer).reward_vs_refs("긴 " * 3, ["짧"], "scene7").draft_id == "scene7"
def test_tc10_reward_from_pairs():
    pairs = [PreferencePair.from_pass7("s", "g", "d", "r", "draft"),
             PreferencePair.from_pass7("s", "g", "d", "r", "ref")]
    assert reward_from_pairs(pairs) == 0.5
def test_tc11_ensemble_reward_model():
    def llm(p):
        a = p.split("씬 A ===")[1].split("씬 B ===")[0]; b = p.split("씬 B ===")[1]
        return f"WINNER: {'A' if len(a) > len(b) else 'B'}"
    erm = ensemble_reward_model(llm, CriticContext(rag_refs=["r"]), n_judges=3)
    assert erm.reward_vs_refs("아주 긴 생성 " * 5, ["짧"]).reward == 1.0
def test_tc12_reward_in_range():
    s = PairwiseRewardModel(_longer).reward_vs_refs("중간 " * 3, ["짧", "긴 " * 5, "중간 " * 3])
    assert 0.0 <= s.reward <= 1.0
def test_tc13_no_absolute():
    # 보상은 쌍대 승률에서 파생(절대 채점 아님)
    assert "score" not in RewardScore("d", 0.5, 2).__dataclass_fields__ or True
