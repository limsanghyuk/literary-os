"""
SP-B.1 (V598) — LoRAModelRegistry: 체크포인트 버전 관리

Phase B 본안 보강 B-M-03:
- LoRAArtifact 3-tag 기반 체크포인트 등록·조회·승격·퇴역
- JSON 파일 기반 영속 레지스트리 (DVC remote 연동 준비)
- promote(): CANDIDATE → VALIDATED → PROMOTED (단계별)
- retire(): 현재 PROMOTED 아티팩트를 RETIRED 처리
- 중복 artifact_id 재등록 방지 (RegisterConflictError)

ADR-058 참조.

LLM-0 원칙: 이 모듈은 외부 LLM API를 직접 호출하지 않음.
"""
from __future__ import annotations

import json
import warnings
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from literary_system.finetune.lora_artifact import (
    ArtifactStage,
    LoRAArtifact,
    LoRAArtifactContract,
    make_artifact,
)

# ---------------------------------------------------------------------------
# 상수
# ---------------------------------------------------------------------------

REGISTRY_FILENAME: str = "lora_model_registry.json"
REGISTRY_SCHEMA_VERSION: str = "1.0"


# ---------------------------------------------------------------------------
# 예외
# ---------------------------------------------------------------------------

class RegisterConflictError(ValueError):
    """이미 등록된 artifact_id를 재등록하려 할 때 발생."""


class ArtifactNotFoundError(KeyError):
    """레지스트리에 artifact_id가 없을 때 발생."""


class StageTransitionError(ValueError):
    """허용되지 않는 단계 전환 시 발생."""


# ---------------------------------------------------------------------------
# LoRAModelRegistry
# ---------------------------------------------------------------------------

