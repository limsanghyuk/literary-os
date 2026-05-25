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


# ─────────────────────────────────────────────────────────────────────────────
# V623 TC-5: V621 AgentEnvelope 통합 (SP-B.2 retrofit)
# ─────────────────────────────────────────────────────────────────────────────

class TestV621AgentEnvelopeIntegration:
    """V621 SP-B.2 retrofit — AgentEnvelope + AgentRoutingPolicy 통합"""

    def test_agent_envelope_import(self):
        """AgentEnvelope 임포트 정상"""
        from literary_system.llm_bridge.agent_envelope import AgentEnvelope, AgentRole
        env = AgentEnvelope(agent_id="v623-test", role=AgentRole.SCENE_WRITER, prompt="드라마 1화")
        assert env is not None

    def test_agent_routing_policy_import(self):
        """AgentRoutingPolicy 임포트 + 4축 가중치 합 검증"""
        from literary_system.llm_bridge.agent_envelope import AgentRoutingPolicy
        policy = AgentRoutingPolicy()
        total = (policy.cost_weight + policy.latency_weight
                 + policy.quality_weight + policy.role_weight)
        assert abs(total - 1.0) < 1e-6, f"가중치 합={total} (기대 1.0)"

    def test_agent_routing_policy_custom_weights(self):
        """AgentRoutingPolicy 커스텀 가중치 합 1.0 유지"""
        from literary_system.llm_bridge.agent_envelope import AgentRoutingPolicy
        policy = AgentRoutingPolicy(
            cost_weight=0.4, latency_weight=0.2,
            quality_weight=0.3, role_weight=0.1
        )
        total = (policy.cost_weight + policy.latency_weight
                 + policy.quality_weight + policy.role_weight)
        assert abs(total - 1.0) < 1e-6

    def test_agent_routing_policy_invalid_raises(self):
        """AgentRoutingPolicy 가중치 합 != 1.0 → ValueError"""
        import pytest
        from literary_system.llm_bridge.agent_envelope import AgentRoutingPolicy
        with pytest.raises(ValueError):
            AgentRoutingPolicy(cost_weight=0.5, latency_weight=0.5,
                               quality_weight=0.5, role_weight=0.5)

    def test_agent_envelope_no_duplicate_class(self):
        """agent_envelope 모듈에 RoutingPolicy(구 이름) 클래스 없음"""
        import literary_system.llm_bridge.agent_envelope as ae
        assert not hasattr(ae, "RoutingPolicy") or ae.RoutingPolicy.__name__ == "AgentRoutingPolicy"

    def test_canonical_bridge_v2_import_agent_routing(self):
        """CanonicalBridgeV2 모듈이 AgentRoutingPolicy를 __all__에 노출"""
        import literary_system.llm_bridge.canonical_bridge_v2 as cb
        assert "AgentRoutingPolicy" in cb.__all__

    def test_bridge_generate_with_envelope_mock(self):
        """_bridge_generate_with_envelope mock 모드 정상 반환"""
        from unittest.mock import MagicMock
        from literary_system.llm_bridge.canonical_bridge_v2 import _bridge_generate_with_envelope
        from literary_system.llm_bridge.agent_envelope import AgentEnvelope, AgentRole
        bridge = MagicMock()
        bridge.generate.return_value = "mock output v623"
        env = AgentEnvelope(agent_id="v623-mock", role=AgentRole.CRITIC, prompt="검토")
        result = _bridge_generate_with_envelope(bridge, env, prompt="검토")
        assert result is not None

    def test_g37_duplicate_zero_pass(self):
        """Gate G37 DuplicateZero — 중복 클래스 0건 PASS"""
        from literary_system.gates.release_gate import GATES
        fn = next((fn for n, d, fn in GATES if "g37" in n.lower()), None)
        assert fn is not None
        r = fn()
        assert r["pass"] is True, f"G37 FAIL: {r}"

    def test_reader_feedback_ingest_import(self):
        """ReaderFeedbackIngest 임포트 + is_phase_c_active 메서드 존재"""
        from literary_system.multiwork.reader_feedback_ingest import ReaderFeedbackIngest
        ingest = ReaderFeedbackIngest()
        assert hasattr(ingest, "is_phase_c_active")
        assert hasattr(ingest, "ingest")

    def test_reader_feedback_phase_c_inactive(self):
        """ReaderFeedbackIngest.is_phase_c_active() == False (Phase B 기간)"""
        from literary_system.multiwork.reader_feedback_ingest import ReaderFeedbackIngest
        ingest = ReaderFeedbackIngest()
        assert ingest.is_phase_c_active() is False


