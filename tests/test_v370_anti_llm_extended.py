"""V370 KoreanAntiLLMFilter 확장 테스트."""
import pytest
from literary_system.prose.anti_llm_filter import KoreanAntiLLMFilter, FilterResult


CLEAN_TEXT = "그가 창문을 열었다. 형광등이 한 번 깜빡였다. 바람이 들어왔다."
CLICHE_HEAVY = "심장이 두근거렸다. 눈물이 차올랐다. 가슴이 먹먹해졌다. 뭔가 이상한 느낌이 들었다. 온몸이 굳어버렸다."


class TestFilterResultType:
    def test_result_is_filter_result(self):
        f = KoreanAntiLLMFilter()
        r = f.filter(CLEAN_TEXT)
        assert isinstance(r, FilterResult)

    def test_filtered_field_is_str(self):
        f = KoreanAntiLLMFilter()
        r = f.filter(CLEAN_TEXT)
        assert isinstance(r.filtered, str)

    def test_score_is_float(self):
        f = KoreanAntiLLMFilter()
        r = f.filter(CLEAN_TEXT)
        assert isinstance(r.score, float)

    def test_score_in_range(self):
        f = KoreanAntiLLMFilter()
        r = f.filter(CLEAN_TEXT)
        assert 0.0 <= r.score <= 10.0

    def test_replacements_is_list(self):
        f = KoreanAntiLLMFilter()
        r = f.filter(CLEAN_TEXT)
        assert isinstance(r.replacements, list)

    def test_n_cliches_is_int(self):
        f = KoreanAntiLLMFilter()
        r = f.filter(CLEAN_TEXT)
        assert isinstance(r.n_cliches, int)


class TestFilterScoring:
    def test_clean_text_high_score(self):
        f = KoreanAntiLLMFilter()
        r = f.filter(CLEAN_TEXT)
        assert r.score >= 8.0

    def test_cliche_heavy_lower_score(self):
        f = KoreanAntiLLMFilter()
        r = f.filter(CLICHE_HEAVY)
        assert r.score < f.filter(CLEAN_TEXT).score

    def test_empty_text_max_score(self):
        f = KoreanAntiLLMFilter()
        r = f.filter("")
        assert r.score == 10.0

    def test_n_cliches_zero_for_clean(self):
        f = KoreanAntiLLMFilter()
        r = f.filter(CLEAN_TEXT)
        assert r.n_cliches == 0

    def test_n_cliches_positive_for_cliche(self):
        f = KoreanAntiLLMFilter()
        r = f.filter(CLICHE_HEAVY)
        assert r.n_cliches > 0


class TestGenreFilter:
    def test_literary_genre_init(self):
        f = KoreanAntiLLMFilter(genre_id="literary")
        assert f is not None

    def test_noir_genre_init(self):
        f = KoreanAntiLLMFilter(genre_id="noir")
        assert f is not None

    def test_fantasy_genre_init(self):
        f = KoreanAntiLLMFilter(genre_id="fantasy")
        assert f is not None

    def test_romance_genre_init(self):
        f = KoreanAntiLLMFilter(genre_id="romance")
        assert f is not None

    def test_historical_genre_init(self):
        f = KoreanAntiLLMFilter(genre_id="historical")
        assert f is not None

    def test_genre_filter_returns_result(self):
        for genre in ["literary", "noir", "fantasy", "romance", "historical"]:
            f = KoreanAntiLLMFilter(genre_id=genre)
            r = f.filter(CLEAN_TEXT)
            assert isinstance(r, FilterResult)

    def test_filtered_nonempty_for_clean(self):
        f = KoreanAntiLLMFilter()
        r = f.filter(CLEAN_TEXT)
        assert len(r.filtered) > 0


class TestFilterIdempotency:
    def test_filtering_twice_stable(self):
        f = KoreanAntiLLMFilter()
        r1 = f.filter(CLEAN_TEXT)
        r2 = f.filter(r1.filtered)
        assert r2.n_cliches == 0  # 두 번째엔 클리셰 없어야

    def test_score_non_decreasing_on_reclean(self):
        f = KoreanAntiLLMFilter()
        r1 = f.filter(CLICHE_HEAVY)
        r2 = f.filter(r1.filtered)
        assert r2.score >= r1.score
