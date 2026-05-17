"""
V445 tests -- DatasetCardGenerator + TrainingDataRegistry (ADR-008)
"""
import json
import tempfile
from pathlib import Path
import pytest
from literary_system.slm.dataset_card_registry import (
    DatasetCardGenerator, TrainingDataRegistry,
    DatasetStats, BiasAnalysis, DatasetVersion,
    ConsentRecord, DeletionRequest,
)
from literary_system.trace.trace_dataset_store import (
    TraceRecord, PromotionTier, make_trace_record,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_BEFORE = {"SP": 0.4, "RU": 0.3, "ET": 0.2}
_AFTER  = {"SP": 0.5, "RU": 0.4, "ET": 0.3}


def _rec(genre="drama", scene_id="sc01", L_total=0.10, episode_no=1) -> TraceRecord:
    return make_trace_record(
        project_id="test_proj",
        episode_no=episode_no,
        scene_id=scene_id,
        seed_contract={"genre": genre, "user_prompt": "씬"},
        style_dna_profile="압박형",
        macroarc_intent="갈등",
        literary_state_before=_BEFORE,
        literary_state_after=_AFTER,
        render_output={scene_id: f"씨 {scene_id} 내용"},
        loss_report={"L_total": L_total},
        reader_estimate={"reader_pull": 0.60, "ai_smell_score": 0.10},
        trajectory_deviation=0.05,
        critic_findings=[],
        repair_applied=False,
        hitl_recommended=False,
        knowledge_pressure=0.3,
    )


def _make_records(n=5):
    genres = ["drama", "thriller", "romance"]
    return [_rec(genre=genres[i % 3], scene_id=f"sc{i:02d}", episode_no=i+1) for i in range(n)]


# ---------------------------------------------------------------------------
# TestDatasetStats
# ---------------------------------------------------------------------------

class TestDatasetStats:
    def test_canonical_ratio(self):
        s = DatasetStats(
            total_records=10, canonical_count=7, candidate_count=3, archive_count=0,
            genre_distribution={"drama": 10}, style_distribution={"A": 10},
            avg_L_total=0.10, avg_reader_pull=0.60,
        )
        assert s.canonical_ratio == 0.7

    def test_to_dict_keys(self):
        s = DatasetStats(
            total_records=5, canonical_count=5, candidate_count=0, archive_count=0,
            genre_distribution={"drama": 5}, style_distribution={"A": 5},
            avg_L_total=0.10, avg_reader_pull=0.60,
        )
        d = s.to_dict()
        assert "total_records" in d
        assert "canonical_ratio" in d
        assert "genre_distribution" in d


# ---------------------------------------------------------------------------
# TestDatasetCardGenerator
# ---------------------------------------------------------------------------

class TestDatasetCardGenerator:
    def test_invalid_license_raises(self):
        with pytest.raises(ValueError):
            DatasetCardGenerator("test", "v1", license_id="unknown-license")

    def test_compute_stats_counts(self):
        gen = DatasetCardGenerator("test_ds", "v1.0")
        records = _make_records(6)
        stats = gen.compute_stats(records)
        assert stats.total_records == 6
        assert stats.canonical_count + stats.candidate_count + stats.archive_count == 6

    def test_compute_stats_genre_distribution(self):
        gen = DatasetCardGenerator("test_ds", "v1.0")
        records = _make_records(6)
        stats = gen.compute_stats(records)
        assert "drama" in stats.genre_distribution

    def test_generate_card_returns_dict(self):
        gen = DatasetCardGenerator("test_ds", "v1.0")
        records = _make_records(4)
        result = gen.generate_card(records)
        assert "card_text" in result
        assert "stats" in result
        assert "bias_analysis" in result

    def test_generate_card_markdown_content(self):
        gen = DatasetCardGenerator("lit_dataset", "v2.0")
        records = _make_records(3)
        result = gen.generate_card(records)
        card = result["card_text"]
        assert "lit_dataset" in card
        assert "license:" in card
        assert "## 통계" in card

    def test_generate_card_saves_file(self):
        gen = DatasetCardGenerator("test_ds", "v1.0")
        records = _make_records(3)
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
            out = f.name
        result = gen.generate_card(records, out_path=out)
        assert Path(out).exists()
        assert Path(out).read_text(encoding="utf-8") == result["card_text"]

    def test_bias_analysis_warnings_on_imbalanced(self):
        gen = DatasetCardGenerator("test_ds", "v1.0")
        stats = DatasetStats(
            total_records=100, canonical_count=5, candidate_count=95, archive_count=0,
            genre_distribution={"drama": 90, "thriller": 10},
            style_distribution={"A": 100},
            avg_L_total=0.15, avg_reader_pull=0.50,
        )
        bias = gen.analyze_bias(stats)
        assert len(bias.warnings) >= 1

    def test_bias_analysis_no_warnings_on_balanced(self):
        gen = DatasetCardGenerator("test_ds", "v1.0")
        stats = DatasetStats(
            total_records=100, canonical_count=70, candidate_count=30, archive_count=0,
            genre_distribution={"drama": 50, "thriller": 50},
            style_distribution={"A": 50, "B": 50},
            avg_L_total=0.10, avg_reader_pull=0.65,
        )
        bias = gen.analyze_bias(stats)
        assert len(bias.warnings) == 0

    def test_pii_count_in_bias(self):
        gen = DatasetCardGenerator("test_ds", "v1.0")
        records = _make_records(3)
        result = gen.generate_card(records, pii_scrubbed=7)
        assert result["bias_analysis"]["pii_scrubbed_count"] == 7


# ---------------------------------------------------------------------------
# TestTrainingDataRegistry
# ---------------------------------------------------------------------------

class TestTrainingDataRegistry:
    def test_register_version_returns_version(self):
        reg = TrainingDataRegistry()
        v = reg.register_version("v1.0.0", "ds", ["id1", "id2"], {"total": 2})
        assert isinstance(v, DatasetVersion)
        assert v.version_tag == "v1.0.0"
        assert len(v.record_ids) == 2

    def test_version_is_immutable(self):
        reg = TrainingDataRegistry()
        v = reg.register_version("v1.0.0", "ds", ["id1"], {})
        with pytest.raises((AttributeError, TypeError)):
            v.version_tag = "v2.0.0"

    def test_list_versions_by_dataset(self):
        reg = TrainingDataRegistry()
        reg.register_version("v1.0", "ds_a", ["a1"], {})
        reg.register_version("v1.0", "ds_b", ["b1"], {})
        reg.register_version("v2.0", "ds_a", ["a2"], {})
        vs = reg.list_versions("ds_a")
        assert len(vs) == 2
        assert all(v.dataset_name == "ds_a" for v in vs)

    def test_consent_record_and_check(self):
        reg = TrainingDataRegistry()
        reg.record_consent("user_01", "ds", purpose="slm_training")
        assert reg.has_consent("user_01", "ds", "slm_training")
        assert not reg.has_consent("user_01", "ds", "evaluation")

    def test_revoke_consent(self):
        reg = TrainingDataRegistry()
        c = reg.record_consent("user_02", "ds")
        assert reg.has_consent("user_02", "ds")
        reg.revoke_consent(c.consent_id)
        assert not reg.has_consent("user_02", "ds")

    def test_revoke_unknown_returns_false(self):
        reg = TrainingDataRegistry()
        assert reg.revoke_consent("no-such-id") is False

    def test_deletion_request_pending(self):
        reg = TrainingDataRegistry()
        req = reg.request_deletion("user_03", "ds", ["id_x", "id_y"])
        assert req.status == "pending"
        assert len(reg.pending_deletions()) == 1

    def test_complete_deletion(self):
        reg = TrainingDataRegistry()
        req = reg.request_deletion("user_04", "ds", ["id_z"])
        result = reg.complete_deletion(req.request_id)
        assert result is True
        assert reg._deletions[req.request_id].status == "completed"
        assert len(reg.pending_deletions()) == 0

    def test_audit_log_append_only(self):
        reg = TrainingDataRegistry()
        reg.register_version("v1", "ds", [], {})
        reg.record_consent("u1", "ds")
        log = reg.audit_log()
        assert len(log) >= 2
        # 복사본이므로 원본 변조 불가
        log.clear()
        assert len(reg.audit_log()) >= 2

    def test_export_json(self):
        reg = TrainingDataRegistry()
        reg.register_version("v1.0", "ds", ["a", "b"], {"total": 2})
        reg.record_consent("u1", "ds")
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            out = f.name
        result = reg.export(out)
        assert Path(out).exists()
        data = json.loads(Path(out).read_text(encoding="utf-8"))
        assert len(data["versions"]) == 1
        assert len(data["consents"]) == 1

    def test_persist_to_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            reg = TrainingDataRegistry(tmp)
            v = reg.register_version("v1.0", "ds", ["a"], {"total": 1})
            # JSON 파일 저장 확인
            vpath = Path(tmp) / f"{v.version_id}.json"
            assert vpath.exists()
            loaded = json.loads(vpath.read_text(encoding="utf-8"))
            assert loaded["version_tag"] == "v1.0"
