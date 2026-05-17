"""
V316 테스트 — TraceDatasetStore + SLMDatasetBuilder + StudioApp 전수 검증.
"""
from __future__ import annotations
import sys, json, tempfile
from pathlib import Path

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from literary_system.trace.trace_dataset_store import (
    TraceDatasetStore, TraceRecord, PromotionTier,
    make_trace_record,
)
from literary_system.slm.dataset_builder import SLMDatasetBuilder


# ── 테스트 픽스처 ──────────────────────────────────────────
def make_sample_record(
    L_total: float = 0.08,
    repair_applied: bool = False,
    genre: str = "political_thriller",
    profile: str = "political_cold",
    render_output: dict | None = None,
) -> TraceRecord:
    return make_trace_record(
        project_id="proj_test",
        episode_no=1,
        scene_id="EP01_SC01",
        seed_contract={"genre": genre, "user_prompt": "정치 스릴러 3화",
                        "format_type": "screenplay"},
        style_dna_profile=profile,
        macroarc_intent="seed_conflict_and_grid",
        literary_state_before={"SP": 0.35, "RU": 0.62, "ET": 0.0,
                                "RD": 0.12, "RT": 0.30, "AC": 0.70,
                                "RO": 0.50, "MR": 0.10},
        literary_state_after= {"SP": 0.47, "RU": 0.58, "ET": 0.05,
                                "RD": 0.14, "RT": 0.35, "AC": 0.70,
                                "RO": 0.52, "MR": 0.11},
        render_output=render_output or {
            "SC01": "그는 서류를 집어들었다. 빗소리가 들렸다.",
            "SC02": "복도가 비어 있었다. 불빛이 흔들렸다.",
        },
        loss_report={"L_total": L_total, "L_struct": 0.02, "L_smell_surface": 0.01},
        reader_estimate={"reader_pull": 0.68, "reader_afterimage": 0.55,
                          "ai_smell_score": 0.05},
        trajectory_deviation=0.04,
        critic_findings=[],
        repair_applied=repair_applied,
        hitl_recommended=False,
        knowledge_pressure=0.45,
        call_count=1,
    )


# ═══════════════════════════════════════════════════════════
# TestTraceRecord
# ═══════════════════════════════════════════════════════════
class TestTraceRecord:

    def test_canonical_promotion_at_012(self):
        r = make_sample_record(L_total=0.08, repair_applied=False)
        assert r.promotion == PromotionTier.CANONICAL

    def test_exactly_012_is_canonical(self):
        r = make_sample_record(L_total=0.12, repair_applied=False)
        assert r.promotion == PromotionTier.CANONICAL

    def test_just_over_012_is_candidate(self):
        r = make_sample_record(L_total=0.13)
        assert r.promotion == PromotionTier.CANDIDATE

    def test_candidate_at_018(self):
        r = make_sample_record(L_total=0.18)
        assert r.promotion == PromotionTier.CANDIDATE

    def test_archive_above_020(self):
        r = make_sample_record(L_total=0.25)
        assert r.promotion == PromotionTier.ARCHIVE

    def test_repair_applied_blocks_canonical(self):
        # repair 적용 시 canonical 불가
        r = make_sample_record(L_total=0.08, repair_applied=True)
        assert r.promotion == PromotionTier.CANDIDATE

    def test_state_delta_calculated(self):
        r = make_sample_record()
        assert "SP" in r.literary_state_delta
        assert abs(r.literary_state_delta["SP"] - 0.12) < 0.01

    def test_trace_id_unique(self):
        r1 = make_sample_record()
        r2 = make_sample_record()
        assert r1.trace_id != r2.trace_id

    def test_slm_pair_canonical(self):
        r = make_sample_record(L_total=0.08)
        pair = r.as_slm_pair()
        assert pair is not None
        assert "instruction" in pair
        assert "output" in pair
        assert "SC01" in pair["output"] or "서류" in pair["output"]

    def test_slm_pair_archive_returns_none(self):
        r = make_sample_record(L_total=0.30)
        pair = r.as_slm_pair()
        assert pair is None

    def test_slm_pair_empty_output_returns_none(self):
        r = make_sample_record(render_output={"SC01": "", "SC02": "   "})
        pair = r.as_slm_pair()
        assert pair is None


