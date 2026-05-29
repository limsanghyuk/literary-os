"""
SP-C.1 (V632) — ConstitutionWeightTracker

LOSConstitution 가중치(w1~w5)를 LOSDB JSON 영속화 스토어에
버전별로 저장하고, 이력 조회 및 롤백을 지원한다.

설계 원칙
---------
- LLM-0: 외부 LLM 호출 없음 (순수 로컬 연산).
- 저장 포맷: JSONL (line-delimited JSON) — 추가 전용(append-only).
  마지막 라인이 최신 버전이다.
- version_id: UUID4 문자열.
- 롤백 시 원본 레코드를 삭제하지 않고 동일 가중치를 새 레코드로 저장.
  이력은 보존된다 (비파괴 롤백).
- 엔트로피 값은 저장 시 자동 계산하여 기록 (참고용, 강제 검증 아님).

ADR-099 참조.
"""
from __future__ import annotations

import json
import math
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from literary_system.constitution.los_constitution import ConstitutionWeights


# ---------------------------------------------------------------------------
# 내부 헬퍼
# ---------------------------------------------------------------------------

def _shannon_entropy(weights: Sequence[float]) -> float:
    """Shannon 엔트로피 H(w) (bits). w_i == 0 이면 해당 항 스킵."""
    h = 0.0
    for w in weights:
        if w > 1e-9:
            h -= w * math.log2(w)
    return h


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# WeightRecord — 단일 버전 레코드
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class WeightRecord:
    """
    ConstitutionWeights 단일 버전 레코드.

    Attributes
    ----------
    version_id : UUID4 문자열 (자동 생성).
    timestamp  : ISO-8601 UTC 타임스탬프.
    weights    : ConstitutionWeights 스냅샷.
    entropy    : Shannon 엔트로피 H(w) (bits) — 저장 시 자동 계산.
    note       : 저장 이유 (옵셔널, 예: "optimised", "rollback:v1.2").
    """

    version_id: str
    timestamp: str
    weights: ConstitutionWeights
    entropy: float
    note: str = ""

    # ------------------------------------------------------------------
    # 직렬화 / 역직렬화
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version_id": self.version_id,
            "timestamp": self.timestamp,
            "weights": self.weights.as_dict(),
            "entropy": self.entropy,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "WeightRecord":
        w = d["weights"]
        weights = ConstitutionWeights(
            drse=float(w["drse"]),
            debt=float(w["debt"]),
            arc=float(w["arc"]),
            tension=float(w["tension"]),
            prose=float(w["prose"]),
        )
        return cls(
            version_id=d["version_id"],
            timestamp=d["timestamp"],
            weights=weights,
            entropy=float(d.get("entropy", 0.0)),
            note=d.get("note", ""),
        )


# ---------------------------------------------------------------------------
# ConstitutionWeightTracker — LOSDB JSONL 영속화 + 버전 관리
# ---------------------------------------------------------------------------

_DEFAULT_STORE = Path("losdb") / "constitution_weights.jsonl"


