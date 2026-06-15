"""
literary_system.validation.human_gt — 인간 GT(작가 평가) 운영 인프라 (V750, ADR-213)

설계: docs/sessions/2026-06-15_human_gt_protocol_L4_v1.md
원칙(LLM-0 / WP-4b 정합):
  - 절대 점수 금지 → 판정은 left/right/tie 만 (G_NO_ABSOLUTE_REWARD).
  - 레퍼런스 앵커는 DB scene_id 만 (LLM 회상 레퍼런스 금지).
  - 수집만, 학습 비실행 (InterventionEvent 적재는 Phase F).
게이트: G_HUMAN_GT_ALIGNMENT — 인간 평가자 간 α≥0.6 AND 패널-인간 일치율 보고.
"""
from __future__ import annotations

import random
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence

from literary_system.validation.pairwise import bt_scores, _load_scene_text
from literary_system.constitution.krippendorff_alpha import KrippendorffAlpha

HUMAN_GT_ALPHA_MIN: float = 0.6          # substantial agreement
GT_CHOICES = ("left", "right", "tie")
GT_QUESTIONS = ("preference", "trait", "canon_proximity")
_WINNER_CODE = {"left": 0.0, "right": 1.0, "tie": 0.5}


class GTMode(str, Enum):
    A_GEN_VS_REAL = "A"       # 생성 vs 실제 (생성기 품질)
    B_PRESTIGE_CALIB = "B"    # 명성차 실제 씬쌍 (평가자 캘리브레이션)
    C_ARBITRATION = "C"       # 공식↔인간 중재


@dataclass(frozen=True)
class GTPair:
    """평가 대상 쌍. 최소 한 쪽은 실제 DB 씬(앵커)이어야 한다."""
    pair_id: str
    left_id: str
    right_id: str
    mode: str
    left_is_real: bool
    right_is_real: bool
    question: str = "preference"
    genre: Optional[str] = None
    difficulty: Optional[str] = None      # "close"(박빙) | "wide"(격차)

    def __post_init__(self) -> None:
        if self.mode not in {m.value for m in GTMode}:
            raise ValueError(f"잘못된 mode: {self.mode}")
        if self.question not in GT_QUESTIONS:
            raise ValueError(f"잘못된 question: {self.question}")
        if not (self.left_is_real or self.right_is_real):
            raise ValueError(
                f"GT 앵커 없음: {self.pair_id} — 최소 한 쪽은 실제 DB 씬이어야 함")


@dataclass(frozen=True)
class GTRecord:
    """인간 1명의 1쌍 판정 (bt_scores 호환: winner/left_id/right_id)."""
    pair_id: str
    left_id: str
    right_id: str
    winner: str               # "left" | "right" | "tie"
    question: str
    evaluator_id: str
    mode: str
    ts: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        if self.winner not in GT_CHOICES:
            raise ValueError(f"winner는 {GT_CHOICES} 중 하나여야 함: {self.winner}")


def validate_anchor(pair: GTPair, db: Any) -> None:
    """실제(real) 앵커가 DB에 실재하는지 검증 — LLM 회상 레퍼런스 차단(WP-4 규칙)."""
    for sid, is_real in ((pair.left_id, pair.left_is_real),
                         (pair.right_id, pair.right_is_real)):
        if is_real and _load_scene_text(sid, db) is None:
            raise ValueError(
                f"실제 앵커 {sid}가 DB에 없음 — LLM 회상 레퍼런스 금지")


def build_blind_sheet(pairs: Sequence[GTPair], db: Any,
                      seed: Optional[int] = None) -> List[Dict[str, Any]]:
    """쌍 목록 → 블라인드 평가지(좌우 무작위·출처 은닉·DB 앵커 검증)."""
    rng = random.Random(seed)
    sheet: List[Dict[str, Any]] = []
    for p in pairs:
        validate_anchor(p, db)
        swap = rng.random() < 0.5
        a, b = (p.right_id, p.left_id) if swap else (p.left_id, p.right_id)
        sheet.append({
            "pair_id": p.pair_id, "A": a, "B": b, "swapped": swap,
            "question": p.question, "mode": p.mode,
        })
    return sheet


