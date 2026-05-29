"""
test_v612_sp_b3_integration.py
V612 SP-B.3 통합 완성 테스트 — Gate G58 (LoRAStackingAdapter) + Gate G59 (SP-B.3 Exit)
"""
from __future__ import annotations
import pytest


# ─────────────────────────────────────────────────────────
# TC-1: LoRAStackingAdapter 핵심 인터페이스
# ─────────────────────────────────────────────────────────
class TestLoRAStackingAdapterCore:
    def test_import_and_version(self):
        from literary_system.serving.lora_stacking_adapter import LoRAStackingAdapter
        assert LoRAStackingAdapter.VERSION == "1.0.0"

    def test_register_and_get(self):
        from literary_system.serving.lora_stacking_adapter import LoRAStackingAdapter, LoRAWeight
        adapter = LoRAStackingAdapter()
        w = LoRAWeight(weight_id="w1", genre="drama", version="1.0",
                       weight_data={"l1": {"a": 0.5}})
        adapter.register(w)
        got = adapter.get("w1")
        assert got is not None
        assert got.genre == "drama"

    def test_list_by_genre(self):
        from literary_system.serving.lora_stacking_adapter import LoRAStackingAdapter, LoRAWeight
        adapter = LoRAStackingAdapter()
        for i in range(3):
            adapter.register(LoRAWeight(f"d{i}", "drama", "1.0", {"l": {}}))
        assert len(adapter.list_by_genre("drama")) == 3
        assert adapter.list_by_genre("unknown") == []

    def test_stack_merge_accuracy(self):
        from literary_system.serving.lora_stacking_adapter import LoRAStackingAdapter, LoRAWeight
        adapter = LoRAStackingAdapter()
        adapter.register(LoRAWeight("wa", "drama", "1.0", {"layer1": {"w": 0.5}}))
        adapter.register(LoRAWeight("wb", "thriller", "1.0", {"layer1": {"w": 0.2}}))
        result = adapter.stack(["wa", "wb"], coefficients=[0.6, 0.4])
        # 0.6*0.5 + 0.4*0.2 = 0.38
        assert abs(result.merged_weights["layer1"]["w"] - 0.38) < 1e-6

    def test_coeff_sum_not_one_raises(self):
        from literary_system.serving.lora_stacking_adapter import LoRAStackingAdapter, LoRAWeight
        adapter = LoRAStackingAdapter()
        adapter.register(LoRAWeight("wa", "drama", "1.0", {"l": {}}))
        adapter.register(LoRAWeight("wb", "thriller", "1.0", {"l": {}}))
        with pytest.raises(ValueError):
            adapter.stack(["wa", "wb"], coefficients=[0.3, 0.4])

    def test_genre_stack_equal_coefficients(self):
        from literary_system.serving.lora_stacking_adapter import LoRAStackingAdapter, LoRAWeight
        adapter = LoRAStackingAdapter()
        adapter.register(LoRAWeight("wa", "drama", "1.0", {"l": {"x": 1.0}}))
        adapter.register(LoRAWeight("wb", "comedy", "1.0", {"l": {"x": 0.0}}))
        result = adapter.genre_stack(["drama", "comedy"], project_id="tc1_test")
        assert abs(result.coeff_sum - 1.0) < 1e-6

    def test_normalize_coefficients(self):
        from literary_system.serving.lora_stacking_adapter import LoRAStackingAdapter, LoRAWeight
        adapter = LoRAStackingAdapter()
        adapter.register(LoRAWeight("wa", "drama", "1.0", {"l": {}}))
        adapter.register(LoRAWeight("wb", "thriller", "1.0", {"l": {}}))
        adapter.register(LoRAWeight("wc", "comedy", "1.0", {"l": {}}))
        norm = adapter.normalize_coefficients(["wa", "wb", "wc"], [2.0, 3.0, 5.0])
        assert abs(sum(norm) - 1.0) < 1e-9
        assert abs(norm[0] - 0.2) < 1e-9
        assert abs(norm[2] - 0.5) < 1e-9

    def test_apply_to_model_structure(self):
        from literary_system.serving.lora_stacking_adapter import LoRAStackingAdapter, LoRAWeight
        adapter = LoRAStackingAdapter()
        adapter.register(LoRAWeight("wa", "drama", "1.0", {"l": {"x": 0.5}}))
        adapter.register(LoRAWeight("wb", "drama", "1.0", {"l": {"x": 0.5}}))
        result = adapter.stack(["wa", "wb"], coefficients=[0.5, 0.5])
        patch = adapter.apply_to_model(result, model_id="llm_test")
        assert "model_id" in patch
        assert "layers_applied" in patch

    def test_stats_keys(self):
        from literary_system.serving.lora_stacking_adapter import LoRAStackingAdapter
        adapter = LoRAStackingAdapter()
        s = adapter.stats()
        assert "registered_weights" in s
        assert "genres" in s


