"""V531~V534 SP2 테스트 (32종)
Covers: CodeDependencyGraph (V531), StagePatchImpactCalculator (V532),
        PlanBuildProtocol (V533), Gate27 (V534)
"""
import pytest
from literary_system.graph_intelligence.sp2 import (
    CodeDependencyGraph, SceneProfile, SceneDependencyKey, CouplingReport,
    StagePatchImpactCalculator, StagePatchRequest, StagePatchImpact, PatchType,
    Gate27, Gate27Result,
    PlanBuildProtocol, ProtocolResult, ProtocolPhase,
)
from literary_system.graph_intelligence import NarrativeGraphStore
from literary_system.graph_intelligence.scene_change_pre_gate import SceneChangePreGate


# ══════════════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════════════

@pytest.fixture
def simple_cdg():
    """3 scenes: sc01↔sc02 (shared char c1+loc palace), sc03 isolated."""
    cdg = CodeDependencyGraph()
    for sid, chars, loc, threads in [
        ("sc01", frozenset(["c1","c2"]), "palace", frozenset(["t1"])),
        ("sc02", frozenset(["c1","c3"]), "palace", frozenset(["t1"])),
        ("sc03", frozenset(["c4"]),      "dungeon", frozenset()),
    ]:
        cdg.register(SceneProfile(
            key=SceneDependencyKey(episode=1, scene_id=sid),
            character_ids=chars,
            location_id=loc,
            plot_thread_ids=threads,
        ))
    cdg.build()
    return cdg


@pytest.fixture
def empty_store():
    return NarrativeGraphStore()


@pytest.fixture
def calculator(simple_cdg, empty_store):
    return StagePatchImpactCalculator(empty_store, simple_cdg)


@pytest.fixture
def gate26(empty_store):
    return SceneChangePreGate(empty_store)


@pytest.fixture
def gate27(simple_cdg, calculator):
    return Gate27(simple_cdg, calculator)


@pytest.fixture
def protocol(gate26, gate27, calculator):
    return PlanBuildProtocol(gate26, gate27, calculator)


# ══════════════════════════════════════════════════════════════════════
# V531 — CodeDependencyGraph (12종)
# ══════════════════════════════════════════════════════════════════════

class TestCodeDependencyGraph:

    def test_build_returns_edge_count(self, simple_cdg):
        # 2 directional edges between sc01↔sc02
        assert simple_cdg.stats()["edge_count"] >= 2

    def test_shared_character_creates_coupling(self, simple_cdg):
        assert "sc02" in simple_cdg.direct_deps("sc01")

    def test_isolated_scene_has_no_deps(self, simple_cdg):
        assert simple_cdg.direct_deps("sc03") == []

    def test_coupling_is_bidirectional(self, simple_cdg):
        assert "sc01" in simple_cdg.direct_deps("sc02")

    def test_coupling_score_nonzero(self, simple_cdg):
        score = simple_cdg.coupling_score("sc01", "sc02")
        assert score > 0.0

    def test_coupling_score_zero_for_uncoupled(self, simple_cdg):
        assert simple_cdg.coupling_score("sc01", "sc03") == 0.0

    def test_bfs_impact_depth1(self, simple_cdg):
        impact = simple_cdg.bfs_impact("sc01", max_depth=1)
        assert "sc02" in impact
        assert "sc03" not in impact

    def test_reverse_deps(self, simple_cdg):
        assert "sc01" in simple_cdg.reverse_deps("sc02")

    def test_requires_build_before_query(self):
        cdg = CodeDependencyGraph()
        cdg.register(SceneProfile(
            key=SceneDependencyKey(1, "s1"),
            character_ids=frozenset(["c1"]),
        ))
        with pytest.raises(RuntimeError):
            cdg.direct_deps("s1")

    def test_explicit_dep_max_score(self):
        cdg = CodeDependencyGraph()
        for sid in ["sA", "sB"]:
            cdg.register(SceneProfile(
                key=SceneDependencyKey(1, sid),
                explicit_deps=frozenset(["sB"]) if sid == "sA" else frozenset(),
            ))
        cdg.build()
        assert cdg.coupling_score("sA", "sB") == 1.0

    def test_shared_plot_thread_increases_score(self):
        cdg = CodeDependencyGraph()
        for sid, threads in [("sX", frozenset(["th1","th2"])), ("sY", frozenset(["th1","th2"]))]:
            cdg.register(SceneProfile(
                key=SceneDependencyKey(1, sid),
                plot_thread_ids=threads,
            ))
        cdg.build()
        assert cdg.coupling_score("sX", "sY") > 0.0

    def test_stats_keys(self, simple_cdg):
        s = simple_cdg.stats()
        assert "scene_count" in s and "edge_count" in s


# ══════════════════════════════════════════════════════════════════════
# V532 — StagePatchImpactCalculator (8종)
# ══════════════════════════════════════════════════════════════════════

