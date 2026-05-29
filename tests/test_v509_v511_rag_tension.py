"""
V509~V511 테스트 — QueryIntentClassifier + DramaLexicon + NarrativeTensionCurve
"""
import pytest, math, sys
sys.path.insert(0, ".")

from literary_system.nie.query_intent_classifier import (
    QueryIntentClassifier, QueryIntent, DramaLexicon, ClassifierResult,
)
from literary_system.nie.narrative_tension_curve import (
    NarrativeTensionCurve, LossResult, TensionPoint,
    T_BASE, T_A1, T_A2, LAMBDA,
)


# ── DramaLexicon ─────────────────────────────────────────────────

class TestDramaLexicon:
    def test_character_boost(self):
        lex = DramaLexicon(["주영", "서준"])
        assert lex.boost_score("주영") == pytest.approx(DramaLexicon.BOOST_CHARACTER)

    def test_episode_boost(self):
        lex = DramaLexicon()
        assert lex.boost_score("화") == pytest.approx(DramaLexicon.BOOST_EPISODE)

    def test_drama_kw_boost(self):
        lex = DramaLexicon()
        assert lex.boost_score("반전") == pytest.approx(DramaLexicon.BOOST_DRAMA_KW)

    def test_unknown_token_no_boost(self):
        lex = DramaLexicon()
        assert lex.boost_score("xyz_unknown") == pytest.approx(1.0)

    def test_emotion_ratio_high_for_emotional_query(self):
        lex = DramaLexicon()
        ratio = lex.emotion_ratio("눈물 슬픔 사랑 감동")
        assert ratio > 0.5

    def test_emotion_ratio_low_for_neutral(self):
        lex = DramaLexicon()
        ratio = lex.emotion_ratio("주인공 씬 구성 플롯")
        assert ratio < 0.3

    def test_character_name_ratio(self):
        lex = DramaLexicon(["도준", "서연"])
        ratio = lex.character_name_ratio("도준 서연 장면")
        assert ratio > 0.4

    def test_add_characters(self):
        lex = DramaLexicon()
        lex.add_characters(["새인물"])
        assert lex.boost_score("새인물") == pytest.approx(DramaLexicon.BOOST_CHARACTER)

    def test_tokenize_and_boost_returns_dict(self):
        lex = DramaLexicon(["A"])
        result = lex.tokenize_and_boost("A 반전 눈물")
        assert isinstance(result, dict)
        assert "a" in result or "A" in result or "반전" in result


# ── QueryIntentClassifier ────────────────────────────────────────

class TestQueryIntentClassifier:
    def test_character_query_classified(self):
        clf = QueryIntentClassifier(character_ids=["도준", "서연", "민호"])
        result = clf.classify("도준 서연 민호 갈등")
        assert result.intent == QueryIntent.CHARACTER

    def test_emotional_query_classified(self):
        clf = QueryIntentClassifier()
        result = clf.classify("눈물 슬픔 배신 분노 감동 그리움")
        assert result.intent == QueryIntent.EMOTIONAL

    def test_plot_query_classified(self):
        clf = QueryIntentClassifier()
        result = clf.classify("3화 반전 씬 구성 결말")
        assert result.intent == QueryIntent.PLOT_EVENT

    def test_character_bm25_weight_high(self):
        clf = QueryIntentClassifier(character_ids=["A", "B", "C", "D"])
        result = clf.classify("A B C D")
        assert result.bm25_weight == pytest.approx(0.70)
        assert result.top_k == 40

    def test_emotional_dense_weight_high(self):
        clf = QueryIntentClassifier()
        result = clf.classify("눈물 슬픔 사랑 그리움 설렘 분노")
        assert result.dense_weight == pytest.approx(0.70)
        assert result.top_k == 60

    def test_plot_balanced_weights(self):
        clf = QueryIntentClassifier()
        result = clf.classify("씬 구성 플롯")
        assert result.bm25_weight == pytest.approx(0.50)
        assert result.dense_weight == pytest.approx(0.50)
        assert result.top_k == 50

    def test_bm25_dense_sum_is_1(self):
        clf = QueryIntentClassifier()
        for q in ["A B", "눈물 슬픔", "씬 구성"]:
            r = clf.classify(q)
            assert r.bm25_weight + r.dense_weight == pytest.approx(1.0)

    def test_confidence_in_range(self):
        clf = QueryIntentClassifier()
        result = clf.classify("눈물 슬픔 사랑")
        assert 0.0 <= result.confidence <= 1.0

    def test_to_dict_structure(self):
        clf = QueryIntentClassifier()
        result = clf.classify("씬 테스트")
        d = result.to_dict()
        assert all(k in d for k in ["intent", "bm25_weight", "dense_weight", "top_k"])

    def test_get_retrieval_params(self):
        clf = QueryIntentClassifier(character_ids=["주인공"])
        params = clf.get_retrieval_params("주인공 장면")
        assert "bm25_weight" in params
        assert "dense_weight" in params
        assert "top_k" in params
        assert "intent" in params

    def test_add_characters_updates_classification(self):
        clf = QueryIntentClassifier()
        clf.add_characters(["새로운주인공A", "새로운주인공B", "새로운주인공C"])
        result = clf.classify("새로운주인공A 새로운주인공B 새로운주인공C 등장")
        assert result.intent == QueryIntent.CHARACTER