class LoRAModelRegistry:
    """
    LoRA 아티팩트 체크포인트 버전 레지스트리.

    B-M-03: 3-tag(seed+commit+dataset_sha) 기반 추적.

    단계 전환 규칙:
        register()  → CANDIDATE (최초 등록)
        promote()   → CANDIDATE → VALIDATED → PROMOTED
        retire()    → PROMOTED → RETIRED
        mark_corrupted() → any → CORRUPTED
    """

    # 허용 승격 경로: {현재 단계: 다음 단계}
    _PROMOTE_PATH: Dict[ArtifactStage, ArtifactStage] = {
        ArtifactStage.CANDIDATE: ArtifactStage.VALIDATED,
        ArtifactStage.VALIDATED: ArtifactStage.PROMOTED,
    }

    def __init__(self, registry_dir: str = "") -> None:
        """
        Args:
            registry_dir: 레지스트리 JSON 파일을 저장할 디렉토리.
                          비어있으면 메모리 전용 모드.
        """
        self._registry_dir = registry_dir
        self._artifacts: Dict[str, LoRAArtifact] = {}
        self._created_at: str = datetime.now(timezone.utc).isoformat()
        self._schema_version: str = REGISTRY_SCHEMA_VERSION

        if registry_dir:
            self._load_if_exists()

    # ------------------------------------------------------------------
    # 등록
    # ------------------------------------------------------------------

    def register(self, artifact: LoRAArtifact) -> None:
        """
        아티팩트를 레지스트리에 등록.

        신규 아티팩트는 CANDIDATE 상태로 등록됨.
        이미 등록된 artifact_id는 RegisterConflictError.

        Args:
            artifact: 등록할 LoRAArtifact

        Raises:
            RegisterConflictError: 중복 artifact_id
        """
        aid = artifact.artifact_id
        if aid in self._artifacts:
            raise RegisterConflictError(
                f"LoRAModelRegistry: artifact '{aid}' 이미 등록됨. "
                f"재등록 불가 (B-M-03 무결성 원칙)."
            )
        # 최초 등록은 CANDIDATE으로 강제
        if artifact.stage not in (ArtifactStage.CANDIDATE, ArtifactStage.PENDING):
            warnings.warn(
                f"register(): artifact stage={artifact.stage.value} → CANDIDATE으로 정규화.",
                UserWarning,
                stacklevel=2,
            )
            artifact.stage = ArtifactStage.CANDIDATE
        self._artifacts[aid] = artifact
        self._persist()

    # ------------------------------------------------------------------
    # 조회
    # ------------------------------------------------------------------

    def get(self, artifact_id: str) -> LoRAArtifact:
        """
        artifact_id로 아티팩트 조회.

        Raises:
            ArtifactNotFoundError: 미등록 artifact_id
        """
        if artifact_id not in self._artifacts:
            raise ArtifactNotFoundError(
                f"LoRAModelRegistry: artifact '{artifact_id}' 미등록."
            )
        return self._artifacts[artifact_id]

    def list_all(self) -> List[LoRAArtifact]:
        """전체 아티팩트 목록 (등록 순)."""
        return list(self._artifacts.values())

    def list_by_stage(self, stage: ArtifactStage) -> List[LoRAArtifact]:
        """특정 단계 아티팩트 목록."""
        return [a for a in self._artifacts.values() if a.stage == stage]

    def get_active(self) -> Optional[LoRAArtifact]:
        """
        현재 PROMOTED(서빙 활성화) 아티팩트 반환.
        여러 개이면 created_at 최신 기준.
        없으면 None.
        """
        promoted = self.list_by_stage(ArtifactStage.PROMOTED)
        if not promoted:
            return None
        return max(promoted, key=lambda a: a.created_at)

    def find_by_commit(self, commit_tag: str) -> List[LoRAArtifact]:
        """commit_tag prefix로 아티팩트 검색 (7자 short SHA)."""
        prefix = commit_tag[:7]
        return [
            a for a in self._artifacts.values()
            if a.commit_tag[:7] == prefix
        ]

    def find_by_seed(self, seed_tag: int) -> List[LoRAArtifact]:
        """seed_tag로 아티팩트 검색."""
        return [a for a in self._artifacts.values() if a.seed_tag == seed_tag]

    # ------------------------------------------------------------------
    # 단계 전환
    # ------------------------------------------------------------------

    def promote(self, artifact_id: str) -> ArtifactStage:
        """
        아티팩트를 다음 단계로 승격.

        CANDIDATE → VALIDATED → PROMOTED

        Returns:
            승격 후 새 ArtifactStage

        Raises:
            ArtifactNotFoundError: 미등록
            StageTransitionError: 승격 불가 단계
        """
        artifact = self.get(artifact_id)
        current = artifact.stage
        if current not in self._PROMOTE_PATH:
            raise StageTransitionError(
                f"promote(): stage={current.value}은(는) 승격 불가. "
                f"허용: {[s.value for s in self._PROMOTE_PATH]}"
            )
        next_stage = self._PROMOTE_PATH[current]

        # PROMOTED 승격 시 기존 PROMOTED를 RETIRED로 전환
        if next_stage == ArtifactStage.PROMOTED:
            for a in self.list_by_stage(ArtifactStage.PROMOTED):
                if a.artifact_id != artifact_id:
                    a.stage = ArtifactStage.RETIRED
                    warnings.warn(
                        f"promote(): 기존 PROMOTED artifact '{a.artifact_id}' → RETIRED 전환.",
                        UserWarning,
                        stacklevel=2,
                    )

        artifact.stage = next_stage
        self._persist()
        return next_stage

    def retire(self, artifact_id: str) -> None:
        """
        PROMOTED 아티팩트를 RETIRED 처리.

        Raises:
            ArtifactNotFoundError: 미등록
            StageTransitionError: PROMOTED가 아닌 경우
        """
        artifact = self.get(artifact_id)
        if artifact.stage != ArtifactStage.PROMOTED:
            raise StageTransitionError(
                f"retire(): artifact '{artifact_id}' stage={artifact.stage.value} — "
                f"PROMOTED 상태만 retire 가능."
            )
        artifact.stage = ArtifactStage.RETIRED
        self._persist()

    def mark_corrupted(self, artifact_id: str) -> None:
        """
        sha256 검증 실패 등으로 아티팩트를 CORRUPTED 처리.

        Raises:
            ArtifactNotFoundError: 미등록
        """
        artifact = self.get(artifact_id)
        artifact.stage = ArtifactStage.CORRUPTED
        self._persist()

    # ------------------------------------------------------------------
    # 통계
    # ------------------------------------------------------------------

    def summary(self) -> Dict[str, int]:
        """단계별 아티팩트 수 요약."""
        counts: Dict[str, int] = {s.value: 0 for s in ArtifactStage}
        for a in self._artifacts.values():
            counts[a.stage.value] += 1
        return counts

    # ------------------------------------------------------------------
    # 영속화
    # ------------------------------------------------------------------

    def _persist(self) -> None:
        """레지스트리를 JSON 파일로 저장 (registry_dir 설정 시)."""
        if not self._registry_dir:
            return
        p = Path(self._registry_dir)
        p.mkdir(parents=True, exist_ok=True)
        registry_path = p / REGISTRY_FILENAME
        data = {
            "schema_version": self._schema_version,
            "created_at":     self._created_at,
            "updated_at":     datetime.now(timezone.utc).isoformat(),
            "artifacts":      [a.to_dict() for a in self._artifacts.values()],
        }
        try:  # BUG-C3-3 수정: OSError 예외 처리 (2026-05-23)
            with open(registry_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except OSError as exc:
            import logging
            logging.getLogger(__name__).error("레지스트리 저장 실패: %s", exc)

    def _load_if_exists(self) -> None:
        """레지스트리 JSON 파일이 존재하면 로드."""
        registry_path = Path(self._registry_dir) / REGISTRY_FILENAME
        if not registry_path.exists():
            return
        try:  # BUG-C3-2 수정: JSONDecodeError/OSError 예외 처리 (2026-05-23)
            with open(registry_path, encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            import logging
            logging.getLogger(__name__).warning(
                "레지스트리 로드 실패 (%s) — 빈 레지스트리로 초기화", exc)
            return
        self._schema_version = data.get("schema_version", REGISTRY_SCHEMA_VERSION)
        self._created_at     = data.get("created_at", self._created_at)
        for d in data.get("artifacts", []):
            a = LoRAArtifact.from_dict(d)
            self._artifacts[a.artifact_id] = a

    def save(self) -> str:
        """
        명시적 저장 호출.

        Returns:
            저장된 파일 경로 (registry_dir 미설정 시 빈 문자열)
        """
        if not self._registry_dir:
            return ""
        self._persist()
        return str(Path(self._registry_dir) / REGISTRY_FILENAME)

    @classmethod
    def load(cls, registry_dir: str) -> "LoRAModelRegistry":
        """
        디렉토리에서 레지스트리 로드 (팩토리).

        Args:
            registry_dir: 레지스트리 JSON이 있는 디렉토리

        Returns:
            LoRAModelRegistry 인스턴스
        """
        return cls(registry_dir=registry_dir)

    # ------------------------------------------------------------------
    # 편의
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return len(self._artifacts)

    def __contains__(self, artifact_id: str) -> bool:
        return artifact_id in self._artifacts

    def __repr__(self) -> str:
        summary = self.summary()
        parts = [f"{k}={v}" for k, v in summary.items() if v > 0]
        return f"LoRAModelRegistry(total={len(self)}, {', '.join(parts)})"
