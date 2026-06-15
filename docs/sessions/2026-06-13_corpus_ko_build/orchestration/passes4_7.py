"""
passes4_7.py — 생성 본체 Pass4~7 (V752, GENERATION_BODY_L4_v1 §Pass4~7 구현)

Pass4 RAG 결선 · Pass5 초안 생성(LLM) · Pass6 구조 sanity 게이트(씬) · Pass7 패널 정련(보상)
아키텍처: 공식=구조 게이트(Pass6, 절대점수 아님) / 패널=품질 보상(Pass7, 쌍대·실대본 앵커).
주입형: retrieve·generate·judge·reference_of (테스트=fake, 운영=ChromaDB/RealOpenAIAdapter/패널).

실행: python passes4_7.py --selftest
"""
from __future__ import annotations
import sys
from typing import Callable, Dict, List, Optional

from schema import SceneBrief, WorkSpec  # type: ignore
from passes import pass2_causality, pass3_scene_brief  # type: ignore

# 구조 게이트용 갈등 마커(씬 단위 sanity — 절대 품질 아님)
_CONFLICT_MARKERS = (
    "위기", "갈등", "충돌", "대립", "긴장", "분노", "배신", "비밀",
    "거짓", "협박", "추격", "위험", "절망", "결단", "맞선",
)


# ── Pass4: RAG 결선 ─────────────────────────────────────────────────────────
def pass4_rag(briefs: List[SceneBrief], *,
              retrieve: Optional[Callable[[SceneBrief], List[str]]] = None,
              nkg_state: Optional[Dict[str, str]] = None,
              unrecovered_motifs: Optional[set] = None) -> List[SceneBrief]:
    """SceneBrief에 rag_refs 결선: 유사 씬(ChromaDB) + NKG 인물상태 + DRSE 미회수 콜백 후보."""
    for b in briefs:
        refs: List[str] = []
        if retrieve:
            refs.extend(retrieve(b) or [])
        cbs = b.targets.get("callback_motifs") or []
        if unrecovered_motifs:
            refs.extend(f"motif:{m}" for m in cbs if m in unrecovered_motifs)
        else:
            refs.extend(f"motif:{m}" for m in cbs)
        if nkg_state:
            refs.extend(f"nkg:{c}={nkg_state[c]}" for c in b.characters if c in nkg_state)
        b.rag_refs = refs
    return briefs


# ── Pass5: 초안 생성 ────────────────────────────────────────────────────────
def pass5_draft(briefs: List[SceneBrief], *,
                generate: Optional[Callable[[SceneBrief, List[str]], str]] = None
                ) -> List[SceneBrief]:
    """SceneBrief → draft. 제약: 레퍼런스 복제 금지(앵커는 품질 기준이지 복사원본 아님)."""
    for b in briefs:
        if generate:
            b.draft = generate(b, b.rag_refs)
        else:
            # 결정론 스텁(테스트용): 구조 충족 텍스트
            cbs = " ".join(b.targets.get("callback_motifs") or [])
            confl = ("갈등이 정면으로 터지며 인물들이 맞선다"
                     if b.targets.get("conflict_intensity_min", 0) > 0
                     else "정적 속에서 인물들의 속내가 천천히 드러난다")
            b.draft = (f"[{b.dramatic_function}] {', '.join(b.characters)}이(가) 마주한 장면이다. "
                       f"{confl}. 참조 모티프: {cbs}.").strip()
    return briefs


# ── Pass6: 구조 sanity 게이트(씬 단위) ──────────────────────────────────────
def pass6_gate(briefs: List[SceneBrief]) -> List[str]:
    """draft 구조 충족 검사(절대점수 아님): 길이·갈등존재·콜백반영. FAIL은 Pass5 재생성 대상."""
    failed: List[str] = []
    for b in briefs:
        d = (b.draft or "").strip()
        reasons: List[str] = []
        if len(d) < 30:
            reasons.append("too_short")
        if b.targets.get("conflict_intensity_min", 0) > 0 and \
                not any(m in d for m in _CONFLICT_MARKERS):
            reasons.append("no_conflict_marker")
        cbs = b.targets.get("callback_motifs") or []
        if cbs and not any(c in d for c in cbs):
            reasons.append("callback_missing")
        b.gate = {"pass": not reasons, "fail_reasons": reasons}
        if reasons:
            failed.append(b.scene_id)
    return failed


# ── Pass7: 패널 정련(보상) ──────────────────────────────────────────────────
def pass7_panel(briefs: List[SceneBrief], *,
                judge: Optional[Callable[[str, str], str]] = None,
                reference_of: Optional[Callable[[SceneBrief], tuple]] = None
                ) -> List[Dict]:
    """게이트 통과 draft vs 동일 기능 실제 레퍼런스 씬 쌍대 비교 → 선호쌍 로그(보상 신호)."""
    pairs: List[Dict] = []
    for b in briefs:
        if not (b.gate and b.gate.get("pass")):
            continue
        ref_id, ref_text = (reference_of(b) if reference_of else (None, None))
        if judge and ref_text:
            pref = judge(b.draft or "", ref_text)        # "draft"|"ref"|"tie"
            b.panel = {"accept": pref in ("draft", "tie"),
                       "pairwise_pref": pref, "reference": ref_id}
            pairs.append({"scene_id": b.scene_id, "ref_id": ref_id, "pref": pref})
        else:
            b.panel = {"accept": True, "pairwise_pref": "no_ref", "reference": None}
    return pairs


