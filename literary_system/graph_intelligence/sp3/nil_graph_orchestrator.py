"""V538~V539 — NILGraphOrchestrator
Wraps NILOrchestrator + NILGraphBridge into a single entry point.
Runs the NIL loop and automatically indexes results into the NarrativeGraph.
LLM-0 compliant for graph operations; NIL loop may call LLMs internally.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from literary_system.graph_intelligence.narrative_graph_indexer import (
    IndexResult, NarrativeGraphIndexer,
)
from literary_system.graph_intelligence.narrative_graph_store import NarrativeGraphStore
from literary_system.graph_intelligence.sp2.code_dependency_graph import CodeDependencyGraph
from literary_system.graph_intelligence.sp3.nil_graph_bridge import (
    NILGraphBridge, NILGraphBridgeConfig,
)
from literary_system.graph_intelligence.sp3.scene_blast_radius_report import (
    BlastRadiusReportBuilder, SceneBlastRadiusReport,
)
from literary_system.graph_intelligence.sp2.stage_patch_impact_calculator import PatchType


@dataclass
class NILGraphResult:
    """Combined result of one NIL loop pass + graph indexing."""
    scene_id: str
    nil_result: object            # NILResult from NILOrchestrator
    index_result: IndexResult     # graph mutations from NILGraphBridge
    blast_report: Optional[SceneBlastRadiusReport] = None


class NILGraphOrchestrator:
    """Unified orchestrator: NIL loop + NarrativeGraph auto-indexing.

    Usage::

        store   = NarrativeGraphStore()
        code_dep = CodeDependencyGraph()
        code_dep.register_batch([...])
        code_dep.build()

        orch = NILGraphOrchestrator(
            nil_orchestrator=NILOrchestrator(),
            store=store,
            code_dep=code_dep,
        )

        result = orch.process_scene(scene_input)
        # result.nil_result  → NIL output (loss, MAE, tension, ...)
        # result.index_result → graph nodes/edges added
        # result.blast_report → pre-computed blast radius for next scene

    Design
    ------
    After each scene is processed by NILOrchestrator, NILGraphBridge translates
    the NILResult into IndexInput and indexes it into NarrativeGraphStore.
    Optionally, a SceneBlastRadiusReport is generated for the *next* scene
    (look-ahead mode) so the caller can check Gate26/27 before the next edit.
    """

    def __init__(
        self,
        nil_orchestrator,
        store: NarrativeGraphStore,
        code_dep: Optional[CodeDependencyGraph] = None,
        bridge_config: Optional[NILGraphBridgeConfig] = None,
        look_ahead: bool = True,
        max_depth: int = 2,
    ) -> None:
        self._nil_orch  = nil_orchestrator
        self._store     = store
        self._code_dep  = code_dep or _EmptyCodeDep()
        self._indexer   = NarrativeGraphIndexer(store)
        self._bridge    = NILGraphBridge(self._indexer, bridge_config)
        self._look_ahead = look_ahead
        self._max_depth  = max_depth
        self._report_builder = BlastRadiusReportBuilder(store, self._code_dep, max_depth)
        self._history: List[NILGraphResult] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process_scene(self, scene_input) -> NILGraphResult:
        """Run NIL loop for one scene, then index into NarrativeGraph."""
        nil_result   = self._nil_orch.process_scene(scene_input)
        index_result = self._bridge.ingest(nil_result, scene_input)

        blast_report = None
        if self._look_ahead:
            try:
                blast_report = self._report_builder.build(
                    nil_result.scene_id, PatchType.EDIT
                )
            except Exception:
                pass  # Degrade gracefully if code_dep not built

        result = NILGraphResult(
            scene_id=nil_result.scene_id,
            nil_result=nil_result,
            index_result=index_result,
            blast_report=blast_report,
        )
        self._history.append(result)
        return result

    def process_episode(self, scene_inputs: List) -> List[NILGraphResult]:
        """Process an entire episode's scenes in sequence."""
        results = []
        for si in scene_inputs:
            results.append(self.process_scene(si))
        return results

    def complete_episode(self) -> None:
        """Delegate episode completion to NILOrchestrator."""
        self._nil_orch.complete_episode()

    def blast_radius(
        self,
        scene_id: str,
        patch_type: PatchType = PatchType.EDIT,
    ) -> SceneBlastRadiusReport:
        """Compute blast radius for any scene in the graph."""
        return self._report_builder.build(scene_id, patch_type)

    @property
    def store(self) -> NarrativeGraphStore:
        return self._store

    @property
    def history(self) -> List[NILGraphResult]:
        return list(self._history)

    @property
    def scene_count(self) -> int:
        return self._nil_orch.scene_count


# Minimal stub for when code_dep is not provided
class _EmptyCodeDep(CodeDependencyGraph):
    def __init__(self):
        super().__init__()
        self._built = True  # pretend built — returns empty results
