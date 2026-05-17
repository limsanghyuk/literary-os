"""
PIA Generator — GDPR/PIPA Privacy Impact Assessment 자동 생성 (V463)

ADR-011: GDPR/PIPA Dual Compliance
LLM-0: 외부 LLM 호출 없음. 모든 평가는 규칙 기반.

PIA (Privacy Impact Assessment / 개인정보 영향평가) 를 수행하여
  - 처리 목적, 범주, 법적 근거, 위험 등급을 자동 산출
  - DPO 승인이 필요한 고위험 처리 항목 플래그 처리
"""
from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# 열거형
# ---------------------------------------------------------------------------

class DataCategory(str, Enum):
    GENERAL = "general"            # 일반 개인정보
    SENSITIVE = "sensitive"        # 민감정보 (GDPR Art.9 / PIPA §23)
    FINANCIAL = "financial"        # 금융정보
    HEALTH = "health"              # 건강/의료
    BIOMETRIC = "biometric"        # 생체정보
    CHILDREN = "children"          # 아동 (<14세 PIPA, <16세 GDPR)
    LOCATION = "location"          # 위치정보
    BEHAVIORAL = "behavioral"      # 행동/프로파일링


class LegalBasis(str, Enum):
    CONSENT = "consent"                        # 정보주체 동의
    CONTRACT = "contract"                      # 계약 이행
    LEGAL_OBLIGATION = "legal_obligation"      # 법적 의무
    VITAL_INTEREST = "vital_interest"          # 생명·신체 보호
    PUBLIC_TASK = "public_task"                # 공익·공무
    LEGITIMATE_INTEREST = "legitimate_interest"  # 정당한 이익


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"     # DPO 승인 필수


class PIAStatus(str, Enum):
    DRAFT = "draft"
    PENDING_DPO = "pending_dpo"
    APPROVED = "approved"
    REJECTED = "rejected"


# ---------------------------------------------------------------------------
# 데이터 클래스
# ---------------------------------------------------------------------------

@dataclass
class ProcessingActivity:
    """개인정보 처리 활동 단위"""
    name: str
    purpose: str
    data_categories: list[DataCategory]
    legal_basis: LegalBasis
    recipients: list[str] = field(default_factory=list)
    retention_days: int = 365
    cross_border: bool = False
    automated_decision: bool = False    # 자동화된 의사결정 (GDPR Art.22)
    children_data: bool = False


@dataclass
class PIARiskItem:
    category: str
    description: str
    likelihood: int         # 1-5
    impact: int             # 1-5
    mitigation: str

    @property
    def score(self) -> int:
        return self.likelihood * self.impact

    @property
    def level(self) -> RiskLevel:
        if self.score >= 20:
            return RiskLevel.VERY_HIGH
        elif self.score >= 12:
            return RiskLevel.HIGH
        elif self.score >= 6:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW


@dataclass
class PIAReport:
    pia_id: str
    tenant_id: str
    activity: ProcessingActivity
    risk_items: list[PIARiskItem]
    overall_risk: RiskLevel
    dpo_required: bool
    status: PIAStatus
    created_at: str
    recommendations: list[str]
    checksum: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "pia_id": self.pia_id,
            "tenant_id": self.tenant_id,
            "activity": {
                "name": self.activity.name,
                "purpose": self.activity.purpose,
                "data_categories": [c.value for c in self.activity.data_categories],
                "legal_basis": self.activity.legal_basis.value,
                "recipients": self.activity.recipients,
                "retention_days": self.activity.retention_days,
                "cross_border": self.activity.cross_border,
                "automated_decision": self.activity.automated_decision,
                "children_data": self.activity.children_data,
            },
            "risk_items": [
                {
                    "category": r.category,
                    "description": r.description,
                    "likelihood": r.likelihood,
                    "impact": r.impact,
                    "score": r.score,
                    "level": r.level.value,
                    "mitigation": r.mitigation,
                }
                for r in self.risk_items
            ],
            "overall_risk": self.overall_risk.value,
            "dpo_required": self.dpo_required,
            "status": self.status.value,
            "created_at": self.created_at,
            "recommendations": self.recommendations,
            "checksum": self.checksum,
        }


# ---------------------------------------------------------------------------
# 위험 평가 규칙 (LLM-0 — 규칙 기반)
# ---------------------------------------------------------------------------

_HIGH_RISK_CATEGORIES = {
    DataCategory.SENSITIVE,
    DataCategory.HEALTH,
    DataCategory.BIOMETRIC,
    DataCategory.CHILDREN,
}