# ─────────────────────────────────────────────────────────────────────────────
# V623 TC-6: V622 SP-B.3 retrofit 통합
# ─────────────────────────────────────────────────────────────────────────────

class TestV622SPB3RetrofitIntegration:
    """V622 SP-B.3 retrofit — ConflictPolicy / WorkloadProfile / AdvSeeds 통합"""

    def test_shared_character_db_v2_import(self):
        """SharedCharacterDBV2 임포트 정상"""
        from literary_system.multiwork.shared_character_db_v2 import SharedCharacterDBV2
        db = SharedCharacterDBV2()
        assert db is not None

    def test_shared_character_db_add_and_get(self):
        """SharedCharacterDBV2 add_character / get_character 흐름"""
        from literary_system.multiwork.shared_character_db_v2 import SharedCharacterDBV2
        db = SharedCharacterDBV2()
        db.add_character("char_v623", name="박지수", role="protagonist")
        char = db.get_character("char_v623")
        assert char is not None

    def test_shared_character_db_detect_conflicts(self):
        """SharedCharacterDBV2 detect_conflicts — 결과 Optional[ConflictRecord]"""
        from literary_system.multiwork.shared_character_db_v2 import SharedCharacterDBV2
        db = SharedCharacterDBV2()
        db.add_character("char_dup", name="홍길동", role="lead")
        db.link_to_project("char_dup", "proj_a")
        db.link_to_project("char_dup", "proj_b")
        conflict = db.detect_conflicts("char_dup", "proj_a", "proj_b")
        # None이거나 ConflictRecord 객체여야 함
        assert conflict is None or hasattr(conflict, "conflict_id")

    def test_multi_work_cim_v2_import(self):
        """MultiWorkCIMV2 임포트 + init_project"""
        from literary_system.multiwork.multi_work_cim_v2 import MultiWorkCIMV2
        cim = MultiWorkCIMV2()
        cim.init_project("v623-proj-a")
        assert True

    def test_multi_work_cim_v2_record_and_stats(self):
        """MultiWorkCIMV2 record_v2 + stats — 예외 없음"""
        from literary_system.multiwork.multi_work_cim_v2 import MultiWorkCIMV2
        cim = MultiWorkCIMV2()
        cim.init_project("v623-proj-b")
        cim.record_v2("v623-proj-b", "char_a", "char_b", reward=0.85)
        stats = cim.stats()
        assert stats is not None

    def test_reward_model_v2_import(self):
        """RewardModelV2 VERSION == '2.0.0'"""
        from literary_system.rlhf.reward_model import RewardModelV2
        m = RewardModelV2()
        assert m.VERSION == "2.0.0"

    def test_reward_model_v2_adv_seeds_count(self):
        """ADV_SEEDS_REQUIRED 5개 이상"""
        from literary_system.rlhf.reward_model import ADV_SEEDS_REQUIRED
        assert len(ADV_SEEDS_REQUIRED) >= 5

    def test_reward_model_v2_score_with_adv_seeds(self):
        """RewardModelV2.score_with_adv_seeds() — 기본 텍스트 점수 0~1"""
        from literary_system.rlhf.reward_model import RewardModelV2
        m = RewardModelV2()
        result = m.score_with_adv_seeds("서울의 봄날, 희준과 지수는 처음 만났다.")
        assert isinstance(result, dict)
        assert "baseline" in result or "base_score" in result or "score" in result

    def test_reward_model_v2_robustness(self):
        """RewardModelV2.robustness_score() — 반환값 0.0~1.0"""
        from literary_system.rlhf.reward_model import RewardModelV2
        m = RewardModelV2()
        score = m.robustness_score("희준은 창문 너머 빗소리를 들었다.")
        assert 0.0 <= score <= 1.0

    def test_reward_model_v2_adversarial_suite(self):
        """RewardModelV2.run_adversarial_suite() — 5시드 모두 실행"""
        from literary_system.rlhf.reward_model import RewardModelV2
        m = RewardModelV2()
        from literary_system.rlhf.reward_model import ADV_SEEDS_REQUIRED
        text = "지수는 희준의 손을 잡았다."
        seeds = [(seed.name, seed.inject_fn(text)) for seed in ADV_SEEDS_REQUIRED]
        results = m.run_adversarial_suite(seeds)
        assert isinstance(results, list)
        assert len(results) >= 5

    def test_genre_transfer_v2_import(self):
        """GenreTransferV2 임포트 정상"""
        from literary_system.multiwork.genre_transfer import GenreTransferV2
        gt = GenreTransferV2()
        assert gt is not None

    def test_workload_profile_via_cim_v2(self):
        """MultiWorkCIMV2 — 3프로젝트 동시 관리 (TRIPLE 시나리오)"""
        from literary_system.multiwork.multi_work_cim_v2 import MultiWorkCIMV2
        cim = MultiWorkCIMV2()
        for i in range(3):
            cim.init_project(f"v623-proj-triple-{i}")
        # 예외 없이 실행 완료
        assert True

    def test_g61_phase_b_exit_gate_pass(self):
        """Gate G61 Phase B Exit Gate PASS (run_release_gate 경유)"""
        from literary_system.gates.release_gate import run_release_gate
        rg = run_release_gate()
        g61 = rg.get("results", {}).get("phase_b_exit_g61", {})
        assert g61.get("pass") is True, f"G61 FAIL: {g61.get('summary')}"


