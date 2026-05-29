#!/usr/bin/env python3
"""
tools/measure_gate_time.py
V587 SP-β — 게이트 실행 시간 측정 도구 (ADR-046)

각 게이트의 실행 시간을 측정하여 CI 티어 배치의 근거 데이터를 생성한다.
결과는 JSON 파일로 저장되며, L0+L1 fast-path ≤ 30초 목표 달성 여부를 검증한다.

사용법:
  python tools/measure_gate_time.py                        # 전체 측정
  python tools/measure_gate_time.py --tier L0 L1          # L0+L1만 측정
  python tools/measure_gate_time.py --output docs/perf/gate_timings_v587.json
  python tools/measure_gate_time.py --quick                # L0+L1 fast-path만 측정

G32 준수: print() 금지 → sys.stdout.write() / logging 사용
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
import traceback
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


def _emit(msg: str = "") -> None:
    """stdout 헬퍼 (G32: print() 금지)."""
    sys.stdout.write(str(msg) + "\n")


def _err(msg: str = "") -> None:
    sys.stderr.write(str(msg) + "\n")


# ---------------------------------------------------------------------------
# 측정 로직
# ---------------------------------------------------------------------------

def measure_gates(tiers: Optional[List[str]] = None) -> Dict:
    """
    게이트 실행 시간 측정.

    Parameters
    ----------
    tiers : list[str] | None
        None = 전체 측정
        ['L0'] = L0만
        ['L0', 'L1'] = L0+L1

    Returns
    -------
    dict: 측정 결과 (gate_id → timing 정보)
    """
    from literary_system.gates.release_gate import GATES, _get_gate_tier

    results = {}
    tier_set = set(tiers) if tiers else None
    _tier_rank = {"L0": 0, "L1": 1, "L2": 2, "L3": 3}

    total_start = time.perf_counter()

    for gate_id, gate_name, gate_fn in GATES:
        gate_tier = _get_gate_tier(gate_id)

        # 티어 필터
        if tier_set is not None:
            max_rank = max(_tier_rank.get(t, 3) for t in tier_set)
            if _tier_rank.get(gate_tier, 2) > max_rank:
                continue

        t0 = time.perf_counter()
        passed = False
        error = None
        try:
            result = gate_fn()
            passed = result.get("pass", False)
        except Exception:
            error = traceback.format_exc()

        elapsed_ms = (time.perf_counter() - t0) * 1000

        results[gate_id] = {
            "name": gate_name,
            "tier": gate_tier,
            "passed": passed,
            "elapsed_ms": round(elapsed_ms, 2),
            **({"error": error} if error else {}),
        }

        status = "✅" if passed else "❌"
        _emit(f"  {status} [{gate_tier}] {gate_id}: {elapsed_ms:.1f}ms")

    total_elapsed = (time.perf_counter() - total_start) * 1000
    return {
        "tiers_measured": list(tier_set) if tier_set else ["ALL"],
        "total_elapsed_ms": round(total_elapsed, 2),
        "gate_count": len(results),
        "gates": results,
    }


def analyze_results(data: Dict) -> Dict:
    """측정 결과 분석 — 티어별 통계 + L0+L1 목표 달성 여부."""
    gates = data["gates"]

    tier_stats: Dict[str, Dict] = {}
    for gate_id, info in gates.items():
        tier = info["tier"]
        if tier not in tier_stats:
            tier_stats[tier] = {"count": 0, "total_ms": 0.0, "max_ms": 0.0, "gates": []}
        tier_stats[tier]["count"] += 1
        tier_stats[tier]["total_ms"] += info["elapsed_ms"]
        tier_stats[tier]["max_ms"] = max(tier_stats[tier]["max_ms"], info["elapsed_ms"])
        tier_stats[tier]["gates"].append(gate_id)

    # L0+L1 합산
    l0_ms = tier_stats.get("L0", {}).get("total_ms", 0.0)
    l1_ms = tier_stats.get("L1", {}).get("total_ms", 0.0)
    l0_l1_total = l0_ms + l1_ms
    l0_l1_target = 30_000.0  # 30초
    l0_l1_pass = l0_l1_total <= l0_l1_target

    # 상위 5개 느린 게이트
    sorted_gates = sorted(gates.items(), key=lambda x: x[1]["elapsed_ms"], reverse=True)
    top5_slowest = [
        {"gate_id": k, "tier": v["tier"], "elapsed_ms": v["elapsed_ms"]}
        for k, v in sorted_gates[:5]
    ]

    return {
        "tier_stats": {
            tier: {
                "count": s["count"],
                "total_ms": round(s["total_ms"], 2),
                "avg_ms": round(s["total_ms"] / s["count"], 2) if s["count"] else 0,
                "max_ms": round(s["max_ms"], 2),
            }
            for tier, s in tier_stats.items()
        },
        "l0_l1_total_ms": round(l0_l1_total, 2),
        "l0_l1_target_ms": l0_l1_target,
        "l0_l1_pass": l0_l1_pass,
        "top5_slowest_gates": top5_slowest,
    }


def save_report(data: Dict, analysis: Dict, output_path: str) -> None:
    """결과 JSON 저장."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    report = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "version": "V587",
        "measurement": data,
        "analysis": analysis,
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    _emit(f"\n📄 결과 저장: {output_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="measure_gate_time",
        description="Literary OS 게이트 실행 시간 측정 (V587 SP-β, ADR-046)",
    )
    p.add_argument(
        "--tier", nargs="+", choices=["L0", "L1", "L2", "L3"],
        help="측정할 티어 (기본: 전체)",
    )
    p.add_argument(
        "--quick", action="store_true",
        help="L0+L1 fast-path만 측정 (--tier L0 L1 단축키)",
    )
    p.add_argument(
        "--output", default="docs/perf/gate_timings_v587.json",
        help="출력 JSON 경로 (기본: docs/perf/gate_timings_v587.json)",
    )
    p.add_argument(
        "--no-save", action="store_true",
        help="JSON 저장 없이 콘솔 출력만",
    )
    return p


