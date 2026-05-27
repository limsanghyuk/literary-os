"""V656 PublicSDK v1.0 테스트 (ADR-116) — 33 TC."""
from __future__ import annotations

import pytest

from literary_system.sdk import (
    AnalyzeError,
    GenerateError,
    LiteraryOSClient,
    LiteraryOSError,
    PredictError,
    RateLimitError,
    RepairError,
    SDKConfig,
    ValidationError,
)
from literary_system.sdk.sdk_models import (
    AnalyzeResult,
    GenerateResult,
    PredictResult,
    QualityScore,
    RepairResult,
)


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def client():
    """offline_mode=True 기본 클라이언트."""
    return LiteraryOSClient(SDKConfig(offline_mode=True, max_rpm=0))


@pytest.fixture
def short_text():
    return "그는 창문을 바라보았다. 비가 내리고 있었다. 오늘은 유난히 외로운 날이었다."


@pytest.fixture
def rich_text():
    return (
        "영수는 갑자기 멈췄다. 눈물이 고였다. 배신감이 폭발했다. "
        "김민준이라고 그에게 소리쳤다. 하지만 대답은 없었다. "
        "그녀는 독백처럼 중얼거렸다. 회상이 머릿속을 가득 채웠다. "
        "분노와 슬픔이 뒤섞인 채 그는 자리를 떠났다."
    )


# ── TC-01~05: SDKConfig ───────────────────────────────────────────────────

class TestSDKConfig:
    def test_default_offline_mode(self):                                  # TC-01
        cfg = SDKConfig()
        assert cfg.offline_mode is True

    def test_max_rpm_default(self):                                        # TC-02
        cfg = SDKConfig()
        assert cfg.max_rpm == 1000

    def test_invalid_timeout_raises(self):                                 # TC-03
        with pytest.raises(ValueError, match="timeout_sec"):
            SDKConfig(timeout_sec=-1)

    def test_invalid_quality_threshold_raises(self):                       # TC-04
        with pytest.raises(ValueError, match="quality_threshold"):
            SDKConfig(quality_threshold=1.5)

    def test_to_dict_keys(self):                                           # TC-05
        cfg = SDKConfig()
        d = cfg.to_dict()
        assert "offline_mode" in d
        assert "max_rpm" in d
        assert "quality_threshold" in d


# ── TC-06~08: 클라이언트 초기화 ───────────────────────────────────────────

class TestClientInit:
    def test_version_string(self, client):                                 # TC-06
        assert client.version == "1.0.0"

    def test_stats_initial(self, client):                                  # TC-07
        s = client.stats()
        assert s["total_calls"] == 0
        assert s["offline_mode"] is True

    def test_default_config_created(self):                                 # TC-08
        c = LiteraryOSClient()
        assert c.config is not None


# ── TC-09~16: analyze() ───────────────────────────────────────────────────

class TestAnalyze:
    def test_returns_analyze_result(self, client, short_text):             # TC-09
        r = client.analyze(short_text)
        assert isinstance(r, AnalyzeResult)

    def test_quality_score_range(self, client, short_text):                # TC-10
        r = client.analyze(short_text)
        q = r.quality
        for val in [q.coherence, q.emotion, q.style, q.character, q.tension]:
            assert 0.0 <= val <= 1.0

    def test_overall_is_average(self, client, short_text):                 # TC-11
        r = client.analyze(short_text)
        q = r.quality
        expected = round(
            (q.coherence + q.emotion + q.style + q.character + q.tension) / 5, 4
        )
        assert abs(q.overall - expected) < 1e-6

    def test_word_count_positive(self, client, short_text):                # TC-12
        r = client.analyze(short_text)
        assert r.word_count > 0

    def test_sentence_count_positive(self, client, short_text):            # TC-13
        r = client.analyze(short_text)
        assert r.sentence_count > 0

    def test_rich_text_fewer_issues(self, client, rich_text):             # TC-14
        r = client.analyze(rich_text)
        short_r = client.analyze("짧은 텍스트입니다.")
        assert len(r.issues) <= len(short_r.issues)

    def test_patterns_extracted(self, client, rich_text):                  # TC-15
        r = client.analyze(rich_text)
        assert isinstance(r.patterns, list)

    def test_too_short_raises(self, client):                               # TC-16
        with pytest.raises(ValidationError):
            client.analyze("짧")

    def test_too_long_raises(self, client):                                # TC-17
        with pytest.raises(ValidationError):
            client.analyze("가" * 50_001)

    def test_non_string_raises(self, client):                              # TC-18
        with pytest.raises(ValidationError):
            client.analyze(12345)  # type: ignore[arg-type]

    def test_call_count_increments(self, client, short_text):              # TC-19
        before = client.stats()["total_calls"]
        client.analyze(short_text)
        assert client.stats()["total_calls"] == before + 1


