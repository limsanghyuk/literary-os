"""learning/pairing/builder.py — P0 선호쌍 빌더 오케스트레이터(fail-fast).

파이프라인: candidates → process(길이매칭→E4) → work-level split(held≥250)
            → ledger emit(I3 no-verbatim) → report. 어떤 단계가 보장 미달이면 즉시 실패.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

from .strategies.base import RawPair, PairVerdict, process_candidate, MIX, allocate
from .scoring import assert_no_sum, ALLOWED_SCHEME
from .splits import work_level_split, PairSplitResult, MIN_HELD
from .emit import ledger_rows, input_set_hash, assert_no_verbatim, write_ledger
from .report import build_report, BuildReport
from .tokenizer import Tokenizer, WhitespaceTokenizer, tokenizer_sha


@dataclass
class PairBuildResult:
    verdicts: List[PairVerdict]
    accepted: List[PairVerdict]
    split: PairSplitResult
    report: BuildReport
    ledger: List[dict]
    tokenizer_sha: str
    input_set_hash: str


def build(candidates: Sequence[RawPair],
          tokenizer: Optional[Tokenizer] = None,
          scheme: str = ALLOWED_SCHEME,
          min_held: int = MIN_HELD,
          ledger_path: Optional[str] = None) -> PairBuildResult:
    # I1 가드 1/3 — sum 진입 즉시 실패
    assert_no_sum(scheme)
    tok = tokenizer or WhitespaceTokenizer()

    verdicts = [process_candidate(c, tok) for c in candidates]
    accepted = [v for v in verdicts if v.accept]
    if not accepted:
        raise RuntimeError("fail-fast: 채택 쌍 0 — 길이매칭/E4가 전부 폐기")

    # 채택 쌍을 dict로 만들어 작품단위 분리(held≥250 보장; 미달 시 splits가 fail-fast)
    acc_dicts = [{"pair_id": v.pair_id, "work_id": v.work_id,
                  "strategy": v.strategy} for v in accepted]
    split = work_level_split(acc_dicts, min_held=min_held)

    tsha = tokenizer_sha(tok)
    ihash = input_set_hash(accepted)
    rows = ledger_rows(accepted, tsha, ihash)
    assert_no_verbatim(rows)            # I3 방어선
    if ledger_path:
        write_ledger(rows, ledger_path)

    rep = build_report(verdicts, held_count=len(split.held))
    return PairBuildResult(verdicts=verdicts, accepted=accepted, split=split,
                       report=rep, ledger=rows,
                       tokenizer_sha=tsha, input_set_hash=ihash)
