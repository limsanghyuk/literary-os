"""V791 — G_MEMORIZATION 암기/표절 하드게이트 단위 테스트."""

from literary_system.learning.memorization_gate import (
    PENALTY,
    MemorizationGateResult,
    apply_memorization_penalty,
    g_memorization,
)


# 긴 한국어 지문 (≥30자, MIN_LEN 통과)
REF = (
    "비가 내리는 새벽 골목에서 그는 낡은 우산을 접고 오래 닫혀 있던 철문을 두드렸다. "
    "안에서는 아무 대답도 들리지 않았고 빗소리만 점점 더 커져 갔다."
)


def test_identical_is_rejected():
    res = g_memorization(REF, REF)
    assert res.plagiarized is True
    assert res.decision == "reject"


def test_empty_candidate_passes_without_error():
    res = g_memorization("", REF)
    assert res.plagiarized is False
    assert res.decision == "pass"
    assert "too_short" in res.detail


def test_empty_reference_passes_without_error():
    res = g_memorization(REF, "")
    assert res.plagiarized is False
    assert res.decision == "pass"


def test_near_duplicate_one_word_changed_is_rejected():
    # 긴 지문에서 단어 하나만 교체 → 긴 연속 일치(contig) 생존 → reject
    near = REF.replace("우산을", "외투를")
    res = g_memorization(near, REF)
    assert res.plagiarized is True
    assert res.decision == "reject"
    assert res.contig_chars >= 25


def test_too_short_passes():
    res = g_memorization("그래.", "그래.")
    assert res.plagiarized is False
    assert res.decision == "pass"
    assert "too_short" in res.detail


def test_unrelated_korean_scenes_pass():
    other = (
        "환한 봄날 공원에서 아이들이 연을 날리고 노부부는 벤치에 앉아 "
        "따뜻한 커피를 나누어 마시며 지나간 시절의 이야기를 천천히 꺼냈다."
    )
    res = g_memorization(other, REF)
    assert res.plagiarized is False
    assert res.decision in ("pass", "review")


def test_verbatim_long_run_is_blocked():
    # candidate가 새 문장 + 원문 한 문장 통째 삽입 → 축자복제 신호
    cand = (
        "그는 잠시 망설였다. "
        "비가 내리는 새벽 골목에서 그는 낡은 우산을 접고 오래 닫혀 있던 철문을 두드렸다."
    )
    res = g_memorization(cand, REF)
    assert res.contig_chars >= 25
    assert res.decision in ("reject", "review")


def test_apply_penalty_on_reject():
    res = g_memorization(REF, REF)
    assert res.plagiarized is True
    assert apply_memorization_penalty(0.8, res) == PENALTY


def test_apply_penalty_keeps_reward_on_pass():
    other = (
        "환한 봄날 공원에서 아이들이 연을 날리고 노부부는 벤치에 앉아 "
        "따뜻한 커피를 나누어 마시며 지나간 시절의 이야기를 천천히 꺼냈다."
    )
    res = g_memorization(other, REF)
    if not res.plagiarized:
        assert apply_memorization_penalty(0.8, res) == 0.8


def test_determinism():
    a = g_memorization(REF, REF).to_dict()
    b = g_memorization(REF, REF).to_dict()
    assert a == b


def test_to_dict_shape():
    res = g_memorization(REF, REF)
    d = res.to_dict()
    for k in (
        "lcs_ratio", "contig_chars", "contig_ratio", "ngram_jaccard",
        "max_overlap", "plagiarized", "decision", "detail", "signals",
    ):
        assert k in d


def test_result_is_dataclass_instance():
    res = g_memorization(REF, REF)
    assert isinstance(res, MemorizationGateResult)