# ─────────────────────────────────────────────────────────────────────────────
# V623 TC-7: Helm 사전 검증 (deploy/helm/train_plane)
# ─────────────────────────────────────────────────────────────────────────────

class TestHelmPreValidation:
    """V623 Helm 사전 검증 — 파일시스템 + Chart 구조"""

    def test_helm_train_plane_dir_exists(self):
        """deploy/helm/train_plane/ 디렉터리 존재"""
        import os
        base = os.path.join(os.path.dirname(__file__), '..', '..', 'deploy', 'helm', 'train_plane')
        assert os.path.isdir(base), "train_plane/ 디렉터리 없음"

    def test_helm_chart_yaml_exists(self):
        """deploy/helm/train_plane/Chart.yaml 파일 존재"""
        import os
        path = os.path.join(os.path.dirname(__file__), '..', '..', 'deploy', 'helm', 'train_plane', 'Chart.yaml')
        assert os.path.isfile(path), "Chart.yaml 없음"

    def test_helm_values_yaml_exists(self):
        """deploy/helm/train_plane/values.yaml 파일 존재"""
        import os
        path = os.path.join(os.path.dirname(__file__), '..', '..', 'deploy', 'helm', 'train_plane', 'values.yaml')
        assert os.path.isfile(path), "values.yaml 없음"

    def test_helm_templates_dir_exists(self):
        """deploy/helm/train_plane/templates/ 디렉터리 존재"""
        import os
        path = os.path.join(os.path.dirname(__file__), '..', '..', 'deploy', 'helm', 'train_plane', 'templates')
        assert os.path.isdir(path), "templates/ 없음"

    def test_helm_chart_yaml_required_fields(self):
        """Chart.yaml — apiVersion / name / version 필드 보유"""
        import os
        path = os.path.join(os.path.dirname(__file__), '..', '..', 'deploy', 'helm', 'train_plane', 'Chart.yaml')
        content = open(path).read()
        for field in ("apiVersion", "name", "version"):
            assert field in content, f"Chart.yaml에 {field} 없음"

    def test_helm_chart_yaml_app_version(self):
        """Chart.yaml — appVersion 필드 존재"""
        import os
        path = os.path.join(os.path.dirname(__file__), '..', '..', 'deploy', 'helm', 'train_plane', 'Chart.yaml')
        content = open(path).read()
        assert "appVersion" in content, "appVersion 없음"

    def test_helm_lint_skip_if_absent(self):
        """helm lint — helm 미설치 시 SKIP, 설치 시 실행"""
        import subprocess
        import pytest
        import os
        try:
            r = subprocess.run(["helm", "version"], capture_output=True, text=True)
            helm_available = (r.returncode == 0)
        except FileNotFoundError:
            helm_available = False
        if not helm_available:
            pytest.skip("helm 미설치 — lint 건너뜀")
        chart_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'deploy', 'helm', 'train_plane')
        lr = subprocess.run(["helm", "lint", chart_dir], capture_output=True, text=True)
        assert lr.returncode == 0, f"helm lint FAIL:\n{lr.stdout}\n{lr.stderr}"


# ─────────────────────────────────────────────────────────────────────────────
# V623 TC-8: 크로스-컴포넌트 통합 (V621+V622+Helm)
# ─────────────────────────────────────────────────────────────────────────────

