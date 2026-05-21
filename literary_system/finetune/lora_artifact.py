"""
SP-B.1 (V598) — LoRAArtifact: safetensors 3-tag 아티팩트 계약

Phase B 본안 보강 B-M-03:
- 3-tag 무결성: seed_tag + commit_tag + dataset_sha_tag
- sha256 체크섬 검증 (load() 시 자동)
- safetensors 포맷 명시적 지원 (실 파일 없을 경우 graceful fallback)
- LoRAArtifactContract 추상 계약 + LoRAArtifact 구현

ADR-058 참조.

LLM-0 원칙: 이 모듈은 외부 LLM API를 직접 호출하지 않음.
"""
from __future__ import annotations

import abc
import hashlib
import json
import time
import warnings
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional


# ---------------------------------------------------------------------------
# 상수
# ---------------------------------------------------------------------------

ARTIFACT_MANIFEST_FILENAME: str = "artifact_manifest.json"
SAFETENSORS_EXTENSION: str = ".safetensors"
ADAPTER_CONFIG_FILENAME: str = "adapter_config.json"


# ---------------------------------------------------------------------------
# ArtifactStage — 아티팩트 수명 주기 상태
# ---------------------------------------------------------------------------

class ArtifactStage(str, Enum):
    """LoRA 아티팩트 수명 주기 단계."""
    PENDING   = "pending"     # 학습 완료 전
    CANDIDATE = "candidate"   # 학습 완료, 검증 전
    VALIDATED = "validated"   # 평가 통과 (EquivalenceTester 5축)
    PROMOTED  = "promoted"    # 서빙 활성화
    RETIRED   = "retired"     # 더 나은 모델로 대체
    CORRUPTED = "corrupted"   # sha256 검증 실패


# ---------------------------------------------------------------------------
# LoRAArtifactContract — 추상 계약
# ---------------------------------------------------------------------------

class LoRAArtifactContract(abc.ABC):
    """
    LoRA 아티팩트 계약 인터페이스.

    B-M-03: 3-tag 무결성(seed+commit+dataset_sha)과
    sha256 검증을 모든 구현체가 준수해야 한다.
    """

    @property
    @abc.abstractmethod
    def artifact_id(self) -> str:
        """아티팩트 고유 식별자."""

    @property
    @abc.abstractmethod
    def seed_tag(self) -> int:
        """재현성 시드 태그."""

    @property
    @abc.abstractmethod
    def commit_tag(self) -> str:
        """학습 시점 git commit SHA (7자 short)."""

    @property
    @abc.abstractmethod
    def dataset_sha_tag(self) -> str:
        """학습 데이터셋 sha256 (32자 hex prefix)."""

    @abc.abstractmethod
    def verify_integrity(self) -> bool:
        """
        sha256 체크섬으로 아티팩트 무결성 검증.
        Returns: True(무결성 OK) / False(손상)
        """

    @abc.abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """직렬화."""

    @classmethod
    @abc.abstractmethod
    def from_dict(cls, d: Dict[str, Any]) -> "LoRAArtifactContract":
        """역직렬화."""


# ---------------------------------------------------------------------------
# LoRAArtifact — 구현체
# ---------------------------------------------------------------------------

