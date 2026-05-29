"""DatasetRegistry — LoRA 데이터셋 버전 관리.

ADR-056: sha256 체크섬 검증 + DVC remote 연동 (graceful degradation).
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import time
import warnings
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class LoRADatasetVersion:
    """단일 데이터셋 버전 메타데이터."""

    version_tag: str
    split_tag: str          # train/val/test
    path: str
    sha256: str
    num_samples: int
    source_hash: str        # 소스 코드 해시 (stale 감지용)
    created_at: float
    dvc_remote: Optional[str] = None
    metadata: Dict = field(default_factory=dict)


class DatasetRegistry:
    """데이터셋 버전 레지스트리.

    Usage:
        registry = DatasetRegistry(Path("registry.json"))
        registry.register("v1.0", "train", path, sha256, 800, src_hash)
        registry.verify("v1.0", "train")
    """

    def __init__(self, registry_path: Optional[Path] = None) -> None:
        self._path = Path(registry_path) if registry_path else None
        self._versions: Dict[str, LoRADatasetVersion] = {}  # key: f"{tag}:{split}"

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def register(
        self,
        version_tag: str,
        split_tag: str,
        path: Path,
        sha256: str,
        num_samples: int,
        source_hash: str,
        dvc_remote: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> DatasetVersion:
        """데이터셋 버전 등록."""
        dv = LoRADatasetVersion(
            version_tag=version_tag,
            split_tag=split_tag,
            path=str(path),
            sha256=sha256,
            num_samples=num_samples,
            source_hash=source_hash,
            created_at=time.time(),
            dvc_remote=dvc_remote,
            metadata=metadata or {},
        )
        self._versions[f"{version_tag}:{split_tag}"] = dv
        if dvc_remote:
            self._dvc_add(path, dvc_remote)
        return dv

    def verify(self, version_tag: str, split_tag: str) -> bool:
        """sha256 체크섬 검증."""
        dv = self.get(version_tag, split_tag)
        if dv is None:
            return False
        p = Path(dv.path)
        if not p.exists():
            return False
        actual = hashlib.sha256(p.read_bytes()).hexdigest()
        return actual == dv.sha256

    def get(
        self, version_tag: str, split_tag: str
    ) -> Optional[LoRADatasetVersion]:
        return self._versions.get(f"{version_tag}:{split_tag}")

    def list_versions(self) -> List[LoRADatasetVersion]:
        return list(self._versions.values())

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, path: Optional[Path] = None) -> None:
        """JSON 파일로 저장."""
        target = Path(path) if path else self._path
        if target is None:
            raise ValueError("No path provided for DatasetRegistry.save()")
        target.parent.mkdir(parents=True, exist_ok=True)
        data = {k: asdict(v) for k, v in self._versions.items()}
        target.write_text(json.dumps(data, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "DatasetRegistry":
        """JSON 파일에서 로드."""
        registry = cls(path)
        path = Path(path)
        if not path.exists():
            return registry
        data = json.loads(path.read_text(encoding="utf-8"))
        for k, v in data.items():
            registry._versions[k] = LoRADatasetVersion(**v)
        return registry

    # ------------------------------------------------------------------
    # DVC integration (graceful degradation)
    # ------------------------------------------------------------------

    @staticmethod
    def _dvc_add(path: Path, remote: str) -> None:
        try:
            subprocess.run(
                ["dvc", "add", str(path)],
                check=True,
                capture_output=True,
                timeout=30,
            )
        except (FileNotFoundError, subprocess.CalledProcessError) as exc:
            warnings.warn(
                f"DVC add failed (graceful degradation): {exc}",
                RuntimeWarning,
                stacklevel=3,
            )

    @staticmethod
    def compute_sha256(path: Path) -> str:
        """파일 sha256 계산 헬퍼."""
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
