"""
tests/unit/test_v668_sudowrite_absorption.py
============================================
V668 Sudowrite 경쟁 흡수 테스트 (G72-2, SP-C.4, ADR-130)
30 TC — 모두 단위 테스트 (외부 의존 없음)
"""
import pytest
from literary_system.absorption.base import (
    AbsorptionStatus,
    CompetitorProfile,
    FeatureGap,
    IPAdvisoryCommit,
    AbsorptionReport,
)
from literary_system.absorption.sudowrite import (
    SudowriteAbsorber,
    IP_ADV_002,
)


# ==========================================================================
# TC01~TC05 — IP_ADV_002 자문 커밋 상수 검증
# ==========================================================================

class TestIPAdv002:
    """TC01~TC05: IP-ADV-002 자문 커밋 불변 속성."""

    def test_tc01_advisory_ref(self):
        """TC01: advisory_ref == 'IP-ADV-002'"""
        assert IP_ADV_002.advisory_ref == "IP-ADV-002"

    def test_tc02_competitor(self):
        """TC02: competitor == 'Sudowrite'"""
        assert IP_ADV_002.competitor == "Sudowrite"

    def test_tc03_cleared_true(self):
        """TC03: cleared == True"""
        assert IP_ADV_002.cleared is True

    def test_tc04_findings_nonempty(self):
        """TC04: findings 리스트 비어있지 않음"""
        assert len(IP_ADV_002.findings) >= 3

    def test_tc05_findings_all_strings(self):
        """TC05: findings 항목 모두 str"""
        for f in IP_ADV_002.findings:
            assert isinstance(f, str) and len(f) > 0


# ==========================================================================
# TC06~TC10 — FeatureGap 목록 기본 속성
# ==========================================================================

class TestSudowriteFeatureGaps:
    """TC06~TC10: _FEATURE_GAPS 기본 속성."""

    def setup_method(self):
        self.absorber = SudowriteAbsorber()

    def test_tc06_total_features_count(self):
        """TC06: 총 기능 격차 수 == 5"""
        assert len(SudowriteAbsorber._FEATURE_GAPS) == 5

    def test_tc07_all_feature_names_nonempty(self):
        """TC07: 모든 FeatureGap.feature_name 비어있지 않음"""
        for fg in SudowriteAbsorber._FEATURE_GAPS:
            assert fg.feature_name, f"feature_name 비어있음: {fg}"

    def test_tc08_story_bible_gap_type_missing(self):
        """TC08: StoryBible gap_type == 'missing'"""
        fg = self.absorber.get_feature("StoryBible")
        assert fg is not None
        assert fg.gap_type == "missing"

    def test_tc09_wormhole_rewrite_priority_high(self):
        """TC09: WormholeRewrite priority == 'high'"""
        fg = self.absorber.get_feature("WormholeRewrite")
        assert fg is not None
        assert fg.priority == "high"

    def test_tc10_realtime_copilot_priority_low(self):
        """TC10: RealtimeCoPilotSuggestion priority == 'low' (Phase D 이관)"""
        fg = self.absorber.get_feature("RealtimeCoPilotSuggestion")
        assert fg is not None
        assert fg.priority == "low"


# ==========================================================================
# TC11~TC18 — SudowriteAbsorber.analyze()
# ==========================================================================

class TestSudowriteAbsorberAnalyze:
    """TC11~TC18: analyze() 반환값 검증."""

    def setup_method(self):
        self.absorber = SudowriteAbsorber()
        self.profile = self.absorber.analyze()

    def test_tc11_returns_competitor_profile(self):
        """TC11: analyze() 반환 타입 == CompetitorProfile"""
        assert isinstance(self.profile, CompetitorProfile)

    def test_tc12_name_sudowrite(self):
        """TC12: profile.name == 'Sudowrite'"""
        assert self.profile.name == "Sudowrite"

    def test_tc13_category_ai_writing(self):
        """TC13: profile.category == 'ai_writing'"""
        assert self.profile.category == "ai_writing"

    def test_tc14_ip_advisory_attached(self):
        """TC14: ip_advisory 첨부됨"""
        assert self.profile.ip_advisory is not None

    def test_tc15_ip_advisory_cleared(self):
        """TC15: ip_advisory.cleared == True"""
        assert self.profile.ip_advisory.cleared is True

    def test_tc16_feature_gaps_nonempty(self):
        """TC16: feature_gaps 리스트 비어있지 않음"""
        assert len(self.profile.feature_gaps) > 0

    def test_tc17_core_differentiators_nonempty(self):
        """TC17: core_differentiators 비어있지 않음"""
        assert len(self.profile.core_differentiators) >= 3

    def test_tc18_status_analyzed(self):
        """TC18: profile.status == AbsorptionStatus.ANALYZED"""
        assert self.profile.status == AbsorptionStatus.ANALYZED


