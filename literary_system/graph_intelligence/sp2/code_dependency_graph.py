"""V531 — CodeDependencyGraph
Script-level dependency graph for screenplay scenes.
Tracks which scenes share characters, locations, props, and plot threads.
LLM-0 compliant.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Optional, Set, Tuple
from collections import defaultdict, deque


@dataclass(frozen=True)
class SceneDependencyKey:
    """Immutable key identifying a scene."""
    episode: int
    scene_id: str


@dataclass
class DependencyEdge:
    """Directed dependency edge between two scenes."""
    src: SceneDependencyKey
    dst: SceneDependencyKey
    reason: str          # e.g. "shared_character", "shared_location", "plot_thread"
    weight: float = 1.0  # coupling strength 0.0–1.0


@dataclass
class SceneProfile:
    """Attributes of a scene used for coupling detection."""
    key: SceneDependencyKey
    character_ids: FrozenSet[str] = field(default_factory=frozenset)
    location_id: str = ""
    prop_ids: FrozenSet[str] = field(default_factory=frozenset)
    plot_thread_ids: FrozenSet[str] = field(default_factory=frozenset)
    # Explicit script-level dependencies (e.g. a scene that continues from another)
    explicit_deps: FrozenSet[str] = field(default_factory=frozenset)  # scene_ids


@dataclass
class CouplingReport:
    """Summary of coupling between two scenes."""
    src_id: str
    dst_id: str
    shared_characters: List[str] = field(default_factory=list)
    shared_location: bool = False
    shared_props: List[str] = field(default_factory=list)
    shared_threads: List[str] = field(default_factory=list)
    explicit: bool = False
    coupling_score: float = 0.0

    def is_coupled(self) -> bool:
        return self.coupling_score > 0.0


class CodeDependencyGraph:
    """Builds and queries a script-level dependency graph of scenes.

    Coupling is inferred from shared structural elements:
    - Characters present in both scenes → weight 0.3 per shared character (capped 0.6)
    - Same location → weight 0.2
    - Shared props → weight 0.1 per shared prop (capped 0.2)
    - Shared plot threads → weight 0.3 per thread (capped 0.6)
    - Explicit dependency → weight 1.0 (override)

    LLM-0: all coupling is computed from structured metadata.
    """

    _W_CHAR    = 0.30
    _W_LOC     = 0.20
    _W_PROP    = 0.10
    _W_THREAD  = 0.30
    _W_EXPLICIT = 1.0

    def __init__(self) -> None:
        self._profiles: Dict[str, SceneProfile] = {}   # scene_id → profile
        self._edges: List[DependencyEdge] = []
        self._adj: Dict[str, List[str]] = defaultdict(list)  # src → [dst]
        self._radj: Dict[str, List[str]] = defaultdict(list)  # dst → [src]
        self._built: bool = False

    # ------------------------------------------------------------------
    # Profile registration
    # ------------------------------------------------------------------

    def register(self, profile: SceneProfile) -> None:
        """Register a scene profile. Must call build() after all registrations."""
        self._profiles[profile.key.scene_id] = profile
        self._built = False

    def register_batch(self, profiles: List[SceneProfile]) -> None:
        for p in profiles:
            self.register(p)

    # ------------------------------------------------------------------
    # Graph construction
    # ------------------------------------------------------------------

    def build(self) -> int:
        """Infer all coupling edges from registered profiles. Returns edge count."""
        self._edges.clear()
        self._adj.clear()
        self._radj.clear()
        ids = list(self._profiles.keys())
        for i, sid_a in enumerate(ids):
            for sid_b in ids[i + 1:]:
                report = self._compute_coupling(sid_a, sid_b)
                if report.is_coupled():
                    self._add_edge(sid_a, sid_b, report)
                    self._add_edge(sid_b, sid_a, report)
        self._built = True
        return len(self._edges)

    def _compute_coupling(self, sid_a: str, sid_b: str) -> CouplingReport:
        pa = self._profiles[sid_a]
        pb = self._profiles[sid_b]
        report = CouplingReport(src_id=sid_a, dst_id=sid_b)

        score = 0.0

        # Explicit deps
        if sid_b in pa.explicit_deps or sid_a in pb.explicit_deps:
            report.explicit = True
            score = self._W_EXPLICIT

        # Shared characters
        shared_chars = sorted(pa.character_ids & pb.character_ids)
        if shared_chars:
            report.shared_characters = shared_chars
            score += min(len(shared_chars) * self._W_CHAR, 0.6)

        # Shared location
        if pa.location_id and pa.location_id == pb.location_id:
            report.shared_location = True
            score += self._W_LOC

        # Shared props
        shared_props = sorted(pa.prop_ids & pb.prop_ids)
        if shared_props:
            report.shared_props = shared_props
            score += min(len(shared_props) * self._W_PROP, 0.2)

        # Shared plot threads
        shared_threads = sorted(pa.plot_thread_ids & pb.plot_thread_ids)
        if shared_threads:
            report.shared_threads = shared_threads
            score += min(len(shared_threads) * self._W_THREAD, 0.6)

        report.coupling_score = round(min(score, 1.0), 4)
        return report

    def _add_edge(self, src: str, dst: str, report: CouplingReport) -> None:
        sp = self._profiles[src]
        dp = self._profiles[dst]
        reasons = []
        if report.shared_characters:
            reasons.append(f"shared_character:{','.join(report.shared_characters[:2])}")
        if report.shared_location:
            reasons.append("shared_location")
        if report.shared_threads:
            reasons.append("shared_thread")
        if report.explicit:
            reasons.append("explicit")
        edge = DependencyEdge(
            src=sp.key, dst=dp.key,
            reason="|".join(reasons) or "coupled",
            weight=report.coupling_score,
        )
        self._edges.append(edge)
        self._adj[src].append(dst)
        self._radj[dst].append(src)

    # ------------------------------------------------------------------
    # Query API
    # ------------------------------------------------------------------

    def _assert_built(self) -> None:
        if not self._built:
            raise RuntimeError("Call build() before querying")

    def direct_deps(self, scene_id: str) -> List[str]:
        """Scenes directly coupled to *scene_id*."""
        self._assert_built()
        return list(set(self._adj.get(scene_id, [])))

    def reverse_deps(self, scene_id: str) -> List[str]:
        """Scenes that depend on *scene_id*."""
        self._assert_built()
        return list(set(self._radj.get(scene_id, [])))

    def bfs_impact(self, scene_id: str, max_depth: int = 2) -> Set[str]:
        """BFS from *scene_id*, collecting all reachable scenes up to max_depth."""
        self._assert_built()
        visited: Set[str] = set()
        q: deque[Tuple[str, int]] = deque([(scene_id, 0)])
        while q:
            cur, d = q.popleft()
            if cur in visited:
                continue
            visited.add(cur)
            if d >= max_depth:
                continue
            for nb in self._adj.get(cur, []):
                if nb not in visited:
                    q.append((nb, d + 1))
        visited.discard(scene_id)
        return visited

    def coupling_score(self, sid_a: str, sid_b: str) -> float:
        """Coupling score between two scenes (0.0 if not coupled)."""
        self._assert_built()
        for e in self._edges:
            if e.src.scene_id == sid_a and e.dst.scene_id == sid_b:
                return e.weight
        return 0.0

    def stats(self) -> Dict[str, int]:
        self._assert_built()
        return {
            "scene_count": len(self._profiles),
            "edge_count": len(self._edges),
        }