# ── 오케스트레이션 (짧은 루프 A 포함) ───────────────────────────────────────
def run_pass4_7(briefs: List[SceneBrief], *, retrieve=None, generate=None,
                judge=None, reference_of=None, max_redraft: int = 1,
                nkg_state=None, unrecovered_motifs=None) -> Dict:
    pass4_rag(briefs, retrieve=retrieve, nkg_state=nkg_state,
              unrecovered_motifs=unrecovered_motifs)
    pass5_draft(briefs, generate=generate)
    failed = pass6_gate(briefs)
    # 짧은 루프 A: 구조 FAIL 씬 재생성(최대 max_redraft회)
    for _ in range(max_redraft):
        if not failed:
            break
        redraft = [b for b in briefs if b.scene_id in failed]
        pass5_draft(redraft, generate=generate)
        failed = pass6_gate(briefs)
    pairs = pass7_panel(briefs, judge=judge, reference_of=reference_of)
    return {"briefs": briefs,
            "gate_failed": [b.scene_id for b in briefs if b.gate and not b.gate["pass"]],
            "preference_pairs": pairs}


# ── 자가검증 ────────────────────────────────────────────────────────────────
def _demo_briefs() -> List[SceneBrief]:
    spec = WorkSpec(title="균열", genre="thriller", n_episodes=1,
                    master_theme="신뢰의 붕괴", conflict_axis="형사 vs 내부자",
                    core_dilemma="진실 vs 안전",
                    characters=[{"name": "준호", "role": "주연", "want": "진실", "flaw": "의심"},
                                {"name": "세아", "role": "상대역", "want": "은폐", "flaw": "공포"}],
                    arc_summary="의심에서 확신으로")
    beats = pass2_causality(spec, motifs=["깨진 유리", "녹취"])
    return pass3_scene_brief(spec, beats)


def _selftest() -> int:
    ok = True
    def chk(c, m):
        nonlocal ok
        print(("  ✅ " if c else "  ❌ ") + m); ok = ok and c

    briefs = _demo_briefs()
    chk(len(briefs) >= 5, f"Pass1~3 SceneBrief 생성: {len(briefs)}")

    # fake 주입: retrieve/generate/judge/reference
    fake_retrieve = lambda b: [f"ko_scene_sim::{b.beat_id}"]
    def fake_gen(b, refs):
        cbs = " ".join(b.targets.get("callback_motifs") or [])
        c = ("갈등이 폭발하며 인물들이 정면으로 부딪친다"
             if b.targets.get("conflict_intensity_min", 0) > 0
             else "정적 속에서 속내가 천천히 드러난다")
        return (f"[{b.dramatic_function}] {', '.join(b.characters)}이(가) 마주한 장면. "
                f"{c}. 참조 모티프: {cbs}. (rag={len(refs)})")
    fake_judge = lambda draft, ref: "draft"      # 데모: 생성 우세 가정
    fake_ref = lambda b: (f"real::{b.beat_id}", "실제 대본 레퍼런스 텍스트")

    res = run_pass4_7(briefs, retrieve=fake_retrieve, generate=fake_gen,
                      judge=fake_judge, reference_of=fake_ref)
    b0 = res["briefs"][0]
    chk(b0.rag_refs and any("sim" in r for r in b0.rag_refs), f"Pass4 RAG 결선: {b0.rag_refs[:2]}")
    chk(b0.draft and len(b0.draft) > 20, "Pass5 초안 생성")
    chk(all(b.gate is not None for b in res["briefs"]), "Pass6 게이트 판정 부여")
    chk(res["preference_pairs"] and all("pref" in p for p in res["preference_pairs"]),
        f"Pass7 선호쌍 로그: {len(res['preference_pairs'])}건")

    # 구조 게이트 변별: 빈약 draft는 FAIL (절대점수 아닌 sanity)
    bad = _demo_briefs()
    for b in bad:
        b.draft = "x"
    f = pass6_gate(bad)
    chk(len(f) == len(bad), "Pass6 빈약 draft 전건 FAIL(구조 sanity)")

    # 짧은 루프 A: FAIL 후 재생성으로 회복
    recov = _demo_briefs()
    state = {"n": 0}
    def flaky(b, refs):
        state["n"] += 1
        return "x" if state["n"] <= len(recov) else fake_gen(b, refs)  # 1차 전부 실패→2차 회복
    res2 = run_pass4_7(recov, generate=flaky, max_redraft=1)
    chk(len(res2["gate_failed"]) == 0, "짧은 루프 A: 재생성 후 구조 충족")

    print("\nSELFTEST", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(_selftest() if "--selftest" in sys.argv else _selftest())
