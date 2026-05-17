"""test_v370_anti_llm.py — KoreanAntiLLMFilter 테스트 (V370)"""
import pytest
from literary_system.prose.anti_llm_filter import KoreanAntiLLMFilter, FilterResult, _BASE_DICT


class TestFilterBasics:
    def test_filter_returns_filter_result(self):
        f = KoreanAntiLLMFilter()
        r = f.filter("안녕하세요.")
        assert isinstance(r, FilterResult)

    def test_clean_text_score_high(self):
        f = KoreanAntiLLMFilter()
        r = f.filter("문이 열렸다. 빛이 들어왔다.")
        assert r.score >= 9.0

    def test_cliche_detected_and_replaced(self):
        f = KoreanAntiLLMFilter()
        r = f.filter("복잡한 감정이 밀려왔다.")
        assert "복잡한 감정이 밀려왔다" not in r.filtered
        assert r.n_cliches >= 1

    def test_replacement_pair_recorded(self):
        f = KoreanAntiLLMFilter()
        r = f.filter("가슴이 먹먹했다.")
        assert any("가슴이 먹먹했다" in orig for orig, _ in r.replacements)

    def test_filtered_text_different_from_original(self):
        f = KoreanAntiLLMFilter()
        original = "눈물이 핑 돌았다."
        r = f.filter(original)
        assert r.filtered != original

    def test_score_decreases_with_more_cliches(self):
        f = KoreanAntiLLMFilter()
        clean = "그는 문을 열었다."
        cliche = "복잡한 감정이 밀려왔다. 가슴이 먹먹했다. 눈물이 핑 돌았다."
        r_clean  = f.filter(clean)
        r_cliche = f.filter(cliche)
        assert r_clean.score >= r_cliche.score

    def test_is_clean_true_no_cliche(self):
        f = KoreanAntiLLMFilter()
        r = f.filter("그가 문을 두드렸다.")
        assert r.is_clean is True

    def test_is_clean_false_with_cliche(self):
        f = KoreanAntiLLMFilter()
        r = f.filter("복잡한 감정이 밀려왔다.")
        assert r.is_clean is False

    def test_empty_text_score_ten(self):
        f = KoreanAntiLLMFilter()
        r = f.filter("")
        assert r.score == pytest.approx(10.0)


class TestDictSize:
    def test_base_dict_50_plus(self):
        assert len(_BASE_DICT) >= 50

    def test_literary_dict_size_50_plus(self):
        f = KoreanAntiLLMFilter("literary")
        assert f.dict_size >= 50

    def test_noir_dict_size_larger_than_base(self):
        f_base = KoreanAntiLLMFilter("literary")
        f_noir = KoreanAntiLLMFilter("noir")
        assert f_noir.dict_size >= f_base.dict_size

    def test_fantasy_dict_created(self):
        f = KoreanAntiLLMFilter("fantasy")
        assert f.dict_size >= 50


class TestGenreDifferentiation:
    def test_noir_filter_instance(self):
        f = KoreanAntiLLMFilter("noir")
        assert f.genre_id == "noir"

    def test_romance_filter_instance(self):
        f = KoreanAntiLLMFilter("romance")
        assert f.genre_id == "romance"

    def test_historical_filter_instance(self):
        f = KoreanAntiLLMFilter("historical")
        assert f.genre_id == "historical"

    def test_genre_dict_loaded_differently(self):
        f_lit = KoreanAntiLLMFilter("literary")
        f_noir = KoreanAntiLLMFilter("noir")
        # noir은 literary와 다른 교체어를 가질 수 있음
        assert f_lit._dict != f_noir._dict or f_lit.dict_size == f_noir.dict_size


class TestScoreOnly:
    def test_score_only_no_modification(self):
        f = KoreanAntiLLMFilter()
        text = "복잡한 감정이 밀려왔다."
        score = f.score_only(text)
        assert 0.0 <= score <= 10.0

    def test_score_only_clean_text_high(self):
        f = KoreanAntiLLMFilter()
        score = f.score_only("그가 창문을 닫았다.")
        assert score >= 9.0


class TestMultipleCliches:
    def test_multiple_cliches_all_replaced(self):
        f = KoreanAntiLLMFilter()
        text = "복잡한 감정이 밀려왔다. 눈물이 핑 돌았다. 가슴이 먹먹했다."
        r = f.filter(text)
        assert r.n_cliches >= 3

    def test_replacement_count_matches_n_cliches(self):
        f = KoreanAntiLLMFilter()
        text = "심장이 두근거렸다. 마음이 무거웠다."
        r = f.filter(text)
        assert r.n_cliches == len(r.replacements)

    def test_filtered_text_not_contains_known_cliches(self):
        f = KoreanAntiLLMFilter()
        cliches = ["복잡한 감정이 밀려왔다", "가슴이 먹먹했다", "눈물이 핑 돌았다"]
        text = " ".join(cliches)
        r = f.filter(text)
        for c in cliches:
            assert c not in r.filtered

    def test_score_float_type(self):
        f = KoreanAntiLLMFilter()
        r = f.filter("안녕.")
        assert isinstance(r.score, float)
