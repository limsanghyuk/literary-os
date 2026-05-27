"""
tests/unit/test_v672_distillation_export.py
V672 DistillationExportPipeline 테스트 (SP-C.4, ADR-134)
TC01~TC30
"""
import pytest
from literary_system.absorption.distillation import (
    DistillationExportPipeline,
    DistilledFeature,
    DistillationReport,
    DistillationPhase,
    _DISTILLED_FEATURES,
)


@pytest.fixture
def pipeline():
    return DistillationExportPipeline()

@pytest.fixture
def report(pipeline):
    return pipeline.run()

@pytest.fixture
def roadmap(pipeline):
    return pipeline.export_roadmap()


# ── TC01~TC05: DistilledFeature 기본 구조 ─────────────────────────────────
def test_tc01_features_list_nonempty():
    assert len(_DISTILLED_FEATURES) >= 19

def test_tc02_feature_id_unique():
    ids = [f.feature_id for f in _DISTILLED_FEATURES]
    assert len(ids) == len(set(ids))

def test_tc03_feature_source_competitors():
    competitors = {f.source_competitor for f in _DISTILLED_FEATURES}
    assert competitors == {"NovelAI", "Sudowrite", "Novelcrafter", "NolanAI", "Jenova"}

def test_tc04_feature_phase_valid():
    valid = {DistillationPhase.IMMEDIATE, DistillationPhase.NEXT, DistillationPhase.DEFERRED}
    for f in _DISTILLED_FEATURES:
        assert f.distillation_phase in valid

def test_tc05_feature_internal_module_nonempty():
    for f in _DISTILLED_FEATURES:
        assert len(f.internal_module) > 0


# ── TC06~TC10: DistillationReport 구조 ───────────────────────────────────
def test_tc06_report_source_gate(report):
    assert report.source_gate == "G72"

def test_tc07_report_export_ready(report):
    assert report.export_ready is True

def test_tc08_report_immediate_min(report):
    assert report.immediate_count >= 10

def test_tc09_report_total_features(report):
    assert len(report.distilled_features) >= 19

def test_tc10_report_counts_sum(report):
    total = report.immediate_count + report.next_count + report.deferred_count
    assert total == len(report.distilled_features)


# ── TC11~TC15: 파이프라인 실행 ─────────────────────────────────────────────
def test_tc11_pipeline_run_returns_report(pipeline):
    r = pipeline.run()
    assert isinstance(r, DistillationReport)

def test_tc12_pipeline_run_idempotent(pipeline):
    r1 = pipeline.run()
    r2 = pipeline.run()
    assert r1.immediate_count == r2.immediate_count

def test_tc13_export_roadmap_nonempty(roadmap):
    assert len(roadmap) >= 19

def test_tc14_roadmap_sorted_by_phase(roadmap):
    phase_order = {"immediate": 0, "next": 1, "deferred": 2}
    phases = [phase_order[item["phase"]] for item in roadmap]
    assert phases == sorted(phases)

def test_tc15_roadmap_item_keys(roadmap):
    required_keys = {"id", "competitor", "feature", "module", "phase", "rationale"}
    for item in roadmap:
        assert required_keys.issubset(set(item.keys()))


# ── TC16~TC20: 경쟁사별 증류 존재 확인 ─────────────────────────────────────
def test_tc16_novel_ai_features_distilled(report):
    sources = {f.source_competitor for f in report.distilled_features}
    assert "NovelAI" in sources

def test_tc17_sudowrite_features_distilled(report):
    sources = {f.source_competitor for f in report.distilled_features}
    assert "Sudowrite" in sources

def test_tc18_novelcrafter_features_distilled(report):
    sources = {f.source_competitor for f in report.distilled_features}
    assert "Novelcrafter" in sources

def test_tc19_nolan_ai_features_distilled(report):
    sources = {f.source_competitor for f in report.distilled_features}
    assert "NolanAI" in sources

def test_tc20_jenova_features_distilled(report):
    sources = {f.source_competitor for f in report.distilled_features}
    assert "Jenova" in sources


# ── TC21~TC25: 특정 DF 항목 확인 ────────────────────────────────────────────
def test_tc21_df001_exists(report):
    ids = [f.feature_id for f in report.distilled_features]
    assert "DF-001" in ids

def test_tc22_df014_script_format_immediate(report):
    fmap = {f.feature_id: f for f in report.distilled_features}
    assert "DF-014" in fmap
    assert fmap["DF-014"].distillation_phase == DistillationPhase.IMMEDIATE

def test_tc23_df019_korean_genre_immediate(report):
    fmap = {f.feature_id: f for f in report.distilled_features}
    assert "DF-019" in fmap
    assert fmap["DF-019"].distillation_phase == DistillationPhase.IMMEDIATE

def test_tc24_immediate_features_have_module(report):
    for f in report.distilled_features:
        if f.distillation_phase == DistillationPhase.IMMEDIATE:
            assert "literary_system" in f.internal_module

def test_tc25_no_empty_feature_ids(report):
    for f in report.distilled_features:
        assert f.feature_id.startswith("DF-")


# ── TC26~TC30: to_dict + G72-D 게이트 연동 ─────────────────────────────────
def test_tc26_report_to_dict_keys(report):
    d = report.to_dict()
    assert "source_gate" in d
    assert "total" in d
    assert "features" in d
    assert "export_ready" in d

def test_tc27_report_to_dict_total(report):
    d = report.to_dict()
    assert d["total"] == len(report.distilled_features)

def test_tc28_custom_pipeline_empty():
    p = DistillationExportPipeline(features=[])
    r = p.run()
    assert r.immediate_count == 0
    assert r.export_ready is True

def test_tc29_g72d_gate_pass():
    from literary_system.gates.release_gate import GATES
    gate_ids = [g[0] for g in GATES]
    assert "distillation_export_g72d" in gate_ids

def test_tc30_g72d_gate_result():
    from literary_system.gates.release_gate import _gate_distillation_export_g72d
    result = _gate_distillation_export_g72d()
    assert result["pass"] is True
    assert result["gate"] == "G72-D"
