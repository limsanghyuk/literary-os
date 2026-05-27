"""
tests/unit/test_v671_jenova_absorption.py
V671 Jenova 경쟁 흡수 테스트 (SP-C.4, G72-5, ADR-133)
TC01~TC30
"""
import pytest
from literary_system.absorption.jenova import JenovaAbsorber, IP_ADV_005
from literary_system.absorption.base import (
    AbsorptionStatus, CompetitorProfile, AbsorptionReport, FeatureGap, IPAdvisoryCommit
)


# ── Fixtures ────────────────────────────────────────────────────────────────
@pytest.fixture
def absorber():
    return JenovaAbsorber()

@pytest.fixture
def profile(absorber):
    return absorber.analyze()

@pytest.fixture
def report(absorber):
    return absorber.build_report()


# ── TC01~TC05: IP 자문 커밋 (IP-ADV-005) ─────────────────────────────────
def test_tc01_ip_advisory_exists():
    assert IP_ADV_005 is not None

def test_tc02_ip_advisory_competitor():
    assert IP_ADV_005.competitor == "Jenova"

def test_tc03_ip_advisory_ref():
    assert IP_ADV_005.advisory_ref == "IP-ADV-005"

def test_tc04_ip_advisory_cleared():
    assert IP_ADV_005.cleared is True

def test_tc05_ip_advisory_findings_count():
    assert len(IP_ADV_005.findings) >= 5


# ── TC06~TC12: CompetitorProfile 구조 검증 ────────────────────────────────
def test_tc06_profile_name(profile):
    assert profile.name == "Jenova"

def test_tc07_profile_version_analyzed(profile):
    assert profile.version_analyzed is not None and len(profile.version_analyzed) > 0

def test_tc08_profile_category(profile):
    assert profile.category == "ai_writing"

def test_tc09_profile_target_market(profile):
    assert "korean" in profile.target_market.lower()

def test_tc10_profile_core_differentiators(profile):
    assert len(profile.core_differentiators) >= 3

def test_tc11_profile_weaknesses(profile):
    assert len(profile.weaknesses) >= 3

def test_tc12_profile_status(profile):
    assert profile.status == AbsorptionStatus.ABSORBED


# ── TC13~TC20: FeatureGap 목록 검증 ─────────────────────────────────────
def test_tc13_feature_gaps_count(profile):
    assert len(profile.feature_gaps) >= 5

def test_tc14_feature_gap_fields(profile):
    for fg in profile.feature_gaps:
        assert fg.feature_name
        assert fg.competitor == "Jenova"
        assert fg.gap_type in ("missing", "inferior", "different_approach")
        assert fg.priority in ("high", "medium", "low")
        assert fg.ip_risk in ("high", "medium", "low")

def test_tc15_korean_genre_blending_present(profile):
    names = [fg.feature_name for fg in profile.feature_gaps]
    assert "KoreanGenreBlending" in names

def test_tc16_emotional_peak_scheduler_present(profile):
    names = [fg.feature_name for fg in profile.feature_gaps]
    assert "EmotionalPeakScheduler" in names

def test_tc17_narrative_coherence_validator_present(profile):
    names = [fg.feature_name for fg in profile.feature_gaps]
    assert "NarrativeCoherenceValidator" in names

def test_tc18_character_relationship_mapper_present(profile):
    names = [fg.feature_name for fg in profile.feature_gaps]
    assert "CharacterRelationshipMapper" in names

def test_tc19_predictive_feedback_high_ip_risk(profile):
    fg_map = {fg.feature_name: fg for fg in profile.feature_gaps}
    assert fg_map["PredictiveAudienceFeedback"].ip_risk == "high"

def test_tc20_high_priority_gaps_have_absorption_note(profile):
    for fg in profile.feature_gaps:
        if fg.priority == "high":
            assert len(fg.absorption_note) > 0


# ── TC21~TC27: AbsorptionReport 검증 ────────────────────────────────────
def test_tc21_report_competitor(report):
    assert report.competitor == "Jenova"

def test_tc22_report_gate_id(report):
    assert report.gate_id == "G72-5"

def test_tc23_report_gate_passed(report):
    assert report.gate_passed is True

def test_tc24_report_absorbed_features_type(report):
    assert isinstance(report.absorbed_features, list)
    for item in report.absorbed_features:
        assert isinstance(item, str)

def test_tc25_report_absorbed_count_min(report):
    assert len(report.absorbed_features) >= 3

def test_tc26_report_rejected_count_min(report):
    assert len(report.rejected_features) >= 1

def test_tc27_report_summary_nonempty(report):
    assert len(report.summary) > 0


# ── TC28~TC30: G72-5 서브게이트 + G72 통합 게이트 연동 ─────────────────
def test_tc28_g72_5_subgate():
    from literary_system.gates.competitor_absorption_gate import run_g72_subgate
    absorber = JenovaAbsorber()
    profile = absorber.analyze()
    report = absorber.build_report()
    sub = run_g72_subgate(
        competitor="Jenova",
        gate_id="G72-5",
        report_passed=report.gate_passed,
        ip_cleared=(profile.ip_advisory is not None and profile.ip_advisory.cleared),
        absorbed_count=len(report.absorbed_features),
        rejected_count=len(report.rejected_features),
        summary=report.summary,
    )
    assert sub.passed is True
    assert sub.ip_cleared is True
    assert sub.gate_id == "G72-5"

def test_tc29_g72_unified_gate_all_pass():
    from literary_system.absorption.novel_ai import NovelAIAbsorber
    from literary_system.absorption.sudowrite import SudowriteAbsorber
    from literary_system.absorption.novelcrafter import NoveltcrafterAbsorber
    from literary_system.absorption.nolan_ai import NolanAIAbsorber
    from literary_system.gates.competitor_absorption_gate import run_g72_subgate, run_g72_gate
    entries = [
        ("NovelAI",      "G72-1", NovelAIAbsorber()),
        ("Sudowrite",    "G72-2", SudowriteAbsorber()),
        ("Novelcrafter", "G72-3", NoveltcrafterAbsorber()),
        ("NolanAI",      "G72-4", NolanAIAbsorber()),
        ("Jenova",       "G72-5", JenovaAbsorber()),
    ]
    subs = []
    for competitor, gate_id, absorber in entries:
        p = absorber.analyze()
        r = absorber.build_report()
        subs.append(run_g72_subgate(
            competitor=competitor, gate_id=gate_id,
            report_passed=r.gate_passed,
            ip_cleared=(p.ip_advisory is not None and p.ip_advisory.cleared),
            absorbed_count=len(r.absorbed_features),
            rejected_count=len(r.rejected_features),
            summary=r.summary,
        ))
    g72 = run_g72_gate(subs)
    assert g72.all_passed is True
    assert g72.total_absorbed >= 15

def test_tc30_release_gate_g72_g72_5():
    from literary_system.gates.release_gate import GATES
    gate_ids = [g[0] for g in GATES]
    assert "jenova_absorption_g72_5" in gate_ids
    assert "competitive_absorption_g72_unified" in gate_ids
