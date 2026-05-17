"""
EUAIActGovernance — EU AI Act 고위험 분류 + 투명성 API (V464)

ADR-012: EU AI Act High-Risk Governance
LLM-0: 외부 LLM 없음. 분류는 규칙 기반.

EU AI Act (2024년 발효):
  - Annex III 고위험 AI 시스템 분류
  - 투명성 의무 (Art.52): 생성 AI 워터마크, 딥페이크 고지
  - 정보주체 권리 (Art.86): AI 결정에 대한 설명 요구권
  - 사용자 권리 화면 (Art.13): 고위험 AI 사용 시 정보 제공
  - 금지 AI 관행 (Art.5): 무의식 조작, 사회적 점수, 생체 실시간 감시

Literary OS 관련 고위험 분류:
  - AI 기반 콘텐츠 추천 (Annex III §4 교육)
  - 개인화 창작 보조 (Annex III §5 고용)
  - 감정 분석 → 개인정보 추론 (Annex III §1 생체)
"""
from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# 열거형
# ---------------------------------------------------------------------------

class AIRiskCategory(str, Enum):
    UNACCEPTABLE = "unacceptable"   # Art.5 금지
    HIGH_RISK = "high_risk"         # Annex III
    LIMITED_RISK = "limited_risk"   # Art.52 투명성 의무
    MINIMAL_RISK = "minimal_risk"   # 자유


class AnnexIIICategory(str, Enum):
    """Annex III 고위험 카테고리"""
    BIOMETRIC = "biometric_identification"
    CRITICAL_INFRA = "critical_infrastructure"
    EDUCATION = "education_vocational"
    EMPLOYMENT = "employment_workers"
    ESSENTIAL_SERVICES = "essential_services"
    LAW_ENFORCEMENT = "law_enforcement"
    MIGRATION = "migration_asylum"
    JUSTICE = "justice_democratic"


class TransparencyObligation(str, Enum):
    AI_WATERMARK = "ai_watermark"               # 생성 AI 콘텐츠 표시
    DEEPFAKE_DISCLOSURE = "deepfake_disclosure" # 딥페이크 고지
    CHATBOT_DISCLOSURE = "chatbot_disclosure"   # 챗봇 고지
    EMOTION_DISCLOSURE = "emotion_disclosure"   # 감정 인식 시스템 고지


# ---------------------------------------------------------------------------
# 데이터 클래스
# ---------------------------------------------------------------------------

@dataclass
class AISystemProfile:
    """평가 대상 AI 시스템 프로파일"""
    system_id: str
    name: str
    purpose: str
    uses_biometric: bool = False
    affects_education: bool = False
    affects_employment: bool = False
    affects_essential_services: bool = False
    uses_emotion_recognition: bool = False
    generates_synthetic_content: bool = False   # Art.52 워터마크 의무
    uses_real_time_biometric: bool = False       # Art.5 금지 가능
    social_scoring: bool = False                 # Art.5 금지
    subliminal_manipulation: bool = False        # Art.5 금지
    interacts_with_users: bool = True


@dataclass
class RiskClassification:
    classification_id: str
    system_id: str
    risk_category: AIRiskCategory
    annex_iii_categories: list[AnnexIIICategory]
    transparency_obligations: list[TransparencyObligation]
    prohibited_practices: list[str]
    conformity_assessment_required: bool
    human_oversight_required: bool
    created_at: str
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "classification_id": self.classification_id,
            "system_id": self.system_id,
            "risk_category": self.risk_category.value,
            "annex_iii_categories": [c.value for c in self.annex_iii_categories],
            "transparency_obligations": [t.value for t in self.transparency_obligations],
            "prohibited_practices": self.prohibited_practices,
            "conformity_assessment_required": self.conformity_assessment_required,
            "human_oversight_required": self.human_oversight_required,
            "created_at": self.created_at,
            "explanation": self.explanation,
        }


@dataclass
class TransparencyRecord:
    """Art.52 투명성 의무 이행 기록"""
    record_id: str
    tenant_id: str
    system_id: str
    obligation: TransparencyObligation
    content_id: str         # 워터마크/고지가 적용된 콘텐츠 ID
    watermark_hash: str     # AI 생성 콘텐츠 식별 해시
    disclosed_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "tenant_id": self.tenant_id,
            "system_id": self.system_id,
            "obligation": self.obligation.value,
            "content_id": self.content_id,
            "watermark_hash": self.watermark_hash,
            "disclosed_at": self.disclosed_at,
        }


