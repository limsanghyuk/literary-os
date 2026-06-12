#!/usr/bin/env python3
"""
WP-1 (V747) — Formula Validation CLI

사용법:
    python tools/run_formula_validation.py --stage 1 --db data/corpus_seed/scenes_5works.jsonl
    python tools/run_formula_validation.py --stage 1 --db data/tristore.db --cost-cap 0.5
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# repo root를 경로에 추가
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from literary_system.validation.formula_harness import Harness
from literary_system.validation.ledger import record, transition


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Literary OS — Formula Lifecycle Validation Runner (WP-1)"
    )
    parser.add_argument("--stage",    type=int, required=True, help="Stage ID (1~6)")
    parser.add_argument("--db",       type=str, required=True, help="SQLite 또는 JSONL 경로")
    parser.add_argument("--cost-cap", type=float, default=1.0, help="비용 상한 USD (기본 1.0)")
    parser.add_argument("--json",     action="store_true",     help="JSON 출력 모드")
    args = parser.parse_args()

    harness = Harness()
    report  = harness.run(stage_id=args.stage, db_path=args.db, cost_cap=args.cost_cap)

    if args.json:
        sys.stdout.write(report.to_json() + "\n")
        return 0

    if report.aborted:
        sys.stdout.write(f"[ABORT] stage={report.stage_id}: {report.abort_reason}\n")
        return 2

    passed_cnt  = sum(1 for r in report.formula_results if r.passed)
    total_cnt   = len(report.formula_results)

    sys.stdout.write(
        f"Stage {report.stage_id} 검증 완료: {passed_cnt}/{total_cnt} 공식 통과\n"
    )
    for r in report.formula_results:
        tag = "PASS" if r.passed else "FAIL"
        sys.stdout.write(
            f"  [{tag}] {r.formula_id:25s}  "
            f"{r.metric_name}={r.value:+.3f}  n={r.n:4d}  "
            f"→ {r.lifecycle_suggestion}\n"
        )

        # ledger 자동 기록
        event = f"stage{report.stage_id}:{tag.lower()}"
        record(r.formula_id, event, args.db)
        if not r.passed:
            transition(r.formula_id, "recalibrate")

    return 0 if passed_cnt == total_cnt else 1


if __name__ == "__main__":
    sys.exit(main())
