"""
tests/test_v546_cleanup.py
V546 Phase 6 Stage A Cleanup — P1~P8 해소 모듈 테스트.

대상:
  - GraphSyncOrchestrator (P1·P2, ADR-027)
  - GateHierarchyManager (P3, ADR-028)
  - LLM0StaticGate (P5, ADR-031)
  - SafetyAugmentedAutoRepair (P6, ADR-030)
  - ADRIndexGenerator (P7)
  - release_gate Gate25~28+LLM0 통합 (P3)
"""
import sys, os, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pathlib import Path


# ═══════════════════════════════════════════════════════════════════
# GraphSyncOrchestrator (P1·P2)
# ═══════════════════════════════════════════════════════════════════

class TestGraphSyncOrchestrator:

    def _make_mock_cim(self, ranks=None):
        """Mock CIM."""
        class _MockCIM:
            def get_pagerank(self):
                return ranks or {"char_A": 0.6, "char_B": 0.3, "char_C": 0.1}
            def set_weight(self, src, tgt, w):
                pass
        return _MockCIM()

    def _make_mock_graph(self, nodes=None, edges=None):
        """Mock NarrativeGraphStore."""
        class _MockNode:
            def __init__(self, nid, ntype="CHARACTER"):
                self.node_id = nid
                self.node_type = ntype
                self.metadata = {}
        class _MockEdge:
            def __init__(self, src, tgt, etype="INFLUENCE", w=0.7):
                self.source_id = src
                self.target_id = tgt
                self.edge_type = etype
                self.weight = w
        class _MockGraph:
            def __init__(self):
                self._nodes = {n.node_id: n for n in (nodes or [_MockNode("char_A")])}
                self._edges = edges or [_MockEdge("char_A", "char_B")]
            def get_node(self, nid):
                return self._nodes.get(nid)
            def all_nodes(self):
                return list(self._nodes.values())
            def all_edges(self):
                return self._edges
        return _MockGraph()

    def test_import(self):
        from literary_system.graph_intelligence.graph_sync_orchestrator import (
            GraphSyncOrchestrator, SyncReport, CIM_TO_GRAPH, GRAPH_TO_CIM, BIDIRECTIONAL
        )
        assert GraphSyncOrchestrator is not None

    def test_sync_cim_to_graph(self):
        from literary_system.graph_intelligence.graph_sync_orchestrator import GraphSyncOrchestrator
        cim = self._make_mock_cim({"char_A": 0.75, "char_B": 0.25})
        graph = self._make_mock_graph()
        gso = GraphSyncOrchestrator(cim, graph)
        report = gso.sync(direction="cim_to_graph")
        assert report.nodes_updated >= 1
        node = graph.get_node("char_A")
        assert node.metadata.get("cim_influence") == pytest.approx(0.75)

    def test_sync_graph_to_cim(self):
        from literary_system.graph_intelligence.graph_sync_orchestrator import GraphSyncOrchestrator
        cim = self._make_mock_cim()
        graph = self._make_mock_graph()
        gso = GraphSyncOrchestrator(cim, graph)
        report = gso.sync(direction="graph_to_cim")
        assert report.edges_reflected >= 1

    def test_sync_bidirectional(self):
        from literary_system.graph_intelligence.graph_sync_orchestrator import GraphSyncOrchestrator
        cim = self._make_mock_cim()
        graph = self._make_mock_graph()
        gso = GraphSyncOrchestrator(cim, graph)
        report = gso.sync()
        assert report.direction == "bidirectional"
        assert gso.sync_count == 1

    def test_get_cim_view(self):
        from literary_system.graph_intelligence.graph_sync_orchestrator import GraphSyncOrchestrator
        cim = self._make_mock_cim({"A": 0.9, "B": 0.1})
        gso = GraphSyncOrchestrator(cim, self._make_mock_graph())
        view = gso.get_cim_view()
        assert view["A"] == pytest.approx(0.9)

    def test_sync_report_to_dict(self):
        from literary_system.graph_intelligence.graph_sync_orchestrator import SyncReport
        r = SyncReport(direction="bidirectional", nodes_updated=3, edges_reflected=2)
        d = r.to_dict()
        assert d["nodes_updated"] == 3
        assert d["edges_reflected"] == 2

    def test_missing_node_warning(self):
        from literary_system.graph_intelligence.graph_sync_orchestrator import GraphSyncOrchestrator
        cim = self._make_mock_cim({"missing_char": 0.5})
        graph = self._make_mock_graph(nodes=[])
        gso = GraphSyncOrchestrator(cim, graph)
        report = gso.sync(direction="cim_to_graph")
        assert len(report.warnings) >= 1


