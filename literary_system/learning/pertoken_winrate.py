"""learning/pertoken_winrate.py — Per-token(길이정규화) 승률 측정 코어 (DESIGN-SGATE-v1, ③).

배경(Round#2 confound): 보고된 W1=0.357은 sumlogP(누적 logπ) 기반이며 **길이 미정규화**다.
held 쌍에서 ref(~415자) < draft(~597자)로, 긴 시퀀스일수록 누적 logp가 더 음수가 되어
'짧은 ref가 유리'한 길이 편향이 W에 섞인다. per-token(logp/토큰수) 정규화로 이 편향을 분리한다.

GPU 불필요: 실제 토큰 logp는 집/GPU 학습에서 생성된 ledger(JSONL)를 **소비**한다. 본 모듈은
순수한 집계·정규화·진단 코어로, 단위 테스트가 가능하다(외부 의존 없음).

핵심 구분
- scheme="sum"     : raw 누적 logp 비교(= Round#2가 쓴 방식, 길이 편향 포함)
- scheme="pertoken": logp/토큰수 비교(길이 편향 제거)
두 스킴의 W를 함께 산출해 'W의 어느 부분이 길이 인공물인가'를 가시화한다.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Sequence

EPS_TIE = 1e-9          # per-token logp 차이가 이 미만이면 무승부


@dataclass(frozen=True)
class SideScore:
    """한 쪽(draft 또는 ref)의 logp와 토큰수. logp는 음수(로그확률 합)."""
    sumlogp: float
    n_tokens: int

    @property
    def per_token(self) -> float:
        return self.sumlogp / max(self.n_tokens, 1)


def per_token_logp(sumlogp: float, n_tokens: int) -> float:
    """길이정규화 logp = sumlogp / max(n_tokens,1). 순수 함수."""
    return sumlogp / max(int(n_tokens), 1)


def pairwise_winner(draft: SideScore, ref: SideScore,
                    scheme: str = "pertoken", eps: float = EPS_TIE) -> str:
    """더 높은(덜 음수인) logp를 받은 쪽이 승. 반환 ∈ {'draft','ref','tie'}.
    scheme='sum'은 누적 logp, 'pertoken'은 토큰당 logp로 비교."""
    if scheme == "sum":
        da, ra = float(draft.sumlogp), float(ref.sumlogp)
    elif scheme == "pertoken":
        da, ra = draft.per_token, ref.per_token
    else:
        raise ValueError(f"unknown scheme: {scheme!r}")
    if abs(da - ra) <= eps:
        return "tie"
    return "draft" if da > ra else "ref"


def win_rate(rows: Sequence[Dict], scheme: str = "pertoken",
             target: str = "draft", eps: float = EPS_TIE) -> float:
    """rows: [{'draft':{'sumlogp','n_tokens'}, 'ref':{...}}] 형태. target 승률(0~1).
    무승부는 0.5로 가산(BT 관례)."""
    n = len(rows)
    if not n:
        return 0.0
    s = 0.0
    for r in rows:
        d = SideScore(float(r["draft"]["sumlogp"]), int(r["draft"]["n_tokens"]))
        f = SideScore(float(r["ref"]["sumlogp"]), int(r["ref"]["n_tokens"]))
        w = pairwise_winner(d, f, scheme=scheme, eps=eps)
        if w == target:
            s += 1.0
        elif w == "tie":
            s += 0.5
    return round(s / n, 4)


# ── 길이 편향 진단(텍스트만으로, GPU/logp 불필요) ──────────────────────────────

def char_len(text: str) -> int:
    return len(text or "")


def ws_token_len(text: str) -> int:
    """공백 분할 토큰 수(언어 무관 거친 프록시)."""
    return len((text or "").split())


@dataclass(frozen=True)
class LengthDiag:
    n: int
    draft_mean: float
    ref_mean: float
    draft_minus_ref: float          # 양수면 draft가 더 긺(짧은 ref가 sum-logp상 유리)
    null_winrate_shorter: float     # '더 짧은 쪽을 승자로' 했을 때 ref 승률(=길이만의 설명력)
    measure: str

    def to_dict(self) -> Dict:
        return {"n": self.n, "draft_mean": self.draft_mean, "ref_mean": self.ref_mean,
                "draft_minus_ref": self.draft_minus_ref,
                "null_winrate_shorter": self.null_winrate_shorter, "measure": self.measure}


def length_diagnostic(pairs: Sequence[Dict],
                      length_fn: Callable[[str], int] = char_len,
                      draft_key: str = "draft", ref_key: str = "ref") -> LengthDiag:
    """draft/ref 텍스트 길이 비대칭과 '짧은 쪽=승자' 귀무모형 승률을 계산.
    null_winrate_shorter가 관측 W(ref 우세)와 비슷하면 W가 길이 인공물일 위험이 큼."""
    n = len(pairs)
    if not n:
        return LengthDiag(0, 0.0, 0.0, 0.0, 0.0, length_fn.__name__)
    dl = [length_fn(p.get(draft_key, "")) for p in pairs]
    rl = [length_fn(p.get(ref_key, "")) for p in pairs]
    dm, rm = sum(dl) / n, sum(rl) / n
    # ref가 더 짧으면(=draft가 더 긺) 귀무모형은 ref를 승자로 찍음
    ref_shorter = sum(1.0 for d, r in zip(dl, rl) if r < d) + \
                  0.5 * sum(1.0 for d, r in zip(dl, rl) if r == d)
    return LengthDiag(n, round(dm, 2), round(rm, 2), round(dm - rm, 2),
                      round(ref_shorter / n, 4), length_fn.__name__)


__all__ = ["SideScore", "per_token_logp", "pairwise_winner", "win_rate",
           "char_len", "ws_token_len", "LengthDiag", "length_diagnostic", "EPS_TIE"]
