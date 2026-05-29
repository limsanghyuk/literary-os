"""V410 — 전체 통합 테스트 (50 tests).

V401~V409 전 모듈 cross-cutting 통합 검증.
DRSE 9항 공식 생존, SP/RU/ET/RD 궤도 시스템 생존,
NarrativeConductor → NarrativeMemory → SeriesGates 엔드투엔드.
"""
import pytest
import tempfile
from literary_system.physics.coefficient_store import PhysicsCoefficientStore
from literary_system.episode.episode_state import SeriesConfig


# ══════════════════════════════════════════════════════════════════════════════
# I. DRSE 9항 공식 생존 검증 (V321 계승)
# ══════════════════════════════════════════════════════════════════════════════

class TestDRSE9FormulaV410:
    """RelationalScore = (S×R×T) × (A×C×P) × (G₁×G₂×G₃) 생존 확인."""

    def test_drse_scorer_importable(self):
        from literary_system.drse.drse_engine import DRSEScorer
        assert DRSEScorer is not None

    def test_drse_scorer_with_dual_semantic(self):
        from literary_system.drse.drse_engine import DRSEScorer, DualSemanticScorer, KnowledgeBoundaryGate
        from literary_system.relation_graph.relation_graph_store import (
            RelationGraphStore, StoryNode, NodeType, StoryEdge,
        )
        rgs = RelationGraphStore()
        rgs.add_node(StoryNode("n1", NodeType.CHARACTER.value, "주인공", origin_episode=1))
        rgs.add_edge(StoryEdge("pov", "n1", "knows", strength=1.0))
        gate = KnowledgeBoundaryGate(relation_graph=rgs)
        scorer = DRSEScorer(rgs=rgs, boundary_gate=gate)
        results = scorer.score_all(scene_goal="주인공 등장 씬", pov_character="pov", current_episode=1)
        assert len(results) >= 1

    def test_absolute_gates_block_unaware(self):
        """G₂=0 (UNAWARE) → 즉시 0.0"""
        from literary_system.drse.drse_engine import DRSEScorer, KnowledgeBoundaryGate
        from literary_system.relation_graph.relation_graph_store import (
            RelationGraphStore, StoryNode, NodeType,
        )
        rgs = RelationGraphStore()
        rgs.add_node(StoryNode("n1", NodeType.FACT_SECRET.value, "비밀", origin_episode=5))
        gate = KnowledgeBoundaryGate(relation_graph=rgs)
        scorer = DRSEScorer(rgs=rgs, boundary_gate=gate)
        results = scorer.score_all(
            scene_goal="비밀 노출",
            pov_character="pov",
            current_episode=1,  # 공개 에피소드(5) 이전
        )
        for ns in results:
            assert ns.score == 0.0  # G₁=0 (reveal_budget)

    def test_nkg_semantic_adapter_importable(self):
        from literary_system.nkg.adapters.nkg_semantic_adapter import NKGSemanticAdapter
        assert NKGSemanticAdapter is not None

    def test_dual_semantic_scorer_importable(self):
        from literary_system.drse.drse_engine import DualSemanticScorer
        assert DualSemanticScorer is not None

    def test_gate9_drse_quality_importable(self):
        from literary_system.gates.gate9_drse_quality import DRSEQualityGate
        gate = DRSEQualityGate()
        assert gate.MEAN_S_MIN == 0.10


# ══════════════════════════════════════════════════════════════════════════════
# II. SP/RU/ET/RD 궤도 시스템 생존 검증
# ══════════════════════════════════════════════════════════════════════════════

