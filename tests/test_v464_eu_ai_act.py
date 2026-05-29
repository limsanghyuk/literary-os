"""
test_v464_eu_ai_act.py — V464 EU AI Act Governance 테스트

ADR-012: EU AI Act High-Risk Governance
"""
import pytest
from literary_system.compliance.eu_ai_act import (
    EUAIActGovernance, AISystemProfile, AIRiskCategory,
    AnnexIIICategory, TransparencyObligation,
)


def _profile(**kwargs) -> AISystemProfile:
    defaults = dict(
        system_id="sys_test",
        name="Literary AI",
        purpose="창작 보조",
        uses_biometric=False,
        affects_education=False,
        affects_employment=False,
        affects_essential_services=False,
        uses_emotion_recognition=False,
        generates_synthetic_content=False,
        uses_real_time_biometric=False,
        social_scoring=False,
        subliminal_manipulation=False,
        interacts_with_users=True,
    )
    defaults.update(kwargs)
    return AISystemProfile(**defaults)


class TestRiskClassification:

    def _gov(self):
        return EUAIActGovernance()

    # --- 금지 관행 ---
    def test_subliminal_manipulation_unacceptable(self):
        gov = self._gov()
        clf = gov.classify_system(_profile(subliminal_manipulation=True))
        assert clf.risk_category == AIRiskCategory.UNACCEPTABLE
        assert len(clf.prohibited_practices) > 0
        assert clf.conformity_assessment_required is True

    def test_social_scoring_unacceptable(self):
        gov = self._gov()
        clf = gov.classify_system(_profile(social_scoring=True))
        assert clf.risk_category == AIRiskCategory.UNACCEPTABLE

    def test_real_time_biometric_unacceptable(self):
        gov = self._gov()
        clf = gov.classify_system(_profile(uses_real_time_biometric=True))
        assert clf.risk_category == AIRiskCategory.UNACCEPTABLE
        assert any("Art.5" in p for p in clf.prohibited_practices)

    # --- 고위험 (Annex III) ---
    def test_biometric_high_risk(self):
        gov = self._gov()
        clf = gov.classify_system(_profile(uses_biometric=True))
        assert clf.risk_category == AIRiskCategory.HIGH_RISK
        assert AnnexIIICategory.BIOMETRIC in clf.annex_iii_categories
        assert clf.human_oversight_required is True
        assert clf.conformity_assessment_required is True

    def test_education_high_risk(self):
        gov = self._gov()
        clf = gov.classify_system(_profile(affects_education=True))
        assert clf.risk_category == AIRiskCategory.HIGH_RISK
        assert AnnexIIICategory.EDUCATION in clf.annex_iii_categories

    def test_employment_high_risk(self):
        gov = self._gov()
        clf = gov.classify_system(_profile(affects_employment=True))
        assert clf.risk_category == AIRiskCategory.HIGH_RISK
        assert AnnexIIICategory.EMPLOYMENT in clf.annex_iii_categories

    def test_multiple_annex_iii(self):
        gov = self._gov()
        clf = gov.classify_system(_profile(
            affects_education=True,
            affects_employment=True,
        ))
        assert clf.risk_category == AIRiskCategory.HIGH_RISK
        assert len(clf.annex_iii_categories) >= 2

    # --- 제한적 위험 (Art.52) ---
    def test_synthetic_content_limited_risk(self):
        gov = self._gov()
        clf = gov.classify_system(_profile(generates_synthetic_content=True))
        assert clf.risk_category == AIRiskCategory.LIMITED_RISK
        assert TransparencyObligation.AI_WATERMARK in clf.transparency_obligations

    def test_emotion_recognition_limited_risk(self):
        gov = self._gov()
        clf = gov.classify_system(_profile(uses_emotion_recognition=True))
        assert TransparencyObligation.EMOTION_DISCLOSURE in clf.transparency_obligations

    def test_chatbot_disclosure(self):
        gov = self._gov()
        clf = gov.classify_system(_profile(interacts_with_users=True))
        assert TransparencyObligation.CHATBOT_DISCLOSURE in clf.transparency_obligations

    # --- 최소 위험 ---
    def test_minimal_risk(self):
        gov = self._gov()
        # 사용자 상호작용도 없음
        clf = gov.classify_system(_profile(interacts_with_users=False))
        assert clf.risk_category == AIRiskCategory.MINIMAL_RISK
        assert clf.conformity_assessment_required is False
        assert clf.human_oversight_required is False

    # --- 저장/조회 ---
    def test_get_classification(self):
        gov = self._gov()
        clf = gov.classify_system(_profile(uses_biometric=True))
        fetched = gov.get_classification(clf.classification_id)
        assert fetched is not None
        assert fetched.classification_id == clf.classification_id

    def test_list_high_risk_systems(self):
        gov = self._gov()
        gov.classify_system(_profile(uses_biometric=True))
        gov.classify_system(_profile(generates_synthetic_content=True))
        assert len(gov.list_high_risk_systems()) == 1

    def test_list_prohibited_systems(self):
        gov = self._gov()
        gov.classify_system(_profile(social_scoring=True))
        gov.classify_system(_profile(uses_biometric=True))
        assert len(gov.list_prohibited_systems()) == 1

    # --- to_dict ---
    def test_to_dict(self):
        gov = self._gov()
        clf = gov.classify_system(_profile(affects_education=True))
        d = clf.to_dict()
        for k in ("classification_id", "risk_category", "annex_iii_categories",
                  "transparency_obligations", "conformity_assessment_required"):
            assert k in d