class TestV623CrossComponentIntegration:
    """V623 V621+V622+Helm 크로스-컴포넌트 통합 검증"""

    def test_cross_agent_envelope_and_cim_v2(self):
        """AgentEnvelope + MultiWorkCIMV2 병존 임포트"""
        from literary_system.llm_bridge.agent_envelope import AgentEnvelope, AgentRoutingPolicy, AgentRole
        from literary_system.multiwork.multi_work_cim_v2 import MultiWorkCIMV2
        env = AgentEnvelope(agent_id="x-v623", role=AgentRole.SCENE_WRITER, prompt="크로스 테스트")
        cim = MultiWorkCIMV2()
        assert env is not None and cim is not None

    def test_cross_reward_model_and_agent_routing(self):
        """RewardModelV2 + AgentRoutingPolicy 독립 동작"""
        from literary_system.rlhf.reward_model import RewardModelV2
        from literary_system.llm_bridge.agent_envelope import AgentRoutingPolicy
        m = RewardModelV2()
        p = AgentRoutingPolicy(cost_weight=0.25, latency_weight=0.25,
                               quality_weight=0.25, role_weight=0.25)
        assert m.VERSION == "2.0.0"
        assert abs(p.cost_weight + p.latency_weight + p.quality_weight + p.role_weight - 1.0) < 1e-6

    def test_cross_reader_feedback_and_reward(self):
        """ReaderFeedbackIngest + RewardModelV2 병존"""
        from literary_system.multiwork.reader_feedback_ingest import ReaderFeedbackIngest
        from literary_system.rlhf.reward_model import RewardModelV2
        ingest = ReaderFeedbackIngest()
        reward = RewardModelV2()
        assert not ingest.is_phase_c_active()
        assert reward.VERSION == "2.0.0"

    def test_cross_helm_and_gate_registry(self):
        """Helm Chart.yaml + Gate 레지스트리 일관성 — apiVersion 필드"""
        import os
        from literary_system.gates.release_gate import GATES
        path = os.path.join(os.path.dirname(__file__), '..', '..', 'deploy', 'helm', 'train_plane', 'Chart.yaml')
        content = open(path).read()
        assert "apiVersion" in content
        assert len(GATES) >= 60

    def test_cross_g37_and_g61_both_pass(self):
        """G37 DuplicateZero + G61 PhaseBExit 동시 PASS"""
        from literary_system.gates.release_gate import GATES, run_release_gate
        # G37: 직접 호출 가능
        fn37 = next((fn for n, d, fn in GATES if "g37" in n.lower()), None)
        assert fn37 is not None
        assert fn37()["pass"] is True, "G37 FAIL"
        # G61: run_release_gate 경유 (직접 호출 시 override=0으로 실패)
        rg = run_release_gate()
        g61 = rg.get("results", {}).get("phase_b_exit_g61", {})
        assert g61.get("pass") is True, f"G61 FAIL: {g61.get('summary')}"

    def test_cross_all_60_gates_registered(self):
        """Gates 총 60개 이상 등록 확인"""
        from literary_system.gates.release_gate import GATES
        assert len(GATES) >= 60, f"총 {len(GATES)}개 (60 기대)"

    def test_cross_lora_pipeline_and_cim(self):
        """SP-B.1 LoRAJobRunner + SP-B.3 MultiWorkCIMV2 병존"""
        from literary_system.finetune.lora_job_runner import LoRAJobRunner
        from literary_system.multiwork.multi_work_cim_v2 import MultiWorkCIMV2
        runner = LoRAJobRunner()
        cim = MultiWorkCIMV2()
        assert runner is not None and cim is not None

    def test_cross_shared_char_db_and_bridge(self):
        """SharedCharacterDBV2 + CanonicalBridgeV2 독립 임포트"""
        from literary_system.multiwork.shared_character_db_v2 import SharedCharacterDBV2
        from literary_system.llm_bridge.canonical_bridge_v2 import CanonicalBridgeV2
        db = SharedCharacterDBV2()
        bridge = CanonicalBridgeV2()
        assert db is not None and bridge is not None

    def test_v623_version_bump(self):
        """pyproject.toml 버전 10.28.0 확인"""
        import os
        try:
            import tomllib
        except ModuleNotFoundError:
            import tomli as tomllib  # type: ignore
        path = os.path.join(os.path.dirname(__file__), '..', '..', 'pyproject.toml')
        with open(path, "rb") as f:
            data = tomllib.load(f)
        version = data["project"]["version"]
        assert version >= "10.28.0", f"버전 {version} (기대 ≥ 10.28.0)"