# ═══════════════════════════════════════════════════════════════════
# GateHierarchyManager (P3)
# ═══════════════════════════════════════════════════════════════════

class TestGateHierarchyManager:

    def test_import(self):
        from literary_system.graph_intelligence.gate_hierarchy_manager import (
            GateHierarchyManager, HierarchyGateResult
        )
        assert GateHierarchyManager is not None

    def test_register_and_run(self):
        from literary_system.graph_intelligence.gate_hierarchy_manager import GateHierarchyManager
        mgr = GateHierarchyManager()

        class _MockResult:
            overall_passed = True

        mgr.register("gate25", lambda **kw: _MockResult())
        result = mgr.run_gate("gate25")
        assert result.passed is True
        assert result.level == "L2"

    def test_unregistered_gate_fails(self):
        from literary_system.graph_intelligence.gate_hierarchy_manager import GateHierarchyManager
        mgr = GateHierarchyManager()
        result = mgr.run_gate("gate99")
        assert result.passed is False

    def test_run_all(self):
        from literary_system.graph_intelligence.gate_hierarchy_manager import GateHierarchyManager
        mgr = GateHierarchyManager()
        mgr.register("gate25", lambda **kw: {"pass": True})
        mgr.register("gate28", lambda **kw: {"pass": True})
        results = mgr.run_all()
        assert len(results) == 2
        summary = mgr.summary(results)
        assert summary["passed"] == 2
        assert summary["failed"] == 0

    def test_make_release_gate_fn(self):
        from literary_system.graph_intelligence.gate_hierarchy_manager import GateHierarchyManager
        mgr = GateHierarchyManager()
        mgr.register("gate25", lambda **kw: {"pass": True})
        fn = mgr.make_release_gate_fn("gate25")
        result = fn()
        assert result["pass"] is True

    def test_level_map(self):
        from literary_system.graph_intelligence.gate_hierarchy_manager import GateHierarchyManager
        mgr = GateHierarchyManager()
        assert mgr.LEVEL_MAP["gate25"] == "L2"
        assert mgr.LEVEL_MAP["gate26"] == "L3"
        assert mgr.LEVEL_MAP["gate27"] == "L3"
        assert mgr.LEVEL_MAP["gate28"] == "L4"


# ═══════════════════════════════════════════════════════════════════
# LLM0StaticGate (P5, ADR-031)
# ═══════════════════════════════════════════════════════════════════

class TestLLM0StaticGate:

    def test_import(self):
        from literary_system.graph_intelligence.llm0_static_gate import (
            LLM0StaticGate, LLM0StaticResult, ViolationRecord
        )
        assert LLM0StaticGate is not None

    def test_clean_code_passes(self, tmp_path):
        from literary_system.graph_intelligence.llm0_static_gate import LLM0StaticGate
        clean = tmp_path / "clean_module.py"
        clean.write_text('def foo():\n    return 42\n')
        gate = LLM0StaticGate(tmp_path)
        result = gate.scan()
        assert result.passed is True
        assert result.scanned_files == 1
        assert len(result.violations) == 0

    def test_openai_import_detected(self, tmp_path):
        from literary_system.graph_intelligence.llm0_static_gate import LLM0StaticGate
        bad = tmp_path / "bad_module.py"
        bad.write_text('import openai\ndef gen(): return openai.ChatCompletion.create()\n')
        gate = LLM0StaticGate(tmp_path)
        result = gate.scan()
        assert result.passed is False
        assert len(result.violations) > 0
        assert any(v.violation_type == "IMPORT" for v in result.violations)

    def test_anthropic_from_import_detected(self, tmp_path):
        from literary_system.graph_intelligence.llm0_static_gate import LLM0StaticGate
        bad = tmp_path / "bad2.py"
        bad.write_text('from anthropic import Anthropic\n')
        gate = LLM0StaticGate(tmp_path)
        result = gate.scan()
        assert result.passed is False

    def test_result_to_dict(self, tmp_path):
        from literary_system.graph_intelligence.llm0_static_gate import LLM0StaticGate
        (tmp_path / "ok.py").write_text("x = 1\n")
        gate = LLM0StaticGate(tmp_path)
        d = gate.scan().to_dict()
        assert "pass" in d
        assert "scanned_files" in d
        assert "violation_count" in d

    def test_empty_dir_passes(self, tmp_path):
        from literary_system.graph_intelligence.llm0_static_gate import LLM0StaticGate
        gate = LLM0StaticGate(tmp_path)
        result = gate.scan()
        assert result.passed is True
        assert result.scanned_files == 0


# ═══════════════════════════════════════════════════════════════════
# SafetyAugmentedAutoRepair (P6, ADR-030)
# ═══════════════════════════════════════════════════════════════════