@dataclass
class LoRAArtifact(LoRAArtifactContract):
    """
    LoRA 파인튜닝 아티팩트.

    3-tag (B-M-03):
        seed_tag:        학습 재현성 시드 (default: 42)
        commit_tag:      git commit SHA 7자 (학습 트리거 시점)
        dataset_sha_tag: 훈련 데이터셋 sha256 32자 prefix

    Attributes:
        artifact_id:     고유 아티팩트 ID (자동 생성)
        base_model:      기반 모델 식별자
        lora_rank:       LoRA rank (e.g. 16)
        artifact_path:   safetensors 파일 경로 (또는 디렉토리)
        sha256:          아티팩트 파일 sha256 체크섬
        stage:           ArtifactStage 수명 주기
        created_at:      UTC ISO 타임스탬프
        metadata:        부가 정보
    """
    # 3-tag (B-M-03)
    _seed_tag: int            = field(default=42)
    _commit_tag: str          = field(default="0000000")
    _dataset_sha_tag: str     = field(default="0" * 32)

    # 아티팩트 정보
    _artifact_id: str         = field(default="")
    base_model: str           = field(default="meta-llama/Llama-3.1-8B")
    lora_rank: int            = field(default=16)
    artifact_path: str        = field(default="")
    sha256: str               = field(default="")
    stage: ArtifactStage      = field(default=ArtifactStage.CANDIDATE)
    created_at: str           = field(default="")
    metadata: Dict[str, Any]  = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self._artifact_id:
            ts = int(time.time() * 1000)
            self._artifact_id = f"lora-{self._commit_tag[:7]}-{ts}"
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    # ------------------------------------------------------------------
    # LoRAArtifactContract 구현
    # ------------------------------------------------------------------

    @property
    def artifact_id(self) -> str:
        return self._artifact_id

    @property
    def seed_tag(self) -> int:
        return self._seed_tag

    @property
    def commit_tag(self) -> str:
        return self._commit_tag

    @property
    def dataset_sha_tag(self) -> str:
        return self._dataset_sha_tag

    def verify_integrity(self) -> bool:
        """
        sha256 체크섬으로 아티팩트 무결성 검증.

        artifact_path가 존재하면 실제 파일을 읽어 sha256 계산.
        파일이 없으면 self.sha256이 비어있지 않은지만 확인.
        """
        if not self.sha256:
            warnings.warn(
                f"LoRAArtifact {self.artifact_id}: sha256 미설정 — 무결성 검증 불가.",
                UserWarning,
                stacklevel=2,
            )
            return False

        # artifact_path 미설정(빈 문자열)이면 sha256 hex 형식만 검사
        if not self.artifact_path:
            return len(self.sha256) == 64 and all(
                c in "0123456789abcdef" for c in self.sha256
            )

        path = Path(self.artifact_path)
        if not path.exists():
            # 파일 없음: 등록된 sha256의 형식만 검사
            return len(self.sha256) == 64 and all(
                c in "0123456789abcdef" for c in self.sha256
            )

        # 파일이 디렉토리면 manifest 파일 대상
        target = path / ARTIFACT_MANIFEST_FILENAME if path.is_dir() else path
        if not target.exists():
            return False

        computed = compute_sha256(str(target))
        if computed != self.sha256:
            warnings.warn(
                f"LoRAArtifact {self.artifact_id}: sha256 불일치 "
                f"(stored={self.sha256[:16]}…, computed={computed[:16]}…)",
                UserWarning,
                stacklevel=2,
            )
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_id":    self._artifact_id,
            "seed_tag":       self._seed_tag,
            "commit_tag":     self._commit_tag,
            "dataset_sha_tag":self._dataset_sha_tag,
            "base_model":     self.base_model,
            "lora_rank":      self.lora_rank,
            "artifact_path":  self.artifact_path,
            "sha256":         self.sha256,
            "stage":          self.stage.value,
            "created_at":     self.created_at,
            "metadata":       self.metadata,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "LoRAArtifact":
        d = dict(d)
        stage_val = d.pop("stage", ArtifactStage.CANDIDATE.value)
        stage = ArtifactStage(stage_val) if isinstance(stage_val, str) else stage_val
        return cls(
            _artifact_id     = d.pop("artifact_id", ""),
            _seed_tag        = d.pop("seed_tag", 42),
            _commit_tag      = d.pop("commit_tag", "0000000"),
            _dataset_sha_tag = d.pop("dataset_sha_tag", "0" * 32),
            base_model       = d.pop("base_model", "meta-llama/Llama-3.1-8B"),
            lora_rank        = d.pop("lora_rank", 16),
            artifact_path    = d.pop("artifact_path", ""),
            sha256           = d.pop("sha256", ""),
            stage            = stage,
            created_at       = d.pop("created_at", ""),
            metadata         = d.pop("metadata", {}),
        )

    # ------------------------------------------------------------------
    # 유틸리티
    # ------------------------------------------------------------------

    @property
    def tag_string(self) -> str:
        """3-tag 요약 문자열: seed={seed}|commit={commit}|dataset={dataset[:8]}"""
        return (
            f"seed={self._seed_tag}"
            f"|commit={self._commit_tag[:7]}"
            f"|dataset={self._dataset_sha_tag[:8]}"
        )

    def save_manifest(self, directory: str) -> str:
        """
        아티팩트 메타데이터를 manifest JSON 파일로 저장.

        Args:
            directory: 저장할 디렉토리 경로

        Returns:
            저장된 manifest 파일 경로
        """
        p = Path(directory)
        p.mkdir(parents=True, exist_ok=True)
        manifest_path = p / ARTIFACT_MANIFEST_FILENAME
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        return str(manifest_path)

    @classmethod
    def load_manifest(cls, manifest_path: str) -> "LoRAArtifact":
        """
        manifest JSON 파일에서 아티팩트 로드.
        로드 후 verify_integrity() 자동 실행.

        Args:
            manifest_path: manifest JSON 경로

        Returns:
            LoRAArtifact 인스턴스

        Raises:
            FileNotFoundError: 파일 없음
            ValueError: sha256 검증 실패
        """
        path = Path(manifest_path)
        if not path.exists():
            raise FileNotFoundError(f"manifest not found: {manifest_path}")
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        artifact = cls.from_dict(d)
        if not artifact.verify_integrity():
            artifact.stage = ArtifactStage.CORRUPTED
            raise ValueError(
                f"LoRAArtifact {artifact.artifact_id}: 무결성 검증 실패 — "
                f"stage=CORRUPTED"
            )
        return artifact


