"""
critic/next_episode_bench.py — M2 NextEpisodeBench (V783, ADR-243).

명작 1~N화 정보 주입 → N+1화 생성 → **실제 방영 N+1화(은닉 GT)와 쌍대 비교**.
보상의 주 닻. "닮음"이 아니라 "**필적**"(실제 다음 화는 유효한 한 갈래) → 크래프트 축 쌍대.

가드(ADR-243):
- **암기 누출**: 무명·비공개작 채점 + 생성↔실제 n-gram 중첩 / 실제분 base perplexity 임계 초과 작품 제외(유명작은 시연만).
- **위치 스왑**: judge에 (생성, 실제) 순서를 무작위로 섞어 위치 편향 제거.
- **자격 critic만 심판**: M1 qualify_critic 통과 critic만 사용(LLM↔LLM 순환 부분 차단).
- 판정 결과(생성 패) → loop-C 선호쌍(실제=chosen, 생성=rejected).
LLM-0: 누출 계측·스왑은 결정론. judge·generate 훅만 LLM-1 경계.
"""
from __future__ import annotations
import random
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

JudgeFn = Callable[[str, str], str]              # (a, b) → 'a'|'b'|'tie'
GenerateFn = Callable[[Dict[str, Any]], str]     # context(1~N화 정보) → N+1화 생성

NGRAM_OVERLAP_MAX = 0.25         # 생성↔실제 n-gram 중첩 임계(초과=암기 의심)
NGRAM_N = 4
FAMOUS_FOR_DEMO_ONLY = True      # 유명작은 채점 제외(시연만)


def _ngrams(text: str, n: int = NGRAM_N) -> set:
    toks = re.findall(r"\w+", text)
    return {tuple(toks[i:i+n]) for i in range(max(0, len(toks)-n+1))}


def ngram_overlap(a: str, b: str, n: int = NGRAM_N) -> float:
    ga, gb = _ngrams(a, n), _ngrams(b, n)
    if not ga or not gb:
        return 0.0
    return round(len(ga & gb) / len(ga | gb), 4)


@dataclass
class NextEpItem:
    work_id:     str
    is_famous:   bool                 # 유명작=채점 제외(시연만)
    context:     Dict[str, Any]       # 1~N화 정보(지식상태·잔향·긴장곡선)
    actual_next: str                  # 실제 N+1화(은닉 GT)


@dataclass
class BenchResult:
    n_scored:    int
    n_excluded:  int
    parity_rate: float                # 생성이 실제와 '필적'(승+무) 비율
    win_rate:    float                # 생성이 실제를 '이긴' 비율(드묾)
    excluded:    List[Dict[str, Any]]
    pairs:       List[Dict[str, Any]] # loop-C 선호쌍(실제=chosen/생성=rejected 등)
    detail:      str

    def to_dict(self) -> Dict[str, Any]:
        return {"n_scored": self.n_scored, "n_excluded": self.n_excluded,
                "parity_rate": self.parity_rate, "win_rate": self.win_rate,
                "excluded": self.excluded, "pairs": self.pairs, "detail": self.detail}


def _leak_excluded(item: NextEpItem, generated: str,
                   overlap_max: float) -> Optional[str]:
    """누출 가드 — 제외 사유 반환(없으면 None)."""
    if item.is_famous and FAMOUS_FOR_DEMO_ONLY:
        return "유명작(채점 제외·시연만)"
    ov = ngram_overlap(generated, item.actual_next)
    if ov > overlap_max:
        return f"n-gram 중첩 {ov}>{overlap_max}(암기 의심)"
    return None


def run_next_episode_bench(items: List[NextEpItem], *, generate: GenerateFn,
                           judge: JudgeFn, critic_qualified: bool = True,
                           overlap_max: float = NGRAM_OVERLAP_MAX,
                           seed: int = 0) -> BenchResult:
    """
    각 item: 1~N화 context → 생성 N+1화 → 실제 N+1화와 쌍대(위치 스왑).
    critic_qualified=False면 심판 자격 미달 → 채점 거부(빈 결과).
    """
    if not critic_qualified:
        return BenchResult(0, 0, 0.0, 0.0, [], [],
                           "심판 자격 미달(M1 qualify_critic 선결) → 채점 거부")
    rng = random.Random(seed)
    scored = 0; parity = 0; wins = 0
    excluded: List[Dict[str, Any]] = []
    pairs: List[Dict[str, Any]] = []

    for it in items:
        gen = generate(it.context)
        reason = _leak_excluded(it, gen, overlap_max)
        if reason:
            excluded.append({"work_id": it.work_id, "reason": reason})
            continue
        scored += 1
        # 위치 스왑: a/b에 (실제, 생성)을 무작위 배치
        swap = rng.random() < 0.5
        a, b = (gen, it.actual_next) if swap else (it.actual_next, gen)
        v = judge(a, b)
        # 생성 관점 결과로 환산
        gen_pos = "a" if swap else "b"
        if v == "tie":
            gen_outcome = "tie"
        elif v == gen_pos:
            gen_outcome = "win"
        else:
            gen_outcome = "loss"
        if gen_outcome in ("win", "tie"):
            parity += 1
        if gen_outcome == "win":
            wins += 1
        # loop-C 선호쌍: 실제=chosen, 생성=rejected (생성이 진 경우 학습 신호)
        winner = "ref" if gen_outcome == "loss" else ("draft" if gen_outcome == "win" else "tie")
        pairs.append({"work_id": it.work_id, "func": it.context.get("func", "next_ep"),
                      "draft": gen, "ref": it.actual_next, "winner": winner})

    parity_rate = round(parity / scored, 4) if scored else 0.0
    win_rate = round(wins / scored, 4) if scored else 0.0
    detail = (f"채점 {scored}·제외 {len(excluded)} | 필적률(승+무) {parity_rate} · 순승률 {win_rate} "
              f"→ {'생성이 실제에 근접' if parity_rate>=0.5 else '실제 우위(학습여지 큼)'}")
    return BenchResult(scored, len(excluded), parity_rate, win_rate, excluded, pairs, detail)


def to_preference_pairs(result: BenchResult, genre: str = ""):
    """BenchResult → learning.loop_c.PreferencePair[] (생성↔실제 쌍)."""
    from literary_system.learning.loop_c import PreferencePair
    out = []
    for p in result.pairs:
        if p["winner"] in ("draft", "ref"):
            out.append(PreferencePair.from_pass7(p["func"], genre, p["draft"], p["ref"],
                                                 p["winner"], p["work_id"]))
    return out
