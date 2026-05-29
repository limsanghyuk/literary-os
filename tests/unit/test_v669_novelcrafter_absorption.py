"""
tests/unit/test_v669_novelcrafter_absorption.py
===============================================
V669 Novelcrafter 경쟁 흡수 테스트 (G72-3, SP-C.4, ADR-131)
30 TC — 단위 테스트 (외부 의존 없음)
"""
import pytest
from literary_system.absorption.base import (
    AbsorptionStatus, CompetitorProfile, FeatureGap, IPAdvisoryCommit, AbsorptionReport,
)
from literary_system.absorption.novelcrafter import NoveltcrafterAbsorber, IP_ADV_003


# ==========================================================================
# TC01~TC05 — IP_ADV_003 자문 커밋 상수 검증
# ==========================================================================

class TestIPAdv003:
    def test_tc01_advisory_ref(self):
        """TC01: advisory_ref == 'IP-ADV-003'"""
        assert IP_ADV_003.advisory_ref == "IP-ADV-003"

    def test_tc02_competitor(self):
        """TC02: competitor == 'Novelcrafter'"""
        assert IP_ADV_003.competitor == "Novelcrafter"

    def test_tc03_cleared_true(self):
        """TC03: cleared == True"""
        assert IP_ADV_003.cleared is True

    def test_tc04_findings_nonempty(self):
        """TC04: findings 리스트 비어있지 않음"""
        assert len(IP_ADV_003.findings) >= 4

    def test_tc05_findings_all_strings(self):
        """TC05: findings 항목 모두 str"""
        for f in IP_ADV_003.findings:
            assert isinstance(f, str) and len(f) > 0


# ==========================================================================
# TC06~TC11 — FeatureGap 목록 기본 속성
# ==========================================================================

class TestNoveltcrafterFeatureGaps:
    def setup_method(self):
        self.absorber = NoveltcrafterAbsorber()

    def test_tc06_total_features_count(self):
        """TC06: 총 기능 격차 수 == 6"""
        assert len(NoveltcrafterAbsorber._FEATURE_GAPS) == 6

    def test_tc07_all_feature_names_nonempty(self):
        """TC07: 모든 FeatureGap.feature_name 비어있지 않음"""
        for fg in NoveltcrafterAbsorber._FEATURE_GAPS:
            assert fg.feature_name

    def test_tc08_codex_gap_type_inferior(self):
        """TC08: CodexWorldDB gap_type == 'inferior'"""
        fg = self.absorber.get_feature("CodexWorldDB")
        assert fg is not None
        assert fg.gap_type == "inferior"

    def test_tc09_scene_outline_priority_high(self):
        """TC09: SceneLevelOutline priority == 'high'"""
        fg = self.absorber.get_feature("SceneLevelOutline")
        assert fg is not None
        assert fg.priority == "high"

    def test_tc10_offline_storage_priority_low(self):
        """TC10: OfflineLocalStorage priority == 'low' (Phase D 이관)"""
        fg = self.absorber.get_feature("OfflineLocalStorage")
        assert fg is not None
        assert fg.priority == "low"

    def test_tc11_offline_storage_different_approach(self):
        """TC11: OfflineLocalStorage gap_type == 'different_approach'"""
        fg = self.absorber.get_feature("OfflineLocalStorage")
        assert fg is not None
        assert fg.gap_type == "different_approach"


# ==========================================================================
# TC12~TC19 — NoveltcrafterAbsorber.analyze()
# ==========================================================================

class TestNoveltcrafterAbsorberAnalyze:
    def setup_method(self):
        self.absorber = NoveltcrafterAbsorber()
        self.profile = self.absorber.analyze()

    def test_tc12_returns_competitor_profile(self):
        """TC12: analyze() 반환 타입 == CompetitorProfile"""
        assert isinstance(self.profile, CompetitorProfile)

    def test_tc13_name_novelcrafter(self):
        """TC13: profile.name == 'Novelcrafter'"""
        assert self.profile.name == "Novelcrafter"

    def test_tc14_category_ai_writing(self):
        """TC14: profile.category == 'ai_writing'"""
        assert self.profile.category == "ai_writing"

    def test_tc15_ip_advisory_attached(self):
        """TC15: ip_advisory 첨부됨"""
        assert self.profile.ip_advisory is not None

    def test_tc16_ip_advisory_cleared(self):
        """TC16: ip_advisory.cleared == True"""
        assert self.profile.ip_advisory.cleared is True

    def test_tc17_feature_gaps_nonempty(self):
        """TC17: feature_gaps 리스트 비어있지 않음"""
        assert len(self.profile.feature_gaps) > 0

    def test_tc18_core_differentiators_gte_4(self):
        """TC18: core_differentiators ≥ 4개"""
        assert len(self.profile.core_differentiators) >= 4

    def test_tc19_status_analyzed(self):
        """TC19: profile.status == AbsorptionStatus.ANALYZED"""
        assert self.profile.status == AbsorptionStatus.ANALYZED


