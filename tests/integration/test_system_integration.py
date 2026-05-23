"""
test_system_integration.py — V613 SP-B.4 시스템 통합 테스트
SP-B.1 (LoRA Fine-tuning) + SP-B.2 (RLHF 루프) + SP-B.3 (MultiWork 협업)
엔드-투-엔드 파이프라인 검증 (ADR-073)
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


# ─────────────────────────────────────────────────────────────────────────────
# TC-1: SP-B.1 LoRA Fine-tuning Pipeline 통합
# ─────────────────────────────────────────────────────────────────────────────

class TestSPB1Integration:
    """SP-B.1: LoRA 파인튜닝 파이프라인 통합"""

    def test_b1_dataset_builder_import(self):
        """LoRADatasetBuilder 임포트 + build 메서드 존재"""
        from literary_system.finetune.lora_dataset_builder import LoRADatasetBuilder
        builder = LoRADatasetBuilder()
        assert hasattr(builder, "build")

    def test_b1_training_config_defaults(self):
        """LoRATrainingConfig 기본값 유효성"""
        from literary_system.finetune.lora_training_config import LoRATrainingConfig
        cfg = LoRATrainingConfig()
        assert cfg.lora_rank > 0
        assert cfg.learning_rate > 0

    def test_b1_job_runner_import(self):
        """LoRAJobRunner 임포트"""
        from literary_system.finetune.lora_job_runner import LoRAJobRunner
        runner = LoRAJobRunner()
        assert runner is not None

    def test_b1_artifact_model_registry_flow(self):
        """LoRAArtifact → LoRAModelRegistry 저장·조회 흐름"""
        from literary_system.finetune.lora_artifact import LoRAArtifact
        from literary_system.finetune.lora_model_registry import LoRAModelRegistry
        artifact = LoRAArtifact(_artifact_id="v613-test-01")
        registry = LoRAModelRegistry()
        registry.register(artifact)
        fetched = registry.get("v613-test-01")
        assert fetched is not None

    def test_b1_inference_gateway_import(self):
        """LoRAInferenceGateway 임포트"""
        from literary_system.finetune.lora_inference_gateway import LoRAInferenceGateway
        gw = LoRAInferenceGateway()
        assert gw is not None

    def test_b1_gate_g53_pass(self):
        """Gate G53 PASS"""
        from literary_system.gates.release_gate import GATES
        fn = next((fn for n, d, fn in GATES if "g53" in n.lower()), None)
        assert fn is not None
        assert fn()["pass"] is True

    def test_b1_gate_g54_pass(self):
        """Gate G54 PASS"""
        from literary_system.gates.release_gate import GATES
        fn = next((fn for n, d, fn in GATES if "g54" in n.lower()), None)
        assert fn is not None
        assert fn()["pass"] is True


# ─────────────────────────────────────────────────────────────────────────────
# TC-2: SP-B.2 RLHF 루프 통합
# ─────────────────────────────────────────────────────────────────────────────

class TestSPB2Integration:
    """SP-B.2: RLHF 루프 통합"""

    def test_b2_reward_model_import(self):
        """RewardModel v1.0 임포트"""
        from literary_system.rlhf.reward_model import RewardModel
        assert RewardModel() is not None

    def test_b2_rlhf_dataset_builder_import(self):
        """RLHFDatasetBuilder 임포트"""
        from literary_system.rlhf.rlhf_dataset_builder import RLHFDatasetBuilder
        assert RLHFDatasetBuilder() is not None

    def test_b2_ppo_trainer_import(self):
        """PPOTrainer 임포트"""
        from literary_system.rlhf.ppo_trainer import PPOTrainer
        assert PPOTrainer() is not None

    def test_b2_constraint_guard_import(self):
        """ConstraintGuard 임포트"""
        from literary_system.rlhf.constraint_guard import ConstraintGuard
        assert ConstraintGuard() is not None

    def test_b2_rlhf_monitor_import(self):
        """RLHFMonitor 임포트"""
        from literary_system.rlhf.rlhf_monitor import RLHFMonitor
        assert RLHFMonitor() is not None

    def test_b2_canary_controller_import(self):
        """CanaryController 임포트 (serving/)"""
        from literary_system.serving.canary_controller import CanaryController
        assert CanaryController() is not None

    def test_b2_canonical_bridge_v2_import(self):
        """CanonicalBridgeV2 임포트 (llm_bridge/)"""
        from literary_system.llm_bridge.canonical_bridge_v2 import CanonicalBridgeV2
        assert CanonicalBridgeV2() is not None

    def test_b2_gate_g55_pass(self):
        """Gate G55 PASS"""
        from literary_system.gates.release_gate import GATES
        fn = next((fn for n, d, fn in GATES if "g55" in n.lower()), None)
        assert fn is not None
        assert fn()["pass"] is True

    def test_b2_gate_g56_pass(self):
        """Gate G56 PASS"""
        from literary_system.gates.release_gate import GATES
        fn = next((fn for n, d, fn in GATES if "g56" in n.lower()), None)
        assert fn is not None
        assert fn()["pass"] is True

    def test_b2_gate_g57_pass(self):
        """Gate G57 PASS"""
        from literary_system.gates.release_gate import GATES
        fn = next((fn for n, d, fn in GATES if "g57" in n.lower()), None)
        assert fn is not None
        assert fn()["pass"] is True


# ─────────────────────────────────────────────────────────────────────────────
# TC-3: SP-B.3 MultiWork 협업 통합
# ─────────────────────────────────────────────────────────────────────────────

class TestSPB3Integration:
    """SP-B.3: MultiWork 협업 통합"""

    def test_b3_shared_character_db_v2_flow(self):
        """SharedCharacterDBV2: add_character → get_character 흐름"""
        from literary_system.multiwork.shared_character_db_v2 import SharedCharacterDBV2
        db = SharedCharacterDBV2()
        db.add_character("char-v613", "Kim", "lead")
        ch = db.get_character("char-v613")
        assert ch is not None

    def test_b3_shared_world_db_v2_flow(self):
        """SharedWorldDBV2: add_location → get_location 흐름"""
        from literary_system.multiwork.shared_world_db_v2 import SharedWorldDBV2
        db = SharedWorldDBV2()
        db.add_location("loc-v613", "Seoul", "한국 수도")
        loc = db.get_location("loc-v613")
        assert loc is not None

    def test_b3_multi_work_orchestrator_v2_import(self):
        """MultiWorkOrchestratorV2 임포트"""
        from literary_system.multiwork.multi_work_orchestrator_v2 import MultiWorkOrchestratorV2
        assert MultiWorkOrchestratorV2() is not None

    def test_b3_multi_work_cim_v2_version(self):
        """MultiWorkCIMV2 version 속성"""
        from literary_system.multiwork.multi_work_cim_v2 import MultiWorkCIMV2
        cim = MultiWorkCIMV2()
        assert hasattr(cim, "version")

    def test_b3_genre_transfer_weighted_transfer(self):
        """GenreTransferV2.weighted_transfer() 정상 실행"""
        from literary_system.multiwork.genre_transfer import GenreTransferV2
        gt = GenreTransferV2()
        result = gt.weighted_transfer(
            source_genre="drama", target_genre="thriller",
            project_id="int-v613", alpha=0.5
        )
        assert result is not None

    def test_b3_lora_stacking_adapter_register_stack(self):
        """LoRAStackingAdapter: LoRAWeight 등록 → stack 흐름"""
        from literary_system.serving.lora_stacking_adapter import LoRAStackingAdapter, LoRAWeight
        adapter = LoRAStackingAdapter()
        w1 = LoRAWeight(weight_id="w613-1", genre="drama", version="1.0",
                        weight_data={"layer0": {"a": 0.8}})
        w2 = LoRAWeight(weight_id="w613-2", genre="thriller", version="1.0",
                        weight_data={"layer0": {"a": 0.6}})
        adapter.register(w1)
        adapter.register(w2)
        stack = adapter.stack(["w613-1", "w613-2"], [0.6, 0.4])
        assert stack is not None

    def test_b3_lora_stacking_adapter_genre_stack(self):
        """LoRAStackingAdapter.genre_stack() — 장르 등록 후 실행"""
        from literary_system.serving.lora_stacking_adapter import LoRAStackingAdapter, LoRAWeight
        adapter = LoRAStackingAdapter()
        wd = LoRAWeight(weight_id="w-drama-613", genre="drama", version="1.0",
                        weight_data={"layer0": {"x": 0.7}})
        wc = LoRAWeight(weight_id="w-comedy-613", genre="comedy", version="1.0",
                        weight_data={"layer0": {"x": 0.5}})
        adapter.register(wd)
        adapter.register(wc)
        stack = adapter.genre_stack(["drama", "comedy"], project_id="v613-int")
        assert stack is not None

    def test_b3_gate_g58_pass(self):
        """Gate G58 PASS"""
        from literary_system.gates.release_gate import GATES
        fn = next((fn for n, d, fn in GATES if "g58" in n.lower()), None)
        assert fn is not None
        assert fn()["pass"] is True

    def test_b3_gate_g59_pass(self):
        """Gate G59 PASS"""
        from literary_system.gates.release_gate import GATES
        fn = next((fn for n, d, fn in GATES if "g59" in n.lower()), None)
        assert fn is not None
        assert fn()["pass"] is True


# ─────────────────────────────────────────────────────────────────────────────
# TC-4: Phase B 크로스-서브페이즈 통합
# ─────────────────────────────────────────────────────────────────────────────

class TestPhaseBCrossIntegration:
    """Phase B 전체 서브페이즈 연결 검증"""

    def test_cross_lora_registry_and_canary(self):
        """SP-B.1 LoRAModelRegistry + SP-B.2 CanaryController 병존"""
        from literary_system.finetune.lora_model_registry import LoRAModelRegistry
        from literary_system.serving.canary_controller import CanaryController
        assert LoRAModelRegistry() is not None
        assert CanaryController() is not None

    def test_cross_reward_model_and_genre_transfer(self):
        """SP-B.2 RewardModel + SP-B.3 GenreTransferV2 독립성"""
        from literary_system.rlhf.reward_model import RewardModel
        from literary_system.multiwork.genre_transfer import GenreTransferV2
        assert RewardModel() is not None
        assert GenreTransferV2() is not None

    def test_cross_lora_inference_and_stacking(self):
        """SP-B.1 LoRAInferenceGateway + SP-B.3 LoRAStackingAdapter 병존"""
        from literary_system.finetune.lora_inference_gateway import LoRAInferenceGateway
        from literary_system.serving.lora_stacking_adapter import LoRAStackingAdapter
        assert LoRAInferenceGateway() is not None
        assert LoRAStackingAdapter() is not None

    def test_cross_full_gate_count(self):
        """총 Gate 수 58개 이상"""
        from literary_system.gates.release_gate import GATES
        assert len(GATES) >= 58

    def test_cross_all_phase_b_gates_pass(self):
        """G53~G59 Phase B 7개 Gate 전부 PASS"""
        from literary_system.gates.release_gate import GATES
        for gid in ["g53", "g54", "g55", "g56", "g57", "g58", "g59"]:
            fn = next((fn for n, d, fn in GATES if gid in n.lower()), None)
            if fn is not None:
                r = fn()
                assert r["pass"] is True, f"Gate {gid} FAIL: {r.get('errors')}"