class TestStagePatchImpactCalculator:

    def test_edit_impact_has_coupling_risk(self, calculator):
        impact = calculator.calculate(StagePatchRequest("sc01", PatchType.EDIT))
        assert impact.coupling_risk > 0.0

    def test_isolated_scene_low_coupling(self, calculator):
        impact = calculator.calculate(StagePatchRequest("sc03", PatchType.EDIT))
        assert impact.coupling_risk == 0.0

    def test_delete_higher_than_edit(self, calculator):
        edit   = calculator.calculate(StagePatchRequest("sc01", PatchType.EDIT))
        delete = calculator.calculate(StagePatchRequest("sc01", PatchType.DELETE))
        assert delete.coupling_risk > edit.coupling_risk

    def test_insert_lowest_impact(self, calculator):
        insert = calculator.calculate(StagePatchRequest("sc01", PatchType.INSERT))
        assert insert.coupling_risk <= 0.20

    def test_coupled_scenes_populated(self, calculator):
        impact = calculator.calculate(StagePatchRequest("sc01", PatchType.EDIT))
        assert "sc02" in impact.coupled_scenes

    def test_risk_level_and_recommendation_set(self, calculator):
        impact = calculator.calculate(StagePatchRequest("sc01", PatchType.EDIT))
        assert impact.risk_level in {"low","medium","high","critical"}
        assert impact.recommendation in {"proceed","review","split_required","hold"}

    def test_summary_string(self, calculator):
        impact = calculator.calculate(StagePatchRequest("sc01", PatchType.EDIT))
        s = impact.summary()
        assert "sc01" in s and "edit" in s

    def test_batch_returns_all(self, calculator):
        reqs = [
            StagePatchRequest("sc01", PatchType.EDIT),
            StagePatchRequest("sc02", PatchType.EDIT),
        ]
        results = calculator.calculate_batch(reqs)
        assert "sc01" in results and "sc02" in results


# ══════════════════════════════════════════════════════════════════════
# V534 — Gate27 (6종)
# ══════════════════════════════════════════════════════════════════════

class TestGate27:

    def test_isolated_scene_approved(self, simple_cdg, calculator):
        gate = Gate27(simple_cdg, calculator)
        assert gate.is_approved("sc03")

    def test_three_checks_present(self, gate27):
        result = gate27.evaluate("sc01")
        assert len(result.checks) == 3
        ids = [c.gate_id for c in result.checks]
        assert "G27-1" in ids and "G27-3" in ids

    def test_zero_threshold_blocks(self, simple_cdg, calculator):
        gate = Gate27(simple_cdg, calculator, direct_max=0)
        result = gate.evaluate("sc01")
        assert result.approved is False

    def test_summary_string(self, gate27):
        result = gate27.evaluate("sc01")
        s = result.summary()
        assert "Gate27" in s

    def test_evaluate_batch(self, gate27):
        results = gate27.evaluate_batch(["sc01", "sc03"])
        assert "sc01" in results and "sc03" in results

    def test_delete_harder_than_edit(self, simple_cdg, calculator):
        gate = Gate27(simple_cdg, calculator, coupling_risk_max=0.10)
        edit_ok   = gate.evaluate("sc01", PatchType.EDIT).approved
        delete_ok = gate.evaluate("sc01", PatchType.DELETE).approved
        # delete has higher multiplier — should be same or harder
        assert not delete_ok or edit_ok  # delete can't be easier than edit


# ══════════════════════════════════════════════════════════════════════
# V533 — PlanBuildProtocol (6종)
# ══════════════════════════════════════════════════════════════════════

class TestPlanBuildProtocol:

    def test_isolated_scene_approved(self, gate26, gate27, calculator):
        proto = PlanBuildProtocol(gate26, gate27, calculator)
        result = proto.run(StagePatchRequest("sc03", PatchType.EDIT))
        assert result.approved is True
        assert result.phase_reached == ProtocolPhase.DONE

    def test_abort_on_extreme_risk(self, gate26, gate27, calculator):
        proto = PlanBuildProtocol(gate26, gate27, calculator, abort_threshold=0.0)
        result = proto.run(StagePatchRequest("sc01", PatchType.EDIT))
        # combined_risk > 0.0 → ABORT in PLAN phase
        assert result.phase_reached == ProtocolPhase.ABORT

    def test_build_fn_called(self, protocol):
        called = []
        def build_fn(sid, pt):
            called.append(sid)
            return True
        protocol.run(StagePatchRequest("sc03", PatchType.EDIT), build_fn=build_fn)
        assert "sc03" in called

    def test_build_fn_false_aborts(self, protocol):
        result = protocol.run(
            StagePatchRequest("sc03", PatchType.EDIT),
            build_fn=lambda sid, pt: False,
        )
        assert result.approved is False
        assert result.phase_reached == ProtocolPhase.ABORT

    def test_gate26_result_attached(self, protocol):
        result = protocol.run(StagePatchRequest("sc03", PatchType.EDIT))
        assert result.gate26_result is not None

    def test_summary_string(self, protocol):
        result = protocol.run(StagePatchRequest("sc03", PatchType.EDIT))
        s = result.summary()
        assert "PlanBuildProtocol" in s
