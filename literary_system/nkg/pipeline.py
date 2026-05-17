"""V340: NKGPipeline — 5단계 완전 구현 파이프라인.

V329 대비 변경:
  - Phase 3 (edge_infer): NKGEdgeInferEngine 실제 구현으로 교체
  - Phase 4 (emotional):  NKGEmotionalLinker 실제 구현으로 교체
  - char_names / emt 파라미터 추가
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from literary_system.nkg.adapters.scene_node_adapter import SceneNodeAdapter
from literary_system.nkg.graph_store import NKGGraphStore
from literary_system.nkg.schema import NKGEdgeType, EpisodeNode as EpisodeNode, SceneNode
from literary_system.nkg.staleness import NKGStalenessTracker

# V340 신규 — lazy import로 하위 호환 유지
try:
    from literary_system.nkg.edge_infer import NKGEdgeInferEngine
    _EDGE_INFER_AVAILABLE = True
except ImportError:
    NKGEdgeInferEngine = None  # type: ignore
    _EDGE_INFER_AVAILABLE = False

try:
    from literary_system.nkg.emotional_linker import NKGEmotionalLinker
    _EMOTIONAL_LINKER_AVAILABLE = True
except ImportError:
    NKGEmotionalLinker = None  # type: ignore
    _EMOTIONAL_LINKER_AVAILABLE = False


@dataclass
class NKGPhase:
    name:        str
    deps:        List[str]
    execute:     Callable[..., Any]
    description: str = ""


@dataclass
class NKGPhaseResult:
    phase_name:  str
    success:     bool
    duration_ms: float = 0.0
    nodes_added: int   = 0
    edges_added: int   = 0
    error:       Optional[str] = None
    data:        Dict[str, Any] = field(default_factory=dict)


class NKGPipeline:
    """5단계 NKG 구축 파이프라인 (V340 완전 구현)."""

    def __init__(self, llm_bridge: Any = None) -> None:
        self.graph:     NKGGraphStore        = NKGGraphStore()
        self.staleness: NKGStalenessTracker  = NKGStalenessTracker()
        self._edge_engine = (NKGEdgeInferEngine(llm_bridge)
                             if _EDGE_INFER_AVAILABLE else None)
        self._emo_linker  = (NKGEmotionalLinker()
                             if _EMOTIONAL_LINKER_AVAILABLE else None)
        self._phases:       List[NKGPhase]  = self._build_phases()
        self._phase_results: List[NKGPhaseResult] = []

    def _build_phases(self) -> List[NKGPhase]:
        return [
            NKGPhase("scan",         [],                          self._phase_scan,
                     "SceneDraftOutput 수집 및 유효성 검사"),
            NKGPhase("node_extract", ["scan"],                    self._phase_node_extract,
                     "SceneDraftOutput → SceneNode 변환"),
            NKGPhase("edge_infer",   ["node_extract"],            self._phase_edge_infer,
                     "패턴 기반 CausalEdge/ForeshadowEdge 추출"),
            NKGPhase("emotional",    ["node_extract"],            self._phase_emotional,
                     "EmotionalVector 기반 EmotionalEchoEdge 생성"),
            NKGPhase("commit",       ["edge_infer", "emotional"], self._phase_commit,
                     "변경사항 최종 반영 + Dirty Flag 클리어"),
        ]

    # ── 전체 실행 ────────────────────────────────────────────
    def run_full(self, episode_id: str,
                 draft_outputs: List[Any],
                 char_names: Optional[List[str]] = None,
                 emt: Any = None) -> List[NKGPhaseResult]:
        ctx: Dict[str, Any] = {
            "episode_id":    episode_id,
            "draft_outputs": draft_outputs,
            "char_names":    char_names or [],
            "emt":           emt,
            "nodes_pending": [],
        }
        self._phase_results.clear()
        ordered   = self._topo_sort()
        completed: Dict[str, NKGPhaseResult] = {}

        for phase in ordered:
            blocked = any(
                dep not in completed or not completed[dep].success
                for dep in phase.deps
            )
            if blocked:
                res = NKGPhaseResult(phase.name, False,
                                     error="dependency not met")
                self._phase_results.append(res)
                completed[phase.name] = res
                continue

            t0 = time.perf_counter()
            try:
                phase.execute(ctx, completed)
                dur = (time.perf_counter() - t0) * 1000
                res = NKGPhaseResult(
                    phase_name   = phase.name,
                    success      = True,
                    duration_ms  = round(dur, 2),
                    nodes_added  = ctx.get(f"_{phase.name}_nodes", 0),
                    edges_added  = ctx.get(f"_{phase.name}_edges", 0),
                    data         = {k: v for k, v in ctx.items()
                                    if k.startswith(f"_{phase.name}_")},
                )
            except Exception as e:
                dur = (time.perf_counter() - t0) * 1000
                res = NKGPhaseResult(phase.name, False,
                                     duration_ms=round(dur, 2), error=str(e))
            completed[phase.name] = res
            self._phase_results.append(res)

        return list(self._phase_results)

    # ── 점진적 갱신 ──────────────────────────────────────────
    def update_incremental(self, scene_id: str,
                           draft_output: Any,
                           episode_id: Optional[str] = None) -> NKGPhaseResult:
        t0 = time.perf_counter()
        node = SceneNodeAdapter.from_draft_output(
            draft_output,
            episode_id=episode_id or str(
                getattr(draft_output, "episode_id",
                        getattr(draft_output, "episode_no", "ep_unknown"))),
        )
        node_id  = node.node_id()
        was_dirty = self.staleness.mark_dirty_if_stale(node_id, node.content)
        if not was_dirty:
            return NKGPhaseResult("incremental_update", True,
                                  data={"skipped": True})
        self.graph.add_node(node)
        self.staleness.register(node_id, node.content_hash)
        self.staleness.clear_dirty(node_id, node.content_hash)
        neighbors_flagged = len(self.graph.neighbors(node_id))
        for nb in self.graph.neighbors(node_id):
            self.staleness.mark_dirty(nb)
        dur = (time.perf_counter() - t0) * 1000
        return NKGPhaseResult(
            "incremental_update", True,
            duration_ms=round(dur, 2), nodes_added=1,
            data={"node_id": node_id, "neighbors_flagged": neighbors_flagged},
        )

    # ── Phase 구현 ───────────────────────────────────────────
    def _phase_scan(self, ctx: Dict, _: Dict) -> None:
        outputs = ctx.get("draft_outputs", [])
        valid   = [o for o in outputs if o is not None]
        ctx["_scan_outputs"] = valid
        ctx["_scan_nodes"]   = len(valid)

    def _phase_node_extract(self, ctx: Dict, _: Dict) -> None:
        ep_id   = ctx.get("episode_id", "ep_unknown")
        outputs = ctx.get("_scan_outputs", [])
        ep_node = EpisodeNode(episode_id=ep_id,
                                 total_scenes=len(outputs),
                                 status="in_progress")
        self.graph.add_node(ep_node)
        nodes: List[SceneNode] = []
        for draft in outputs:
            try:
                node = SceneNodeAdapter.from_draft_output(draft, episode_id=ep_id)
                self.graph.add_node(node)
                self.staleness.register(node.node_id(), node.content_hash)
                nodes.append(node)
            except Exception:
                pass
        ctx["_node_extract_nodes"]    = len(nodes)
        ctx["_extracted_scene_nodes"] = nodes

    def _phase_edge_infer(self, ctx: Dict, _: Dict) -> None:
        """Phase 3 (V340 실제 구현): NKGEdgeInferEngine 사용."""
        nodes      = ctx.get("_extracted_scene_nodes", [])
        char_names = ctx.get("char_names", [])
        edges_added = 0
        fsh_nodes   = 0

        if self._edge_engine is not None and nodes:
            try:
                result = self._edge_engine.infer(nodes, char_names=char_names)
                for edge in getattr(result, "edges", []):
                    self.graph.add_edge(edge)
                    edges_added += 1
                for fsh in result.foreshadow_nodes:
                    self.graph.add_foreshadow_node(fsh)
                    fsh_nodes += 1
                ctx["_edge_infer_causal_count"]    = len(result.causal_pairs)
                ctx["_edge_infer_foreshadow_count"] = len(result.foreshadow_pairs)
            except Exception as e:
                ctx["_edge_infer_error"] = str(e)
                # fallback: 순서 기반 기본 연결
                sorted_n = sorted(nodes, key=lambda n: n.scene_index)
                for i in range(len(sorted_n) - 1):
                    try:
                        self.graph.add_edge_raw(
                            sorted_n[i].node_id(), sorted_n[i+1].node_id(),
                            NKGEdgeType.CAUSAL_LINK, weight=0.6, confidence=0.5)
                        edges_added += 1
                    except Exception:
                        pass
        else:
            # NKGEdgeInferEngine 미설치 — 순서 기반 fallback
            sorted_n = sorted(nodes, key=lambda n: n.scene_index)
            for i in range(len(sorted_n) - 1):
                try:
                    self.graph.add_edge_raw(
                        sorted_n[i].node_id(), sorted_n[i+1].node_id(),
                        NKGEdgeType.CAUSAL_LINK, weight=0.6, confidence=0.5)
                    edges_added += 1
                except Exception:
                    pass

        ctx["_edge_infer_edges"]      = edges_added
        ctx["_edge_infer_fsh_nodes"]  = fsh_nodes

    def _phase_emotional(self, ctx: Dict, _: Dict) -> None:
        """Phase 4 (V340 실제 구현): NKGEmotionalLinker 사용."""
        nodes = ctx.get("_extracted_scene_nodes", [])
        emt   = ctx.get("emt")
        edges_added = 0

        if self._emo_linker is not None and len(nodes) >= 2:
            try:
                if emt is not None:
                    result = self._emo_linker.link_with_tracker(nodes, emt)
                else:
                    result = self._emo_linker.link(nodes)
                for edge in result.all_edges():
                    self.graph.add_edge(edge)
                    edges_added += 1
                ctx["_emotional_max_sim"]  = result.max_similarity
                ctx["_emotional_mean_sim"] = result.mean_similarity
            except Exception as e:
                ctx["_emotional_error"] = str(e)

        ctx["_emotional_edges"] = edges_added

    def _phase_commit(self, ctx: Dict, _: Dict) -> None:
        cleared = self.staleness.clear_all_dirty()
        ctx["_commit_cleared"] = cleared

    # ── 위상 정렬 ────────────────────────────────────────────
    def _topo_sort(self) -> List[NKGPhase]:
        in_deg = {p.name: len(p.deps) for p in self._phases}
        queue  = [p for p in self._phases if in_deg[p.name] == 0]
        result: List[NKGPhase] = []
        while queue:
            phase = queue.pop(0)
            result.append(phase)
            for other in self._phases:
                if phase.name in other.deps:
                    in_deg[other.name] -= 1
                    if in_deg[other.name] == 0:
                        queue.append(other)
        return result

    def last_results(self) -> List[NKGPhaseResult]:
        return list(self._phase_results)

    def stats(self) -> Dict[str, Any]:
        return {
            "graph":              self.graph.stats(),
            "staleness":          self.staleness.stats(),
            "phases":             len(self._phases),
            "edge_infer_ready":   _EDGE_INFER_AVAILABLE,
            "emotional_ready":    _EMOTIONAL_LINKER_AVAILABLE,
        }