# ── TC-20~24: repair() ────────────────────────────────────────────────────

class TestRepair:
    def test_returns_repair_result(self, client, short_text):              # TC-20
        r = client.repair(short_text, ["too_few_sentences"])
        assert isinstance(r, RepairResult)

    def test_original_preserved(self, client, short_text):                 # TC-21
        r = client.repair(short_text, ["too_few_sentences"])
        assert r.original_text == short_text

    def test_score_fields_populated(self, client, short_text):             # TC-22
        r = client.repair(short_text, ["too_few_sentences"])
        assert 0.0 <= r.score_before <= 1.0
        assert 0.0 <= r.score_after <= 1.0

    def test_invalid_target_score_raises(self, client, short_text):       # TC-23
        with pytest.raises(ValidationError, match="target_score"):
            client.repair(short_text, [], target_score=0.0)

    def test_empty_issues_no_error(self, client, short_text):              # TC-24
        r = client.repair(short_text, [])
        assert r.repaired_text == short_text


# ── TC-25~29: predict() ───────────────────────────────────────────────────

class TestPredict:
    def test_returns_predict_result(self, client, short_text):             # TC-25
        r = client.predict(short_text)
        assert isinstance(r, PredictResult)

    def test_default_n_predictions(self, client, short_text):              # TC-26
        r = client.predict(short_text, n=3)
        assert len(r.predictions) == 3

    def test_rank_ordering(self, client, short_text):                      # TC-27
        r = client.predict(short_text, n=3)
        ranks = [p.rank for p in r.predictions]
        assert ranks == sorted(ranks)

    def test_invalid_n_raises(self, client, short_text):                   # TC-28
        with pytest.raises(ValidationError, match="n"):
            client.predict(short_text, n=11)

    def test_style_hint_injected(self, client, short_text):                # TC-29
        r = client.predict(short_text, n=1, style_hint="thriller")
        assert "thriller" in r.predictions[0].synopsis


# ── TC-30~33: generate() ──────────────────────────────────────────────────

class TestGenerate:
    def test_returns_generate_result(self, client):                        # TC-30
        r = client.generate(
            title="운명의 교차로",
            characters=["이지수", "박민호"],
            setting="비 오는 골목길",
            conflict="오래된 비밀이 드러나다",
        )
        assert isinstance(r, GenerateResult)

    def test_scene_text_nonempty(self, client):                            # TC-31
        r = client.generate(
            title="마지막 선택",
            characters=["김철수"],
            setting="병원 복도",
            conflict="죽음과 삶의 기로",
        )
        assert len(r.scene_text) > 0

    def test_empty_title_raises(self, client):                             # TC-32
        with pytest.raises(ValidationError, match="title"):
            client.generate(
                title="",
                characters=["A"],
                setting="s",
                conflict="c",
            )

    def test_empty_characters_raises(self, client):                        # TC-33
        with pytest.raises(ValidationError, match="characters"):
            client.generate(
                title="T",
                characters=[],
                setting="s",
                conflict="c",
            )
