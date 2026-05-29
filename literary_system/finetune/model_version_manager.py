"""
ModelVersionManager v2 — 파인튜닝 모델 버전 관리 (V472)

ADR-006: ModelLifecycle (등록·승격·드리프트·폐기, 30일 롤백)
ADR-017: Canary KPI Monitor (5분 윈도우, 자동 롤백)

설계:
  - 모델 등록 (register)
  - 카나리 단계적 승격 (1% → 5% → 25% → 100%)
  - 30일 롤백 보관 보장
  - 자동 폐기: 등록 후 31일 초과 + 비활성
  - LLM-0: 버전 관리 로직 전체 규칙 기반
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

# ---------------------------------------------------------------------------
# 열거형
# ---------------------------------------------------------------------------

class ModelStage(str, Enum):
    REGISTERED = "registered"     # 등록 완료
    CANARY = "canary"             # 카나리 배포 중
    PRODUCTION = "production"     # 프로덕션 100%
    RETIRED = "retired"           # 폐기


class PromotionStep(str, Enum):
    PCT_1 = "1pct"
    PCT_5 = "5pct"
    PCT_25 = "25pct"
    PCT_100 = "100pct"


# 카나리 단계 순서
CANARY_STEPS = [1, 5, 25, 100]


# ---------------------------------------------------------------------------
# 데이터 클래스
# ---------------------------------------------------------------------------

@dataclass
class ModelArtifact:
    artifact_id: str
    model_id: str
    base_model: str
    method: str               # lora / qlora / openai_t2
    file_path: str | None = None
    checksum: str = ""
    size_mb: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "model_id": self.model_id,
            "base_model": self.base_model,
            "method": self.method,
            "file_path": self.file_path,
            "checksum": self.checksum,
            "size_mb": self.size_mb,
            "created_at": self.created_at,
        }


@dataclass
class ModelVersion:
    version_id: str
    model_id: str
    version_tag: str          # e.g. "v1.0", "v1.1-canary"
    stage: ModelStage
    canary_pct: int           # 0~100 트래픽 비율
    artifact: ModelArtifact
    eval_report_id: str | None = None
    safety_report_id: str | None = None
    registered_at: str = ""
    promoted_at: str | None = None
    retired_at: str | None = None
    rollback_deadline: str = ""    # 30일 롤백 보장 기한
    promotion_history: list[dict[str, Any]] = field(default_factory=list)
    notes: str = ""

    def __post_init__(self):
        now = datetime.now(timezone.utc)
        if not self.registered_at:
            self.registered_at = now.isoformat()
        if not self.rollback_deadline:
            self.rollback_deadline = (now + timedelta(days=30)).isoformat()

    @property
    def is_rollback_available(self) -> bool:
        deadline = datetime.fromisoformat(self.rollback_deadline)
        return datetime.now(timezone.utc) <= deadline

    def to_dict(self) -> dict[str, Any]:
        return {
            "version_id": self.version_id,
            "model_id": self.model_id,
            "version_tag": self.version_tag,
            "stage": self.stage.value,
            "canary_pct": self.canary_pct,
            "artifact_id": self.artifact.artifact_id,
            "eval_report_id": self.eval_report_id,
            "safety_report_id": self.safety_report_id,
            "registered_at": self.registered_at,
            "promoted_at": self.promoted_at,
            "retired_at": self.retired_at,
            "rollback_deadline": self.rollback_deadline,
            "rollback_available": self.is_rollback_available,
            "promotion_history": self.promotion_history,
            "notes": self.notes,
        }


# ---------------------------------------------------------------------------
# ModelVersionManager v2
# ---------------------------------------------------------------------------

class ModelVersionManager:
    """
    ADR-006 모델 버전 관리자.

    register(model_id, artifact) → version_id
    canary_promote(version_id, pct) → ModelVersion
    promote_to_production(version_id) → ModelVersion
    rollback(version_id) → bool
    retire(version_id) → bool
    list_versions(model_id) → list[ModelVersion]
    """

    MAX_RETAINED_VERSIONS = 10  # 모델당 최대 버전 수

    def __init__(self) -> None:
        self._versions: dict[str, ModelVersion] = {}       # version_id → ModelVersion
        self._by_model: dict[str, list[str]] = {}           # model_id → [version_ids]

    # ------------------------------------------------------------------
    # 등록
    # ------------------------------------------------------------------

    def register(
        self,
        model_id: str,
        artifact: ModelArtifact,
        version_tag: str | None = None,
        eval_report_id: str | None = None,
        safety_report_id: str | None = None,
        notes: str = "",
    ) -> str:
        """
        파인튜닝 모델 등록.
        Returns: version_id
        """
        version_id = f"ver-{str(uuid.uuid4())[:8]}"
        existing = self._by_model.get(model_id, [])
        if version_tag is None:
            version_tag = f"v{len(existing) + 1}.0"

        version = ModelVersion(
            version_id=version_id,
            model_id=model_id,
            version_tag=version_tag,
            stage=ModelStage.REGISTERED,
            canary_pct=0,
            artifact=artifact,
            eval_report_id=eval_report_id,
            safety_report_id=safety_report_id,
            notes=notes,
        )
        self._versions[version_id] = version
        self._by_model.setdefault(model_id, []).append(version_id)
        return version_id

    # ------------------------------------------------------------------
    # 카나리 승격
    # ------------------------------------------------------------------

    def canary_promote(
        self,
        version_id: str,
        pct: int,
    ) -> ModelVersion:
        """
        카나리 트래픽 비율 설정 (1 → 5 → 25 → 100).
        100%이면 PRODUCTION으로 전환.
        """
        version = self._get_or_raise(version_id)
        if version.stage == ModelStage.RETIRED:
            raise ValueError(f"폐기된 버전은 승격 불가: {version_id}")
        if pct not in CANARY_STEPS:
            raise ValueError(f"카나리 비율은 {CANARY_STEPS} 중 하나여야 합니다.")

        now = datetime.now(timezone.utc).isoformat()
        prev_pct = version.canary_pct
        version.canary_pct = pct
        version.stage = ModelStage.PRODUCTION if pct == 100 else ModelStage.CANARY
        if version.stage == ModelStage.PRODUCTION:
            version.promoted_at = now

        version.promotion_history.append({
            "from_pct": prev_pct,
            "to_pct": pct,
            "promoted_at": now,
        })
        return version

    def promote_to_production(self, version_id: str) -> ModelVersion:
        """100% 프로덕션 직행 승격"""
        return self.canary_promote(version_id, 100)

    # ------------------------------------------------------------------
    # 롤백 (ADR-006: 30일 보장)
    # ------------------------------------------------------------------

    def rollback(self, version_id: str) -> bool:
        """
        버전을 REGISTERED 상태로 롤백.
        30일 기한 내에만 가능.
        """
        version = self._get_or_raise(version_id)
        if not version.is_rollback_available:
            raise ValueError(
                f"롤백 기한 초과 ({version.rollback_deadline}). "
                "ADR-006: 30일 보장 기간 종료."
            )
        if version.stage == ModelStage.RETIRED:
            return False

        now = datetime.now(timezone.utc).isoformat()
        prev_stage = version.stage.value   # Bug-Fix: 변경 전에 캡처
        version.stage = ModelStage.REGISTERED
        version.canary_pct = 0
        version.promotion_history.append({
            "action": "rollback",
            "from_stage": prev_stage,
            "rolled_back_at": now,
        })
        return True

    # ------------------------------------------------------------------
    # 폐기
    # ------------------------------------------------------------------

    def retire(self, version_id: str) -> bool:
        """버전 폐기 (RETIRED 상태)"""
        version = self._get_or_raise(version_id)
        if version.stage == ModelStage.RETIRED:
            return False
        now = datetime.now(timezone.utc).isoformat()
        version.stage = ModelStage.RETIRED
        version.retired_at = now
        return True

    def auto_retire_expired(self) -> list[str]:
        """
        31일 초과 + 비프로덕션 버전 자동 폐기.
        Returns: 폐기된 version_id 목록
        """
        retired: list[str] = []
        now = datetime.now(timezone.utc)
        for version in self._versions.values():
            if version.stage in (ModelStage.RETIRED, ModelStage.PRODUCTION):
                continue
            reg_dt = datetime.fromisoformat(version.registered_at)
            if (now - reg_dt).days > 30:
                version.stage = ModelStage.RETIRED
                version.retired_at = now.isoformat()
                retired.append(version.version_id)
        return retired

    # ------------------------------------------------------------------
    # 조회
    # ------------------------------------------------------------------

    def get_version(self, version_id: str) -> ModelVersion:
        return self._get_or_raise(version_id)

    def list_versions(
        self,
        model_id: str | None = None,
        stage_filter: ModelStage | None = None,
    ) -> list[ModelVersion]:
        if model_id:
            ids = self._by_model.get(model_id, [])
            versions = [self._versions[vid] for vid in ids if vid in self._versions]
        else:
            versions = list(self._versions.values())
        if stage_filter:
            versions = [v for v in versions if v.stage == stage_filter]
        return sorted(versions, key=lambda v: v.registered_at, reverse=True)

    def get_production_version(self, model_id: str) -> ModelVersion | None:
        for v in self.list_versions(model_id):
            if v.stage == ModelStage.PRODUCTION:
                return v
        return None

    def _get_or_raise(self, version_id: str) -> ModelVersion:
        v = self._versions.get(version_id)
        if v is None:
            raise KeyError(f"버전 미발견: {version_id}")
        return v