@dataclass
class UserRightsScreen:
    """Art.13 사용자 권리 정보 화면"""
    screen_id: str
    system_id: str
    ai_system_name: str
    risk_level: str
    purpose_description: str
    data_used: list[str]
    human_oversight: bool
    right_to_explanation: bool
    contact_dpo: str
    generated_at: str

    def render_text(self) -> str:
        oversight = "인간 감독 있음" if self.human_oversight else "자동화 처리"
        explanation = "설명 요구 가능" if self.right_to_explanation else "해당 없음"
        return (
            f"=== AI 시스템 정보 (EU AI Act Art.13) ===\n"
            f"시스템명: {self.ai_system_name}\n"
            f"위험 등급: {self.risk_level}\n"
            f"목적: {self.purpose_description}\n"
            f"사용 데이터: {', '.join(self.data_used)}\n"
            f"인간 감독: {oversight}\n"
            f"설명 요구권: {explanation}\n"
            f"DPO 연락처: {self.contact_dpo}"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "screen_id": self.screen_id,
            "system_id": self.system_id,
            "ai_system_name": self.ai_system_name,
            "risk_level": self.risk_level,
            "purpose_description": self.purpose_description,
            "data_used": self.data_used,
            "human_oversight": self.human_oversight,
            "right_to_explanation": self.right_to_explanation,
            "contact_dpo": self.contact_dpo,
            "generated_at": self.generated_at,
            "rendered_text": self.render_text(),
        }


# ---------------------------------------------------------------------------
# EUAIActGovernance
# ---------------------------------------------------------------------------