# ==========================================================================
# TC20~TC26 — NoveltcrafterAbsorber.build_report()
# ==========================================================================

class TestNoveltcrafterAbsorberBuildReport:
    def setup_method(self):
        self.absorber = NoveltcrafterAbsorber()
        self.report = self.absorber.build_report()

    def test_tc20_returns_absorption_report(self):
        """TC20: build_report() 반환 타입 == AbsorptionReport"""
        assert isinstance(self.report, AbsorptionReport)

    def test_tc21_competitor_novelcrafter(self):
        """TC21: report.competitor == 'Novelcrafter'"""
        assert self.report.competitor == "Novelcrafter"

    def test_tc22_gate_id_g72_3(self):
        """TC22: report.gate_id == 'G72-3'"""
        assert self.report.gate_id == "G72-3"

    def test_tc23_gate_passed_true(self):
        """TC23: report.gate_passed == True"""
        assert self.report.gate_passed is True

    def test_tc24_absorbed_gte_3(self):
        """TC24: absorbed_features 수 ≥ 3"""
        assert len(self.report.absorbed_features) >= 3

    def test_tc25_rejected_lte_2(self):
        """TC25: rejected_features 수 ≤ 2"""
        assert len(self.report.rejected_features) <= 2

    def test_tc26_summary_nonempty(self):
        """TC26: summary 비어있지 않음"""
        assert len(self.report.summary) > 20


# ==========================================================================
# TC27~TC28 — 편의 메서드
# ==========================================================================

class TestNoveltcrafterAbsorberHelpers:
    def setup_method(self):
        self.absorber = NoveltcrafterAbsorber()

    def test_tc27_get_feature_exists(self):
        """TC27: 존재하는 기능명 조회 → FeatureGap 반환"""
        fg = self.absorber.get_feature("AIDraftGenerate")
        assert fg is not None
        assert fg.feature_name == "AIDraftGenerate"

    def test_tc28_get_feature_not_found(self):
        """TC28: 존재하지 않는 기능명 조회 → None 반환"""
        assert self.absorber.get_feature("NonExistentXYZ") is None


# ==========================================================================
# TC29~TC30 — G72-3 게이트 통합 검증
# ==========================================================================

class TestG72_3Gate:
    def test_tc29_gate_conditions_all_met(self):
        """TC29: ip_cleared + absorbed≥3 + rejected≤2 모두 충족."""
        absorber = NoveltcrafterAbsorber()
        profile = absorber.analyze()
        report = absorber.build_report()

        ip_ok = profile.ip_advisory is not None and profile.ip_advisory.cleared
        absorbed_ok = len(report.absorbed_features) >= 3
        rejected_ok = len(report.rejected_features) <= 2

        assert ip_ok, "IP 자문 미클리어"
        assert absorbed_ok, f"흡수 기능 부족: {len(report.absorbed_features)}"
        assert rejected_ok, f"보류 기능 초과: {len(report.rejected_features)}"
        assert report.gate_passed

    def test_tc30_gate_module_integration(self):
        """TC30: competitor_absorption_gate.run_g72_subgate() 연동 정상."""
        from literary_system.gates.competitor_absorption_gate import run_g72_subgate
        absorber = NoveltcrafterAbsorber()
        profile = absorber.analyze()
        report = absorber.build_report()
        sub = run_g72_subgate(
            competitor="Novelcrafter",
            gate_id="G72-3",
            report_passed=report.gate_passed,
            ip_cleared=profile.ip_advisory.cleared,
            absorbed_count=len(report.absorbed_features),
            rejected_count=len(report.rejected_features),
            summary=report.summary,
        )
        assert sub.passed is True
        assert sub.competitor == "Novelcrafter"
        assert sub.gate_id == "G72-3"
