"""
generation/pass_pipeline.py — 7-pass 생성 파이프라인 L4 (V781, ADR-241).

씨드(premise) → Pass1 거시설계 → Pass2 인과비트 → Pass3 씬브리프 →
Pass4 RAG정박 → Pass5 초안생성 → Pass6 구조게이트 → Pass7 패널판정.

핵심 배선:
- Pass5 `generate` 훅 = **loop-C로 학습되는 생성기가 꽂히는 자리**(LLM-1/로컬 모델). 미주입 시 stub.
- Pass4 `retrieve` 훅 = corpus_ko RAG. Pass7 `judge` 훅 = critic 패널(쌍대).
- Pass6 = 공식 구조 sanity(LLM-0). 생성 절반 ↔ 평가·학습 절반(critic·loop-C)의 연결점.
LLM-0: 파이프라인 골격은 LLM 미호출. 외부 LLM은 generate/judge 훅(critic 경계) 안에서만.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from literary_system.generation.schema import (
    WorkSpec, Beat, SceneBrief, STANDARD_ARC, INTENT)

RetrieveFn = Callable[[SceneBrief], List[str]]          # brief → 참조 텍스트들
GenerateFn = Callable[[SceneBrief, List[str]], str]     # (brief, rag_refs) → 초안
JudgeFn = Callable[[str, str], str]                     # (draft, ref) → 'draft'|'ref'|'tie'


def _t_ideal(curve: List[float], pos: float) -> float:
    if not curve: return 0.5
    return round(curve[min(int(pos * len(curve)), len(curve) - 1)], 3)


@dataclass
class GenerationResult:
    spec:    WorkSpec
    beats:   List[Beat]
    briefs:  List[SceneBrief]
    gate_issues: List[str]
    panel:   List[Dict[str, Any]]

    @property
    def summary(self) -> str:
        wins = sum(1 for p in self.panel if p.get("winner") == "draft")
        return (f"Gen[{self.spec.title}] beats={len(self.beats)} scenes={len(self.briefs)} "
                f"gate_issues={len(self.gate_issues)} panel_win={wins}/{len(self.panel)}")

    def to_dict(self) -> Dict[str, Any]:
        return {"spec": self.spec.to_dict(), "beats": [b.to_dict() for b in self.beats],
                "briefs": [s.to_dict() for s in self.briefs],
                "gate_issues": self.gate_issues, "panel": self.panel, "summary": self.summary}

    def to_preference_pairs(self):
        """Pass7 패널 → loop-C 선호쌍(learning.loop_c.PreferencePair). 생성↔학습 연결."""
        from literary_system.learning.loop_c import PreferencePair
        pairs = []
        for p in self.panel:
            if p.get("winner") in ("draft", "ref") and p.get("draft") and p.get("ref"):
                pairs.append(PreferencePair.from_pass7(
                    p.get("func", ""), self.spec.genre, p["draft"], p["ref"],
                    p["winner"], p.get("scene_id", "")))
        return pairs


class PassPipeline:
    """7-pass 생성 본체. 훅(retrieve/generate/judge) 주입으로 RAG·생성기·critic 연결."""

    def __init__(self, genre_curve: Optional[List[float]] = None) -> None:
        self._curve = genre_curve or [0.3, 0.35, 0.45, 0.55, 0.6, 0.7, 0.8, 0.85, 0.9, 0.6]

    # ── Pass 1~3: 설계 (LLM-0) ─────────────────────────────
    def pass1_premise(self, premise: Dict[str, Any]) -> WorkSpec:
        return WorkSpec(
            title=premise["title"], genre=premise["genre"], n_episodes=premise.get("n_episodes", 1),
            master_theme=premise["master_theme"], conflict_axis=premise["conflict_axis"],
            core_dilemma=premise["core_dilemma"], characters=premise["characters"],
            arc_summary=premise.get("arc_summary",
                f"{premise['master_theme']}를 축으로 {premise['conflict_axis']} 대립이 {premise['core_dilemma']}로 수렴"))

    def pass2_causality(self, spec: WorkSpec, motifs: List[str]) -> List[Beat]:
        beats: List[Beat] = []
        for i, (fn, pos, parent) in enumerate(STANDARD_ARC):
            plant = motifs[:2] if fn in ("setup", "inciting") else (motifs[2:3] if fn == "rising" else [])
            payoff = motifs[:1] if fn == "climax" else (motifs[1:2] if fn == "resolution" else [])
            beats.append(Beat(f"B{i+1:02d}", fn, pos, parent, INTENT[fn], plant, payoff,
                              _t_ideal(self._curve, pos)))
        return beats

    def pass3_scene_brief(self, spec: WorkSpec, beats: List[Beat]) -> List[SceneBrief]:
        briefs: List[SceneBrief] = []
        names = [c["name"] for c in spec.characters]
        for k, b in enumerate(beats):
            tt = b.target_tension
            chars = names[:2] if b.function in ("setup", "resolution") else names[:3]
            briefs.append(SceneBrief(
                scene_id=f"{spec.title}::S{k+1:02d}", beat_id=b.beat_id,
                slug={"location": "TBD", "time": "낮", "int_ext": "실내"},
                characters=chars, dramatic_function=b.function,
                targets={"tension_band": [round(max(0, tt-0.12), 2), round(min(1, tt+0.12), 2)],
                         "conflict_intensity_min": 0.2 if b.function in ("crisis", "climax") else 0.0,
                         "callback_motifs": b.payoff_motifs}))
        return briefs

    # ── Pass 4~7: RAG → 생성 → 게이트 → 패널 ───────────────
    def pass4_rag(self, briefs: List[SceneBrief], retrieve: Optional[RetrieveFn]) -> None:
        for b in briefs:
            b.rag_refs = list(retrieve(b)) if retrieve else []

    def pass5_draft(self, briefs: List[SceneBrief], generate: Optional[GenerateFn]) -> None:
        """생성기 훅(loop-C 학습 모델)로 초안 생성. 미주입 시 stub 표식."""
        for b in briefs:
            b.draft = generate(b, b.rag_refs) if generate else f"[STUB draft {b.scene_id}]"

    def pass6_gate(self, briefs: List[SceneBrief]) -> List[str]:
        """구조 sanity(LLM-0): 초안 존재·등장인물 반영·콜백 회수 점검."""
        issues: List[str] = []
        for b in briefs:
            if not b.draft or b.draft.startswith("[STUB"):
                issues.append(f"{b.scene_id}: 초안 없음/stub")
            cb = b.targets.get("callback_motifs", [])
            if cb and b.draft and not any(m in b.draft for m in cb):
                issues.append(f"{b.scene_id}: 콜백 모티프 미회수 {cb}")
            b.gate = {"ok": (b.draft is not None and not b.draft.startswith("[STUB"))}
        return issues

    def pass7_panel(self, briefs: List[SceneBrief], judge: Optional[JudgeFn],
                    references: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """씬별 초안 vs 명작 참조 쌍대 판정(critic). loop-C 선호쌍 입력 생성."""
        out: List[Dict[str, Any]] = []
        for b in briefs:
            ref = (references or {}).get(b.scene_id) or (b.rag_refs[0] if b.rag_refs else "")
            winner = judge(b.draft or "", ref) if (judge and ref) else "tie"
            b.panel = {"winner": winner, "ref": ref[:40]}
            out.append({"scene_id": b.scene_id, "func": b.dramatic_function,
                        "winner": winner, "draft": b.draft, "ref": ref})
        return out

    # ── 전체 실행 ──────────────────────────────────────────
    def run(self, premise: Dict[str, Any], motifs: Optional[List[str]] = None, *,
            retrieve: Optional[RetrieveFn] = None, generate: Optional[GenerateFn] = None,
            judge: Optional[JudgeFn] = None,
            references: Optional[Dict[str, str]] = None) -> GenerationResult:
        spec = self.pass1_premise(premise)
        beats = self.pass2_causality(spec, motifs or ["비밀", "배신", "구원"])
        briefs = self.pass3_scene_brief(spec, beats)
        self.pass4_rag(briefs, retrieve)
        self.pass5_draft(briefs, generate)
        issues = self.pass6_gate(briefs)
        panel = self.pass7_panel(briefs, judge, references)
        return GenerationResult(spec, beats, briefs, issues, panel)