def main(argv=None):
    logging.basicConfig(level=logging.WARNING)
    parser = build_parser()
    args = parser.parse_args(argv)

    tiers = args.tier
    if args.quick:
        tiers = ["L0", "L1"]

    tier_label = "+".join(sorted(tiers)) if tiers else "ALL"
    _emit(f"\n🔬 Literary OS 게이트 시간 측정 — 티어: {tier_label}")
    _emit("=" * 60)

    # 측정
    data = measure_gates(tiers=tiers)

    # 분석
    analysis = analyze_results(data)

    # 요약 출력
    _emit("\n📊 티어별 통계:")
    for tier in ["L0", "L1", "L2", "L3"]:
        s = analysis["tier_stats"].get(tier)
        if s:
            _emit(f"  {tier}: {s['count']}개 게이트, 총 {s['total_ms']:.1f}ms, "
                  f"평균 {s['avg_ms']:.1f}ms, 최대 {s['max_ms']:.1f}ms")

    l0l1_status = "✅ PASS" if analysis["l0_l1_pass"] else "❌ FAIL"
    _emit(f"\n⚡ L0+L1 fast-path: {analysis['l0_l1_total_ms']:.1f}ms "
          f"/ 목표 {analysis['l0_l1_target_ms']:.0f}ms → {l0l1_status}")

    _emit("\n🐌 상위 5 느린 게이트:")
    for g in analysis["top5_slowest_gates"]:
        _emit(f"  [{g['tier']}] {g['gate_id']}: {g['elapsed_ms']:.1f}ms")

    _emit(f"\n전체 측정 시간: {data['total_elapsed_ms']:.1f}ms ({data['gate_count']}개 게이트)")

    # 저장
    if not args.no_save:
        save_report(data, analysis, args.output)

    # 종료 코드: L0+L1 목표 미달 시 실패
    if tiers and set(tiers) <= {"L0", "L1"} and not analysis["l0_l1_pass"]:
        _err(f"\n⛔ L0+L1 fast-path {analysis['l0_l1_total_ms']:.0f}ms > 30,000ms 목표 미달")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
