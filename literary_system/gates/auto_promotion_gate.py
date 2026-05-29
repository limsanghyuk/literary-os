"""
auto_promotion_gate.py — AutoPromotionGate G62 (V635, ADR-077)

SP-C.1 Self-Learning Loop의 자동 승격 게이트.
LoRA 모델이 VALIDATED → PROMOTED 상태로 자동 승격하기 위한 조건 검증.

조건:
  1. R(scene) ≥ R_THRESHOLD (0.78) — LOSConstitution 장면 품질 평균
  2. 롤백 횟수 = 0 (ConstitutionWeightTracker 이력 기준)

LLM-0 원칙 완전 준수 (외부 LLM 호출 없음)
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Sequence

# ─────────────────────────────────────────────
# 상수
# ─────────────────────────────────────────────
R_THRESHOLD: float = 0.78       # 최소 장면 품질 점수
MAX_ROLLBACKS: int = 0          # 허용 롤백 횟수 (0 = 롤백 없어야 함)
_DEFAULT_STORE: str = "data/losdb/auto_promotion_gate.jsonl"
_MEMORY_SENTINEL: str = ":memory:"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─────────────────────────────────────────────
# 결과 데이터클래스
# ─────────────────────────────────────────────
@dataclass
class GateResult:
    """AutoPromotionGate 단일 평가 결과."""
    result_id: str
    evaluated_at: str           # ISO-8601 UTC
    passed: bool                # G62 PASS 여부
    r_score: float              # 장면 품질 평균 점수
    rollback_count: int         # 평가 시점 롤백 횟수
    scene_count: int            # 평가된 장면 수
    reason: str                 # 판정 사유
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "result_id": self.result_id,
            "evaluated_at": self.evaluated_at,
            "passed": self.passed,
            "r_score": self.r_score,
            "rollback_count": self.rollback_count,
            "scene_count": self.scene_count,
            "reason": self.reason,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "GateResult":
        return cls(
            result_id=d["result_id"],
            evaluated_at=d["evaluated_at"],
            passed=bool(d["passed"]),
            r_score=float(d["r_score"]),
            rollback_count=int(d["rollback_count"]),
            scene_count=int(d["scene_count"]),
            reason=d["reason"],
            note=d.get("note", ""),
        )


# ─────────────────────────────────────────────
# AutoPromotionGate
# ─────────────────────────────────────────────
class AutoPromotionGate:
    """
    SP-C.1 자동 승격 게이트 — G62.

    Parameters
    ----------
    store_path : str
        JSONL 파일 경로. `:memory:` 이면 메모리 전용 모드.
    r_threshold : float
        장면 품질 최소 기준 (기본 0.78).
    max_rollbacks : int
        허용 롤백 횟수 (기본 0 — 롤백 없어야 승격 가능).
    """

    def __init__(
        self,
        store_path: str = _DEFAULT_STORE,
        r_threshold: float = R_THRESHOLD,
        max_rollbacks: int = MAX_ROLLBACKS,
    ) -> None:
        if not (0.0 < r_threshold <= 1.0):
            raise ValueError(
                f"r_threshold 는 (0, 1] 범위여야 합니다: {r_threshold}"
            )
        if max_rollbacks < 0:
            raise ValueError(
                f"max_rollbacks 는 0 이상이어야 합니다: {max_rollbacks}"
            )

        self._store_path = store_path
        self._r_threshold = r_threshold
        self._max_rollbacks = max_rollbacks
        self._results: List[GateResult] = []
        self._memory_mode = (store_path == _MEMORY_SENTINEL)

        if not self._memory_mode:
            self._load_from_file()

    # ── I/O ──
    def _load_from_file(self) -> None:
        p = Path(self._store_path)
        if not p.exists():
            return
        with p.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    self._results.append(GateResult.from_dict(json.loads(line)))

    def _append_to_file(self, result: GateResult) -> None:
        p = Path(self._store_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(result.to_dict(), ensure_ascii=False) + "\n")

    # ── 핵심 메서드 ──
    def evaluate(
        self,
        scene_scores: Sequence[float],
        rollback_count: int,
        note: str = "",
        now: Optional[datetime] = None,
    ) -> GateResult:
        """
        G62 게이트를 평가한다.

        Parameters
        ----------
        scene_scores : Sequence[float]
            장면별 LOSConstitution 품질 점수 목록 (0.0~1.0).
        rollback_count : int
            ConstitutionWeightTracker 기준 롤백 횟수.
        note : str
            자유 메모.
        now : datetime, optional
            평가 시각 (테스트용 주입).

        Returns
        -------
        GateResult

        Raises
        ------
        ValueError
            scene_scores 가 비어 있는 경우.
        """
        if not scene_scores:
            raise ValueError("scene_scores 가 비어 있습니다.")
        if rollback_count < 0:
            raise ValueError(f"rollback_count 는 0 이상이어야 합니다: {rollback_count}")

        ts = now if now is not None else datetime.now(timezone.utc)
        r_score = sum(scene_scores) / len(scene_scores)

        # 판정
        failures: List[str] = []
        _EPS = 1e-9
        if r_score < self._r_threshold - _EPS:
            failures.append(
                f"R={r_score:.4f} < threshold {self._r_threshold}"
            )
        if rollback_count > self._max_rollbacks:
            failures.append(
                f"rollback_count={rollback_count} > max {self._max_rollbacks}"
            )

        passed = len(failures) == 0
        if passed:
            reason = (
                f"G62 PASS — R={r_score:.4f} ≥ {self._r_threshold}, "
                f"rollbacks={rollback_count} ≤ {self._max_rollbacks}"
            )
        else:
            reason = "G62 FAIL — " + "; ".join(failures)

        result = GateResult(
            result_id=str(uuid.uuid4()),
            evaluated_at=ts.isoformat(),
            passed=passed,
            r_score=r_score,
            rollback_count=rollback_count,
            scene_count=len(scene_scores),
            reason=reason,
            note=note,
        )

        self._results.append(result)
        if not self._memory_mode:
            self._append_to_file(result)

        return result

    # ── 조회 ──
    def history(self) -> List[GateResult]:
        """전체 평가 이력 (오래된 순)."""
        return list(self._results)

    def last_result(self) -> Optional[GateResult]:
        """가장 최근 평가 결과. 없으면 None."""
        if not self._results:
            return None
        return self._results[-1]

    def count(self) -> int:
        """총 평가 횟수."""
        return len(self._results)

    def clear(self) -> None:
        """전체 이력 삭제."""
        self._results.clear()
        if not self._memory_mode:
            p = Path(self._store_path)
            if p.exists():
                p.unlink()

    @property
    def r_threshold(self) -> float:
        return self._r_threshold

    @property
    def max_rollbacks(self) -> int:
        return self._max_rollbacks


# ─────────────────────────────────────────────
# run_g62_gate — release_gate.py 통합용
# ─────────────────────────────────────────────
# G62 골든 장면 점수 (LOSConstitution 기준 검증된 샘플 — SP-C.1 기준선)
_G62_GOLDEN_SCENE_SCORES: List[float] = [
    0.82, 0.79, 0.85, 0.81, 0.83,   # 드라마 장면 5개
    0.80, 0.78, 0.84, 0.82, 0.80,   # 멜로 장면 5개
]
_G62_GOLDEN_ROLLBACK_COUNT: int = 0  # SP-C.1 기준선: 롤백 없음


def run_g62_gate() -> dict:
    """
    G62 게이트 실행 — release_gate.py 에서 호출.

    골든 장면 세트 10개를 사용하여 G62 조건을 검증한다:
    - R ≥ 0.78
    - 롤백 횟수 = 0

    Returns
    -------
    dict: gate_name, pass, passed, checkpoints, details
    """
    checkpoints = []
    errors: List[str] = []

    # CP-1: 모듈 임포트 검증
    try:
        from literary_system.gates.auto_promotion_gate import (
            AutoPromotionGate as _APG,
            GateResult as _GR,
            R_THRESHOLD as _RT,
            MAX_ROLLBACKS as _MR,
        )
        checkpoints.append("CP-1 AutoPromotionGate 임포트 성공")
    except Exception as e:
        errors.append(f"CP-1 임포트 실패: {e}")
        return {
            "gate_name": "AutoPromotionGate G62 — SP-C.1 자동 승격 (ADR-077)",
            "gate": "G62",
            "pass": False,
            "passed": False,
            "checkpoints": checkpoints,
            "errors": errors,
        }

    # CP-2: 상수 검증
    try:
        assert _RT == 0.78, f"R_THRESHOLD {_RT} ≠ 0.78"
        assert _MR == 0, f"MAX_ROLLBACKS {_MR} ≠ 0"
        checkpoints.append("CP-2 상수 R_THRESHOLD=0.78, MAX_ROLLBACKS=0 확인")
    except AssertionError as e:
        errors.append(f"CP-2 상수 오류: {e}")

    # CP-3: 공개 API 임포트 (constitution/__init__)
    try:
        from literary_system.constitution import (
            AutoPromotionGate as _APG2,
            GateResult as _GR2,
            R_THRESHOLD as _RT2,
            MAX_ROLLBACKS as _MR2,
        )
        checkpoints.append("CP-3 constitution.__init__ 공개 API 확인")
    except Exception as e:
        errors.append(f"CP-3 공개 API 오류: {e}")

    # CP-4: 골든셋 PASS 판정
    try:
        gate = _APG(store_path=_MEMORY_SENTINEL)
        result = gate.evaluate(
            scene_scores=_G62_GOLDEN_SCENE_SCORES,
            rollback_count=_G62_GOLDEN_ROLLBACK_COUNT,
            note="G62 release gate 골든셋",
        )
        if not result.passed:
            errors.append(f"CP-4 골든셋 FAIL: {result.reason}")
        else:
            checkpoints.append(
                f"CP-4 골든셋 PASS — R={result.r_score:.4f}, rollbacks=0"
            )
    except Exception as e:
        errors.append(f"CP-4 평가 오류: {e}")

    # CP-5: FAIL 케이스 판정 (R < 0.78)
    try:
        gate2 = _APG(store_path=_MEMORY_SENTINEL)
        r2 = gate2.evaluate(scene_scores=[0.60, 0.65, 0.70], rollback_count=0)
        assert not r2.passed, "R 미달 케이스가 PASS로 잘못 판정됨"
        checkpoints.append("CP-5 R 미달 FAIL 판정 정상")
    except Exception as e:
        errors.append(f"CP-5 FAIL 케이스 오류: {e}")

    # CP-6: 롤백 초과 FAIL 케이스
    try:
        gate3 = _APG(store_path=_MEMORY_SENTINEL)
        r3 = gate3.evaluate(scene_scores=[0.80, 0.82, 0.79], rollback_count=1)
        assert not r3.passed, "롤백 초과 케이스가 PASS로 잘못 판정됨"
        checkpoints.append("CP-6 롤백 초과 FAIL 판정 정상")
    except Exception as e:
        errors.append(f"CP-6 롤백 케이스 오류: {e}")

    # CP-7: GateResult 직렬화 검증
    try:
        gate4 = _APG(store_path=_MEMORY_SENTINEL)
        r4 = gate4.evaluate(scene_scores=[0.80], rollback_count=0)
        restored = _GR.from_dict(r4.to_dict())
        assert restored.result_id == r4.result_id
        assert abs(restored.r_score - r4.r_score) < 1e-9
        checkpoints.append("CP-7 GateResult 직렬화/역직렬화 정상")
    except Exception as e:
        errors.append(f"CP-7 직렬화 오류: {e}")

    passed = len(errors) == 0
    return {
        "gate_name": "AutoPromotionGate G62 — SP-C.1 자동 승격 (ADR-077)",
        "gate": "G62",
        "pass": passed,
        "passed": passed,
        "checkpoints": checkpoints,
        "passed_count": len(checkpoints),
        "total_count": 7,
        "errors": errors,
    }
