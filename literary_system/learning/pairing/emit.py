"""learning/pairing/emit.py — I3 no-verbatim ledger 방출.

산출물(ledger JSONL)에는 명작 원문 텍스트를 절대 포함하지 않는다. 통계·식별자·해시만
기록한다. logp/sumlogp는 GPU 학습에서 채워지는 자리(P0 시점 None 허용).
"""
from __future__ import annotations
import hashlib
import json
from typing import List, Sequence

from .strategies.base import PairVerdict


def input_set_hash(verdicts: Sequence[PairVerdict]) -> str:
    """채택 쌍 집합의 동결 해시(ablation 입력셋 고정용 — G2). pair_id 정렬 기반."""
    ids = sorted(v.pair_id for v in verdicts if v.accept)
    h = hashlib.sha256()
    for i in ids:
        h.update(i.encode("utf-8")); h.update(b"\x00")
    return h.hexdigest()[:16]


def ledger_rows(verdicts: Sequence[PairVerdict], tokenizer_sha: str,
                input_hash: str) -> List[dict]:
    """채택 쌍만 ledger 행으로. 텍스트 0 — n_tokens·식별자·해시만(I3)."""
    rows = []
    for v in verdicts:
        if not v.accept:
            continue
        rows.append({
            "pair_id": v.pair_id,
            "work_id": v.work_id,
            "strategy": v.strategy,
            "chosen_n_tokens": v.chosen_n_tokens,
            "rejected_n_tokens": v.rejected_n_tokens,
            "token_delta_ratio": round(v.length.token_delta_ratio, 6),
            "char_soft_flag": v.soft_flag,
            "e4_decision": v.e4_decision,
            # GPU 학습에서 채워질 자리(P0=None). per-token 전용.
            "chosen_sumlogp": None, "rejected_sumlogp": None,
            "tokenizer_sha": tokenizer_sha,
            "input_set_hash": input_hash,
            "scheme": "pertoken",
        })
    return rows


_HANGUL_RUN = None
def assert_no_verbatim(rows: Sequence[dict]) -> None:
    """방어선: ledger 행에 한글 연속 20자 이상(원문 누설 의심) 있으면 실패(I3)."""
    import re
    global _HANGUL_RUN
    if _HANGUL_RUN is None:
        _HANGUL_RUN = re.compile(r"[가-힣]{20,}")
    for r in rows:
        for k, val in r.items():
            if isinstance(val, str) and _HANGUL_RUN.search(val):
                raise ValueError(f"I3 위반: ledger 필드 {k!r}에 원문 의심 한글 연속")


def write_ledger(rows: Sequence[dict], path: str) -> int:
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return len(rows)