# ═══════════════════════════════════════════════════════════
# TestTraceDatasetStore
# ═══════════════════════════════════════════════════════════
class TestTraceDatasetStore:

    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.store = TraceDatasetStore(self.tmpdir)

    def test_commit_canonical_creates_file(self):
        r = make_sample_record(L_total=0.08)
        result = self.store.commit(r)
        assert result["promotion"] == PromotionTier.CANONICAL
        assert Path(self.tmpdir, "canonical_fewshot.jsonl").exists()

    def test_commit_candidate_creates_file(self):
        r = make_sample_record(L_total=0.16)
        self.store.commit(r)
        assert Path(self.tmpdir, "candidate_fewshot.jsonl").exists()

    def test_all_traces_always_written(self):
        for L in [0.05, 0.15, 0.30]:
            self.store.commit(make_sample_record(L_total=L))
        lines = Path(self.tmpdir, "all_traces.jsonl").read_text().strip().split("\n")
        assert len(lines) == 3

    def test_get_by_trace_id(self):
        r = make_sample_record()
        self.store.commit(r)
        retrieved = self.store.get(r.trace_id)
        assert retrieved is not None
        assert retrieved.trace_id == r.trace_id

    def test_search_by_genre(self):
        self.store.commit(make_sample_record(genre="political_thriller"))
        self.store.commit(make_sample_record(genre="noir_crime"))
        self.store.commit(make_sample_record(genre="political_thriller"))
        results = self.store.search_by_genre("political_thriller")
        assert len(results) == 2

    def test_search_by_genre_with_tier(self):
        self.store.commit(make_sample_record(L_total=0.08))   # canonical
        self.store.commit(make_sample_record(L_total=0.16))   # candidate
        self.store.commit(make_sample_record(L_total=0.30))   # archive
        canonical = self.store.search_by_genre("political_thriller", PromotionTier.CANONICAL)
        assert len(canonical) == 1

    def test_best_canonical(self):
        for L in [0.05, 0.09, 0.11, 0.25]:
            self.store.commit(make_sample_record(L_total=L))
        best = self.store.best_canonical("political_thriller", n=2)
        assert len(best) == 2
        assert best[0].loss_report["L_total"] <= best[1].loss_report["L_total"]

    def test_repair_log_saved(self):
        r = make_sample_record()
        self.store.commit(r)
        self.store.commit_repair_log(
            r.trace_id, ["SC01"], "원본 텍스트", "수정 텍스트", "AI_connective_결국", 0.18, 0.10
        )
        assert Path(self.tmpdir, "repair_log.jsonl").exists()
        log = json.loads(Path(self.tmpdir, "repair_log.jsonl").read_text().strip())
        assert log["improvement"] == round(0.18 - 0.10, 4)

    def test_critic_log_saved(self):
        r = make_sample_record()
        self.store.commit(r)
        self.store.commit_critic_log(
            r.trace_id,
            [{"pattern": "AI_connective_결국", "priority": 75}],
            "micro_refine"
        )
        assert Path(self.tmpdir, "critic_log.jsonl").exists()

    def test_export_slm_dataset(self):
        for L in [0.06, 0.10, 0.17, 0.30]:
            self.store.commit(make_sample_record(L_total=L))
        out = Path(self.tmpdir, "test_slm.jsonl")
        result = self.store.export_slm_dataset(out, max_L_total=0.20)
        assert result["exported"] == 3  # 0.30은 제외
        assert out.exists()
        lines = out.read_text().strip().split("\n")
        assert len(lines) == 3

    def test_statistics(self):
        for L in [0.08, 0.15, 0.28]:
            self.store.commit(make_sample_record(L_total=L))
        stats = self.store.statistics()
        assert stats["total_traces"] == 3
        assert "by_tier" in stats
        assert "avg_L_total" in stats
        assert "slm_ready_count" in stats


