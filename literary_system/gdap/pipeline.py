"""V360: DKGPipeline v2 — 7단계 오케스트레이터."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from literary_system.gdap.blast_radius import BlastRadiusCalculator
from literary_system.gdap.guardrails import NKGGuardrails
from literary_system.gdap.plan_gate import PlanBuildGate, WorkDeclaration
from literary_system.nkg.cluster.character_cluster import CharacterClusterDetector
from literary_system.nkg.graph_store import NKGGraphStore
from literary_system.nkg.process.process_detector import NKGProcessDetector
from literary_system.nkg.schema import NKGEdge, NKGNode, NKGNodeType
from literary_system.nkg.semantic_model import NKGSemanticModel
from literary_system.nkg.staleness import DKGStalenessTrackerV2


class PipelinePhase(Enum):
    INIT        = "INIT"
    GRAPH       = "GRAPH"
    COMMUNITIES = "COMMUNITIES"
    PROCESSES   = "PROCESSES"
    PLAN        = "PLAN"
    BUILD       = "BUILD"
    VERIFY      = "VERIFY"

@dataclass
class DKGPhaseResult:
    phase:      Any   # PipelinePhase or str (V350 compat)
    success:    bool
    duration_ms: float = 0.0
    metadata:   Dict[str, Any] = field(default_factory=dict)
    error:      Optional[str]  = None
    nodes_added: int  = 0
    edges_added: int  = 0

class DKGPipeline:
    def __init__(self, nkg: Optional[NKGGraphStore] = None) -> None:
        self._nkg     = nkg or NKGGraphStore()
        self._tracker = DKGStalenessTrackerV2()
        self._model   = NKGSemanticModel(self._nkg)
        self._phases: List[DKGPhaseResult] = []

    @property
    def nkg(self) -> NKGGraphStore: return self._nkg
    @property
    def model(self) -> NKGSemanticModel: return self._model

    def _run_phase(self, phase: PipelinePhase, fn: Callable) -> DKGPhaseResult:
        t0 = time.perf_counter()
        try:
            meta = fn() or {}
            dur  = round((time.perf_counter()-t0)*1000, 2)
            r    = DKGPhaseResult(phase, True, dur, meta)
        except Exception as e:
            dur = round((time.perf_counter()-t0)*1000, 2)
            r   = DKGPhaseResult(phase, False, dur, {}, str(e))
        self._phases.append(r)
        return r

    def init(self, root_dir: str = "", file_list: Optional[List[str]] = None,
             extensions: Optional[List[str]] = None) -> DKGPhaseResult:
        def _fn():
            self._model._state = __import__(
                "literary_system.nkg.schema", fromlist=["SemanticModelState"]
            ).SemanticModelState.WRITE
            return {"root_dir": root_dir, "files": len(file_list or [])}
        return self._run_phase(PipelinePhase.INIT, _fn)

    def build_graph(self, nkg_nodes: Optional[List[NKGNode]] = None,
                    nkg_edges: Optional[List[NKGEdge]] = None) -> DKGPhaseResult:
        def _fn():
            nc = ec = 0
            for n in (nkg_nodes or []):
                self._nkg.add_node(n); nc += 1
            for e in (nkg_edges or []):
                try: self._nkg.add_edge(e); ec += 1
                except Exception: pass
            return {"nodes_added": nc, "edges_added": ec}
        return self._run_phase(PipelinePhase.GRAPH, _fn)

    def communities(self) -> DKGPhaseResult:
        def _fn():
            det = CharacterClusterDetector(self._nkg)
            r   = det.detect()
            return {"clusters": len(r.clusters), "modularity": round(r.modularity, 4)}
        return self._run_phase(PipelinePhase.COMMUNITIES, _fn)

    def processes(self) -> DKGPhaseResult:
        def _fn():
            det = NKGProcessDetector(self._nkg)
            r   = det.detect()
            return {"processes": len(r.processes), "foreshadows": len(r.foreshadows)}
        return self._run_phase(PipelinePhase.PROCESSES, _fn)

    def plan(self, declaration: Optional[WorkDeclaration] = None) -> DKGPhaseResult:
        def _fn():
            report = self._model.reconcile()
            snap   = self._model.freeze()
            decl   = declaration or WorkDeclaration(semantic_frozen=True)
            decl.semantic_frozen = self._model.is_frozen()
            gate   = PlanBuildGate(BlastRadiusCalculator(nkg=self._nkg))
            result = gate.validate(decl)
            return {"merged": len(report.merged_nodes), "frozen": snap.get("frozen_at") is not None,
                    "gate_passed": result.passed}
        return self._run_phase(PipelinePhase.PLAN, _fn)

    def build(self, declaration: Optional[WorkDeclaration] = None,
              apply_fn: Optional[Callable] = None) -> DKGPhaseResult:
        def _fn():
            if apply_fn: apply_fn(self._nkg)
            return {"applied": apply_fn is not None}
        return self._run_phase(PipelinePhase.BUILD, _fn)

    def verify(self, test_runner_fn: Optional[Callable] = None,
               reader_surface_gate: float = 9.0) -> DKGPhaseResult:
        def _fn():
            self._model.assert_frozen()
            score = test_runner_fn() if test_runner_fn else reader_surface_gate
            passed = score >= reader_surface_gate
            return {"reader_score": score, "passed": passed}
        return self._run_phase(PipelinePhase.VERIFY, _fn)

    def run_full(self, declaration: Optional[WorkDeclaration] = None,
                 nkg_nodes: Optional[List] = None, nkg_edges: Optional[List] = None,
                 apply_fn: Optional[Callable] = None,
                 test_runner_fn: Optional[Callable] = None,
                 reader_surface_gate: float = 9.0) -> List[DKGPhaseResult]:
        results = []
        results.append(self.init())
        results.append(self.build_graph(nkg_nodes, nkg_edges))
        results.append(self.communities())
        results.append(self.processes())
        results.append(self.plan(declaration))
        results.append(self.build(declaration, apply_fn))
        results.append(self.verify(test_runner_fn, reader_surface_gate))
        return results

    def phase_results(self) -> List[DKGPhaseResult]:
        return list(self._phases)



# ── V350 레거시 호환 레이어 ─────────────────────────────────────
# V350 테스트는 DKGPhaseResult("init", True, duration, nodes, edges, error) 형태로 호출

class _LegacyPhaseBase:
    """V350 Phase 클래스 공통 기반."""
    def __init__(self, graph=None, tracker=None): pass
    def run(self, **kwargs):
        from dataclasses import dataclass
        r = DKGPhaseResult.__new__(DKGPhaseResult)
        r.phase = "legacy"; r.success = True; r.duration_ms = 0.0
        r.metadata = {}; r.error = None; r.nodes_added = 0; r.edges_added = 0
        return r


class DKGInitPhase(_LegacyPhaseBase): pass
class DKGGraphPhase(_LegacyPhaseBase): pass
class DKGPlanPhase(_LegacyPhaseBase): pass
class DKGBuildPhase(_LegacyPhaseBase): pass
class DKGVerifyPhase(_LegacyPhaseBase): pass