class TestAIWatermark:

    def test_apply_watermark(self):
        gov = EUAIActGovernance()
        record = gov.apply_watermark(
            tenant_id="t1",
            system_id="literary_gen",
            content_id="story_001",
            content_text="옛날 옛적 어느 마을에 용감한 기사가 살았습니다.",
        )
        assert record.record_id
        assert record.watermark_hash
        assert len(record.watermark_hash) == 32
        assert record.obligation == TransparencyObligation.AI_WATERMARK

    def test_verify_watermark_success(self):
        gov = EUAIActGovernance()
        content = "AI 생성 소설 텍스트"
        content_id = "c001"
        system_id = "literary_gen"
        record = gov.apply_watermark("t1", system_id, content_id, content)
        assert gov.verify_watermark(record.record_id, content, content_id, system_id) is True

    def test_verify_watermark_tampered(self):
        gov = EUAIActGovernance()
        content = "원본 텍스트"
        record = gov.apply_watermark("t1", "sys", "c001", content)
        # 콘텐츠 변조
        assert gov.verify_watermark(record.record_id, "변조된 텍스트", "c001", "sys") is False

    def test_verify_nonexistent_record(self):
        gov = EUAIActGovernance()
        assert gov.verify_watermark("nonexistent", "text", "c001", "sys") is False

    def test_get_transparency_records(self):
        gov = EUAIActGovernance()
        gov.apply_watermark("t1", "sys_a", "c001", "text1")
        gov.apply_watermark("t1", "sys_a", "c002", "text2")
        gov.apply_watermark("t1", "sys_b", "c003", "text3")
        assert len(gov.get_transparency_records("sys_a")) == 2
        assert len(gov.get_transparency_records("sys_b")) == 1

    def test_watermark_deterministic(self):
        """동일 입력 → 동일 해시"""
        gov = EUAIActGovernance()
        content = "같은 텍스트"
        r1 = gov.apply_watermark("t1", "sys", "c001", content)
        r2 = gov.apply_watermark("t1", "sys", "c001", content)
        assert r1.watermark_hash == r2.watermark_hash


