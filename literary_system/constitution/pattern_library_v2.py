"""
SP-C.1 (V633) — PatternLibraryV2

LOSConstitution V2의 학습된 패턴(장면 구성 패턴, 문장 리듬 패턴 등)을
압축(Compression) 및 랭킹(Ranking)하여 LOSDB에 영속화한다.

설계 원칙
---------
- LLM-0: 외부 LLM 호출 없음 (순수 로컬 연산).
- 압축 전략: 코사인 유사도 기반 중복 제거.
  sim(a, b) = dot(a, b) / (||a|| * ||b||)
  임계값(similarity_threshold) 초과 시 중복으로 판단, 낮은 랭크 항목 제거.
- 랭킹 전략: 사용 빈도(freq) × 엔트로피 가중치(entropy_weight) 원점수.
  rank_score = freq * entropy_weight
- 저장 포맷: JSONL (line-delimited JSON).
  압축 후 재작성(rewrite) 방식 — 파일 모드에서 전체 교체.

ADR-075 참조.
"""
from __future__ import annotations

import json
import math
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple


# ---------------------------------------------------------------------------
# 내부 헬퍼
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _l2_norm(vec: Sequence[float]) -> float:
    return math.sqrt(sum(x * x for x in vec))


def _cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    """두 벡터의 코사인 유사도. 영벡터면 0 반환."""
    if len(a) != len(b):
        raise ValueError(f"벡터 길이 불일치: {len(a)} vs {len(b)}")
    dot = sum(x * y for x, y in zip(a, b))
    na, nb = _l2_norm(a), _l2_norm(b)
    if na < 1e-9 or nb < 1e-9:
        return 0.0
    return dot / (na * nb)


# ---------------------------------------------------------------------------
# PatternEntry — 단일 패턴 레코드
# ---------------------------------------------------------------------------


@dataclass
class PatternEntry:
    """
    단일 패턴 레코드.

    Attributes
    ----------
    pattern_id     : UUID4 문자열.
    label          : 패턴 레이블 (예: "고조-절정-해소", "AABB-리듬").
    description    : 사람이 읽을 수 있는 설명.
    embedding      : 패턴 표현 float 벡터 (압축 유사도에 사용).
                     빈 리스트이면 압축 비교에서 제외됨.
    freq           : 학습/관찰된 사용 빈도.
    entropy_weight : Constitution 엔트로피 가중치 (0.0~1.0).
    created_at     : ISO-8601 UTC.
    note           : 자유 메모.
    """

    pattern_id: str
    label: str
    description: str
    embedding: List[float] = field(default_factory=list)
    freq: int = 1
    entropy_weight: float = 1.0
    created_at: str = field(default_factory=_now_iso)
    note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "label": self.label,
            "description": self.description,
            "embedding": self.embedding,
            "freq": self.freq,
            "entropy_weight": self.entropy_weight,
            "created_at": self.created_at,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "PatternEntry":
        return cls(
            pattern_id=d["pattern_id"],
            label=d["label"],
            description=d["description"],
            embedding=list(d.get("embedding", [])),
            freq=int(d.get("freq", 1)),
            entropy_weight=float(d.get("entropy_weight", 1.0)),
            created_at=d.get("created_at", _now_iso()),
            note=d.get("note", ""),
        )

    @property
    def rank_score(self) -> float:
        """랭킹 원점수 = freq × entropy_weight."""
        return max(0, self.freq) * max(0.0, self.entropy_weight)


# ---------------------------------------------------------------------------
# PatternLibraryV2 — LOSDB JSONL 영속화 + 압축 + 랭킹
# ---------------------------------------------------------------------------

_DEFAULT_STORE = Path("losdb") / "pattern_library_v2.jsonl"