class EUAIActGovernance:
    """
    EU AI Act 거버넌스 엔진.

    classify_system()    → 위험 분류
    apply_watermark()    → Art.52 AI 생성 콘텐츠 워터마크
    generate_user_rights_screen() → Art.13 사용자 권리 화면
    check_prohibited()   → Art.5 금지 관행 체크
    """

    def __init__(self) -> None:
        self._classifications: dict[str, RiskClassification] = {}
        self._transparency_records: dict[str, TransparencyRecord] = {}
        self._user_rights_screens: dict[str, UserRightsScreen] = {}

    # ------------------------------------------------------------------
    # 1. 위험 분류 (Art.5 + Annex III)
    # ------------------------------------------------------------------

    def classify_system(self, profile: AISystemProfile) -> RiskClassification:
        """AI 시스템 프로파일 → 위험 분류"""
        prohibited = self._check_prohibited_practices(profile)

        if prohibited:
            category = AIRiskCategory.UNACCEPTABLE
            annex_cats: list[AnnexIIICategory] = []
            transparency: list[TransparencyObligation] = []
        else:
            annex_cats = self._map_annex_iii(profile)
            transparency = self._map_transparency(profile)

            if annex_cats:
                category = AIRiskCategory.HIGH_RISK
            elif transparency:
                category = AIRiskCategory.LIMITED_RISK
            else:
                category = AIRiskCategory.MINIMAL_RISK

        conformity_required = category in (
            AIRiskCategory.HIGH_RISK, AIRiskCategory.UNACCEPTABLE
        )
        human_oversight = category == AIRiskCategory.HIGH_RISK

        explanation = self._build_explanation(category, annex_cats, prohibited)

        clf = RiskClassification(
            classification_id=str(uuid.uuid4()),
            system_id=profile.system_id,
            risk_category=category,
            annex_iii_categories=annex_cats,
            transparency_obligations=transparency,
            prohibited_practices=prohibited,
            conformity_assessment_required=conformity_required,
            human_oversight_required=human_oversight,
            created_at=datetime.now(timezone.utc).isoformat(),
            explanation=explanation,
        )
        self._classifications[clf.classification_id] = clf
        return clf

    # ------------------------------------------------------------------
    # 2. AI 워터마크 (Art.52 §2 — 생성 AI 콘텐츠 표시)
    # ------------------------------------------------------------------

    def apply_watermark(
        self,
        tenant_id: str,
        system_id: str,
        content_id: str,
        content_text: str,
    ) -> TransparencyRecord:
        """AI 생성 콘텐츠에 워터마크 해시 적용"""
        # C2PA 스타일 콘텐츠 해시 (실제 스테가노그래피는 LLM-0 원칙상 로컬 처리)
        watermark_hash = hashlib.sha256(
            f"AI_GENERATED:{system_id}:{content_id}:{content_text[:64]}".encode()
        ).hexdigest()[:32]

        record = TransparencyRecord(
            record_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            system_id=system_id,
            obligation=TransparencyObligation.AI_WATERMARK,
            content_id=content_id,
            watermark_hash=watermark_hash,
            disclosed_at=datetime.now(timezone.utc).isoformat(),
        )
        self._transparency_records[record.record_id] = record
        return record

    def verify_watermark(self, record_id: str, content_text: str, content_id: str, system_id: str) -> bool:
        """워터마크 검증 (콘텐츠 무결성)"""
        record = self._transparency_records.get(record_id)
        if not record:
            return False
        expected = hashlib.sha256(
            f"AI_GENERATED:{system_id}:{content_id}:{content_text[:64]}".encode()
        ).hexdigest()[:32]
        return record.watermark_hash == expected

    # ------------------------------------------------------------------
    # 3. 사용자 권리 화면 (Art.13)
    # ------------------------------------------------------------------

    def generate_user_rights_screen(
        self,
        system_id: str,
        classification: RiskClassification,
        data_used: list[str],
        contact_dpo: str = "privacy@literary-os.com",
    ) -> UserRightsScreen:
        screen = UserRightsScreen(
            screen_id=str(uuid.uuid4()),
            system_id=system_id,
            ai_system_name=f"Literary OS AI ({system_id})",
            risk_level=classification.risk_category.value,
            purpose_description=self._purpose_description(classification),
            data_used=data_used,
            human_oversight=classification.human_oversight_required,
            right_to_explanation=classification.risk_category == AIRiskCategory.HIGH_RISK,
            contact_dpo=contact_dpo,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )
        self._user_rights_screens[screen.screen_id] = screen
        return screen

    # ------------------------------------------------------------------
    # 4. Art.5 금지 관행 체크
    # ------------------------------------------------------------------

    def check_prohibited(self, profile: AISystemProfile) -> list[str]:
        return self._check_prohibited_practices(profile)

    # ------------------------------------------------------------------
    # 내부 헬퍼
    # ------------------------------------------------------------------

    @staticmethod
    def _check_prohibited_practices(profile: AISystemProfile) -> list[str]:
        violations: list[str] = []
        if profile.subliminal_manipulation:
            violations.append("Art.5(1)(a): 무의식적 조작 기법 사용 금지")
        if profile.social_scoring:
            violations.append("Art.5(1)(c): 사회적 점수 평가 AI 금지")
        if profile.uses_real_time_biometric:
            violations.append("Art.5(1)(d): 공공장소 실시간 생체 원격식별 금지 (예외 적용 확인 필요)")
        return violations

    @staticmethod
    def _map_annex_iii(profile: AISystemProfile) -> list[AnnexIIICategory]:
        cats: list[AnnexIIICategory] = []
        if profile.uses_biometric and not profile.uses_real_time_biometric:
            cats.append(AnnexIIICategory.BIOMETRIC)
        if profile.affects_education:
            cats.append(AnnexIIICategory.EDUCATION)
        if profile.affects_employment:
            cats.append(AnnexIIICategory.EMPLOYMENT)
        if profile.affects_essential_services:
            cats.append(AnnexIIICategory.ESSENTIAL_SERVICES)
        return cats

    @staticmethod
    def _map_transparency(profile: AISystemProfile) -> list[TransparencyObligation]:
        obligations: list[TransparencyObligation] = []
        if profile.generates_synthetic_content:
            obligations.append(TransparencyObligation.AI_WATERMARK)
        if profile.uses_emotion_recognition:
            obligations.append(TransparencyObligation.EMOTION_DISCLOSURE)
        if profile.interacts_with_users:
            obligations.append(TransparencyObligation.CHATBOT_DISCLOSURE)
        return obligations

    @staticmethod
    def _build_explanation(
        category: AIRiskCategory,
        annex_cats: list[AnnexIIICategory],
        prohibited: list[str],
    ) -> str:
        if prohibited:
            return f"금지 AI 관행 감지: {'; '.join(prohibited)}"
        if category == AIRiskCategory.HIGH_RISK:
            cats_str = ", ".join(c.value for c in annex_cats)
            return f"Annex III 고위험 분류: {cats_str}. 적합성 평가(CE 마킹), 기술 문서화, 인간 감독 의무."
        if category == AIRiskCategory.LIMITED_RISK:
            return "Art.52 투명성 의무 적용 — AI 생성 콘텐츠 표시, 챗봇 고지 필수."
        return "최소 위험 — 추가 규제 의무 없음."

    @staticmethod
    def _purpose_description(clf: RiskClassification) -> str:
        if clf.risk_category == AIRiskCategory.HIGH_RISK:
            cats = ", ".join(c.value for c in clf.annex_iii_categories)
            return f"고위험 AI 시스템 ({cats}) — 개인에 중대한 영향을 미치는 결정 지원"
        if clf.risk_category == AIRiskCategory.LIMITED_RISK:
            return "제한적 위험 AI — 창작 콘텐츠 생성 및 사용자 상호작용"
        return "최소 위험 AI — 일반 보조 기능"

    # ------------------------------------------------------------------
    # 조회
    # ------------------------------------------------------------------

    def get_classification(self, classification_id: str) -> RiskClassification | None:
        return self._classifications.get(classification_id)

    def list_high_risk_systems(self) -> list[RiskClassification]:
        return [c for c in self._classifications.values()
                if c.risk_category == AIRiskCategory.HIGH_RISK]

    def list_prohibited_systems(self) -> list[RiskClassification]:
        return [c for c in self._classifications.values()
                if c.risk_category == AIRiskCategory.UNACCEPTABLE]

    def get_transparency_records(self, system_id: str) -> list[TransparencyRecord]:
        return [r for r in self._transparency_records.values() if r.system_id == system_id]