class TestSafetyAugmentedAutoRepair:

    def _make_mock_executor(self, exec_ok=True):
        class _MockResult:
            executed = exec_ok
        class _MockExecutor:
            _protocol = None
            def execute(self, rec):
                if not exec_ok:
                    raise RuntimeError("Mock exec fail")
                return _MockResult()
        return _MockExecutor()

    def _make_mock_graph(self):
        class _Node:
            node_id = "n1"
        class _MockGraph:
            def all_nodes(self): return [_Node()]
            def all_edges(self): return []
        return _MockGraph()

    def _make_rec(self, severity=0.3, blast=0.5):
        class _Rec:
            rec_id = "rec_test"
            issue_id = "issue_001"
            work_id = "work_001"
            blast_ratio = blast
        r = _Rec()
        r.severity = severity
        return r

    def test_import(self):
        from literary_system.graph_intelligence.asd.safety_augmented_auto_repair import (
            SafetyAugmentedAutoRepair, SafetyRepairResult, SafetyCheckResult
        )
        assert SafetyAugmentedAutoRepair is not None

    def test_all_steps_pass(self):
        from literary_system.graph_intelligence.asd.safety_augmented_auto_repair import SafetyAugmentedAutoRepair
        saar = SafetyAugmentedAutoRepair(
            self._make_mock_executor(), self._make_mock_graph()
        )
        result = saar.safe_execute(self._make_rec())
        assert result.executed is True
        assert result.abort_reason is None
        assert result.rollback_available is True

    def test_blast_radius_too_high_aborts(self):
        from literary_system.graph_intelligence.asd.safety_augmented_auto_repair import SafetyAugmentedAutoRepair
        saar = SafetyAugmentedAutoRepair(
            self._make_mock_executor(), self._make_mock_graph(),
            max_blast=0.60
        )
        result = saar.safe_execute(self._make_rec(blast=0.80))
        assert result.executed is False
        assert "Blast Radius" in result.abort_reason

    def test_invalid_severity_aborts(self):
        from literary_system.graph_intelligence.asd.safety_augmented_auto_repair import SafetyAugmentedAutoRepair
        saar = SafetyAugmentedAutoRepair(
            self._make_mock_executor(), self._make_mock_graph()
        )
        result = saar.safe_execute(self._make_rec(severity=1.5))
        assert result.executed is False
        assert "DryRun" in result.abort_reason

    def test_rollback_snapshot_recorded(self):
        from literary_system.graph_intelligence.asd.safety_augmented_auto_repair import SafetyAugmentedAutoRepair
        saar = SafetyAugmentedAutoRepair(
            self._make_mock_executor(), self._make_mock_graph()
        )
        result = saar.safe_execute(self._make_rec())
        assert result.rollback_snapshot is not None
        assert "node_ids" in result.rollback_snapshot

    def test_result_to_dict(self):
        from literary_system.graph_intelligence.asd.safety_augmented_auto_repair import SafetyAugmentedAutoRepair
        saar = SafetyAugmentedAutoRepair(
            self._make_mock_executor(), self._make_mock_graph()
        )
        result = saar.safe_execute(self._make_rec())
        d = result.to_dict()
        assert "executed" in d
        assert "safety_checks" in d


# ═══════════════════════════════════════════════════════════════════
# ADRIndexGenerator (P7)
# ═══════════════════════════════════════════════════════════════════