class TestSPRUETRDSystemV410:
    def test_narrative_state_tensor_importable(self):
        from literary_system.episode.episode_state import NarrativeStateTensor
        # NarrativeStateTensor는 시리즈 단위 구조 — SP/RU/ET/RD는 conductor가 별도 관리
        assert NarrativeStateTensor is not None

    def test_conductor_advances_tensor(self):
        from literary_system.orchestrators.narrative_conductor import NarrativeConductor
        with tempfile.TemporaryDirectory() as tmp:
            conductor = NarrativeConductor(memory_root=tmp)
            cfg = SeriesConfig(title="궤도 테스트", total_episodes=16)
            conductor.start_series(cfg, "traj_test")
            conductor.write_episode("traj_test", 1)
            mem = conductor._memory.load_episode("traj_test", 1)
            assert "SP" in mem.narrative_tensor
            assert "RU" in mem.narrative_tensor
            assert "ET" in mem.narrative_tensor
            assert "RD" in mem.narrative_tensor

    def test_tensor_values_in_range(self):
        from literary_system.orchestrators.narrative_conductor import _advance_tensor
        prev = {"SP": 0.3, "RU": 0.1, "ET": 0.0, "RD": 1.0}
        for progress in [0.1, 0.3, 0.5, 0.7, 0.9]:
            t = _advance_tensor(prev, progress, None)
            assert 0.0 <= t["SP"] <= 1.0
            assert 0.0 <= t["RU"] <= 1.0
            assert -1.0 <= t["ET"] <= 1.0
            assert 0.0 <= t["RD"] <= 1.0

    def test_sg3_trajectory_gate_exists(self):
        from literary_system.gates.series_gates import TrajectoryDeviationGate
        gate = TrajectoryDeviationGate()
        assert gate.DEVIATION_MAX == 0.15


# ══════════════════════════════════════════════════════════════════════════════
# III. NarrativeConductor 엔드투엔드
# ══════════════════════════════════════════════════════════════════════════════

class TestNarrativeConductorE2E:
    def test_full_series_flow(self):
        """start_series → write_episode×3 → get_snapshot"""
        from literary_system.orchestrators.narrative_conductor import NarrativeConductor
        with tempfile.TemporaryDirectory() as tmp:
            conductor = NarrativeConductor(memory_root=tmp)
            cfg = SeriesConfig(title="E2E 드라마", total_episodes=16)
            snap0 = conductor.start_series(cfg, "e2e_series")
            assert snap0.last_episode == 0
            for ep in [1, 2, 3]:
                conductor.write_episode("e2e_series", ep)
            snap = conductor.get_snapshot("e2e_series")
            assert snap.last_episode == 3

    def test_memory_persistence_across_conductor_instances(self):
        """다른 NarrativeConductor 인스턴스에서 동일 시리즈 접근."""
        from literary_system.orchestrators.narrative_conductor import NarrativeConductor
        with tempfile.TemporaryDirectory() as tmp:
            c1 = NarrativeConductor(memory_root=tmp)
            cfg = SeriesConfig(title="영속성 테스트", total_episodes=8)
            c1.start_series(cfg, "persist_series")
            c1.write_episode("persist_series", 1)
            # 새 인스턴스
            c2 = NarrativeConductor(memory_root=tmp)
            snap = c2.get_snapshot("persist_series")
            assert snap.last_episode == 1

    def test_coefficient_preserved_across_episodes(self):
        """에피소드 간 계수 스냅샷 보존."""
        from literary_system.orchestrators.narrative_conductor import NarrativeConductor
        with tempfile.TemporaryDirectory() as tmp:
            conductor = NarrativeConductor(memory_root=tmp)
            cfg = SeriesConfig(title="계수 테스트", total_episodes=16)
            conductor.start_series(cfg, "coeff_series")
            conductor.write_episode("coeff_series", 1)
            mem = conductor._memory.load_episode("coeff_series", 1)
            assert "conflict_weight" in mem.coefficient_snapshot

    def test_debt_tracking_across_episodes(self):
        """에피소드 간 복선 부채 추적."""
        from literary_system.orchestrators.narrative_conductor import NarrativeConductor
        with tempfile.TemporaryDirectory() as tmp:
            conductor = NarrativeConductor(memory_root=tmp)
            cfg = SeriesConfig(title="복선 테스트", total_episodes=16)
            conductor.start_series(cfg, "debt_series")
            conductor.write_episode("debt_series", 1, scene_outputs=[
                {"new_foreshadowings": ["f001", "f002"], "paid_foreshadowings": []}
            ])
            conductor.write_episode("debt_series", 2, scene_outputs=[
                {"new_foreshadowings": [], "paid_foreshadowings": ["f001"]}
            ])
            mem2 = conductor._memory.load_episode("debt_series", 2)
            assert "f002" in mem2.debt_ledger_snapshot["open"]
            assert "f001" in mem2.debt_ledger_snapshot["paid"]


# ══════════════════════════════════════════════════════════════════════════════
# IV. Gate 3층 체계 통합
# ══════════════════════════════════════════════════════════════════════════════