def record_from_sheet(sheet_row: Dict[str, Any], choice_ab: str,
                      evaluator_id: str) -> GTRecord:
    """평가지 응답(A/B/tie) → 원래 left/right 좌표로 역변환한 GTRecord."""
    if choice_ab not in ("A", "B", "tie"):
        raise ValueError("choice_ab는 A|B|tie 중 하나여야 함")
    swapped = bool(sheet_row["swapped"])
    A, B = sheet_row["A"], sheet_row["B"]
    left_id, right_id = (B, A) if swapped else (A, B)
    if choice_ab == "tie":
        winner = "tie"
    elif choice_ab == "A":
        winner = "right" if swapped else "left"
    else:  # "B"
        winner = "left" if swapped else "right"
    return GTRecord(
        pair_id=sheet_row["pair_id"], left_id=left_id, right_id=right_id,
        winner=winner, question=sheet_row["question"],
        evaluator_id=evaluator_id, mode=sheet_row["mode"])


def aggregate_winrate(records: Sequence[GTRecord]) -> Dict[str, float]:
    """쌍대 BT 점수 (tie 제외)."""
    nontie = [r for r in records if r.winner != "tie"]
    judgments = [{"left_id": r.left_id, "right_id": r.right_id, "winner": r.winner}
                 for r in nontie]
    return bt_scores(judgments) if judgments else {}


def majority_by_pair(records: Sequence[GTRecord]) -> Dict[str, str]:
    """쌍별 인간 다수결 winner."""
    byp: Dict[str, List[str]] = defaultdict(list)
    for r in records:
        byp[r.pair_id].append(r.winner)
    return {pid: Counter(ws).most_common(1)[0][0] for pid, ws in byp.items()}


def inter_rater_alpha(records: Sequence[GTRecord]):
    """평가자 간 Krippendorff α (nominal: left=0/right=1/tie=0.5)."""
    rater_data: Dict[str, Dict[str, Optional[float]]] = defaultdict(dict)
    for r in records:
        rater_data[r.evaluator_id][r.pair_id] = _WINNER_CODE[r.winner]
    return KrippendorffAlpha("nominal").compute(dict(rater_data))


def panel_alignment(human_records: Sequence[GTRecord],
                    panel_judgments: Sequence[Any]) -> Dict[str, Any]:
    """인간 쌍별 다수결 vs 패널(LLM) winner 일치율 — 패널 캘리브레이션 신호."""
    hmaj = majority_by_pair(human_records)
    pmap: Dict[str, str] = {}
    for j in panel_judgments:
        pid = j.get("pair_id") if isinstance(j, dict) else getattr(j, "pair_id", None)
        w = j["winner"] if isinstance(j, dict) else getattr(j, "winner", None)
        if pid and w:
            pmap[pid] = w
    common = [pid for pid in hmaj if pid in pmap and hmaj[pid] != "tie"]
    if not common:
        return {"n": 0, "alignment": 0.0}
    agree = sum(1 for pid in common if hmaj[pid] == pmap[pid])
    return {"n": len(common), "alignment": round(agree / len(common), 4)}


def run_g_human_gt_alignment(human_records: Sequence[GTRecord],
                             panel_judgments: Optional[Sequence[Any]] = None) -> Dict[str, Any]:
    """G_HUMAN_GT_ALIGNMENT: 평가자 간 α≥0.6 게이트 + 패널-인간 일치율 보고."""
    if not human_records:
        return {"gate": "G_HUMAN_GT_ALIGNMENT", "passed": False,
                "reason": "GT 레코드 없음", "alpha": 0.0}
    ar = inter_rater_alpha(human_records)
    align = panel_alignment(human_records, panel_judgments or [])
    passed = ar.alpha >= HUMAN_GT_ALPHA_MIN
    return {
        "gate": "G_HUMAN_GT_ALIGNMENT", "passed": passed,
        "alpha": round(ar.alpha, 4), "alpha_min": HUMAN_GT_ALPHA_MIN,
        "panel_alignment": align, "n_records": len(human_records),
        "summary": ar.summary,
    }
