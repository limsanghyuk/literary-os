"""learning/pairing/scoring.py — I1 per-token 전용 채점 + sum 3중 차단(가드 1/3).

sum-logp는 길이 confound이므로 본 빌더에서 금지한다. 차단 3중:
 (1) 함수 가드: assert_no_sum() — 본 모듈(런타임)
 (2) CLI 거부 플래그: builder CLI가 --scheme sum 거부
 (3) pre-commit 정적검사: scheme="sum" 리터럴 차단(레포 훅)
"""
from __future__ import annotations
from literary_system.learning.pertoken_winrate import SideScore, pairwise_winner

ALLOWED_SCHEME = "pertoken"


def assert_no_sum(scheme: str) -> None:
    """sum 경로 진입 시 즉시 실패(가드 1/3)."""
    if scheme != ALLOWED_SCHEME:
        raise ValueError(
            f"I1 위반: 채점 스킴은 '{ALLOWED_SCHEME}'만 허용(요청={scheme!r}). "
            f"sum-logp는 길이 confound이므로 금지(Round#2 ROLLBACK 근거).")


def winner_pertoken(chosen: SideScore, rejected: SideScore) -> str:
    """per-token logp로만 승자 판정. 반환 ∈ {'chosen','rejected','tie'}."""
    assert_no_sum(ALLOWED_SCHEME)
    w = pairwise_winner(draft=chosen, ref=rejected, scheme=ALLOWED_SCHEME)
    return {"draft": "chosen", "ref": "rejected", "tie": "tie"}[w]