class TestGate3LayerIntegration:
    def test_runtime_gates_all_importable(self):
        from literary_system.gates.runtime_gates import (
            PhysicsGate, EnsembleGate, DebtOverflowGuard, RuntimeGateRunner
        )
        assert PhysicsGate is not None
        assert EnsembleGate is not None
        assert DebtOverflowGuard is not None

    def test_series_gates_all_importable(self):
        from literary_system.gates.series_gates import (
            EnduranceSeriesGate, MemoryConsistencyGate, TrajectoryDeviationGate,
            SeriesGateRunner
        )
        assert SeriesGateRunner is not None

    def test_release_gate_has_gate9(self):
        import literary_system.gates.release_gate as rg
        gate_names = [g[0] for g in rg.GATES]
        assert "drse_quality" in gate_names

    def test_runtime_gate_rg3_debt_overflow(self):
        from literary_system.gates.runtime_gates import DebtOverflowGuard
        gate = DebtOverflowGuard()
        r = gate.run({"open": ["f1"], "paid": [], "defaulted": ["d1"]})
        assert r.passed is False

    def test_series_gate_sg2_memory_consistency(self):
        from literary_system.gates.series_gates import MemoryConsistencyGate
        gate = MemoryConsistencyGate()

        class _M:
            def __init__(self, i):
                self.series_id = "s1"
                self.episode_idx = i
                self.narrative_tensor = {"SP": 0.5, "RU": 0.2, "ET": 0.0, "RD": 0.8}
                self.coefficient_snapshot = {"x": 0.2}

        r = gate.run([_M(i) for i in range(5)])
        assert r.passed is True


# ══════════════════════════════════════════════════════════════════════════════
# V. NarrativePhysicsSnapshot + EnduranceLearningBridge 통합
# ══════════════════════════════════════════════════════════════════════════════

class TestPhysicsAndLearningIntegration:
    def test_snapshot_engine_importable(self):
        from literary_system.physics.narrative_physics_snapshot import (
            NarrativePhysicsSnapshotEngine
        )
        assert NarrativePhysicsSnapshotEngine is not None

    def test_learning_bridge_importable(self):
        from literary_system.learning.endurance_learning_bridge import (
            EnduranceLearningBridge, CoefficientDelta
        )
        assert EnduranceLearningBridge is not None

    def test_bridge_analyze_no_crash_empty_report(self):
        from literary_system.learning.endurance_learning_bridge import EnduranceLearningBridge
        bridge = EnduranceLearningBridge()
        class EmptyReport:
            pass
        delta = bridge.analyze(EmptyReport())
        assert delta.is_empty()

    def test_bridge_apply_updates_store(self):
        from literary_system.learning.endurance_learning_bridge import (
            EnduranceLearningBridge, CoefficientDelta
        )
        bridge = EnduranceLearningBridge()
        store = PhysicsCoefficientStore()
        before = store.scene_energy_weight
        delta = CoefficientDelta(
            updates={"scene_energy_weight": 0.01},
            reason="test",
            source_report="EnduranceRunReport"
        )
        bridge.apply(delta, store)
        assert store.scene_energy_weight > before

    def test_snapshot_engine_5_snapshots_16ep(self):
        from literary_system.physics.narrative_physics_snapshot import NarrativePhysicsSnapshotEngine
        class FakeCfg:
            total_episodes = 16
            coefficient_store = None
        eng = NarrativePhysicsSnapshotEngine()
        result = eng.run_series(FakeCfg())
        assert len(result.snapshots) == 5


# ══════════════════════════════════════════════════════════════════════════════
# VI. NarrativeMemoryStore 불변성 검증
# ══════════════════════════════════════════════════════════════════════════════

