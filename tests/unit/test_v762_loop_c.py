"""test_v762_loop_c.py — loop-C 선호쌍·DPO 적재 (V762, ADR-222). TC01~TC16."""
import json, tempfile, os
import pytest
from literary_system.learning.loop_c import (
    PreferencePair, load_preference_pairs, to_dpo_dataset, write_dpo_jsonl,
    generation_win_rate, reference_strength, summarize, LoopCReport,
)

# 인라인 픽스처(개발자 dpo_pairs.jsonl 포맷)
FIX = [
    {"func": "inciting", "genre": "thriller", "ref_id": "추격자::S80", "winner": "ref", "draft": "생성 골목 씬", "ref": "추격자 실제 씬"},
    {"func": "setup", "genre": "thriller", "ref_id": "올드보이::S1", "winner": "draft", "draft": "생성 도입 씬 긴 텍스트", "ref": "올드보이 실제"},
    {"func": "climax", "genre": "thriller", "ref_id": "추격자::S80", "winner": "ref", "draft": "생성 절정", "ref": "추격자 절정"},
    {"func": "rising", "genre": "thriller", "ref_id": "곡성::S5", "winner": "draft", "draft": "생성 상승", "ref": "곡성 씬"},
]

def test_tc01_from_pass7_draft_win():
    p = PreferencePair.from_pass7("setup", "thriller", "DRAFT", "REF", "draft")
    assert p.chosen == "DRAFT" and p.rejected == "REF"
def test_tc02_from_pass7_ref_win():
    p = PreferencePair.from_pass7("setup", "thriller", "DRAFT", "REF", "ref")
    assert p.chosen == "REF" and p.rejected == "DRAFT"
def test_tc03_invalid_winner():
    with pytest.raises(ValueError): PreferencePair.from_pass7("s", "g", "d", "r", "best")
def test_tc04_meta(): 
    p = PreferencePair.from_pass7("setup", "thriller", "d", "r", "draft", "ref::1")
    assert p.meta["func"] == "setup" and p.meta["ref_id"] == "ref::1"
def test_tc05_source_default():
    assert PreferencePair.from_pass7("s", "g", "d", "r", "draft").source == "panel"

def _write(fix):
    fd, path = tempfile.mkstemp(suffix=".jsonl"); os.close(fd)
    with open(path, "w", encoding="utf-8") as f:
        for d in fix: f.write(json.dumps(d, ensure_ascii=False) + "\n")
    return path

def test_tc06_load_pairs():
    ps = load_preference_pairs(_write(FIX)); assert len(ps) == 4
def test_tc07_load_winner_mapping():
    ps = load_preference_pairs(_write(FIX))
    ref_pair = [p for p in ps if p.meta["winner"] == "ref"][0]
    assert ref_pair.chosen == "추격자 실제 씬"  # ref 우세 → 명작이 chosen
def test_tc08_to_dpo():
    d = to_dpo_dataset(load_preference_pairs(_write(FIX)))
    assert all({"prompt", "chosen", "rejected"} == set(x) for x in d)
def test_tc09_write_dpo_roundtrip():
    ps = load_preference_pairs(_write(FIX))
    fd, out = tempfile.mkstemp(suffix=".jsonl"); os.close(fd)
    n = write_dpo_jsonl(ps, out)
    assert n == 4 and sum(1 for _ in open(out, encoding="utf-8")) == 4
def test_tc10_win_rate():
    ps = load_preference_pairs(_write(FIX))
    assert generation_win_rate(ps) == 0.5  # 2 draft / 4
def test_tc11_win_rate_empty(): assert generation_win_rate([]) == 0.0
def test_tc12_reference_strength():
    ps = load_preference_pairs(_write(FIX))
    rs = reference_strength(ps)
    assert "추격자::S80" in rs and "GEN" in rs
def test_tc13_summarize():
    r = summarize(load_preference_pairs(_write(FIX)))
    assert isinstance(r, LoopCReport) and r.n_pairs == 4 and r.by_winner["draft"] == 2
def test_tc14_summary_str():
    assert "loop-C" in summarize(load_preference_pairs(_write(FIX))).summary
def test_tc15_by_function():
    r = summarize(load_preference_pairs(_write(FIX)))
    assert "setup" in r.by_function and "climax" in r.by_function
def test_tc16_no_absolute_score():
    # 쌍대(chosen/rejected)만, 절대점수 필드 없음
    p = PreferencePair.from_pass7("s", "g", "d", "r", "draft")
    assert "score" not in p.__dataclass_fields__
