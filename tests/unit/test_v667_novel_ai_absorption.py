"""
tests/unit/test_v667_novel_ai_absorption.py
V667 SP-C.4 — NovelAI 경쟁 흡수 분석기 테스트 (ADR-129, G72-1)
"""
import pytest
from literary_system.absorption.base import (
    CompetitorProfile, AbsorptionReport, FeatureGap,
    IPAdvisoryCommit, AbsorptionStatus,
)
from literary_system.absorption.novel_ai import NovelAIAbsorber
from literary_system.gates.competitor_absorption_gate import (
    run_g72_subgate, run_g72_gate, G72SubResult,
)


class TestFeatureGap:
    def test_feature_gap_creation(self):
        gap = FeatureGap(
            feature_name="fast transfer",
            competitor="NovelAI",
            gap_type="inferior",
            priority="high",
            ip_risk="low",
        )
        assert gap.feature_name == "fast transfer"
        assert gap.ip_risk == "low"

    def test_feature_gap_high_ip_risk(self):
        gap = FeatureGap(
            feature_name="image gen",
            competitor="NovelAI",
            gap_type="missing",
            priority="low",
            ip_risk="high",
        )
        assert gap.ip_risk == "high"


class TestIPAdvisoryCommit:
    def test_ip_advisory_cleared(self):
        adv = IPAdvisoryCommit(
            competitor="NovelAI",
            commit_hash="abc123",
            advisory_ref="IP-ADV-001",
            findings=["텍스트 파이프라인: IP 리스크 없음."],
            cleared=True,
        )
        assert adv.cleared is True
        assert len(adv.findings) == 1

    def test_ip_advisory_not_cleared(self):
        adv = IPAdvisoryCommit(
            competitor="NovelAI",
            commit_hash="",
            advisory_ref="IP-ADV-001",
            cleared=False,
        )
        assert adv.cleared is False


class TestCompetitorProfile:
    def test_profile_status_default(self):
        profile = CompetitorProfile(
            name="NovelAI",
            version_analyzed="v3.x",
            category="ai_writing",
            pricing_model="subscription",
            target_market="anime writers",
        )
        assert profile.status == AbsorptionStatus.PENDING

    def test_profile_with_gaps(self):
        gap = FeatureGap("StyleDNA", "NovelAI", "inferior", "high", "low")
        profile = CompetitorProfile(
            name="NovelAI",
            version_analyzed="v3.x",
            category="ai_writing",
            pricing_model="sub",
            target_market="anime",
            feature_gaps=[gap],
        )
        assert len(profile.feature_gaps) == 1


class TestNovelAIAbsorber:
    def setup_method(self):
        self.absorber = NovelAIAbsorber()

    def test_analyze_returns_profile(self):
        profile = self.absorber.analyze()
        assert isinstance(profile, CompetitorProfile)
        assert profile.name == "NovelAI"

    def test_profile_has_core_differentiators(self):
        profile = self.absorber.analyze()
        assert len(profile.core_differentiators) >= 3

    def test_profile_has_weaknesses(self):
        profile = self.absorber.analyze()
        assert len(profile.weaknesses) >= 3

    def test_profile_has_feature_gaps(self):
        profile = self.absorber.analyze()
        assert len(profile.feature_gaps) >= 3

    def test_high_ip_risk_gap_exists(self):
        """이미지 생성 항목은 IP risk HIGH로 분류되어야 한다."""
        profile = self.absorber.analyze()
        high_risk = [g for g in profile.feature_gaps if g.ip_risk == "high"]
        assert len(high_risk) >= 1

    def test_ip_advisory_set(self):
        profile = self.absorber.analyze()
        assert profile.ip_advisory is not None
        assert profile.ip_advisory.advisory_ref == "IP-ADV-001"

    def test_ip_advisory_cleared(self):
        profile = self.absorber.analyze()
        assert profile.ip_advisory.cleared is True

    def test_ip_advisory_has_findings(self):
        profile = self.absorber.analyze()
        assert len(profile.ip_advisory.findings) >= 3

    def test_status_analyzed(self):
        profile = self.absorber.analyze()
        assert profile.status == AbsorptionStatus.ANALYZED

    def test_build_report_returns_report(self):
        report = self.absorber.build_report()
        assert isinstance(report, AbsorptionReport)

    def test_report_gate_id(self):
        report = self.absorber.build_report()
        assert report.gate_id == "G72-1"

    def test_report_gate_passed(self):
        report = self.absorber.build_report()
        assert report.gate_passed is True

    def test_report_absorbed_features(self):
        report = self.absorber.build_report()
        assert len(report.absorbed_features) >= 2

    def test_report_rejected_features(self):
        report = self.absorber.build_report()
        assert len(report.rejected_features) >= 1

    def test_image_gen_rejected(self):
        """이미지 생성 파이프라인은 rejected에 있어야 한다."""
        report = self.absorber.build_report()
        image_rejected = any("이미지" in f or "image" in f.lower()
                             for f in report.rejected_features)
        assert image_rejected

    def test_report_passed_method(self):
        report = self.absorber.build_report()
        assert report.passed() is True

    def test_summary_not_empty(self):
        report = self.absorber.build_report()
        assert len(report.summary) > 20


class TestG72Gate:
    def test_subgate_pass(self):
        result = run_g72_subgate(
            competitor="NovelAI",
            gate_id="G72-1",
            report_passed=True,
            ip_cleared=True,
            absorbed_count=3,
            rejected_count=2,
            summary="NovelAI 분석 완료",
        )
        assert result.passed is True

    def test_subgate_fail_no_ip(self):
        result = run_g72_subgate(
            competitor="Test",
            gate_id="G72-1",
            report_passed=True,
            ip_cleared=False,
            absorbed_count=3,
            rejected_count=1,
        )
        assert result.passed is False

    def test_subgate_fail_report(self):
        result = run_g72_subgate(
            competitor="Test",
            gate_id="G72-1",
            report_passed=False,
            ip_cleared=True,
            absorbed_count=0,
            rejected_count=0,
        )
        assert result.passed is False

    def test_g72_all_pass(self):
        subs = [
            run_g72_subgate("A", f"G72-{i}", True, True, 2, 1)
            for i in range(1, 6)
        ]
        report = run_g72_gate(subs)
        assert report.all_passed is True
        assert report.total_absorbed == 10

    def test_g72_partial_fail(self):
        subs = [
            run_g72_subgate("A", "G72-1", True, True, 2, 1),
            run_g72_subgate("B", "G72-2", True, False, 2, 1),  # IP 미완료
        ]
        report = run_g72_gate(subs)
        assert report.all_passed is False

    def test_g72_to_dict(self):
        subs = [run_g72_subgate("X", "G72-1", True, True, 3, 2)]
        report = run_g72_gate(subs)
        d = report.to_dict()
        assert d["gate"] == "G72"
        assert "sub_results" in d

    def test_novel_ai_full_flow(self):
        """NovelAI 전체 흐름: Absorber → Report → G72-1 서브 게이트."""
        absorber = NovelAIAbsorber()
        report = absorber.build_report()
        sub = run_g72_subgate(
            competitor=report.competitor,
            gate_id=report.gate_id,
            report_passed=report.gate_passed,
            ip_cleared=report.profile.ip_advisory.cleared,
            absorbed_count=len(report.absorbed_features),
            rejected_count=len(report.rejected_features),
            summary=report.summary,
        )
        assert sub.passed is True
        assert sub.ip_cleared is True