# ==========================================================================
# TC19~TC26 — SudowriteAbsorber.build_report()
# ==========================================================================

class TestSudowriteAbsorberBuildReport:
    """TC19~TC26: build_report() 반환값 검증."""

    def setup_method(self):
        self.absorber = SudowriteAbsorber()
        self.report = self.absorber.build_report()

    def test_tc19_returns_absorption_report(self):
        """TC19: build_report() 반환 타입 == AbsorptionReport"""
        assert isinstance(self.report, AbsorptionReport)

    def test_tc20_competitor_sudowrite(self):
        """TC20: report.competitor == 'Sudowrite'"""
        assert self.report.competitor == "Sudowrite"

    def test_tc21_gate_id_g72_2(self):
        """TC21: report.gate_id == 'G72-2'"""
        assert self.report.gate_id == "G72-2"

    def test_tc22_gate_passed_true(self):
        """TC22: report.gate_passed == True"""
        assert self.report.gate_passed is True

    def test_tc23_absorbed_gte_3(self):
        """TC23: absorbed_features 수 ≥ 3"""
        assert len(self.report.absorbed_features) >= 3

    def test_tc24_rejected_lte_2(self):
        """TC24: rejected_features 수 ≤ 2"""
        assert len(self.report.rejected_features) <= 2

    def test_tc25_summary_nonempty(self):
        """TC25: summary 비어있지 않음"""
        assert len(self.report.summary) > 20

    def test_tc26_profile_embedded(self):
        """TC26: report.profile.name == 'Sudowrite'"""
        assert self.report.profile.name == "Sudowrite"


# ==========================================================================
# TC27~TC28 — 편의 메서드
# ==========================================================================

class TestSudowriteAbsorberHelpers:
    """TC27~TC28: 편의 메서드 검증."""

    def setup_method(self):
        self.absorber = SudowriteAbsorber()

    def test_tc27_get_feature_exists(self):
        """TC27: 존재하는 기능명 조회 → FeatureGap 반환"""
        fg = self.absorber.get_feature("DescribeSensoryExpansion")
        assert fg is not None
        assert fg.feature_name == "DescribeSensoryExpansion"

    def test_tc28_get_feature_not_found(self):
        """TC28: 존재하지 않는 기능명 조회 → None 반환"""
        fg = self.absorber.get_feature("NonExistentFeature_XYZ")
        assert fg is None


# ==========================================================================
# TC29~TC30 — G72-2 게이트 통합 검증
# ==========================================================================

class TestG72_2Gate:
    """TC29~TC30: G72-2 게이트 통과 조건 통합 검증."""

    def test_tc29_gate_conditions_all_met(self):
        """TC29: ip_cleared + absorbed≥3 + rejected≤2 모두 충족."""
        absorber = SudowriteAbsorber()
        profile = absorber.analyze()
        report = absorber.build_report()

        ip_ok = profile.ip_advisory is not None and profile.ip_advisory.cleared
        absorbed_ok = len(report.absorbed_features) >= 3
        rejected_ok = len(report.rejected_features) <= 2

        assert ip_ok, "IP 자문 미클리어"
        assert absorbed_ok, f"흡수 기능 부족: {len(report.absorbed_features)}"
        assert rejected_ok, f"보류 기능 초과: {len(report.rejected_features)}"
        assert report.gate_passed, "gate_passed == False"

    def test_tc30_gate_module_integration(self):
        """TC30: competitor_absorption_gate.run_g72_subgate() 연동 정상."""
        from literary_system.gates.competitor_absorption_gate import run_g72_subgate

        absorber = SudowriteAbsorber()
        profile = absorber.analyze()
        report = absorber.build_report()

        sub = run_g72_subgate(
            competitor="Sudowrite",
            gate_id="G72-2",
            report_passed=report.gate_passed,
            ip_cleared=profile.ip_advisory.cleared,
            absorbed_count=len(report.absorbed_features),
            rejected_count=len(report.rejected_features),
            summary=report.summary,
        )
        assert sub.passed is True
        assert sub.competitor == "Sudowrite"
        assert sub.gate_id == "G72-2"
