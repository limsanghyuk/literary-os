"""
WP-1 (V747) — Formula Lifecycle Harness.

tools/formula_validation/harness.py 로직 승격 (경로 하드코딩 제거).
LLM 호출 0회 — 완전 로컬.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from literary_system.validation.formula_registry import REGISTRY, SceneRow
from literary_system.validation.stage_registry import STAGES


# ──────────────────────────────────────────────────────────────
# 결과 DTO
# ──────────────────────────────────────────────────────────────

@dataclass
class FormulaResult:
    formula_id:           str
    metric_name:          str
    value:                float
    n:                    int
    passed:               bool
    lifecycle_suggestion: str  # "promote"|"hold"|"recalibrate"|"deprecated_candidate"


@dataclass
class StageReport:
    stage_id:        int
    formula_results: List[FormulaResult] = field(default_factory=list)
    aborted:         bool = False
    abort_reason:    str  = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage_id":       self.stage_id,
            "aborted":        self.aborted,
            "abort_reason":   self.abort_reason,
            "formula_results": [
                {
                    "formula_id":           r.formula_id,
                    "metric_name":          r.metric_name,
                    "value":                round(r.value, 6),
                    "n":                    r.n,
                    "passed":               r.passed,
                    "lifecycle_suggestion": r.lifecycle_suggestion,
                }
                for r in self.formula_results
            ],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


# ──────────────────────────────────────────────────────────────
# 통계 유틸
# ──────────────────────────────────────────────────────────────

def _spearman(a: List[float], b: List[float]) -> float:
    n = len(a)
    if n < 2:
        return 0.0

    def rank(x: List[float]) -> List[float]:
        idx = sorted(range(n), key=lambda i: x[i])
        r = [0.0] * n
        for pos, i in enumerate(idx):
            r[i] = float(pos + 1)
        return r

    ra, rb = rank(a), rank(b)
    ma = sum(ra) / n
    mb = sum(rb) / n
    num = sum((ra[i] - ma) * (rb[i] - mb) for i in range(n))
    den = math.sqrt(
        sum((ra[i] - ma) ** 2 for i in range(n))
        * sum((rb[i] - mb) ** 2 for i in range(n))
    )
    return num / den if den > 0 else 0.0


def _lifecycle_suggestion(passed: bool) -> str:
    return "promote" if passed else "recalibrate"


# ──────────────────────────────────────────────────────────────
# Harness
# ──────────────────────────────────────────────────────────────

class Harness:
    """
    공식 생애주기 검증 Harness.

    사용 예::

        harness = Harness()
        report  = harness.run(stage_id=1, db_path="data/corpus_seed/scenes_5works.jsonl")
        print(report.to_json())
    """

    def __init__(self, registry: Optional[Dict[str, Any]] = None) -> None:
        self._registry: Dict[str, Any] = registry if registry is not None else REGISTRY

    # ------------------------------------------------------------------
    def run(
        self,
        stage_id:  int,
        db_path:   str,
        cost_cap:  float = 1.0,
    ) -> StageReport:
        """
        stage_id:  1~6 (STAGES 키)
        db_path:   SQLite 경로 또는 JSONL 폴백
        cost_cap:  비용 상한(USD) — 현재 순수 로컬이므로 0.0 소비; 미래 LLM 확장 대비
        """
        report = StageReport(stage_id=stage_id)

        if stage_id not in STAGES:
            report.aborted = True
            report.abort_reason = f"stage_id={stage_id} 미정의 (STAGES 범위: 1~6)"
            return report

        stage_cfg   = STAGES[stage_id]
        tau         = stage_cfg["tau"]
        min_n       = stage_cfg.get("min_n", 1)
        metric_name = stage_cfg["metric"]
        gt_field    = stage_cfg["gt"]

        # 비용 상한 사전 확인 (현재 로컬 → 0.0)
        current_cost = 0.0
        if current_cost > cost_cap:  # pragma: no cover
            report.aborted = True
            report.abort_reason = f"cost_cap {cost_cap:.2f} 초과 ({current_cost:.2f})"
            return report

        rows = self._load_rows(db_path, gt_field)
        if not rows:
            report.aborted = True
            report.abort_reason = f"씬 데이터 미발견 (db_path={db_path!r})"
            return report

        for fid, entry in self._registry.items():
            if entry.get("lifecycle") == "deprecated":
                continue

            scores = [entry["score_fn"](r) for r in rows]
            gt     = [float(r.get(gt_field, 0.5)) for r in rows]
            n      = len(scores)

            if metric_name == "spearman":
                value = _spearman(scores, gt)
            else:
                # f1, dtw_pct 등 — 데이터 도착 시 확장
                value = 0.0

            passed = (n >= min_n) and (value >= tau)
            report.formula_results.append(
                FormulaResult(
                    formula_id           = fid,
                    metric_name          = metric_name,
                    value                = value,
                    n                    = n,
                    passed               = passed,
                    lifecycle_suggestion = _lifecycle_suggestion(passed),
                )
            )

        return report

    # ------------------------------------------------------------------
    @staticmethod
    def _load_rows(db_path: str, gt_field: str) -> List[SceneRow]:
        """SQLite 또는 JSONL 폴백으로 씬 행 반환 (최대 5,000행)."""
        p = Path(db_path)
        if not p.exists():
            return []

        if p.suffix in (".jsonl", ".json"):
            rows: List[SceneRow] = []
            with open(p, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        if "scenes" in obj:
                            rows.extend(obj["scenes"])
                        else:
                            rows.append(obj)
                    except json.JSONDecodeError:
                        pass
            return rows

        # SQLite
        try:
            import sqlite3
            con = sqlite3.connect(str(p))
            con.row_factory = sqlite3.Row
            cur = con.execute("SELECT * FROM scene_feature LIMIT 5000")
            result = [dict(r) for r in cur.fetchall()]
            con.close()
            return result
        except Exception:
            return []