# ═══════════════════════════════════════════════════════════
# TestSLMDatasetBuilder
# ═══════════════════════════════════════════════════════════
class TestSLMDatasetBuilder:

    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.store = TraceDatasetStore(self.tmpdir)
        for L in [0.06, 0.10, 0.14, 0.18, 0.25, 0.30]:
            self.store.commit(make_sample_record(L_total=L))
        self.builder = SLMDatasetBuilder(self.store)

    def test_alpaca_dataset_count(self):
        out = Path(self.tmpdir, "alpaca.json")
        result = self.builder.build_alpaca_dataset(out, max_L_total=0.18)
        assert result["format"] == "alpaca"
        assert result["total_records"] == 4  # ≤0.18인 것: 0.06/0.10/0.14/0.18
        assert out.exists()

    def test_alpaca_format_structure(self):
        out = Path(self.tmpdir, "alpaca.json")
        self.builder.build_alpaca_dataset(out, max_L_total=0.20)
        data = json.loads(out.read_text())
        assert len(data) > 0
        for entry in data:
            assert "instruction" in entry
            assert "input" in entry
            assert "output" in entry
            assert "metadata" in entry

    def test_openai_dataset_jsonl(self):
        out = Path(self.tmpdir, "openai.jsonl")
        result = self.builder.build_openai_dataset(out, max_L_total=0.20)
        assert out.exists()
        lines = out.read_text().strip().split("\n")
        assert len(lines) > 0
        for line in lines:
            entry = json.loads(line)
            assert "messages" in entry
            assert len(entry["messages"]) == 3  # system/user/assistant

    def test_openai_messages_roles(self):
        out = Path(self.tmpdir, "openai2.jsonl")
        self.builder.build_openai_dataset(out)
        first_line = json.loads(Path(out).read_text().strip().split("\n")[0])
        roles = [m["role"] for m in first_line["messages"]]
        assert roles == ["system", "user", "assistant"]

    def test_quality_report(self):
        out = Path(self.tmpdir, "quality.json")
        report = self.builder.build_quality_report(out)
        assert "overview" in report
        assert "genre_avg_L_total" in report
        assert "repair_analysis" in report
        assert out.exists()

    def test_filter_by_reader_pull(self):
        # reader_pull이 낮은 레코드 추가
        low_pull_r = make_sample_record(L_total=0.10)
        low_pull_r.reader_estimate["reader_pull"] = 0.10
        self.store.commit(low_pull_r)

        out = Path(self.tmpdir, "filtered.json")
        result = self.builder.build_alpaca_dataset(
            out, max_L_total=0.20, min_reader_pull=0.40
        )
        # reader_pull 0.10인 레코드는 제외되어야 함
        data = json.loads(out.read_text())
        for entry in data:
            assert entry["metadata"]["reader_pull"] >= 0.40


# ═══════════════════════════════════════════════════════════
# TestStudioApp
# ═══════════════════════════════════════════════════════════
class TestStudioApp:

    def test_mock_app_creates(self):
        from apps.studio_api.main import create_studio_app
        app = create_studio_app("/tmp/studio_test")
        assert app is not None

    def test_mock_app_run_generate(self):
        from apps.studio_api.main import create_studio_app, MockStudioApp
        app = create_studio_app("/tmp/studio_test", "/nonexistent")
        if isinstance(app, MockStudioApp):
            result = app.run_generate("정치 스릴러 3화")
            assert "episodes" in result
            assert len(result["episodes"]) == 3

    def test_mock_app_status(self):
        from apps.studio_api.main import MockStudioApp
        app = MockStudioApp("/tmp/studio_test", None)
        status = app.get_status()
        assert "status" in status

    def test_edit_handlers_return_dict(self):
        from apps.studio_api.main import (
            _edit_reduce_dialogue, _edit_add_residue,
            _edit_delay_reveal, _edit_fix_pdi
        )
        class FakeReq:
            scene_id = "EP01_SC01"
            instruction = ""

        for handler in [_edit_reduce_dialogue, _edit_add_residue,
                         _edit_delay_reveal, _edit_fix_pdi]:
            result = handler(FakeReq())
            assert "edit_type" in result
            assert "instruction" in result
            assert "status" in result