class ConstitutionWeightTracker:
    """
    ConstitutionWeights LOSDB 영속화 트래커.

    파일 포맷: JSONL — 한 줄 = WeightRecord JSON.
    최신 버전 = 마지막 라인.
    롤백은 비파괴적 — 대상 레코드를 새 레코드로 재저장.

    Parameters
    ----------
    store_path : JSONL 파일 경로 (기본값 'losdb/constitution_weights.jsonl').

    Example
    -------
    >>> tracker = ConstitutionWeightTracker(":memory:")
    >>> w = ConstitutionWeights(drse=0.25, debt=0.25, arc=0.20,
    ...                         tension=0.15, prose=0.15)
    >>> vid = tracker.save(w, note="initial")
    >>> latest = tracker.load_latest()
    >>> assert latest.drse == 0.25
    """

    # 메모리 모드 식별자
    _MEMORY_SENTINEL = ":memory:"

    def __init__(self, store_path: str | Path = _DEFAULT_STORE) -> None:
        self._memory_mode = str(store_path) == self._MEMORY_SENTINEL
        if self._memory_mode:
            self._records: List[WeightRecord] = []
            self._path: Optional[Path] = None
        else:
            self._path = Path(store_path)
            self._records = []  # 캐시 (lazy load)
            self._loaded = False

    # ------------------------------------------------------------------
    # 퍼블릭 API
    # ------------------------------------------------------------------

    def save(
        self,
        weights: ConstitutionWeights,
        note: str = "",
    ) -> str:
        """
        가중치를 새 버전으로 저장한다.

        Parameters
        ----------
        weights : 저장할 ConstitutionWeights.
        note    : 저장 이유 (옵셔널).

        Returns
        -------
        str : 새로 생성된 version_id.
        """
        vals = list(weights.as_dict().values())
        record = WeightRecord(
            version_id=str(uuid.uuid4()),
            timestamp=_now_iso(),
            weights=weights,
            entropy=_shannon_entropy(vals),
            note=note,
        )
        self._append(record)
        return record.version_id

    def load_latest(self) -> ConstitutionWeights:
        """
        가장 최근 저장된 ConstitutionWeights 반환.

        Raises
        ------
        RuntimeError : 저장된 레코드가 없는 경우.
        """
        records = self._all_records()
        if not records:
            raise RuntimeError(
                "ConstitutionWeightTracker: 저장된 가중치 레코드가 없습니다."
            )
        return records[-1].weights

    def rollback(self, version_id: str) -> ConstitutionWeights:
        """
        특정 version_id로 롤백한다.

        롤백은 비파괴적 — 대상 버전의 가중치를 '새 레코드'로 저장한다.
        이력은 그대로 보존되며, load_latest()는 롤백된 가중치를 반환한다.

        Parameters
        ----------
        version_id : 복원 대상 버전 ID.

        Returns
        -------
        ConstitutionWeights : 롤백된 가중치.

        Raises
        ------
        KeyError : version_id를 찾을 수 없는 경우.
        """
        records = self._all_records()
        target: Optional[WeightRecord] = None
        for r in records:
            if r.version_id == version_id:
                target = r
                break
        if target is None:
            raise KeyError(
                f"ConstitutionWeightTracker: version_id '{version_id}' 를 찾을 수 없습니다."
            )
        rollback_note = f"rollback:{version_id}"
        self.save(target.weights, note=rollback_note)
        return target.weights

    def history(self) -> List[WeightRecord]:
        """
        전체 WeightRecord 이력을 시간 순(오래된 것→최신)으로 반환.

        Returns
        -------
        List[WeightRecord] : 불변 리스트 복사본.
        """
        return list(self._all_records())

    def latest_record(self) -> Optional[WeightRecord]:
        """가장 최근 WeightRecord 반환 (없으면 None)."""
        records = self._all_records()
        return records[-1] if records else None

    def count(self) -> int:
        """저장된 레코드 수."""
        return len(self._all_records())

    def clear(self) -> None:
        """
        모든 레코드 삭제 (주로 테스트용).
        메모리 모드: 내부 리스트 초기화.
        파일 모드: 파일 삭제.
        """
        if self._memory_mode:
            self._records.clear()
        else:
            self._loaded = False
            self._records.clear()
            if self._path and self._path.exists():
                self._path.unlink()

    # ------------------------------------------------------------------
    # 내부 저장소 헬퍼
    # ------------------------------------------------------------------

    def _all_records(self) -> List[WeightRecord]:
        if self._memory_mode:
            return self._records
        # 파일 모드 — lazy load
        if not self._loaded:
            self._records = self._load_from_file()
            self._loaded = True
        return self._records

    def _append(self, record: WeightRecord) -> None:
        if self._memory_mode:
            self._records.append(record)
            return
        # 파일 모드
        assert self._path is not None
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")
        # 캐시 갱신
        self._records.append(record)

    def _load_from_file(self) -> List[WeightRecord]:
        assert self._path is not None
        if not self._path.exists():
            return []
        records: List[WeightRecord] = []
        with self._path.open("r", encoding="utf-8") as f:
            for lineno, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                    records.append(WeightRecord.from_dict(d))
                except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
                    raise RuntimeError(
                        f"ConstitutionWeightTracker: {self._path} 라인 {lineno} 파싱 실패 — {exc}"
                    ) from exc
        return records
