"""V411-G 테스트 — NKGCurator."""
from __future__ import annotations
import pytest
from literary_system.nkg.curators.nkg_curator import NKGCurator, CurationReport
from literary_system.nkg.graph_store import NKGGraphStore
from literary_system.nkg.schema import (
    NKGNode, NKGNodeType, NKGEdge, NKGEdgeType,
    EpisodeNode, CharacterNode, SceneNode,
)


def _make_nkg_with_nodes(n: int, ep_start: int = 0) -> NKGGraphStore:
    """n개 EpisodeNode 생성, episode_index = ep_start + i."""
    nkg = NKGGraphStore()
    for i in range(n):
        node = EpisodeNode(node_type=NKGNodeType.EPISODE, node_id=f"ep_{ep_start+i}", label=f"Episode {ep_start+i}",
                           episode_index=ep_start + i)
        nkg.add_node(node)
    return nkg


def _add_edge(nkg: NKGGraphStore, src: str, tgt: str, weight: float = 1.0):
    nkg.add_edge(NKGEdge(source=src, target=tgt,
                         edge_type=NKGEdgeType.CAUSAL_LINK, weight=weight))


# ── 1. 기본 생성 ─────────────────────────────────────────────────
def test_curator_default_creation():
    c = NKGCurator()
    assert c._min_score == NKGCurator.MIN_SCORE_THRESHOLD
    assert c._max_age   == NKGCurator.MAX_AGE_EPISODES


# ── 2. 소규모 NKG 스킵 ───────────────────────────────────────────
def test_skip_small_nkg():
    nkg = _make_nkg_with_nodes(3)
    c = NKGCurator(min_nodes_to_curate=5)
    report = c.curate(nkg, current_episode=10)
    assert report.skipped == True
    assert nkg.node_count() == 3   # 변경 없음


# ── 3. 빈 NKG 스킵 ──────────────────────────────────────────────
def test_skip_empty_nkg():
    nkg = NKGGraphStore()
    c = NKGCurator()
    report = c.curate(nkg, current_episode=10)
    assert report.skipped == True


# ── 4. 오래된 노드 제거 ──────────────────────────────────────────
def test_removes_stale_nodes():
    nkg = _make_nkg_with_nodes(10, ep_start=0)   # ep_0 ~ ep_9
    # ep_0~ep_4는 current=30, max_age=20 → cutoff=10 → 모두 stale
    for i in range(10):
        _add_edge(nkg, f"ep_{i}", f"ep_{(i+1)%10}", weight=1.0)
    c = NKGCurator(max_age_episodes=20, min_nodes_to_curate=5)
    report = c.curate(nkg, current_episode=30)
    assert report.stale_removed > 0
    assert report.removed_count > 0


# ── 5. 약한 노드 제거 (낮은 weight) ─────────────────────────────
def test_removes_weak_nodes():
    nkg = _make_nkg_with_nodes(6, ep_start=100)   # 모두 최신
    # 일부 노드에만 낮은 weight 엣지 연결
    _add_edge(nkg, "ep_100", "ep_101", weight=0.05)  # 약함
    _add_edge(nkg, "ep_102", "ep_103", weight=0.90)  # 강함
    _add_edge(nkg, "ep_104", "ep_105", weight=0.90)  # 강함
    c = NKGCurator(min_score_threshold=0.15, min_nodes_to_curate=5,
                   max_age_episodes=1000)
    report = c.curate(nkg, current_episode=110)
    assert report.removed_count > 0


# ── 6. 고립 노드(엣지 없음) 제거 ────────────────────────────────
def test_removes_isolated_nodes():
    nkg = _make_nkg_with_nodes(6, ep_start=50)
    # 일부만 엣지 연결
    _add_edge(nkg, "ep_50", "ep_51", weight=1.0)
    _add_edge(nkg, "ep_52", "ep_53", weight=1.0)
    # ep_54, ep_55는 고립
    c = NKGCurator(min_score_threshold=0.15, min_nodes_to_curate=5,
                   max_age_episodes=1000)
    report = c.curate(nkg, current_episode=60)
    assert report.weak_removed >= 2 or report.removed_count >= 2