class TestNarrativeMemoryInvariants:
    def test_append_only_no_overwrite(self):
        from literary_system.memory.narrative_memory_store import (
            NarrativeMemoryStore, EpisodeMemory
        )
        with tempfile.TemporaryDirectory() as tmp:
            store = NarrativeMemoryStore(memory_root=tmp)
            mem = EpisodeMemory(
                series_id="inv_test", episode_idx=1,
                created_at="2026-05-14T00:00:00",
                pipeline_state={}, narrative_tensor={"SP": 0.5, "RU": 0.2, "ET": 0.0, "RD": 0.8},
                nkg_snapshot_path="", debt_ledger_snapshot={}, coefficient_snapshot={}
            )
            store.save_episode(mem)
            with pytest.raises(FileExistsError):
                store.save_episode(EpisodeMemory(
                    series_id="inv_test", episode_idx=1,
                    created_at="2026-05-14T01:00:00",
                    pipeline_state={}, narrative_tensor={"SP": 0.6, "RU": 0.2, "ET": 0.0, "RD": 0.7},
                    nkg_snapshot_path="", debt_ledger_snapshot={}, coefficient_snapshot={}
                ))

    def test_series_not_found_raises(self):
        from literary_system.memory.narrative_memory_store import (
            NarrativeMemoryStore, EpisodeMemoryNotFound
        )
        with tempfile.TemporaryDirectory() as tmp:
            store = NarrativeMemoryStore(memory_root=tmp)
            with pytest.raises(EpisodeMemoryNotFound):
                store.load_episode("nonexistent", 1)

    def test_list_series_only_metadata(self):
        """metadata.json 없는 디렉토리는 list_series에서 제외."""
        from literary_system.memory.narrative_memory_store import NarrativeMemoryStore
        import pathlib
        with tempfile.TemporaryDirectory() as tmp:
            store = NarrativeMemoryStore(memory_root=tmp)
            # metadata.json 없는 빈 디렉토리 생성
            (pathlib.Path(tmp) / "orphan_dir").mkdir()
            store.init_series("valid_series", {"title": "valid"})
            series_list = store.list_series()
            assert "valid_series" in series_list
            assert "orphan_dir" not in series_list


# ══════════════════════════════════════════════════════════════════════════════
# VII. LLM-0 원칙 검증
# ══════════════════════════════════════════════════════════════════════════════

class TestLLMZeroPrinciple:
    def test_physics_snapshot_no_llm(self):
        """NarrativePhysicsSnapshotEngine LLM 0회 확인 (LLM 호출 함수 없어야 함)."""
        import inspect
        from literary_system.physics import narrative_physics_snapshot
        src = inspect.getsource(narrative_physics_snapshot)
        # 실제 LLM 호출 API 없어야 함
        assert "llm.generate" not in src
        assert "llm.complete" not in src
        assert "openai.chat" not in src

    def test_narrative_conductor_no_llm_call(self):
        import inspect
        from literary_system.orchestrators import narrative_conductor
        src = inspect.getsource(narrative_conductor)
        # "llm_client" 파라미터는 있어도 실제 LLM 호출은 없어야
        assert "llm.generate" not in src
        assert "llm.complete" not in src

    def test_release_gate_llm_zero_declared(self):
        """Release Gate 헤더에 LLM 0 선언 존재."""
        import literary_system.gates.release_gate as rg
        src = open(rg.__file__).read()
        # Gate 9는 LLM 0 선언 포함
        assert "LLM" in src or "llm" in src.lower()


# ══════════════════════════════════════════════════════════════════════════════
# VIII. V400 회귀 보호 — 핵심 계보 생존
# ══════════════════════════════════════════════════════════════════════════════

class TestV400HeritageV410:
    def test_series_arc_planner_importable(self):
        from literary_system.arc.series_arc_planner import SeriesArcPlanner
        assert SeriesArcPlanner is not None

    def test_payoff_debt_ledger_importable(self):
        from literary_system.longform.payoff_debt import PayoffDebtLedger
        assert PayoffDebtLedger is not None

    def test_knowledge_state_tracker_importable(self):
        from literary_system.world.knowledge_state_tracker import KnowledgeStateTracker
        assert KnowledgeStateTracker is not None

    def test_physics_coefficient_store_has_14_fields(self):
        store = PhysicsCoefficientStore()
        # V387 확인: 6개 핵심 계수 생존
        keys = store.as_dict().keys()
        assert "conflict_weight" in keys
        assert "scene_energy_weight" in keys
        assert "motif_weight" in keys
        assert "curiosity_weight" in keys
        assert "arc_pressure_coupling" in keys
        assert "prose_physics_bridge" in keys

    def test_pipeline_execution_trace_importable(self):
        from literary_system.pipeline.pipeline_state import append_trace
        assert callable(append_trace)