# ─────────────────────────────────────────────────────────
# TC-2: Gate G58 직접 실행
# ─────────────────────────────────────────────────────────
class TestGateG58:
    def test_gate_g58_pass(self):
        from literary_system.gates.release_gate import _gate_lora_stacking_g58
        result = _gate_lora_stacking_g58()
        assert result["pass"] is True, f"G58 오류: {result.get('errors')}"

    def test_gate_g58_all_checkpoints(self):
        from literary_system.gates.release_gate import _gate_lora_stacking_g58
        result = _gate_lora_stacking_g58()
        assert len(result["checkpoints"]) == 8

    def test_gate_g58_no_errors(self):
        from literary_system.gates.release_gate import _gate_lora_stacking_g58
        result = _gate_lora_stacking_g58()
        assert result.get("errors", []) == []


# ─────────────────────────────────────────────────────────
# TC-3: SP-B.3 7모듈 임포트 + 인터페이스
# ─────────────────────────────────────────────────────────
class TestSPB3Modules:
    def test_shared_character_db_v2(self):
        from literary_system.multiwork.shared_character_db_v2 import SharedCharacterDBV2
        db = SharedCharacterDBV2()
        assert hasattr(db, "add_character") and hasattr(db, "get_character")

    def test_shared_world_db_v2(self):
        from literary_system.multiwork.shared_world_db_v2 import SharedWorldDBV2
        wdb = SharedWorldDBV2()
        assert hasattr(wdb, "add_location") and hasattr(wdb, "get_location")

    def test_multi_work_orchestrator_v2(self):
        from literary_system.multiwork.multi_work_orchestrator_v2 import MultiWorkOrchestratorV2
        assert MultiWorkOrchestratorV2 is not None

    def test_multi_work_cim_v2_version_and_reward(self):
        from literary_system.multiwork.multi_work_cim_v2 import MultiWorkCIMV2
        cim = MultiWorkCIMV2()
        assert cim.version is not None
        assert hasattr(cim, "reward_weighted_global_weight")

    def test_genre_transfer_v2_methods(self):
        from literary_system.multiwork.genre_transfer import GenreTransferV2, GenreAdaptationReport
        gt = GenreTransferV2()
        assert hasattr(gt, "transfer") and hasattr(gt, "weighted_transfer")

    def test_genre_transfer_weighted_transfer_returns_report(self):
        from literary_system.multiwork.genre_transfer import GenreTransferV2, GenreAdaptationReport
        gt = GenreTransferV2()
        report = gt.weighted_transfer("drama", "thriller", project_id="tc3")
        assert isinstance(report, GenreAdaptationReport)

    def test_lora_stacking_adapter_genre_stack(self):
        from literary_system.serving.lora_stacking_adapter import LoRAStackingAdapter, LoRAWeight
        adapter = LoRAStackingAdapter()
        adapter.register(LoRAWeight("x1", "drama", "1.0", {"l": {"v": 0.8}}))
        adapter.register(LoRAWeight("x2", "thriller", "1.0", {"l": {"v": 0.6}}))
        result = adapter.genre_stack(["drama", "thriller"], project_id="tc3_test")
        assert abs(result.coeff_sum - 1.0) < 1e-6