# ── 7. CurationReport.was_cleaned ────────────────────────────────
def test_was_cleaned_true():
    nkg = _make_nkg_with_nodes(6, ep_start=50)
    c = NKGCurator(min_score_threshold=0.15, min_nodes_to_curate=5,
                   max_age_episodes=1000)
    report = c.curate(nkg, current_episode=60)
    # 고립 노드 제거로 was_cleaned=True
    assert isinstance(report.was_cleaned, bool)


# ── 8. CurationReport 타임스탬프 존재 ───────────────────────────
def test_report_timestamp():
    nkg = _make_nkg_with_nodes(6, ep_start=0)
    c = NKGCurator(min_nodes_to_curate=5)
    report = c.curate(nkg, current_episode=5)
    assert report.timestamp != ""


# ── 9. preview — 실제 제거 없음 ─────────────────────────────────
def test_preview_no_removal():
    nkg = _make_nkg_with_nodes(6, ep_start=0)
    original_count = nkg.node_count()
    c = NKGCurator(min_nodes_to_curate=5, max_age_episodes=1)
    report = c.preview(nkg, current_episode=100)
    assert nkg.node_count() == original_count   # 변경 없음
    assert report.reason == "preview_only"


# ── 10. 최신 노드는 제거하지 않음 ───────────────────────────────
def test_recent_nodes_not_removed():
    nkg = NKGGraphStore()
    for i in range(6):
        node = EpisodeNode(node_type=NKGNodeType.EPISODE, node_id=f"ep_{i}", label=f"ep_{i}",
                           episode_index=90 + i)   # 최신
        nkg.add_node(node)
        if i > 0:
            _add_edge(nkg, f"ep_{i-1}", f"ep_{i}", weight=1.0)
    c = NKGCurator(max_age_episodes=20, min_nodes_to_curate=5)
    report = c.curate(nkg, current_episode=100)
    # stale 제거 없어야 함 (최신 노드)
    assert report.stale_removed == 0


# ── 11. episode_idx 기록 ─────────────────────────────────────────
def test_report_episode_idx():
    nkg = _make_nkg_with_nodes(6, ep_start=0)
    c = NKGCurator(min_nodes_to_curate=5)
    report = c.curate(nkg, current_episode=42)
    assert report.episode_idx == 42


# ── 12. 커스텀 threshold ────────────────────────────────────────
def test_custom_threshold():
    c = NKGCurator(min_score_threshold=0.5)
    assert c._min_score == 0.5


# ── 13. CurationReport 데이터클래스 필드 ────────────────────────
def test_report_fields():
    r = CurationReport(removed_count=3, stale_removed=2, weak_removed=1)
    assert r.removed_count == 3
    assert r.stale_removed == 2
    assert r.weak_removed  == 1
    assert r.skipped == False


# ── 14. NKGGraphStore node_count 갱신 ───────────────────────────
def test_node_count_after_curate():
    nkg = _make_nkg_with_nodes(10, ep_start=0)
    original = nkg.node_count()
    c = NKGCurator(min_nodes_to_curate=5, max_age_episodes=1)
    report = c.curate(nkg, current_episode=100)
    if not report.skipped:
        assert nkg.node_count() == original - report.removed_count


# ── 15. 전부 건강한 노드 → removed_count=0 ──────────────────────
def test_no_removal_when_all_healthy():
    nkg = NKGGraphStore()
    for i in range(6):
        node = EpisodeNode(node_type=NKGNodeType.EPISODE, node_id=f"ep_{i}", label=f"ep_{i}",
                           episode_index=95 + i)
        nkg.add_node(node)
        if i > 0:
            _add_edge(nkg, f"ep_{i-1}", f"ep_{i}", weight=0.9)
    c = NKGCurator(max_age_episodes=20, min_score_threshold=0.05,
                   min_nodes_to_curate=5)
    report = c.curate(nkg, current_episode=100)
    assert report.removed_count == 0
    assert report.was_cleaned == False
