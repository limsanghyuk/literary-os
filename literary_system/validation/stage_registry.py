"""
WP-1 (V747) — Stage 임계값 사전등록 상수.

변경 시 별도 커밋 + 사유 의무화 (DEV_PROTOCOL §2).
임계값은 코드 상수 — 런타임 변경 불가.
"""
from __future__ import annotations

from typing import Any, Dict

# 사전등록 Stage 임계 (immutable in code)
STAGES: Dict[int, Dict[str, Any]] = {
    1: dict(gt="quality_proxy",  metric="spearman", tau=0.40, min_n=30),
    2: dict(gt="plant_payoff",   metric="spearman", tau=0.40, min_n=20),
    3: dict(gt="payoff_actual",  metric="f1",       tau=0.60, min_works=1),
    4: dict(gt="panel_median",   metric="spearman", tau=0.40, min_n=30),
    5: dict(gt="labeled_curves", metric="dtw_pct",  tau=0.30, min_works=2),
    6: dict(gt="blind_pref",     metric="spearman", tau=0.50, min_n=30),
}