class PatternLibraryV2:
    """
    PatternLibraryV2: 패턴 압축·랭킹 라이브러리.

    파일 포맷: JSONL — 한 줄 = PatternEntry JSON.
    압축(compress)은 파일 전체 재작성 방식.

    Parameters
    ----------
    store_path           : JSONL 파일 경로 (기본값 'losdb/pattern_library_v2.jsonl').
    similarity_threshold : 중복 판정 코사인 유사도 임계값 (기본 0.92).

    Example
    -------
    >>> import uuid
    >>> lib = PatternLibraryV2(":memory:")
    >>> e = PatternEntry(pattern_id=str(uuid.uuid4()), label="A",
    ...                  description="test", embedding=[1.0, 0.0], freq=5)
    >>> lib.add(e)
    >>> top = lib.rank(top_k=1)
    >>> assert top[0].label == "A"
    """

    _MEMORY_SENTINEL = ":memory:"

    def __init__(
        self,
        store_path: str | Path = _DEFAULT_STORE,
        similarity_threshold: float = 0.92,
    ) -> None:
        if not (0.0 < similarity_threshold <= 1.0):
            raise ValueError(
                f"similarity_threshold 범위 오류: {similarity_threshold} (0 < t ≤ 1)"
            )
        self._sim_threshold = similarity_threshold
        self._memory_mode = str(store_path) == self._MEMORY_SENTINEL
        if self._memory_mode:
            self._entries: List[PatternEntry] = []
            self._path: Optional[Path] = None
        else:
            self._path = Path(store_path)
            self._entries = []
            self._loaded = False

    # ------------------------------------------------------------------
    # 퍼블릭 API
    # ------------------------------------------------------------------

    def add(self, entry: PatternEntry) -> None:
        """패턴 추가."""
        self._append(entry)

    def add_many(self, entries: Sequence[PatternEntry]) -> None:
        """여러 패턴 일괄 추가."""
        for e in entries:
            self._append(e)

    def rank(self, top_k: Optional[int] = None) -> List[PatternEntry]:
        """
        랭킹 순으로 정렬된 PatternEntry 목록 반환.

        정렬 기준: rank_score (freq × entropy_weight) 내림차순.
        동점 시 created_at 오름차순.

        Parameters
        ----------
        top_k : 상위 K개만 반환. None이면 전체.
        """
        entries = list(self._all_entries())
        sorted_entries = sorted(
            entries,
            key=lambda e: (-e.rank_score, e.created_at),
        )
        if top_k is not None:
            return sorted_entries[:top_k]
        return sorted_entries

    def compress(
        self,
        similarity_threshold: Optional[float] = None,
    ) -> Tuple[int, int]:
        """
        중복 패턴 압축.

        코사인 유사도가 threshold 초과인 패턴 쌍에서 rank_score가 낮은 항목 제거.
        embedding이 없는 항목은 항상 유지.

        Parameters
        ----------
        similarity_threshold : 임계값. None이면 인스턴스 초기값 사용.

        Returns
        -------
        (before, after) : 압축 전후 패턴 수.
        """
        threshold = (
            similarity_threshold
            if similarity_threshold is not None
            else self._sim_threshold
        )
        entries = list(self._all_entries())
        before = len(entries)

        # rank_score 내림차순 정렬 후 greedy 중복 제거
        sorted_entries = sorted(entries, key=lambda e: -e.rank_score)
        kept: List[PatternEntry] = []
        for candidate in sorted_entries:
            if not candidate.embedding:
                kept.append(candidate)
                continue
            is_dup = False
            for existing in kept:
                if not existing.embedding:
                    continue
                if len(candidate.embedding) != len(existing.embedding):
                    continue
                sim = _cosine_similarity(candidate.embedding, existing.embedding)
                if sim > threshold:
                    is_dup = True
                    break
            if not is_dup:
                kept.append(candidate)

        after = len(kept)

        if self._memory_mode:
            self._entries = kept
        else:
            self._rewrite(kept)

        return before, after

    def all_entries(self) -> List[PatternEntry]:
        """전체 PatternEntry 목록 반환 (복사본)."""
        return list(self._all_entries())

    def count(self) -> int:
        """현재 패턴 수."""
        return len(self._all_entries())

    def find_by_label(self, label: str) -> List[PatternEntry]:
        """레이블로 패턴 검색."""
        return [e for e in self._all_entries() if e.label == label]

    def find_similar(
        self,
        query_embedding: Sequence[float],
        top_k: int = 5,
        threshold: float = 0.0,
    ) -> List[Tuple[float, PatternEntry]]:
        """
        쿼리 임베딩과 유사한 패턴 반환.

        Returns
        -------
        List[(similarity, PatternEntry)] — 유사도 내림차순.
        """
        results: List[Tuple[float, PatternEntry]] = []
        for entry in self._all_entries():
            if not entry.embedding:
                continue
            if len(entry.embedding) != len(query_embedding):
                continue
            sim = _cosine_similarity(list(query_embedding), entry.embedding)
            if sim >= threshold:
                results.append((sim, entry))
        results.sort(key=lambda x: -x[0])
        return results[:top_k]

    def increment_freq(self, pattern_id: str, delta: int = 1) -> None:
        """
        특정 패턴의 freq 증가.

        Raises
        ------
        KeyError : pattern_id를 찾을 수 없는 경우.
        """
        entries = self._all_entries()
        idx = next(
            (i for i, e in enumerate(entries) if e.pattern_id == pattern_id), None
        )
        if idx is None:
            raise KeyError(f"PatternLibraryV2: pattern_id '{pattern_id}' 없음")
        old = entries[idx]
        updated = PatternEntry(
            pattern_id=old.pattern_id,
            label=old.label,
            description=old.description,
            embedding=list(old.embedding),
            freq=old.freq + delta,
            entropy_weight=old.entropy_weight,
            created_at=old.created_at,
            note=old.note,
        )
        entries[idx] = updated
        if self._memory_mode:
            self._entries = entries
        else:
            self._rewrite(entries)

    def clear(self) -> None:
        """
        전체 패턴 삭제 (주로 테스트용).
        메모리 모드: 내부 리스트 초기화.
        파일 모드: 파일 삭제.
        """
        if self._memory_mode:
            self._entries.clear()
        else:
            self._loaded = False
            self._entries.clear()
            if self._path and self._path.exists():
                self._path.unlink()

    # ------------------------------------------------------------------
    # 내부 저장소 헬퍼
    # ------------------------------------------------------------------

    def _all_entries(self) -> List[PatternEntry]:
        if self._memory_mode:
            return self._entries
        if not self._loaded:
            self._entries = self._load_from_file()
            self._loaded = True
        return self._entries

    def _append(self, entry: PatternEntry) -> None:
        if self._memory_mode:
            self._entries.append(entry)
            return
        assert self._path is not None
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")
        if self._loaded:
            self._entries.append(entry)
        else:
            self._entries = self._load_from_file()
            self._loaded = True

    def _rewrite(self, entries: List[PatternEntry]) -> None:
        """파일 전체 재작성."""
        assert self._path is not None
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w", encoding="utf-8") as f:
            for e in entries:
                f.write(json.dumps(e.to_dict(), ensure_ascii=False) + "\n")
        self._entries = list(entries)
        self._loaded = True

    def _load_from_file(self) -> List[PatternEntry]:
        assert self._path is not None
        if not self._path.exists():
            return []
        entries: List[PatternEntry] = []
        with self._path.open("r", encoding="utf-8") as f:
            for lineno, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                    entries.append(PatternEntry.from_dict(d))
                except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
                    raise RuntimeError(
                        f"PatternLibraryV2: {self._path} 라인 {lineno} 파싱 실패 — {exc}"
                    ) from exc
        return entries
