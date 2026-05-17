"""NarrativeMemoryStore — V407.

시리즈 단위 상태 영속화 저장소 (append-only).
세션 간 NKGGraphStore / PayoffDebtLedger / PhysicsCoefficientStore / SP·RU·ET·RD 궤도 보존.

설계 원칙 (3인 합의):
  - save_episode(): 기존 파일 있으면 FileExistsError (덮어쓰기 금지)
  - load_episode(): 파일 없으면 EpisodeMemoryNotFound
  - list_series(): metadata.json 있는 디렉토리만 반환
  - pickle은 NKG 전용; 나머지는 JSON (사람이 읽을 수 있음)
  - LLM 0회
"""
from __future__ import annotations

import json
import os
import pathlib
import pickle
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ── 예외 ──────────────────────────────────────────────────────────────────────

class EpisodeMemoryNotFound(FileNotFoundError):
    """요청한 에피소드 메모리 파일이 없음."""
    pass


class SeriesNotFound(FileNotFoundError):
    """요청한 시리즈 디렉토리 또는 metadata.json이 없음."""
    pass


# ── EpisodeMemory 데이터 구조 ─────────────────────────────────────────────────

@dataclass
class EpisodeMemory:
    """단일 에피소드 완료 후 저장되는 상태 스냅샷 (설계도 F)."""
    series_id: str
    episode_idx: int                      # 0=초기, 1~N=에피소드
    created_at: str                       # ISO 8601
    pipeline_state: Dict[str, Any]        # LiteraryPipelineState.model_dump() 또는 dict
    narrative_tensor: Dict[str, float]    # {SP, RU, ET, RD}
    nkg_snapshot_path: str                # "ep001_nkg.pkl" (상대 경로, 없으면 "")
    debt_ledger_snapshot: Dict[str, Any]  # PayoffDebtLedger.to_dict() 또는 {}
    coefficient_snapshot: Dict[str, float]  # PhysicsCoefficientStore.as_dict()
    cost_ledger: Optional[Dict[str, Any]] = None  # V411-H CostLedger.to_dict() (선택)

    def to_dict(self) -> dict:
        return {
            "series_id": self.series_id,
            "episode_idx": self.episode_idx,
            "created_at": self.created_at,
            "pipeline_state": self.pipeline_state,
            "narrative_tensor": self.narrative_tensor,
            "nkg_snapshot_path": self.nkg_snapshot_path,
            "debt_ledger_snapshot": self.debt_ledger_snapshot,
            "coefficient_snapshot": self.coefficient_snapshot,
            "cost_ledger": self.cost_ledger,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "EpisodeMemory":
        return cls(
            series_id=d["series_id"],
            episode_idx=d["episode_idx"],
            created_at=d.get("created_at", ""),
            pipeline_state=d.get("pipeline_state", {}),
            narrative_tensor=d.get("narrative_tensor", {}),
            nkg_snapshot_path=d.get("nkg_snapshot_path", ""),
            debt_ledger_snapshot=d.get("debt_ledger_snapshot", {}),
            coefficient_snapshot=d.get("coefficient_snapshot", {}),
            cost_ledger=d.get("cost_ledger", None),
        )

    @property
    def episode_key(self) -> str:
        return f"ep{self.episode_idx:03d}"


# ── NarrativeMemoryStore ──────────────────────────────────────────────────────

class NarrativeMemoryStore:
    """V407 — append-only 시리즈 상태 영속화 저장소.

    파일 구조:
      {memory_root}/{series_id}/
        metadata.json
        ep000.json  (초기 상태)
        ep001.json
        ep001_nkg.pkl
        ...

    환경변수 LITERARY_OS_MEMORY_ROOT 없으면 /tmp/literary_os_memory 사용.
    """

    DEFAULT_MEMORY_ROOT = "/tmp/literary_os_memory"

    def __init__(self, memory_root: Optional[str] = None) -> None:
        root = memory_root or os.environ.get(
            "LITERARY_OS_MEMORY_ROOT", self.DEFAULT_MEMORY_ROOT
        )
        self._root = pathlib.Path(root)

    # ── 시리즈 관리 ───────────────────────────────────────────────────────────

    def init_series(self, series_id: str, metadata: dict) -> pathlib.Path:
        """시리즈 디렉토리 초기화 (metadata.json 생성).

        이미 존재하면 FileExistsError.
        """
        series_dir = self._series_dir(series_id)
        series_dir.mkdir(parents=True, exist_ok=True)
        meta_path = series_dir / "metadata.json"
        if meta_path.exists():
            raise FileExistsError(f"Series '{series_id}' already initialized: {meta_path}")
        meta_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        return series_dir

    def get_series_metadata(self, series_id: str) -> dict:
        meta_path = self._series_dir(series_id) / "metadata.json"
        if not meta_path.exists():
            raise SeriesNotFound(f"Series '{series_id}' not found: {meta_path}")
        return json.loads(meta_path.read_text(encoding="utf-8"))

    def list_series(self) -> List[str]:
        """metadata.json 있는 시리즈 ID 목록 반환."""
        if not self._root.exists():
            return []
        return sorted(
            d.name
            for d in self._root.iterdir()
            if d.is_dir() and (d / "metadata.json").exists()
        )

    # ── 에피소드 저장/로드 ────────────────────────────────────────────────────

    def save_episode(
        self,
        memory: EpisodeMemory,
        nkg_object: Optional[Any] = None,   # NKGGraphStore 인스턴스 (optional)
    ) -> str:
        """EpisodeMemory를 JSON으로 저장 (append-only: 덮어쓰기 금지).

        Returns:
            저장된 JSON 파일 경로 (str)
        """
        series_dir = self._series_dir(memory.series_id)
        series_dir.mkdir(parents=True, exist_ok=True)

        json_path = series_dir / f"{memory.episode_key}.json"
        if json_path.exists():
            raise FileExistsError(
                f"Episode already saved (append-only): {json_path}"
            )

        # NKG pickle 저장
        nkg_rel_path = ""
        if nkg_object is not None:
            pkl_path = series_dir / f"{memory.episode_key}_nkg.pkl"
            with pkl_path.open("wb") as f:
                pickle.dump(nkg_object, f)
            nkg_rel_path = f"{memory.episode_key}_nkg.pkl"

        # nkg_snapshot_path 덮어쓰기
        memory.nkg_snapshot_path = nkg_rel_path

        json_path.write_text(
            json.dumps(memory.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return str(json_path)

    def load_episode(self, series_id: str, episode_idx: int) -> EpisodeMemory:
        """저장된 EpisodeMemory 로드.

        Raises:
            EpisodeMemoryNotFound: 파일 없음
        """
        ep_key = f"ep{episode_idx:03d}"
        json_path = self._series_dir(series_id) / f"{ep_key}.json"
        if not json_path.exists():
            raise EpisodeMemoryNotFound(
                f"Episode {episode_idx} not found for series '{series_id}': {json_path}"
            )
        data = json.loads(json_path.read_text(encoding="utf-8"))
        return EpisodeMemory.from_dict(data)

    def load_series(self, series_id: str) -> List[EpisodeMemory]:
        """시리즈의 모든 에피소드 메모리 로드 (episode_idx 순 정렬)."""
        series_dir = self._series_dir(series_id)
        if not series_dir.exists():
            raise SeriesNotFound(f"Series '{series_id}' not found")
        memories = []
        for json_path in sorted(series_dir.glob("ep*.json")):
            if "_nkg" in json_path.name:
                continue
            data = json.loads(json_path.read_text(encoding="utf-8"))
            memories.append(EpisodeMemory.from_dict(data))
        return sorted(memories, key=lambda m: m.episode_idx)

    def get_latest_episode(self, series_id: str) -> Optional[EpisodeMemory]:
        """최신 에피소드 메모리 반환. 없으면 None."""
        try:
            memories = self.load_series(series_id)
            return memories[-1] if memories else None
        except SeriesNotFound:
            return None

    def load_nkg(self, series_id: str, episode_idx: int) -> Optional[Any]:
        """에피소드 NKG pickle 로드. 없으면 None."""
        ep_key = f"ep{episode_idx:03d}"
        pkl_path = self._series_dir(series_id) / f"{ep_key}_nkg.pkl"
        if not pkl_path.exists():
            return None
        with pkl_path.open("rb") as f:
            return pickle.load(f)

    # ── 내부 헬퍼 ─────────────────────────────────────────────────────────────

    def _series_dir(self, series_id: str) -> pathlib.Path:
        return self._root / series_id