# ── NarrativeTensionCurve ────────────────────────────────────────

class TestNarrativeTensionCurve:
    def test_t_ideal_at_zero(self):
        ntc = NarrativeTensionCurve()
        val = ntc.t_ideal(0.0)
        expected = T_BASE + T_A1 * math.sin(-0.50) + T_A2 * math.sin(0.0)
        assert val == pytest.approx(expected)

    def test_t_ideal_at_half(self):
        ntc = NarrativeTensionCurve()
        val = ntc.t_ideal(0.5)
        expected = T_BASE + T_A1 * math.sin(math.pi - 0.50) + T_A2 * math.sin(3 * math.pi)
        assert val == pytest.approx(expected)

    def test_ideal_curve_length(self):
        ntc = NarrativeTensionCurve()
        curve = ntc.ideal_curve(n_points=50)
        assert len(curve) == 50

    def test_ideal_curve_t_range(self):
        ntc = NarrativeTensionCurve()
        curve = ntc.ideal_curve(n_points=100)
        ts = [p[0] for p in curve]
        assert ts[0] == pytest.approx(0.0)
        assert ts[-1] == pytest.approx(1.0)

    def test_record_creates_tension_point(self):
        ntc = NarrativeTensionCurve()
        point = ntc.record(scene_idx=3, total_scenes=10, actual_tension=0.7)
        assert isinstance(point, TensionPoint)
        assert point.actual == pytest.approx(0.7)

    def test_l_tension_zero_when_perfect(self):
        ntc = NarrativeTensionCurve()
        for i in range(10):
            ideal = ntc.t_ideal(i / 9)
            ntc.record(i, 10, ideal)  # actual == ideal
        assert ntc.compute_l_tension() == pytest.approx(0.0, abs=1e-10)

    def test_l_tension_positive_when_imperfect(self):
        ntc = NarrativeTensionCurve()
        for i in range(10):
            ntc.record(i, 10, 0.9)  # 항상 0.9
        assert ntc.compute_l_tension() > 0.0

    def test_l_coverage_zero_when_met(self):
        loss = NarrativeTensionCurve.compute_l_coverage(
            target_counts={"A": 3, "B": 2},
            actual_counts={"A": 3, "B": 2},
        )
        assert loss == pytest.approx(0.0)

    def test_l_coverage_positive_when_short(self):
        loss = NarrativeTensionCurve.compute_l_coverage(
            target_counts={"A": 5},
            actual_counts={"A": 2},
        )
        assert loss == pytest.approx(9.0)  # (5-2)²=9

    def test_l_final_structure(self):
        ntc = NarrativeTensionCurve()
        ntc.record(0, 5, 0.6)
        result = ntc.compute_l_final(
            target_counts={"A": 3},
            actual_counts={"A": 2},
        )
        assert isinstance(result, LossResult)
        # [B2-FIX] ADR-020 준수 수식: L_final = λ·L_tension + (1-λ)·L_coverage
        assert result.l_final == pytest.approx(
            LAMBDA * result.l_tension + (1 - LAMBDA) * result.l_coverage
        )

    def test_update_lambda(self):
        ntc = NarrativeTensionCurve()
        ntc.update_lambda(0.5)
        assert ntc.get_config()["lambda"] == pytest.approx(0.5)

    def test_update_fourier_coefficients(self):
        ntc = NarrativeTensionCurve()
        ntc.update_fourier_coefficients(base=0.55, a1=0.35, a2=0.15)
        cfg = ntc.get_config()
        assert cfg["base"] == pytest.approx(0.55)
        assert cfg["a1"] == pytest.approx(0.35)

    def test_reset_clears_points(self):
        ntc = NarrativeTensionCurve()
        ntc.record(0, 5, 0.6)
        ntc.reset()
        assert len(ntc.get_points()) == 0

    def test_tension_point_to_dict(self):
        ntc = NarrativeTensionCurve()
        pt = ntc.record(0, 10, 0.7)
        d = pt.to_dict()
        assert all(k in d for k in ["t", "actual", "ideal", "diff_sq"])