# ─────────────────────────────────────────────────────────
# TC-4: CP-7 데이터 흐름 — GenreTransferV2 → LoRAStackingAdapter
# ─────────────────────────────────────────────────────────
class TestSPB3DataFlow:
    def test_genre_transfer_to_lora_stack_flow(self):
        from literary_system.multiwork.genre_transfer import GenreTransferV2
        from literary_system.serving.lora_stacking_adapter import LoRAStackingAdapter, LoRAWeight

        gt = GenreTransferV2()
        adapter = LoRAStackingAdapter()
        adapter.register(LoRAWeight("d1", "drama", "1.0", {"l": {"w": 0.7}}))
        adapter.register(LoRAWeight("t1", "thriller", "1.0", {"l": {"w": 0.3}}))

        report = gt.weighted_transfer("drama", "thriller", project_id="flow_test", alpha=0.5)
        genres = list({report.source_genre, report.target_genre} & set(adapter.list_genres()))
        if not genres:
            genres = ["drama", "thriller"]

        stack_result = adapter.genre_stack(genres, project_id="flow_test")
        assert abs(stack_result.coeff_sum - 1.0) < 1e-6
        assert len(stack_result.merged_weights) > 0

    def test_full_sp_b3_pipeline(self):
        """7모듈 간이 통합 파이프라인 — 실 흐름 확인."""
        from literary_system.multiwork.shared_character_db_v2 import SharedCharacterDBV2
        from literary_system.multiwork.shared_world_db_v2 import SharedWorldDBV2
        from literary_system.multiwork.multi_work_cim_v2 import MultiWorkCIMV2
        from literary_system.multiwork.genre_transfer import GenreTransferV2
        from literary_system.serving.lora_stacking_adapter import LoRAStackingAdapter, LoRAWeight

        char_db = SharedCharacterDBV2()
        world_db = SharedWorldDBV2()
        cim = MultiWorkCIMV2()
        gt = GenreTransferV2()
        adapter = LoRAStackingAdapter()

        char_db.add_character("c1", "주인공", "protagonist", genre_tags=["drama"])
        assert char_db.get_character("c1") is not None

        world_db.add_location("loc1", "서울", "현대 도시")
        assert world_db.get_location("loc1") is not None

        assert cim.version is not None

        report = gt.weighted_transfer("drama", "thriller", project_id="full_test")
        assert report is not None

        adapter.register(LoRAWeight("lw1", "drama", "1.0", {"fc": {"bias": 0.1}}))
        adapter.register(LoRAWeight("lw2", "thriller", "1.0", {"fc": {"bias": 0.2}}))
        stack = adapter.genre_stack(["drama", "thriller"], project_id="full_test")
        assert abs(stack.coeff_sum - 1.0) < 1e-6


# ─────────────────────────────────────────────────────────
# TC-5: Gate G59 직접 실행
# ─────────────────────────────────────────────────────────
class TestGateG59:
    def test_gate_g59_pass(self):
        from literary_system.gates.release_gate import _gate_sp_b3_exit_g59
        result = _gate_sp_b3_exit_g59()
        assert result["pass"] is True, f"G59 오류: {result.get('errors')}"

    def test_gate_g59_all_checkpoints(self):
        from literary_system.gates.release_gate import _gate_sp_b3_exit_g59
        result = _gate_sp_b3_exit_g59()
        assert len(result["checkpoints"]) == 7

    def test_gate_g59_no_errors(self):
        from literary_system.gates.release_gate import _gate_sp_b3_exit_g59
        result = _gate_sp_b3_exit_g59()
        assert result.get("errors", []) == []


# ─────────────────────────────────────────────────────────
# TC-6: 릴리즈 게이트 등록 확인
# ─────────────────────────────────────────────────────────
class TestGateRegistration:
    def test_g58_registered_in_gates(self):
        from literary_system.gates.release_gate import GATES
        ids = [g[0] for g in GATES]
        assert "lora_stacking_g58" in ids

    def test_g59_registered_in_gates(self):
        from literary_system.gates.release_gate import GATES
        ids = [g[0] for g in GATES]
        assert "sp_b3_exit_g59" in ids

    def test_gate_count_includes_g58_g59(self):
        from literary_system.gates.release_gate import GATES
        # V611 기준 56 gates + G58 + G59 = 58
        assert len(GATES) >= 58
