"""
tests/unit/test_v670_nolan_ai_absorption.py
===========================================
V670 NolanAI 경쟁 흡수 테스트 (G72-4, SP-C.4, ADR-132)
30 TC — 단위 테스트 (외부 의존 없음)
"""
import pytest
from literary_system.absorption.base import (
    AbsorptionStatus, CompetitorProfile, FeatureGap, IPAdvisoryCommit, AbsorptionReport,
)
from literary_system.absorption.nolan_ai import NolanAIAbsorber, IP_ADV_004


class TestIPAdv004:
    def test_tc01_advisory_ref(self):
        assert IP_ADV_004.advisory_ref == "IP-ADV-004"

    def test_tc02_competitor(self):
        assert IP_ADV_004.competitor == "NolanAI"

    def test_tc03_cleared_true(self):
        assert IP_ADV_004.cleared is True

    def test_tc04_findings_nonempty(self):
        assert len(IP_ADV_004.findings) >= 4

    def test_tc05_findings_all_strings(self):
        for f in IP_ADV_004.findings:
            assert isinstance(f, str) and len(f) > 0


class TestNolanAIFeatureGaps:
    def setup_method(self):
        self.absorber = NolanAIAbsorber()

    def test_tc06_total_features_count(self):
        assert len(NolanAIAbsorber._FEATURE_GAPS) == 6

    def test_tc07_all_feature_names_nonempty(self):
        for fg in NolanAIAbsorber._FEATURE_GAPS:
            assert fg.feature_name

    def test_tc08_script_format_engine_high_priority(self):
        fg = self.absorber.get_feature("ScriptFormatEngine")
        assert fg is not None and fg.priority == "high"

    def test_tc09_scene_heading_missing(self):
        fg = self.absorber.get_feature("SceneHeadingAutocomplete")
        assert fg is not None and fg.gap_type == "missing"

    def test_tc10_character_voice_inferior(self):
        fg = self.absorber.get_feature("CharacterVoiceConsistency")
        assert fg is not None and fg.gap_type == "inferior"

    def test_tc11_final_draft_ip_risk_medium(self):
        fg = self.absorber.get_feature("FinalDraftExport")
        assert fg is not None and fg.ip_risk == "medium"


class TestNolanAIAbsorberAnalyze:
    def setup_method(self):
        self.absorber = NolanAIAbsorber()
        self.profile = self.absorber.analyze()

    def test_tc12_returns_competitor_profile(self):
        assert isinstance(self.profile, CompetitorProfile)

    def test_tc13_name_nolanai(self):
        assert self.profile.name == "NolanAI"

    def test_tc14_category_ai_writing(self):
        assert self.profile.category == "ai_writing"

    def test_tc15_ip_advisory_attached(self):
        assert self.profile.ip_advisory is not None

    def test_tc16_ip_advisory_cleared(self):
        assert self.profile.ip_advisory.cleared is True

    def test_tc17_feature_gaps_nonempty(self):
        assert len(self.profile.feature_gaps) > 0

    def test_tc18_core_differentiators_gte_4(self):
        assert len(self.profile.core_differentiators) >= 4

    def test_tc19_status_analyzed(self):
        assert self.profile.status == AbsorptionStatus.ANALYZED


class TestNolanAIAbsorberBuildReport:
    def setup_method(self):
        self.absorber = NolanAIAbsorber()
        self.report = self.absorber.build_report()

    def test_tc20_returns_absorption_report(self):
        assert isinstance(self.report, AbsorptionReport)

    def test_tc21_competitor_nolanai(self):
        assert self.report.competitor == "NolanAI"

    def test_tc22_gate_id_g72_4(self):
        assert self.report.gate_id == "G72-4"

    def test_tc23_gate_passed_true(self):
        assert self.report.gate_passed is True

    def test_tc24_absorbed_gte_3(self):
        assert len(self.report.absorbed_features) >= 3

    def test_tc25_rejected_lte_2(self):
        assert len(self.report.rejected_features) <= 2

    def test_tc26_summary_mentions_fountain(self):
        assert "Fountain" in self.report.summary or "IP" in self.report.summary

    def test_tc27_profile_name_correct(self):
        assert self.report.profile.name == "NolanAI"


class TestNolanAIAbsorberHelpers:
    def setup_method(self):
        self.absorber = NolanAIAbsorber()

    def test_tc28_get_feature_exists(self):
        fg = self.absorber.get_feature("ProductionBreakdown")
        assert fg is not None and fg.feature_name == "ProductionBreakdown"

    def test_tc29_get_feature_not_found(self):
        assert self.absorber.get_feature("NonExistentXYZ") is None


class TestG72_4Gate:
    def test_tc30_gate_conditions_and_module_integration(self):
        """TC30: ip_cleared + absorbed≥3 + rejected≤2 + run_g72_subgate() 연동."""
        from literary_system.gates.competitor_absorption_gate import run_g72_subgate
        absorber = NolanAIAbsorber()
        profile = absorber.analyze()
        report = absorber.build_report()

        assert profile.ip_advisory.cleared
        assert len(report.absorbed_features) >= 3
        assert len(report.rejected_features) <= 2
        assert report.gate_passed

        sub = run_g72_subgate(
            competitor="NolanAI",
            gate_id="G72-4",
            report_passed=report.gate_passed,
            ip_cleared=profile.ip_advisory.cleared,
            absorbed_count=len(report.absorbed_features),
            rejected_count=len(report.rejected_features),
            summary=report.summary,
        )
        assert sub.passed is True
        assert sub.gate_id == "G72-4"