# ---------------------------------------------------------------------------
# 유틸리티 함수
# ---------------------------------------------------------------------------

def compute_sha256(file_path: str, chunk_size: int = 65536) -> str:
    """
    파일 sha256 체크섬 계산.

    Args:
        file_path:  대상 파일 경로
        chunk_size: 읽기 청크 크기

    Returns:
        64자 hex 문자열
    """
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def make_artifact(
    base_model: str,
    lora_rank: int,
    seed_tag: int,
    commit_tag: str,
    dataset_sha_tag: str,
    artifact_path: str = "",
    sha256: str = "",
    metadata: Optional[Dict[str, Any]] = None,
) -> LoRAArtifact:
    """
    LoRAArtifact 팩토리 함수 (B-M-03 3-tag).

    Args:
        base_model:       기반 모델
        lora_rank:        LoRA rank
        seed_tag:         재현성 시드
        commit_tag:       git commit SHA
        dataset_sha_tag:  데이터셋 sha256 prefix
        artifact_path:    safetensors 파일/디렉토리 경로
        sha256:           아티팩트 파일 sha256 (미지정 시 자동 계산)
        metadata:         부가 정보

    Returns:
        LoRAArtifact 인스턴스
    """
    if sha256 == "" and artifact_path and Path(artifact_path).exists():
        target = Path(artifact_path)
        if target.is_dir():
            manifest = target / ARTIFACT_MANIFEST_FILENAME
            sha256 = compute_sha256(str(manifest)) if manifest.exists() else ""
        else:
            sha256 = compute_sha256(artifact_path)

    return LoRAArtifact(
        _seed_tag        = seed_tag,
        _commit_tag      = commit_tag,
        _dataset_sha_tag = dataset_sha_tag,
        base_model       = base_model,
        lora_rank        = lora_rank,
        artifact_path    = artifact_path,
        sha256           = sha256,
        metadata         = metadata or {},
    )
