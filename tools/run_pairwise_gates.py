"""
run_pairwise_gates.py — G_PAIRWISE_REGRESSION + G_TRANSITIVITY 게이트 (ADR-211, V749)

사용법:
    python tools/run_pairwise_gates.py [--json] [--db PATH]

종료 코드:
    0 — 두 게이트 모두 PASS
    1 — 하나 이상 FAIL
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock

# ── 경로 설정 ──────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from literary_system.validation.pairwise import (
    PairwiseJudgment,
    bt_scores,
    compare,
    transitivity_check,
)
from literary_system.validation.pairwise_fixtures import (
    REGRESSION_MIN_WIN_RATE,
    REGRESSION_PAIRS,
)


# ── G_PAIRWISE_REGRESSION ─────────────────────────────────────────────────────

def _run_regression(
    db: Any,
    judge_fn=None,
    cost_cap: float = 1.0,
) -> Dict[str, Any]:
    """
    명작 vs 강열화 11쌍 판정.
    judge_fn: (a_id, b_id, db) -> Literal["left","right"] — 테스트 오버라이드용.
    실 운영에서는 pairwise.compare() 사용.
    """
    wins = 0
    judgments: List[PairwiseJudgment] = []

    for canonical_id, degraded_id in REGRESSION_PAIRS:
        if judge_fn is not None:
            winner = judge_fn(canonical_id, degraded_id, db)
            j: PairwiseJudgment = {
                "pair_id": f"{canonical_id}_vs_{degraded_id}",
                "left_id": canonical_id,
                "right_id": degraded_id,
                "winner": winner,
                "mode": "preference",
                "trait": None,
                "rationale": "fixture_judge",
                "judge_id": "fixture",
                "position_seed": 0,
            }
        else:
            j = compare(
                canonical_id,
                degraded_id,
                db=db,
                mode="preference",
                cost_cap=cost_cap / len(REGRESSION_PAIRS),
            )

        judgments.append(j)
        if j["winner"] == "left":
            wins += 1

    win_rate = wins / len(REGRESSION_PAIRS)
    passed = win_rate >= REGRESSION_MIN_WIN_RATE

    return {
        "gate": "G_PAIRWISE_REGRESSION",
        "pass": passed,
        "wins": wins,
        "total": len(REGRESSION_PAIRS),
        "win_rate": round(win_rate, 4),
        "threshold": REGRESSION_MIN_WIN_RATE,
        "judgments": judgments,
    }


# ── G_TRANSITIVITY ────────────────────────────────────────────────────────────

_TRANSITIVITY_MAX_CYCLE_RATE: float = 0.05  # < 5%


def _run_transitivity(
    judgments: List[PairwiseJudgment],
) -> Dict[str, Any]:
    """판정 결과 집합에 대해 cycle rate 검사."""
    if not judgments:
        return {
            "gate": "G_TRANSITIVITY",
            "pass": True,
            "cycle_rate": 0.0,
            "threshold": _TRANSITIVITY_MAX_CYCLE_RATE,
            "note": "no judgments — trivially transitive",
        }

    rate = transitivity_check(judgments)
    passed = rate < _TRANSITIVITY_MAX_CYCLE_RATE

    return {
        "gate": "G_TRANSITIVITY",
        "pass": passed,
        "cycle_rate": round(rate, 4),
        "threshold": _TRANSITIVITY_MAX_CYCLE_RATE,
    }


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="WP-4b pairwise gates (ADR-211)")
    parser.add_argument("--json", action="store_true", help="JSON 출력")
    parser.add_argument("--db", default=":memory:", help="씬 DB 경로 (SQLite)")
    parser.add_argument("--cost-cap", type=float, default=1.0)
    args = parser.parse_args()

    # 실 운영: db 연결 후 compare() 호출
    # 여기서는 structural 검증만 수행 (실 DB 없을 때 mock DB)
    db = args.db  # pairwise.compare()는 db를 투과 전달

    reg = _run_regression(db=db, cost_cap=args.cost_cap)
    trans = _run_transitivity(reg["judgments"])

    results = {
        "G_PAIRWISE_REGRESSION": reg,
        "G_TRANSITIVITY": trans,
        "overall_pass": reg["pass"] and trans["pass"],
    }

    if args.json:
        sys.stdout.write(json.dumps(results, indent=2) + "\n")
    else:
        for name, r in [("G_PAIRWISE_REGRESSION", reg), ("G_TRANSITIVITY", trans)]:
            status = "✅ PASS" if r["pass"] else "❌ FAIL"
            sys.stdout.write(f"{status} {name}\n")
            for k, v in r.items():
                if k not in ("pass", "gate", "judgments"):
                    sys.stdout.write(f"  {k}: {v}\n")
        overall = "✅ ALL PASS" if results["overall_pass"] else "❌ GATE FAIL"
        sys.stdout.write(f"\n{overall}\n")

    return 0 if results["overall_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
