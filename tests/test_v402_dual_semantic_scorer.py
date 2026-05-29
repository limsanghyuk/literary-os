"""V402 — DualSemanticScorer + DRSEScorer NKG 주입 테스트 (16 tests)"""
import pytest
from literary_system.drse.drse_engine import (
    DualSemanticScorer, TFIDFSemanticScorer, KeywordSemanticScorer,
    DRSEScorer, KnowledgeBoundaryGate
)
from literary_system.relation_graph.relation_graph_store import (
    RelationGraphStore, StoryNode, StoryEdge, NodeType
)
from literary_system.nkg.graph_store import NKGGraphStore
from literary_system.nkg.schema import NKGNodeType, NKGSceneNode
from literary_system.nkg.adapters.nkg_semantic_adapter import NKGSemanticAdapter


def _make_nkg_scene(nkg, node_id, label):
    node = NKGSceneNode(node_type=NKGNodeType.SCENE, node_id=node_id, label=label)
    nkg.add_node(node)
    return node


def _make_rgs_with_node():
    rgs = RelationGraphStore()
    n1 = StoryNode("n1", NodeType.CHARACTER.value, "형사 김민준", origin_episode=1)
    rgs.add_node(n1)
    rgs.add_edge(StoryEdge("pov", "n1", "knows", strength=1.0))
    gate = KnowledgeBoundaryGate(relation_graph=rgs)
    return rgs, gate


class TestDualSemanticScorerBasic:
    def test_import(self):
        assert DualSemanticScorer is not None

    def test_no_nkg_uses_tfidf(self):
        scorer = DualSemanticScorer()
        s = scorer.score("형사 수사 살인", "형사 살인 사건")
        assert isinstance(s, float)
        assert 0.0 <= s <= 1.0

    def test_tfidf_only_backward_compatible(self):
        tfidf = TFIDFSemanticScorer()
        dual = DualSemanticScorer(tfidf=tfidf, nkg_adapter=None)
        text, goal = "형사 살인 수사", "살인 사건 수사"
        assert dual.score(text, goal) == tfidf.score(text, goal)

    def test_empty_nkg_adapter_falls_back(self):
        nkg = NKGGraphStore()
        adapter = NKGSemanticAdapter(nkg)   # empty NKG — is_ready()=False
        tfidf = TFIDFSemanticScorer()
        dual = DualSemanticScorer(tfidf=tfidf, nkg_adapter=adapter)
        text, goal = "형사 수사", "살인 사건"
        assert dual.score(text, goal) == tfidf.score(text, goal)

    def test_nkg_ready_returns_max(self):
        nkg = NKGGraphStore()
        _make_nkg_scene(nkg, "s1", "형사 살인 수사 현장")
        adapter = NKGSemanticAdapter(nkg)
        tfidf = TFIDFSemanticScorer()
        dual = DualSemanticScorer(tfidf=tfidf, nkg_adapter=adapter)
        text, goal = "형사 수사 단서", "살인 사건 수사"
        s_dual = dual.score(text, goal)
        s_tfidf = tfidf.score(text, goal)
        assert s_dual >= s_tfidf - 1e-9

    def test_score_range(self):
        nkg = NKGGraphStore()
        _make_nkg_scene(nkg, "s1", "형사 수사")
        adapter = NKGSemanticAdapter(nkg)
        dual = DualSemanticScorer(nkg_adapter=adapter)
        s = dual.score("형사 수사", "살인 사건")
        assert 0.0 <= s <= 1.0

    def test_exception_in_nkg_falls_back(self):
        class BrokenAdapter:
            def is_ready(self): return True
            def score(self, a, b): raise RuntimeError("broken")
        tfidf = TFIDFSemanticScorer()
        dual = DualSemanticScorer(tfidf=tfidf, nkg_adapter=BrokenAdapter())
        s = dual.score("text", "goal")
        assert s == tfidf.score("text", "goal")


class TestDRSEScorerNKGInjection:
    def test_drse_no_nkg_works(self):
        rgs, gate = _make_rgs_with_node()
        scorer = DRSEScorer(rgs=rgs, boundary_gate=gate, nkg=None)
        assert isinstance(scorer.semantic, TFIDFSemanticScorer)

    def test_drse_with_nkg_uses_dual(self):
        rgs, gate = _make_rgs_with_node()
        nkg = NKGGraphStore()
        scorer = DRSEScorer(rgs=rgs, boundary_gate=gate, nkg=nkg)
        assert isinstance(scorer.semantic, DualSemanticScorer)

    def test_drse_nkg_scores_correctly(self):
        rgs, gate = _make_rgs_with_node()
        nkg = NKGGraphStore()
        _make_nkg_scene(nkg, "s1", "형사 수사 씬")
        scorer = DRSEScorer(rgs=rgs, boundary_gate=gate, nkg=nkg)
        nodes = list(rgs.all_nodes())
        ns = scorer.score_node(nodes[0], "형사 수사", "pov", 1)
        assert 0.0 <= ns.score <= 10.0

    def test_drse_explicit_scorer_overrides_nkg(self):
        rgs, gate = _make_rgs_with_node()
        nkg = NKGGraphStore()
        keyword = KeywordSemanticScorer()
        scorer = DRSEScorer(rgs=rgs, boundary_gate=gate,
                            semantic_scorer=keyword, nkg=nkg)
        assert isinstance(scorer.semantic, KeywordSemanticScorer)

    def test_backward_compat_no_nkg_param(self):
        rgs, gate = _make_rgs_with_node()
        scorer = DRSEScorer(rgs=rgs, boundary_gate=gate)
        assert isinstance(scorer.semantic, TFIDFSemanticScorer)

    def test_drse_structure_source_check(self):
        import literary_system.drse.drse_engine as mod
        src = open(mod.__file__).read()
        assert "DualSemanticScorer" in src
        assert "nkg_adapter" in src

    def test_drse_engine_has_dual_scorer_class(self):
        from literary_system.drse.drse_engine import DualSemanticScorer as DS
        ds = DS()
        assert hasattr(ds, 'score')
        assert callable(ds.score)

    def test_dual_scorer_is_semantic_scorer_subclass(self):
        from literary_system.drse.drse_engine import SemanticScorer
        assert issubclass(DualSemanticScorer, SemanticScorer)
