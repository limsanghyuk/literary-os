"""test_passes4_7.py — 생성 본체 Pass4~7 테스트 (V752)."""
import importlib.util, sys
from pathlib import Path
import pytest

_ORCH = (Path(__file__).resolve().parents[2]
         / "docs/sessions/2026-06-13_corpus_ko_build/orchestration")
if not (_ORCH / "passes4_7.py").exists():
    pytest.skip("passes4_7.py 없음", allow_module_level=True)
sys.path.insert(0, str(_ORCH))
import passes4_7 as P   # noqa: E402

def _briefs():
    return P._demo_briefs()

def test_tc01_demo_briefs(): assert len(_briefs()) >= 5
def test_tc02_pass4_fills_refs():
    bs = P.pass4_rag(_briefs(), retrieve=lambda b: ["sim::1"])
    assert all(isinstance(b.rag_refs, list) for b in bs) and bs[0].rag_refs
def test_tc03_pass4_motif_callbacks():
    bs = P.pass4_rag(_briefs())
    assert any(any(r.startswith("motif:") for r in b.rag_refs) for b in bs)
def test_tc04_pass5_stub_draft():
    bs = P.pass5_draft(_briefs())
    assert all(b.draft and len(b.draft) >= 30 for b in bs)
def test_tc05_pass5_injected_gen():
    bs = P.pass5_draft(_briefs(), generate=lambda b, r: "주입생성 " * 10)
    assert bs[0].draft.startswith("주입생성")
def test_tc06_pass6_valid_pass():
    bs = P.pass5_draft(P.pass4_rag(_briefs()))
    P.pass6_gate(bs)
    assert all(b.gate is not None for b in bs)
def test_tc07_pass6_too_short_fails():
    bs = _briefs()
    for b in bs: b.draft = "x"
    failed = P.pass6_gate(bs)
    assert len(failed) == len(bs) and "too_short" in bs[0].gate["fail_reasons"]
def test_tc08_pass6_no_conflict_marker():
    bs = [b for b in _briefs() if b.targets.get("conflict_intensity_min", 0) > 0][:1]
    assert bs, "conflict 비트 존재"
    bs[0].draft = "조용히 차를 마신다. " * 5  # 갈등 마커 없음
    P.pass6_gate(bs)
    assert "no_conflict_marker" in bs[0].gate["fail_reasons"]
def test_tc09_pass6_callback_missing():
    bs = [b for b in _briefs() if b.targets.get("callback_motifs")][:1]
    if bs:
        bs[0].draft = "갈등이 터진다. " * 5  # 콜백 모티프 누락
        P.pass6_gate(bs)
        assert "callback_missing" in bs[0].gate["fail_reasons"]
def test_tc10_pass7_preference_pairs():
    bs = P.pass5_draft(P.pass4_rag(_briefs()))
    P.pass6_gate(bs)
    pairs = P.pass7_panel(bs, judge=lambda d, r: "draft",
                          reference_of=lambda b: ("real::x", "레퍼런스"))
    assert pairs and all("pref" in p for p in pairs)
def test_tc11_pass7_no_ref():
    bs = P.pass5_draft(P.pass4_rag(_briefs()))
    P.pass6_gate(bs)
    P.pass7_panel(bs)
    assert any(b.panel and b.panel["pairwise_pref"] == "no_ref" for b in bs)
def test_tc12_orchestrate_clean():
    res = P.run_pass4_7(_briefs(), retrieve=lambda b: ["s"],
                        generate=lambda b, r: "갈등이 터진다 " * 8 + "참조 모티프: 깨진 유리",
                        judge=lambda d, r: "draft",
                        reference_of=lambda b: ("r", "ref"))
    assert isinstance(res["preference_pairs"], list)
def test_tc13_short_loop_a_recovers():
    briefs = _briefs(); st = {"n": 0}
    def flaky(b, r):
        st["n"] += 1
        return "x" if st["n"] <= len(briefs) else ("갈등이 터진다 " * 8 + "참조 모티프: " + " ".join(b.targets.get("callback_motifs") or []))
    res = P.run_pass4_7(briefs, generate=flaky, max_redraft=1)
    assert len(res["gate_failed"]) == 0
def test_tc14_selftest(): assert P._selftest() == 0
def test_tc15_no_absolute_score():
    # Pass6 게이트는 pass/fail + 이유만, 절대 점수 필드 없음 (G_NO_ABSOLUTE_REWARD 정합)
    bs = P.pass5_draft(P.pass4_rag(_briefs())); P.pass6_gate(bs)
    assert set(bs[0].gate.keys()) == {"pass", "fail_reasons"}
