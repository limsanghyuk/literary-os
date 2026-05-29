"""V328 Task16: DataChunker + CausalContinuationPlanBuilder + ReferencePackSteering 테스트."""
import sys, os, json, tempfile; sys.path.insert(0,"/tmp/literary_os_v328")
import pytest
from literary_system.slm.data_chunker import DataChunker
from literary_system.causal.causal_continuation_plan_builder import (
    CausalContinuationPlanBuilder, CausalPlan)
from literary_system.analyzer.reference_pack_steering import ReferencePackSteering

# ── DataChunker ──────────────────────────────────────────────────────
class TestDataChunker:
    def test_empty_file(self, tmp_path):
        f = tmp_path / "empty.jsonl"
        f.write_text("")
        c = DataChunker(chunk_size=10)
        chunks = c.iter_chunks(str(f))
        assert isinstance(chunks, list)

    def test_chunks_correct_size(self, tmp_path):
        f = tmp_path / "data.jsonl"
        rows = [json.dumps({"i": i}) for i in range(25)]
        f.write_text("\n".join(rows))
        c = DataChunker(chunk_size=10)
        chunks = c.iter_chunks(str(f))
        assert len(chunks) == 3
        assert len(chunks[0]) == 10
        assert len(chunks[2]) == 5

    def test_missing_file_returns_empty(self):
        c = DataChunker()
        chunks = c.iter_chunks("/nonexistent/path.jsonl")
        assert chunks == []

    def test_run_pipeline_with_mock(self, tmp_path):
        f = tmp_path / "trace.jsonl"
        rows = [json.dumps({"scene": i, "text": f"씬{i}"}) for i in range(20)]
        f.write_text("\n".join(rows))

        class MockTraceStore:
            def export_slm_dataset(self, path):
                pass  # file already written
        class MockSLMBuilder:
            def __init__(self): self.batches = []
            def add_batch(self, batch): self.batches.append(batch)

        builder = MockSLMBuilder()
        c = DataChunker(chunk_size=10)
        result = c.run_pipeline(MockTraceStore(), builder, str(f))
        assert result["chunks_processed"] >= 2
        assert result["pairs_total"] == 20

    def test_pipeline_export_called(self, tmp_path):
        f = tmp_path / "trace.jsonl"
        f.write_text("")
        called = []
        class MockTraceStore:
            def export_slm_dataset(self, path): called.append(path)
        c = DataChunker()
        c.run_pipeline(MockTraceStore(), object(), str(f))
        assert len(called) == 1

# ── CausalContinuationPlanBuilder ────────────────────────────────────
class TestCausalContinuationPlanBuilder:
    def test_build_with_data(self):
        b = CausalContinuationPlanBuilder()
        data = {"seeds":["씨앗1"],"tension_forward":0.8,"key_events":["사건A"]}
        plan = b.build(episode_no=2, handoff_data=data)
        assert isinstance(plan, CausalPlan)
        assert plan.built == True
        assert "씨앗1" in plan.seeds
        assert plan.tension_fwd == pytest.approx(0.8)

    def test_build_empty_data(self):
        b = CausalContinuationPlanBuilder()
        plan = b.build(episode_no=1)
        assert plan.built == True
        assert plan.seeds == []

    def test_build_with_store(self):
        class MockStore:
            def get_handoff(self, ep):
                return {"seeds":["store_seed"],"tension_forward":0.7,"key_events":[]}
        b = CausalContinuationPlanBuilder(handoff_store=MockStore())
        plan = b.build(episode_no=3)
        assert "store_seed" in plan.seeds

    def test_episode_no_stored(self):
        b = CausalContinuationPlanBuilder()
        plan = b.build(episode_no=5)
        assert plan.episode_no == 5

    def test_tension_fwd_default(self):
        b = CausalContinuationPlanBuilder()
        plan = b.build(episode_no=1, handoff_data={})
        assert 0.0 <= plan.tension_fwd <= 1.0

# ── ReferencePackSteering ─────────────────────────────────────────────
class TestReferencePackSteering:
    def test_no_pack_returns_input(self):
        s = ReferencePackSteering()
        obj = {"score": 0.8}
        assert s.steer(obj) is obj

    def test_none_input_returns_none(self):
        s = ReferencePackSteering()
        assert s.steer(None) is None

    def test_with_mock_pack_dict(self):
        class MockPack:
            def get_signals(self): return ["signal_A","signal_B"]
        s = ReferencePackSteering(reference_pack=MockPack())
        result = s.steer({"analysis": "ok"})
        assert "steering_signals" in result
        assert "signal_A" in result["steering_signals"]

    def test_pack_exception_returns_input(self):
        class BrokenPack:
            def get_signals(self): raise RuntimeError("fail")
        s = ReferencePackSteering(reference_pack=BrokenPack())
        obj = {"x": 1}
        result = s.steer(obj)
        assert result is obj
