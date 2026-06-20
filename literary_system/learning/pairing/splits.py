"""learning/pairing/splits.py — I4 작품단위 train/held 분리.

같은 작품(work_id)의 씬이 train/held에 동시 출현하면 누설(leak)이다. 작품 전체를
한쪽에만 배정하고, held 쌍 수 ≥ MIN_HELD를 보장한다. 결정론(seed 정렬).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Sequence

MIN_HELD = 250


class LeakError(RuntimeError):
    """train/held에 동일 work_id가 동시 출현(I4 위반)."""


@dataclass(frozen=True)
class SplitResult:
    train: List[dict]
    held: List[dict]
    held_works: List[str]
    train_works: List[str]

    def assert_no_leak(self) -> None:
        overlap = set(self.train_works) & set(self.held_works)
        if overlap:
            raise LeakError(f"work_id leak across train/held: {sorted(overlap)}")


def work_level_split(pairs: Sequence[dict], min_held: int = MIN_HELD,
                     work_key: str = "work_id") -> SplitResult:
    """작품 단위로 held를 채운다. 작품을 work_id 정렬 순서로 held에 누적,
    held 쌍 수 ≥ min_held가 되면 나머지를 train으로. held가 끝내 부족하면 fail-fast."""
    by_work: Dict[str, List[dict]] = {}
    for p in pairs:
        by_work.setdefault(str(p.get(work_key, "")), []).append(dict(p))

    works_sorted = sorted(by_work.keys())
    held: List[dict] = []
    held_works: List[str] = []
    train: List[dict] = []
    train_works: List[str] = []

    for w in works_sorted:
        if len(held) < min_held:
            held.extend(by_work[w]); held_works.append(w)
        else:
            train.extend(by_work[w]); train_works.append(w)

    if len(held) < min_held:
        raise RuntimeError(
            f"held shortfall: {len(held)} < min_held={min_held} "
            f"(전체 {len(pairs)}쌍/{len(works_sorted)}작품으로 부족 — 입력 확대 필요)")

    res = SplitResult(train=train, held=held,
                      held_works=held_works, train_works=train_works)
    res.assert_no_leak()
    return res
