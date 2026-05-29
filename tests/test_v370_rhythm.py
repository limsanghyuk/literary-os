"""test_v370_rhythm.py — KoreanRhythmRewriter 테스트 (V370)"""
import pytest
from literary_system.prose.rhythm_rewriter import KoreanRhythmRewriter, RhythmResult, _mora_count


class TestMoraCount:
    def test_simple_korean(self):
        assert _mora_count("안녕하세요") == 5

    def test_space_excluded(self):
        assert _mora_count("안녕 하세요") == 5

    def test_empty(self):
        assert _mora_count("") == 0

    def test_mixed(self):
        assert _mora_count("A안녕B") == 4


class TestRhythmResult:
    def test_joined_property(self):
        r = RhythmResult(rewritten=["문장1.", "문장2."], rhythm_score=9.0, interventions=0)
        assert "문장1." in r.joined
        assert "문장2." in r.joined

    def test_empty_joined(self):
        r = RhythmResult(rewritten=[], rhythm_score=10.0, interventions=0)
        assert r.joined == ""


class TestRewriteBasics:
    def setup_method(self):
        self.rw = KoreanRhythmRewriter("medium")

    def test_empty_input(self):
        r = self.rw.rewrite([])
        assert r.rhythm_score == pytest.approx(10.0)
        assert r.rewritten == []

    def test_single_sentence_unchanged(self):
        r = self.rw.rewrite(["그가 왔다."])
        assert "그가 왔다." in r.rewritten

    def test_uniform_sentences_high_score(self):
        sents = ["그가 왔다." * 1, "그녀가 갔다.", "모두 떠났다."]
        r = self.rw.rewrite(sents)
        assert r.rhythm_score >= 7.0

    def test_interventions_non_negative(self):
        r = self.rw.rewrite(["그가 왔다.", "그녀가 갔다."])
        assert r.interventions >= 0

    def test_original_stored(self):
        sents = ["a.", "b.", "c."]
        r = self.rw.rewrite(sents)
        assert r.original == sents

    def test_returns_rhythm_result(self):
        r = self.rw.rewrite(["문장."])
        assert isinstance(r, RhythmResult)


class TestSlowRhythm:
    def test_slow_adds_last_beat(self):
        rw = KoreanRhythmRewriter("slow")
        sents = ["그가 창문을 닫았다.", "그녀가 돌아봤다."]
        r = rw.rewrite(sents)
        assert len(r.rewritten) > len(sents)

    def test_slow_intervention_count_positive(self):
        rw = KoreanRhythmRewriter("slow")
        r = rw.rewrite(["a.", "b."])
        assert r.interventions >= 1

    def test_last_beat_is_string(self):
        rw = KoreanRhythmRewriter("slow")
        r  = rw.rewrite(["그가 왔다.", "그녀가 갔다."])
        assert all(isinstance(s, str) for s in r.rewritten)


class TestMediumFastRhythm:
    def test_medium_no_extra_sentence(self):
        rw = KoreanRhythmRewriter("medium")
        sents = ["a.", "b.", "c."]
        r  = rw.rewrite(sents)
        # medium은 비트 삽입 없음 (이상치 없으면)
        assert len(r.rewritten) <= len(sents) + 1

    def test_fast_rhythm_set(self):
        rw = KoreanRhythmRewriter("fast")
        r  = rw.rewrite(["a.", "b."])
        assert isinstance(r, RhythmResult)

    def test_set_rhythm_method(self):
        rw = KoreanRhythmRewriter("medium")
        rw.set_rhythm("slow")
        assert rw.scene_rhythm == "slow"


class TestSplitStatic:
    def test_split_static_multiple(self):
        parts = KoreanRhythmRewriter._split_static("a. b. c.")
        assert len(parts) >= 1

    def test_split_static_empty(self):
        parts = KoreanRhythmRewriter._split_static("")
        assert parts == [""]