_RISK_RULES: list[dict] = [
    {
        "id": "R01",
        "condition": lambda a: any(c in _HIGH_RISK_CATEGORIES for c in a.data_categories),
        "category": "민감 데이터 처리",
        "description": "민감정보·건강·생체·아동 데이터 처리는 높은 침해 위험을 수반합니다.",
        "likelihood": 3, "impact": 5,
        "mitigation": "최소 수집 원칙 적용, 별도 동의 확보, 암호화 저장 의무화",
    },
    {
        "id": "R02",
        "condition": lambda a: a.cross_border,
        "category": "국경 간 이전",
        "description": "EU/KR 규정 외 국가로 개인정보 이전 시 적정성 결정 또는 표준계약조항(SCC) 필요.",
        "likelihood": 3, "impact": 4,
        "mitigation": "이전 국가 적정성 평가, SCC 체결, 이전 기록 유지",
    },
    {
        "id": "R03",
        "condition": lambda a: a.automated_decision,
        "category": "자동화된 의사결정",
        "description": "GDPR Art.22 / PIPA §16 — 프로파일링·자동 결정에 대한 정보주체 이의제기권 보장 필요.",
        "likelihood": 2, "impact": 4,
        "mitigation": "인간 검토 옵션 제공, 결정 근거 설명 API 구현",
    },
    {
        "id": "R04",
        "condition": lambda a: a.children_data,
        "category": "아동 개인정보",
        "description": "아동(GDPR <16세, PIPA <14세) 데이터는 법정대리인 동의 필수.",
        "likelihood": 4, "impact": 5,
        "mitigation": "연령 인증 메커니즘 구현, 법정대리인 동의 플로우 확보",
    },
    {
        "id": "R05",
        "condition": lambda a: a.retention_days > 365 * 3,
        "category": "장기 보존",
        "description": "3년 초과 개인정보 보존은 목적 외 처리 위험 증가.",
        "likelihood": 2, "impact": 3,
        "mitigation": "보존 기간 재검토, 익명화·삭제 자동화 파이프라인 구축",
    },
    {
        "id": "R06",
        "condition": lambda a: a.legal_basis == LegalBasis.LEGITIMATE_INTEREST,
        "category": "정당한 이익 법적 근거",
        "description": "정당한 이익(LIA) 근거는 이익 균형 테스트(Balancing Test) 문서화 필요.",
        "likelihood": 3, "impact": 3,
        "mitigation": "LIA 문서 작성, 정보주체 이익·권리 침해 여부 평가 기록",
    },
    {
        "id": "R07",
        "condition": lambda a: len(a.recipients) > 5,
        "category": "다수 수신자",
        "description": "5개 초과 수신자에게 공유 시 정보 통제력 약화.",
        "likelihood": 3, "impact": 3,
        "mitigation": "수신자 목록 최소화, 데이터 처리 위탁 계약(DPA) 전수 체결",
    },
]


# ---------------------------------------------------------------------------
# PIAGenerator
# ---------------------------------------------------------------------------

class PIAGenerator:
    """
    GDPR/PIPA 개인정보 영향평가(PIA) 자동 생성기.

    LLM-0: 외부 LLM 없음. 규칙 엔진 기반 위험 산출.
    """

    def __init__(self) -> None:
        self._reports: dict[str, PIAReport] = {}

    # ------------------------------------------------------------------
    def generate(self, tenant_id: str, activity: ProcessingActivity) -> PIAReport:
        """ProcessingActivity → PIAReport 생성"""
        risk_items: list[PIARiskItem] = []

        for rule in _RISK_RULES:
            if rule["condition"](activity):
                risk_items.append(PIARiskItem(
                    category=rule["category"],
                    description=rule["description"],
                    likelihood=rule["likelihood"],
                    impact=rule["impact"],
                    mitigation=rule["mitigation"],
                ))

        # overall_risk = 최고 점수 항목 기준
        if risk_items:
            max_score = max(r.score for r in risk_items)
            if max_score >= 20:
                overall = RiskLevel.VERY_HIGH
            elif max_score >= 12:
                overall = RiskLevel.HIGH
            elif max_score >= 6:
                overall = RiskLevel.MEDIUM
            else:
                overall = RiskLevel.LOW
        else:
            overall = RiskLevel.LOW

        dpo_required = overall in (RiskLevel.HIGH, RiskLevel.VERY_HIGH)
        status = PIAStatus.PENDING_DPO if dpo_required else PIAStatus.DRAFT

        recommendations = self._build_recommendations(activity, overall)

        pia_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()

        report = PIAReport(
            pia_id=pia_id,
            tenant_id=tenant_id,
            activity=activity,
            risk_items=risk_items,
            overall_risk=overall,
            dpo_required=dpo_required,
            status=status,
            created_at=created_at,
            recommendations=recommendations,
        )

        # 무결성 체크섬
        report.checksum = self._checksum(report)
        self._reports[pia_id] = report
        return report

    # ------------------------------------------------------------------
    def get_report(self, pia_id: str) -> PIAReport | None:
        return self._reports.get(pia_id)

    def list_reports(self, tenant_id: str) -> list[PIAReport]:
        return [r for r in self._reports.values() if r.tenant_id == tenant_id]

    def pending_dpo_reports(self) -> list[PIAReport]:
        return [r for r in self._reports.values() if r.status == PIAStatus.PENDING_DPO]

    # ------------------------------------------------------------------
    @staticmethod
    def _build_recommendations(activity: ProcessingActivity, risk: RiskLevel) -> list[str]:
        recs: list[str] = []
        if risk in (RiskLevel.HIGH, RiskLevel.VERY_HIGH):
            recs.append("DPO 사전 자문 및 DPIA(Data Protection Impact Assessment) 정식 수행 권고")
        if activity.cross_border:
            recs.append("국경 간 이전 전 적정성 결정 확인 또는 SCC/BCR 체결 필수")
        if activity.children_data:
            recs.append("아동 동의 플로우 법적 검토 및 법정대리인 확인 메커니즘 구현")
        if activity.automated_decision:
            recs.append("자동화 결정에 대한 인간 검토 옵션 및 이의제기 프로세스 문서화")
        if DataCategory.BIOMETRIC in activity.data_categories:
            recs.append("생체정보 별도 동의서 확보 및 접근 제어 강화")
        if not recs:
            recs.append("현재 위험 수준 낮음 — 정기 재검토(6개월) 일정 설정 권고")
        return recs

    @staticmethod
    def _checksum(report: PIAReport) -> str:
        payload = json.dumps({
            "pia_id": report.pia_id,
            "tenant_id": report.tenant_id,
            "activity_name": report.activity.name,
            "overall_risk": report.overall_risk.value,
            "created_at": report.created_at,
        }, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()[:16]
