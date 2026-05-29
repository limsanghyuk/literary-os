"""
DataResidencyRouter — 데이터 상주 라우터 (V467)

ADR-016: DataResidencyRouter (KR/EU/US 지역 라우팅)
LLM-0: 외부 LLM 없음. 규칙 기반 라우팅.

설계:
  - 테넌트/사용자 지역 정책에 따라 데이터 저장/처리 경로 결정
  - KR: 국내 우선 (PIPA §30), EU: GDPR 적정성 결정 국가 한정
  - US: CCPA 적용 + SCCs
  - 지역 정책 위반 시 RouteViolation 기록
  - 테넌트별 고정 정책 + 사용자별 오버라이드 지원

지역 코드:
  KR-SEOUL, KR-BUSAN   → 한국 데이터센터
  EU-IE, EU-DE         → EU 데이터센터 (아일랜드, 독일)
  US-VA, US-OR         → 미국 데이터센터 (버지니아, 오레곤)
  GLOBAL               → 최적 지역 자동 선택
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

# ---------------------------------------------------------------------------
# 열거형
# ---------------------------------------------------------------------------

class DataRegion(str, Enum):
    KR_SEOUL = "kr-seoul"
    KR_BUSAN = "kr-busan"
    EU_IE = "eu-ie"         # 아일랜드
    EU_DE = "eu-de"         # 독일
    US_VA = "us-va"         # 버지니아
    US_OR = "us-or"         # 오레곤
    GLOBAL = "global"       # 자동 선택


class ResidencyPolicy(str, Enum):
    KR_ONLY = "kr_only"             # 한국 내 한정 (PIPA 강화)
    EU_ONLY = "eu_only"             # EU 내 한정 (GDPR 적정성)
    US_ONLY = "us_only"             # 미국 내 한정
    KR_EU = "kr_eu"                 # 한국 + EU 허용
    KR_US = "kr_us"                 # 한국 + 미국 허용
    ANY = "any"                     # 제한 없음


class RouteResult(str, Enum):
    ROUTED = "routed"               # 정상 라우팅
    VIOLATION = "violation"         # 정책 위반
    FALLBACK = "fallback"           # 폴백 지역 사용


# ---------------------------------------------------------------------------
# 지역 정책 테이블
# ---------------------------------------------------------------------------

# 지역 코드 → 법적 관할 (법적 준거법)
_REGION_JURISDICTION: dict[DataRegion, str] = {
    DataRegion.KR_SEOUL: "KR",
    DataRegion.KR_BUSAN: "KR",
    DataRegion.EU_IE: "EU",
    DataRegion.EU_DE: "EU",
    DataRegion.US_VA: "US",
    DataRegion.US_OR: "US",
    DataRegion.GLOBAL: "GLOBAL",
}

# 정책별 허용 지역
_POLICY_ALLOWED_REGIONS: dict[ResidencyPolicy, set[DataRegion]] = {
    ResidencyPolicy.KR_ONLY: {DataRegion.KR_SEOUL, DataRegion.KR_BUSAN},
    ResidencyPolicy.EU_ONLY: {DataRegion.EU_IE, DataRegion.EU_DE},
    ResidencyPolicy.US_ONLY: {DataRegion.US_VA, DataRegion.US_OR},
    ResidencyPolicy.KR_EU: {DataRegion.KR_SEOUL, DataRegion.KR_BUSAN, DataRegion.EU_IE, DataRegion.EU_DE},
    ResidencyPolicy.KR_US: {DataRegion.KR_SEOUL, DataRegion.KR_BUSAN, DataRegion.US_VA, DataRegion.US_OR},
    ResidencyPolicy.ANY: set(DataRegion),
}

# 정책별 기본 우선 지역 (latency 최적)
_POLICY_DEFAULT_REGION: dict[ResidencyPolicy, DataRegion] = {
    ResidencyPolicy.KR_ONLY: DataRegion.KR_SEOUL,
    ResidencyPolicy.EU_ONLY: DataRegion.EU_IE,
    ResidencyPolicy.US_ONLY: DataRegion.US_VA,
    ResidencyPolicy.KR_EU: DataRegion.KR_SEOUL,
    ResidencyPolicy.KR_US: DataRegion.KR_SEOUL,
    ResidencyPolicy.ANY: DataRegion.KR_SEOUL,
}


# ---------------------------------------------------------------------------
# 데이터 클래스
# ---------------------------------------------------------------------------

@dataclass
class TenantResidencyConfig:
    """테넌트별 데이터 상주 설정"""
    tenant_id: str
    policy: ResidencyPolicy
    preferred_region: DataRegion | None = None   # None이면 정책 기본값
    allow_fallback: bool = True                  # 주 지역 불가 시 폴백 허용
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        now = datetime.now(timezone.utc).isoformat()
        if not self.created_at:
            self.created_at = now
        self.updated_at = now


@dataclass
class ResidencyRouteDecision:
    decision_id: str
    tenant_id: str
    requested_region: DataRegion | None
    routed_region: DataRegion
    result: RouteResult
    policy: ResidencyPolicy
    reason: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "tenant_id": self.tenant_id,
            "requested_region": self.requested_region.value if self.requested_region else None,
            "routed_region": self.routed_region.value,
            "result": self.result.value,
            "policy": self.policy.value,
            "reason": self.reason,
            "created_at": self.created_at,
        }


@dataclass
class RouteViolation:
    violation_id: str
    tenant_id: str
    requested_region: DataRegion
    policy: ResidencyPolicy
    reason: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "violation_id": self.violation_id,
            "tenant_id": self.tenant_id,
            "requested_region": self.requested_region.value,
            "policy": self.policy.value,
            "reason": self.reason,
            "created_at": self.created_at,
        }


# ---------------------------------------------------------------------------
# DataResidencyRouter
# ---------------------------------------------------------------------------

class DataResidencyRouter:
    """
    ADR-016 데이터 상주 라우터.

    route(tenant_id, requested_region) → RouteDecision
      - 테넌트 정책 확인
      - 요청 지역이 정책 내 허용 여부 판단
      - 위반 시 violations 기록, fallback 지역 반환

    LLM-0: 외부 LLM 없음. 정적 정책 테이블 기반.
    """

    def __init__(self) -> None:
        self._configs: dict[str, TenantResidencyConfig] = {}
        self._decisions: list[RouteDecision] = []
        self._violations: list[RouteViolation] = []

    # ------------------------------------------------------------------
    # 설정 관리
    # ------------------------------------------------------------------

    def set_tenant_config(self, config: TenantResidencyConfig) -> None:
        self._configs[config.tenant_id] = config

    def get_tenant_config(self, tenant_id: str) -> TenantResidencyConfig | None:
        return self._configs.get(tenant_id)

    # ------------------------------------------------------------------
    # 라우팅 결정
    # ------------------------------------------------------------------

    def route(
        self,
        tenant_id: str,
        requested_region: DataRegion | None = None,
        data_type: str = "general",
    ) -> RouteDecision:
        """
        데이터 라우팅 결정.

        requested_region=None이면 테넌트 기본 지역으로 라우팅.
        """
        config = self._configs.get(tenant_id)
        if config is None:
            # 미설정 테넌트 → ANY 정책 기본값
            config = TenantResidencyConfig(
                tenant_id=tenant_id,
                policy=ResidencyPolicy.ANY,
            )

        policy = config.policy
        allowed = _POLICY_ALLOWED_REGIONS[policy]
        default_region = config.preferred_region or _POLICY_DEFAULT_REGION[policy]

        now = datetime.now(timezone.utc).isoformat()

        # 지역 요청 없음 → 기본 지역 사용
        if requested_region is None:
            decision = RouteDecision(
                decision_id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                requested_region=None,
                routed_region=default_region,
                result=RouteResult.ROUTED,
                policy=policy,
                reason=f"기본 지역 사용: {default_region.value}",
                created_at=now,
            )
            self._decisions.append(decision)
            return decision

        # 요청 지역이 허용 목록 내
        if requested_region in allowed:
            decision = RouteDecision(
                decision_id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                requested_region=requested_region,
                routed_region=requested_region,
                result=RouteResult.ROUTED,
                policy=policy,
                reason=f"정책 허용 지역: {requested_region.value}",
                created_at=now,
            )
            self._decisions.append(decision)
            return decision

        # 정책 위반
        violation = RouteViolation(
            violation_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            requested_region=requested_region,
            policy=policy,
            reason=f"{requested_region.value}은(는) {policy.value} 정책 위반",
            created_at=now,
        )
        self._violations.append(violation)

        if config.allow_fallback:
            # 폴백 → 허용 지역 중 기본값
            fallback = default_region
            decision = RouteDecision(
                decision_id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                requested_region=requested_region,
                routed_region=fallback,
                result=RouteResult.FALLBACK,
                policy=policy,
                reason=f"정책 위반({requested_region.value}) → 폴백: {fallback.value}",
                created_at=now,
            )
        else:
            # 폴백 불허 → 위반 기록 + 기본 지역
            decision = RouteDecision(
                decision_id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                requested_region=requested_region,
                routed_region=default_region,
                result=RouteResult.VIOLATION,
                policy=policy,
                reason=f"정책 위반: {requested_region.value} ({policy.value} 불허)",
                created_at=now,
            )
        self._decisions.append(decision)
        return decision

    # ------------------------------------------------------------------
    # 조회
    # ------------------------------------------------------------------

    def get_violations(self, tenant_id: str | None = None) -> list[RouteViolation]:
        if tenant_id:
            return [v for v in self._violations if v.tenant_id == tenant_id]
        return list(self._violations)

    def get_decisions(self, tenant_id: str | None = None) -> list[RouteDecision]:
        if tenant_id:
            return [d for d in self._decisions if d.tenant_id == tenant_id]
        return list(self._decisions)

    def is_region_allowed(self, tenant_id: str, region: DataRegion) -> bool:
        config = self._configs.get(tenant_id)
        if config is None:
            return True   # 미설정 → ANY
        return region in _POLICY_ALLOWED_REGIONS[config.policy]

RouteDecision = ResidencyRouteDecision  # V579 backward-compat alias
