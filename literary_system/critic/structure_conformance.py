"""
critic/structure_conformance.py — c3 구조 비퇴행 R 생산자 (V788, ADR-246, DESIGN-SGATE-v1).

G_LOOPC_WINRATE 3차 조건(c3)의 결손 생산자를 구현. winrate_gate.c3는 r_before/r_after를
'주입받기만' 하고 어떤 모듈도 계산하지 않았다(=N/A 자동통과). 본 모듈이 그 R을 생산한다.

★G_NO_ABSOLUTE_REWARD 준수: R은 DPO 보상이 아니라 *floor(통과 바닥)*. 절대 점수로 학습 신호에
넣지 않는다. 굿하트 회피 — 구조 적합은 '깨진 것을 거른다'는 음성/결정론 성격으로만 사용.

R = 3성분 (DESIGN-SGATE-v1 §4):
  R_struct ∈ [0,1] : 결정론적 구조 적합률(5 가중 체크)
      callback 0.25 · character 0.20 · tension-band 0.20 · plant→payoff 0.20 · function 0.15
  R_pair           : after-vs-before STRUCTURE 쌍대 자기비교 패배율 ≤ 0.5  (1 - loss_rate)
  R_path           : 병리 비증가 (distribution_guard penalty 하락 없음)
c3 = (R_struct 비퇴행) ∧ (R_pair 패배율≤0.5) ∧ (R_path 비증가)

LLM-0/LLM-1: R_struct·R_path는 순수 결정론(LLM 미호출). R_pair는 STRUCTURE축 쌍대 critic 주입
(기본 MockCritic=결정론, 운영 시 LLM critic). 절대점수 미사용.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

from literary_system.critic.distribution_guard import compute_stats, EMOTION_WORDS
from literary_system.critic.base import (
    CriticAxis, CriticContext, CriticInterface, MockCritic,
)

# 구조 적합률 5체크 가중 (합=1.0). DESIGN-SGATE-v1 §4 고정.
W_CALLBACK = 0.25
W_CHARACTER = 0.20
W_TENSION = 0.20
W_PLANT_PAYOFF = 0.20
W_FUNCTION = 0.15

R_REGRESSION_TOL = 0.0       # R_struct 비퇴행 허용 오차
PAIR_LOSS_MAX = 0.5          # after가 before에 패배하는 비율 상한

# 갈등/긴장 프록시용 키워드(긴장 밴드 추정, 결정론). 대사·감정·충돌 신호.
_CONFLICT_WORDS = ["죽", "피", "칼", "총", "배신", "거짓", "비밀", "위협", "도망", "추격",
                   "체포", "복수", "싸움", "고발", "협박", "납치", "사고", "폭발", "충돌", "대결"]
# 기능별 표지(결정론 휴리스틱). 존재 여부만 본다(약한 신호 0.15 가중).
_FUNCTION_MARKERS: Dict[str, List[str]] = {
    "setup":      ["아침", "일상", "소개", "처음", "평범"],
    "inciting":   ["사건", "갑자기", "발견", "전화", "소식"],
    "rising":     ["하지만", "그러나", "점점", "더욱", "긴장"],
    "midpoint":   ["반전", "사실", "알고보니", "뒤집", "정체"],
    "crisis":     ["최악", "절망", "막다른", "딜레마", "선택의"],
    "climax":     ["대결", "마침내", "결판", "맞선", "끝장"],
    "resolution": ["이후", "여파", "남은", "조용", "끝"],
}


def _tokens(text: str) -> List[str]:
    return re.findall(r"\w+", text or "")


def tension_proxy(text: str) -> float:
    """draft 텍스트 → 긴장 프록시 ∈ [0,1] (결정론). 충돌어 밀도+감정어율+문장부호 강도."""
    toks = _tokens(text)
    n = len(toks) or 1
    conflict = sum(text.count(w) for w in _CONFLICT_WORDS)
    emo = sum(text.count(w) for w in EMOTION_WORDS)
    bang = text.count("!") + text.count("?") + text.count("…")
    raw = (conflict * 2.0 + emo + bang) / n          # 밀도
    return round(min(1.0, raw * 3.0), 4)             # 스케일·클립


# ---------- 입력 정규화: SceneBrief 객체/딕셔너리/Beat 모두 허용 ----------

def _scene_get(s: Any, key: str, default=None):
    if isinstance(s, dict):
        return s.get(key, default)
    return getattr(s, key, default)


def _targets(s: Any) -> Dict[str, Any]:
    t = _scene_get(s, "targets", {}) or {}
    return t if isinstance(t, dict) else {}


# ---------- R_struct: 5 가중 결정론 체크 ----------

@dataclass
class StructStruct:
    r_struct: float
    breakdown: Dict[str, float]
    n_scenes: int

    def to_dict(self) -> Dict[str, Any]:
        return {"r_struct": self.r_struct, "breakdown": self.breakdown, "n_scenes": self.n_scenes}


def r_struct(scenes: Sequence[Any]) -> StructStruct:
    """씬(draft 포함) 시퀀스 → 구조 적합률 ∈ [0,1]. 각 체크는 '충족 씬 비율'."""
    scenes = list(scenes)
    n = len(scenes) or 1

    cb_hit = ch_hit = tn_hit = fn_hit = 0
    # plant→payoff: 앞 씬에서 심은 모티프가 뒤 씬 draft에서 회수되는지(전역).
    planted: List[Tuple[int, str]] = []
    payoff_total = 0
    payoff_done = 0

    for idx, s in enumerate(scenes):
        draft = _scene_get(s, "draft") or ""
        tg = _targets(s)

        # 1) callback: targets.callback_motifs 가 draft에 실제 등장
        cbs = tg.get("callback_motifs") or []
        if cbs:
            hit = sum(1 for m in cbs if m and m in draft)
            if hit >= max(1, len(cbs) // 2):    # 과반 회수면 충족
                cb_hit += 1
        else:
            cb_hit += 1                          # 회수 요구 없으면 위반 아님(중립 통과)

        # 2) character: 선언 인물이 draft에 등장
        chars = _scene_get(s, "characters") or []
        if chars:
            appear = sum(1 for c in chars if c and c in draft)
            if appear >= max(1, len(chars) // 2):
                ch_hit += 1
        else:
            ch_hit += 1

        # 3) tension-band: 측정 긴장 프록시가 목표 밴드 내
        band = tg.get("tension_band") or _scene_get(s, "tension_band")
        if band and len(band) == 2:
            tv = tension_proxy(draft)
            if band[0] <= tv <= band[1]:
                tn_hit += 1
        else:
            tn_hit += 1

        # 4) plant→payoff 누적
        for m in (_scene_get(s, "plant_motifs") or []):
            if m:
                planted.append((idx, m))
        for m in (_scene_get(s, "payoff_motifs") or []):
            if m:
                payoff_total += 1
                # 앞에서 심겼고 현재 draft에 등장하면 회수 완료
                if any(pm == m and pidx <= idx for pidx, pm in planted) and m in draft:
                    payoff_done += 1

        # 5) function: 기능 표지 존재(약한 신호)
        fn = _scene_get(s, "dramatic_function") or _scene_get(s, "function") or ""
        markers = _FUNCTION_MARKERS.get(fn, [])
        if not markers or any(mk in draft for mk in markers):
            fn_hit += 1

    cb = cb_hit / n
    ch = ch_hit / n
    tn = tn_hit / n
    pp = (payoff_done / payoff_total) if payoff_total else 1.0   # 회수 대상 없으면 중립 1.0
    fn = fn_hit / n

    score = round(W_CALLBACK*cb + W_CHARACTER*ch + W_TENSION*tn
                  + W_PLANT_PAYOFF*pp + W_FUNCTION*fn, 4)
    return StructStruct(score, {"callback": round(cb,4), "character": round(ch,4),
                                "tension": round(tn,4), "plant_payoff": round(pp,4),
                                "function": round(fn,4)}, len(scenes))


# ---------- R_pair: after vs before STRUCTURE 쌍대 자기비교 ----------

@dataclass
class StructPair:
    loss_rate: float            # after가 before에 패배한 비율
    r_pair: float               # 1 - loss_rate
    wins: int; losses: int; ties: int
    passed: bool                # loss_rate ≤ 0.5

    def to_dict(self) -> Dict[str, Any]:
        return {"loss_rate": self.loss_rate, "r_pair": self.r_pair, "wins": self.wins,
                "losses": self.losses, "ties": self.ties, "passed": self.passed}


def r_pair(before_scenes: Sequence[Any], after_scenes: Sequence[Any],
           rag_refs: Optional[List[str]] = None,
           critic: Optional[CriticInterface] = None) -> StructPair:
    """동일 씬슬롯의 after draft를 before draft와 STRUCTURE축으로 쌍대 비교.
    절대점수 미사용 — winner∈{a,b,tie}. a=after, b=before. after 패배율이 0.5 이하면 비퇴행.
    rag_refs는 G_LLM1_RAG 충족용(없으면 자기참조 1건 주입)."""
    critic = critic or MockCritic(CriticAxis.STRUCTURE)
    ctx = CriticContext(rag_refs=rag_refs or ["<self-compare>"], genre=None)
    wins = losses = ties = 0
    for a, b in zip(after_scenes, before_scenes):
        a_text = _scene_get(a, "draft") or ""
        b_text = _scene_get(b, "draft") or ""
        v = critic.evaluate(a_text, b_text, ctx)   # a=after, b=before
        if v.winner == "a":   wins += 1
        elif v.winner == "b": losses += 1
        else:                 ties += 1
    total = wins + losses + ties or 1
    loss_rate = round(losses / total, 4)
    return StructPair(loss_rate, round(1.0 - loss_rate, 4), wins, losses, ties,
                      passed=loss_rate <= PAIR_LOSS_MAX)


# ---------- R_path: 병리 비증가 ----------

def _pathology_penalty(scenes: Sequence[Any]) -> float:
    """씬 draft 전체의 병리 누적 감점(≤0). distribution_guard 재사용."""
    from literary_system.critic.distribution_guard import distribution_guard
    total = 0.0
    for s in scenes:
        draft = _scene_get(s, "draft") or ""
        total += distribution_guard(draft).penalty
    return round(total, 3)


@dataclass
class StructPath:
    before_penalty: float
    after_penalty: float
    passed: bool                # after_penalty >= before_penalty (병리 비증가)

    def to_dict(self) -> Dict[str, Any]:
        return {"before_penalty": self.before_penalty, "after_penalty": self.after_penalty,
                "passed": self.passed}


def r_path(before_scenes: Sequence[Any], after_scenes: Sequence[Any]) -> StructPath:
    bp = _pathology_penalty(before_scenes)
    ap = _pathology_penalty(after_scenes)
    return StructPath(bp, ap, passed=ap >= bp - 1e-9)


# ---------- 통합: c3 구조 비퇴행 판정 + winrate_gate 연동 스칼라 ----------

@dataclass
class StructuralNonRegression:
    r_before: float                 # before R_struct (winrate_gate c3 입력)
    r_after: float                  # after  R_struct
    struct_before: Dict[str, Any]
    struct_after: Dict[str, Any]
    pair: Dict[str, Any]
    path: Dict[str, Any]
    c3_struct: bool
    c3_pair: bool
    c3_path: bool
    passed: bool                    # 3성분 AND
    detail: str

    def to_dict(self) -> Dict[str, Any]:
        return {"r_before": self.r_before, "r_after": self.r_after,
                "struct_before": self.struct_before, "struct_after": self.struct_after,
                "pair": self.pair, "path": self.path,
                "c3_struct": self.c3_struct, "c3_pair": self.c3_pair, "c3_path": self.c3_path,
                "passed": self.passed, "detail": self.detail}


def structural_nonregression(before_scenes: Sequence[Any], after_scenes: Sequence[Any],
                             rag_refs: Optional[List[str]] = None,
                             critic: Optional[CriticInterface] = None,
                             r_tol: float = R_REGRESSION_TOL) -> StructuralNonRegression:
    """c3 = (R_struct 비퇴행) ∧ (R_pair 패배율≤0.5) ∧ (R_path 비증가).
    반환 r_before/r_after는 g_loopc_winrate(r_before=, r_after=)에 그대로 주입 가능."""
    sb = r_struct(before_scenes)
    sa = r_struct(after_scenes)
    pr = r_pair(before_scenes, after_scenes, rag_refs=rag_refs, critic=critic)
    pa = r_path(before_scenes, after_scenes)

    c3_struct = sa.r_struct >= sb.r_struct - r_tol
    c3_pair = pr.passed
    c3_path = pa.passed
    passed = c3_struct and c3_pair and c3_path

    notes = []
    if not c3_struct: notes.append(f"R_struct 퇴행 {sb.r_struct}->{sa.r_struct}")
    if not c3_pair:   notes.append(f"쌍대 패배율 {pr.loss_rate}>{PAIR_LOSS_MAX}")
    if not c3_path:   notes.append(f"병리 증가 {pa.before_penalty}->{pa.after_penalty}")
    detail = "구조 비퇴행 통과(3성분)" if passed else "구조 퇴행: " + ", ".join(notes)

    return StructuralNonRegression(
        r_before=sb.r_struct, r_after=sa.r_struct,
        struct_before=sb.to_dict(), struct_after=sa.to_dict(),
        pair=pr.to_dict(), path=pa.to_dict(),
        c3_struct=c3_struct, c3_pair=c3_pair, c3_path=c3_path,
        passed=passed, detail=detail)
