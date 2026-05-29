"""V383 — MotifResidueGraphBuilder 테스트."""
import pytest
from literary_system.physics.motif_residue import MotifResidueGraphBuilder, MotifResidueGraph, MotifOrphanWarning


@pytest.fixture
def builder():
    return MotifResidueGraphBuilder()


class TestMotifResidueBasic:
    def test_returns_graph_type(self, builder):
        g = builder.build({'sword': 3}, {'sword': 5}, current_episode=10)
        assert isinstance(g, MotifResidueGraph)

    def test_empty_motifs(self, builder):
        g = builder.build({}, {}, current_episode=0)
        assert g.average_residue == 0.0
        assert g.orphan_warnings == []

    def test_node_created(self, builder):
        g = builder.build({'sword': 3}, {'sword': 2}, current_episode=3)
        assert 'sword' in g.nodes

    def test_residue_score_range(self, builder):
        g = builder.build({'ring': 5}, {'ring': 0}, current_episode=10)
        node = g.nodes['ring']
        assert 0.0 <= node.residue_score <= 1.0

    def test_recent_motif_higher_score(self, builder):
        g = builder.build(
            {'old': 3, 'new': 3},
            {'old': 0, 'new': 10},
            current_episode=10
        )
        assert g.nodes['new'].residue_score >= g.nodes['old'].residue_score

    def test_orphan_warning_low_residue(self, builder):
        # 오래 전 등장 + 2회 이상 → 잔상 경고
        g = builder.build({'ghost': 3}, {'ghost': 0}, current_episode=30)
        assert len(g.orphan_warnings) > 0

    def test_orphan_warning_type(self, builder):
        g = builder.build({'ghost': 5}, {'ghost': 0}, current_episode=50)
        if g.orphan_warnings:
            assert isinstance(g.orphan_warnings[0], MotifOrphanWarning)

    def test_no_orphan_recent_motif(self, builder):
        # 최근 등장 → 잔상 충분 → 경고 없음
        g = builder.build({'hero': 5}, {'hero': 10}, current_episode=10)
        assert g.orphan_warnings == []

    def test_single_appearance_no_orphan(self, builder):
        # 1회 등장은 orphan 경고 없음 (MIN_APPEARANCES=2)
        g = builder.build({'once': 1}, {'once': 0}, current_episode=30)
        assert g.orphan_warnings == []

    def test_average_residue_multiple(self, builder):
        g = builder.build(
            {'a': 5, 'b': 5},
            {'a': 10, 'b': 10},
            current_episode=10
        )
        assert g.average_residue > 0.0

    def test_deterministic(self, builder):
        args = ({'x': 4}, {'x': 3}, 5)
        g1 = builder.build(*args)
        g2 = builder.build(*args)
        assert g1.average_residue == g2.average_residue

    def test_appearances_stored(self, builder):
        g = builder.build({'k': 7}, {'k': 5}, current_episode=5)
        assert g.nodes['k'].appearances == 7

    def test_last_seen_stored(self, builder):
        g = builder.build({'k': 2}, {'k': 4}, current_episode=6)
        assert g.nodes['k'].last_seen_episode == 4

    def test_orphan_message_contains_motif_id(self, builder):
        g = builder.build({'villain': 4}, {'villain': 0}, current_episode=40)
        if g.orphan_warnings:
            assert 'villain' in g.orphan_warnings[0].message