class TestUserRightsScreen:

    def test_generate_screen_high_risk(self):
        gov = EUAIActGovernance()
        clf = gov.classify_system(_profile(affects_education=True))
        screen = gov.generate_user_rights_screen(
            system_id="sys_1",
            classification=clf,
            data_used=["행동 데이터", "학습 기록"],
            contact_dpo="dpo@test.com",
        )
        assert screen.screen_id
        assert screen.human_oversight is True
        assert screen.right_to_explanation is True
        assert "dpo@test.com" in screen.contact_dpo

    def test_generate_screen_minimal_risk(self):
        gov = EUAIActGovernance()
        clf = gov.classify_system(_profile(interacts_with_users=False))
        screen = gov.generate_user_rights_screen(
            system_id="sys_2",
            classification=clf,
            data_used=["익명 통계"],
        )
        assert screen.right_to_explanation is False
        assert screen.human_oversight is False

    def test_render_text_contains_key_info(self):
        gov = EUAIActGovernance()
        clf = gov.classify_system(_profile(affects_employment=True))
        screen = gov.generate_user_rights_screen("sys_3", clf, ["고용 데이터"])
        text = screen.render_text()
        assert "EU AI Act" in text
        assert "위험 등급" in text
        assert "DPO" in text

    def test_to_dict(self):
        gov = EUAIActGovernance()
        clf = gov.classify_system(_profile(uses_biometric=True))
        screen = gov.generate_user_rights_screen("sys_4", clf, ["생체 데이터"])
        d = screen.to_dict()
        for k in ("screen_id", "risk_level", "human_oversight",
                  "right_to_explanation", "rendered_text"):
            assert k in d


class TestEUAIActIntegration:

    def test_literary_os_profile_classification(self):
        """Literary OS 실제 프로파일 — 생성AI + 사용자 상호작용 → LIMITED_RISK"""
        gov = EUAIActGovernance()
        profile = AISystemProfile(
            system_id="literary_os_main",
            name="Literary OS 창작 AI",
            purpose="한국 드라마 스타일 소설 생성 보조",
            uses_biometric=False,
            affects_education=False,
            affects_employment=False,
            affects_essential_services=False,
            uses_emotion_recognition=False,
            generates_synthetic_content=True,
            uses_real_time_biometric=False,
            social_scoring=False,
            subliminal_manipulation=False,
            interacts_with_users=True,
        )
        clf = gov.classify_system(profile)
        assert clf.risk_category == AIRiskCategory.LIMITED_RISK
        assert TransparencyObligation.AI_WATERMARK in clf.transparency_obligations
        assert TransparencyObligation.CHATBOT_DISCLOSURE in clf.transparency_obligations
        assert clf.conformity_assessment_required is False

    def test_full_governance_flow(self):
        """분류 → 워터마크 적용 → 사용자 권리 화면"""
        gov = EUAIActGovernance()

        # 1. 분류
        profile = _profile(generates_synthetic_content=True, interacts_with_users=True)
        clf = gov.classify_system(profile)

        # 2. 워터마크
        record = gov.apply_watermark(
            "tenant_1", profile.system_id, "story_042",
            "AI가 생성한 소설의 첫 단락입니다.",
        )
        assert gov.verify_watermark(
            record.record_id,
            "AI가 생성한 소설의 첫 단락입니다.",
            "story_042",
            profile.system_id,
        )

        # 3. 사용자 권리 화면
        screen = gov.generate_user_rights_screen(
            profile.system_id, clf,
            data_used=["창작 입력 텍스트", "스타일 선호도"],
        )
        assert screen.right_to_explanation == (clf.risk_category == AIRiskCategory.HIGH_RISK)
        assert len(screen.render_text()) > 50

    def test_check_prohibited_all_clean(self):
        gov = EUAIActGovernance()
        profile = _profile()
        violations = gov.check_prohibited(profile)
        assert violations == []

    def test_check_prohibited_multiple_violations(self):
        gov = EUAIActGovernance()
        profile = _profile(subliminal_manipulation=True, social_scoring=True)
        violations = gov.check_prohibited(profile)
        assert len(violations) == 2