class TestADRIndexGenerator:

    def test_import(self):
        from literary_system.graph_intelligence.adr_index_generator import (
            ADRIndexGenerator, ADREntry
        )
        assert ADRIndexGenerator is not None

    def test_scan_real_adr_dir(self):
        import os
        from literary_system.graph_intelligence.adr_index_generator import ADRIndexGenerator
        adr_dir = os.path.join(
            os.path.dirname(__file__), "..", "docs", "adr"
        )
        gen = ADRIndexGenerator(adr_dir=adr_dir)
        entries = gen.scan()
        # ADR-027~031 포함 확인
        nums = {e.number for e in entries}
        for expected in [27, 28, 29, 30, 31]:
            assert expected in nums, f"ADR-{expected:03d} 미발견"

    def test_generate_index_contains_table(self, tmp_path):
        from literary_system.graph_intelligence.adr_index_generator import ADRIndexGenerator, ADREntry
        entries = [
            ADREntry(number=27, slug="CIM Sync", title="CIM-NarrativeGraph 동기화",
                     status="Accepted", filename="ADR-027.md"),
            ADREntry(number=28, slug="Gate Hierarchy", title="Gate 계층",
                     status="Accepted", filename="ADR-028.md"),
        ]
        gen = ADRIndexGenerator(adr_dir=tmp_path, output_dir=tmp_path)
        index_text = gen.generate_index(entries)
        assert "ADR-027" in index_text
        assert "ADR-028" in index_text
        assert "|" in index_text  # 테이블 형식

    def test_generate_mermaid(self, tmp_path):
        from literary_system.graph_intelligence.adr_index_generator import ADRIndexGenerator, ADREntry
        entries = [
            ADREntry(number=31, slug="LLM0", title="LLM-0 Static Gate",
                     status="Accepted", supersedes=["ADR-001"], filename="ADR-031.md"),
        ]
        gen = ADRIndexGenerator(adr_dir=tmp_path, output_dir=tmp_path)
        mermaid = gen.generate_mermaid(entries)
        assert "graph LR" in mermaid
        assert "ADR-031" in mermaid
        assert "supersedes" in mermaid

    def test_write_outputs(self, tmp_path):
        from literary_system.graph_intelligence.adr_index_generator import ADRIndexGenerator, ADREntry
        entries = [ADREntry(number=27, slug="test", title="Test ADR",
                            status="Accepted", filename="ADR-027.md")]
        gen = ADRIndexGenerator(adr_dir=tmp_path, output_dir=tmp_path)
        paths = gen.write(entries)
        assert paths["index"].exists()
        assert paths["mermaid"].exists()

    def test_empty_dir(self, tmp_path):
        from literary_system.graph_intelligence.adr_index_generator import ADRIndexGenerator
        gen = ADRIndexGenerator(adr_dir=tmp_path)
        entries = gen.scan()
        assert entries == []


# ═══════════════════════════════════════════════════════════════════
# release_gate Gate25~28 + LLM0 통합 (P3)
# ═══════════════════════════════════════════════════════════════════

class TestReleaseGateV546Integration:

    def test_gates_count_at_least_27(self):
        from literary_system.gates.release_gate import GATES
        assert len(GATES) >= 27

    def test_gate25_registered(self):
        from literary_system.gates.release_gate import GATES
        ids = [g[0] for g in GATES]
        assert "nie_convergence_gate25" in ids

    def test_gate26_registered(self):
        from literary_system.gates.release_gate import GATES
        ids = [g[0] for g in GATES]
        assert "narrative_blast_gate26" in ids

    def test_gate27_registered(self):
        from literary_system.gates.release_gate import GATES
        ids = [g[0] for g in GATES]
        assert "code_coupling_gate27" in ids

    def test_gate28_registered(self):
        from literary_system.gates.release_gate import GATES
        ids = [g[0] for g in GATES]
        assert "story_quality_gate28" in ids

    def test_llm0_static_registered(self):
        from literary_system.gates.release_gate import GATES
        ids = [g[0] for g in GATES]
        assert "llm0_static_analysis" in ids

    def test_gate25_fn_callable(self):
        from literary_system.gates.release_gate import GATES
        fn = next(fn for gid, _, fn in GATES if gid == "nie_convergence_gate25")
        result = fn()
        assert "pass" in result

    def test_gate28_fn_callable(self):
        from literary_system.gates.release_gate import GATES
        fn = next(fn for gid, _, fn in GATES if gid == "story_quality_gate28")
        result = fn()
        assert "pass" in result

    def test_llm0_fn_callable(self):
        from literary_system.gates.release_gate import GATES
        fn = next(fn for gid, _, fn in GATES if gid == "llm0_static_analysis")
        result = fn()
        assert "pass" in result
        assert result["pass"] is True  # graph_intelligence/에 LLM 호출 없음


# ═══════════════════════════════════════════════════════════════════
# P8: Retroactive Blueprint 등록 확인
# ═══════════════════════════════════════════════════════════════════

class TestP8RetroactiveBlueprint:

    def test_adr_027_to_031_exist(self):
        import os
        adr_dir = os.path.join(
            os.path.dirname(__file__), "..", "docs", "adr"
        )
        for num in [27, 28, 29, 30, 31]:
            matches = list(Path(adr_dir).glob(f"ADR-{num:03d}*.md"))
            assert len(matches) >= 1, f"ADR-{num:03d} 파일 없음"

    def test_changelog_v546_exists(self):
        import os
        repo = os.path.join(os.path.dirname(__file__), "..")
        # V347 이후 CHANGELOG는 docs/changelog/로 이전됨 (루트+서브 양쪽 검색)
        matches = (
            list(Path(repo).glob("CHANGELOG_V546*.md"))
            + list(Path(repo).glob("docs/changelog/CHANGELOG_V546*.md"))
        )
        assert len(matches) >= 1, "CHANGELOG_V546.md 없음 (루트 또는 docs/changelog/)"
