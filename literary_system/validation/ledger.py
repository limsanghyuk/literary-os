"""
WP-1 (V747) — Formula Lifecycle Ledger.

record()  : docs/formula_ledger.md에 이벤트 append (커밋 대상)
transition(): 상태 전이 + 2회 연속 미달 → deprecated_candidate 자동 표기
"""
from __future__ import annotations

import datetime
from pathlib import Path
from typing import Dict, Optional

REPO_ROOT    = Path(__file__).resolve().parent.parent.parent
LEDGER_PATH  = REPO_ROOT / "docs" / "formula_ledger.md"

_VALID_STATES = frozenset(["candidate", "validated", "recalibrate", "deprecated"])

# ──────────────────────────────────────────────────────────────
# 세션 상태 (메모리 — 테스트 격리 가능)
# ──────────────────────────────────────────────────────────────
_state:             Dict[str, str] = {}
_consecutive_fails: Dict[str, int] = {}


def _load_state() -> None:
    """REGISTRY에서 초기 lifecycle 상태 로드 (지연 임포트)."""
    global _state, _consecutive_fails
    if not _state:
        from literary_system.validation.formula_registry import REGISTRY
        for fid, entry in REGISTRY.items():
            _state[fid]             = entry.get("lifecycle", "candidate")
            _consecutive_fails[fid] = 0


# ──────────────────────────────────────────────────────────────
# 공개 API
# ──────────────────────────────────────────────────────────────

def record(
    formula_id:    str,
    event:         str,
    evidence_path: str,
    ledger_path:   Optional[Path] = None,
) -> None:
    """
    공식 이벤트를 docs/formula_ledger.md에 append.
    ledger_path 지정 시 해당 경로 사용 (테스트용).
    """
    _load_state()
    target = ledger_path if ledger_path is not None else LEDGER_PATH
    ts     = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    state  = _state.get(formula_id, "unknown")
    line   = f"| {ts} | {formula_id} | {event} | {state} | {evidence_path} |\n"

    if not target.parent.exists():
        target.parent.mkdir(parents=True, exist_ok=True)

    if not target.exists():
        header = (
            "# Formula Lifecycle Ledger\n\n"
            "| timestamp | formula_id | event | lifecycle | evidence_path |\n"
            "|-----------|------------|-------|-----------|---------------|\n"
        )
        target.write_text(header, encoding="utf-8")

    with open(target, "a", encoding="utf-8") as f:
        f.write(line)


def transition(
    formula_id:  str,
    new_state:   str,
    ledger_path: Optional[Path] = None,
) -> str:
    """
    lifecycle 상태 전이.

    규칙:
      - recalibrate 2회 연속 → deprecated 자동 승격
      - deprecated → deprecated (terminal state)
      - 전이 이벤트를 ledger에 자동 기록

    반환: 실제 적용된 new_state (2회 미달 시 "deprecated" 가능)
    """
    _load_state()
    old = _state.get(formula_id, "candidate")

    if old == "deprecated":
        return "deprecated"

    effective = new_state
    if new_state == "recalibrate":
        _consecutive_fails[formula_id] = _consecutive_fails.get(formula_id, 0) + 1
        if _consecutive_fails[formula_id] >= 2:
            effective = "deprecated"
    else:
        _consecutive_fails[formula_id] = 0

    _state[formula_id] = effective
    record(formula_id, f"transition:{old}->{effective}", "auto", ledger_path=ledger_path)
    return effective


def get_lifecycle(formula_id: str) -> str:
    """현재 lifecycle 상태 반환."""
    _load_state()
    return _state.get(formula_id, "candidate")


def reset_for_test() -> None:
    """테스트 격리용 전역 상태 초기화."""
    global _state, _consecutive_fails
    _state             = {}
    _consecutive_fails = {}
