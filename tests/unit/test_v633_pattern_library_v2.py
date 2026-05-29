"""
V633 — test_v633_pattern_library_v2.py
PatternLibraryV2 단위 테스트 TC-01 ~ TC-33

ADR-075 / SP-C.1 검증 범위
- TC-01~05: 기본 add / count / all_entries
- TC-06~10: rank() 정렬 및 top_k
- TC-11~15: compress() 압축 로직
- TC-16~19: find_by_label / find_similar
- TC-20~22: increment_freq
- TC-23~26: 파일 모드 영속화
- TC-27~29: clear / 예외 처리
- TC-30~33: __init__ 공개 API 및 통합 시나리오
"""
from __future__ import annotations

import json
import math
import tempfile
import uuid
from pathlib import Path

import pytest

from literary_system.constitution import PatternEntry, PatternLibraryV2
from literary_system.constitution.pattern_library_v2 import (
    _cosine_similarity,
    _l2_norm,
)


# ---------------------------------------------------------------------------
# 헬퍼 팩토리
# ---------------------------------------------------------------------------

def _entry(
    label: str,
    freq: int = 1,
    entropy_weight: float = 1.0,
    embedding: list | None = None,
    note: str = "",
) -> PatternEntry:
    return PatternEntry(
        pattern_id=str(uuid.uuid4()),
        label=label,
        description=f"{label} 설명",
        embedding=embedding if embedding is not None else [],
        freq=freq,
        entropy_weight=entropy_weight,
        note=note,
    )


# ---------------------------------------------------------------------------
# 픽스처
# ---------------------------------------------------------------------------

@pytest.fixture
def lib():
    return PatternLibraryV2(":memory:")


@pytest.fixture
def e_high():
    return _entry("고조-절정-해소", freq=10, entropy_weight=0.9,
                  embedding=[1.0, 0.0, 0.0])


@pytest.fixture
def e_mid():
    return _entry("AABB-리듬", freq=5, entropy_weight=0.8,
                  embedding=[0.0, 1.0, 0.0])


@pytest.fixture
def e_low():
    return _entry("대화-반전", freq=2, entropy_weight=0.5,
                  embedding=[0.0, 0.0, 1.0])


# ---------------------------------------------------------------------------
# TC-01~05: add / count / all_entries
# ---------------------------------------------------------------------------

def test_tc01_add_increases_count(lib, e_high):
    lib.add(e_high)
    assert lib.count() == 1


def test_tc02_count_zero_initially(lib):
    assert lib.count() == 0


def test_tc03_add_many(lib, e_high, e_mid, e_low):
    lib.add_many([e_high, e_mid, e_low])
    assert lib.count() == 3


def test_tc04_all_entries_returns_copy(lib, e_high):
    lib.add(e_high)
    result = lib.all_entries()
    result.clear()
    assert lib.count() == 1


def test_tc05_entry_label_preserved(lib, e_high):
    lib.add(e_high)
    assert lib.all_entries()[0].label == "고조-절정-해소"


# ---------------------------------------------------------------------------
# TC-06~10: rank()
# ---------------------------------------------------------------------------

def test_tc06_rank_by_score_desc(lib, e_high, e_mid, e_low):
    lib.add_many([e_low, e_high, e_mid])
    ranked = lib.rank()
    assert ranked[0].label == "고조-절정-해소"  # score=9.0
    assert ranked[1].label == "AABB-리듬"       # score=4.0
    assert ranked[2].label == "대화-반전"       # score=1.0


def test_tc07_rank_top_k(lib, e_high, e_mid, e_low):
    lib.add_many([e_high, e_mid, e_low])
    top1 = lib.rank(top_k=1)
    assert len(top1) == 1
    assert top1[0].label == "고조-절정-해소"


def test_tc08_rank_score_formula(e_high):
    # rank_score = freq * entropy_weight
    assert e_high.rank_score == pytest.approx(10 * 0.9)


def test_tc09_rank_empty_returns_empty(lib):
    assert lib.rank() == []


def test_tc10_rank_tie_order(lib):
    """동점 시 created_at 오름차순."""
    import time
    a = _entry("A", freq=5, entropy_weight=1.0)
    time.sleep(0.01)
    b = _entry("B", freq=5, entropy_weight=1.0)
    lib.add_many([b, a])
    ranked = lib.rank()
    # a 가 먼저 생성 → 동점 시 a가 앞
    assert ranked[0].label == "A"


# ---------------------------------------------------------------------------
# TC-11~15: compress()
# ---------------------------------------------------------------------------

def test_tc11_compress_removes_duplicate(lib):
    """코사인 유사도 > threshold → 낮은 rank 항목 제거."""
    # 거의 동일한 두 벡터
    e1 = _entry("P1", freq=10, embedding=[1.0, 0.001])
    e2 = _entry("P2", freq=2,  embedding=[1.0, 0.001])
    lib.add_many([e1, e2])
    before, after = lib.compress(similarity_threshold=0.90)
    assert before == 2
    assert after == 1
    assert lib.all_entries()[0].label == "P1"  # 높은 rank 유지


def test_tc12_compress_keeps_orthogonal(lib):
    """직교 벡터 → 유사도=0 → 둘 다 유지."""
    e1 = _entry("P1", freq=5, embedding=[1.0, 0.0])
    e2 = _entry("P2", freq=3, embedding=[0.0, 1.0])
    lib.add_many([e1, e2])
    before, after = lib.compress(similarity_threshold=0.90)
    assert after == 2


def test_tc13_compress_no_embedding_always_kept(lib):
    """임베딩 없는 항목은 항상 유지."""
    e_no_emb = _entry("NoEmb", freq=1, embedding=[])
    lib.add(e_no_emb)
    before, after = lib.compress()
    assert after == 1


def test_tc14_compress_returns_before_after_counts(lib, e_high, e_mid):
    lib.add_many([e_high, e_mid])
    before, after = lib.compress()
    assert before == 2
    assert after == 2  # 직교이므로 제거 없음


def test_tc15_compress_threshold_boundary(lib):
    """sim == threshold 는 중복 아님(> 조건)."""
    # 완전히 동일한 벡터 → sim = 1.0
    e1 = _entry("P1", freq=10, embedding=[1.0, 0.0])
    e2 = _entry("P2", freq=2,  embedding=[1.0, 0.0])
    lib.add_many([e1, e2])
    # threshold = 1.0 → sim > 1.0 은 불가 → 제거 안 됨
    before, after = lib.compress(similarity_threshold=1.0)
    assert after == 2


# ---------------------------------------------------------------------------
# TC-16~19: find_by_label / find_similar
# ---------------------------------------------------------------------------

def test_tc16_find_by_label_exact(lib, e_high, e_mid):
    lib.add_many([e_high, e_mid])
    result = lib.find_by_label("고조-절정-해소")
    assert len(result) == 1
    assert result[0].label == "고조-절정-해소"


def test_tc17_find_by_label_missing(lib, e_high):
    lib.add(e_high)
    assert lib.find_by_label("없는레이블") == []


def test_tc18_find_similar_returns_sorted(lib, e_high, e_mid, e_low):
    lib.add_many([e_high, e_mid, e_low])
    # [1,0,0] 쿼리 → e_high 가장 유사
    results = lib.find_similar([1.0, 0.0, 0.0], top_k=3)
    assert results[0][1].label == "고조-절정-해소"
    assert results[0][0] == pytest.approx(1.0)


def test_tc19_find_similar_threshold_filter(lib, e_high, e_mid):
    lib.add_many([e_high, e_mid])
    # threshold=0.9 → [1,0,0] 쿼리에서 e_high(sim=1.0)만 통과
    results = lib.find_similar([1.0, 0.0, 0.0], threshold=0.9)
    assert len(results) == 1
    assert results[0][1].label == "고조-절정-해소"


# ---------------------------------------------------------------------------
# TC-20~22: increment_freq
# ---------------------------------------------------------------------------

def test_tc20_increment_freq_updates_score(lib, e_high):
    lib.add(e_high)
    pid = lib.all_entries()[0].pattern_id
    lib.increment_freq(pid, delta=5)
    updated = lib.find_by_label("고조-절정-해소")[0]
    assert updated.freq == 15


def test_tc21_increment_freq_default_delta(lib, e_mid):
    lib.add(e_mid)
    pid = lib.all_entries()[0].pattern_id
    lib.increment_freq(pid)
    assert lib.find_by_label("AABB-리듬")[0].freq == 6


def test_tc22_increment_freq_unknown_raises_key_error(lib):
    with pytest.raises(KeyError):
        lib.increment_freq("00000000-0000-0000-0000-000000000000")


# ---------------------------------------------------------------------------
# TC-23~26: 파일 모드 영속화
# ---------------------------------------------------------------------------

def test_tc23_file_mode_persists_across_instances(e_high, e_mid):
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "patterns.jsonl"
        lib1 = PatternLibraryV2(path)
        lib1.add_many([e_high, e_mid])

        lib2 = PatternLibraryV2(path)
        assert lib2.count() == 2
        assert lib2.rank()[0].label == "고조-절정-해소"


def test_tc24_file_mode_jsonl_format(e_high):
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "patterns.jsonl"
        lib = PatternLibraryV2(path)
        lib.add(e_high)
        lines = path.read_text().strip().split("\n")
        assert len(lines) == 1
        d = json.loads(lines[0])
        assert d["label"] == "고조-절정-해소"
        assert d["freq"] == 10


def test_tc25_file_mode_auto_creates_parent_dir(e_high):
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "nested" / "deep" / "patterns.jsonl"
        lib = PatternLibraryV2(path)
        lib.add(e_high)
        assert path.exists()


def test_tc26_file_mode_compress_persists(e_high, e_mid):
    """파일 모드에서 compress 후 재로드 시 압축 결과 유지."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "patterns.jsonl"
        lib1 = PatternLibraryV2(path)
        # 직교 패턴 2개 → 압축 후 2개 유지
        lib1.add_many([e_high, e_mid])
        lib1.compress()

        lib2 = PatternLibraryV2(path)
        assert lib2.count() == 2


# ---------------------------------------------------------------------------
# TC-27~29: clear / 예외 처리
# ---------------------------------------------------------------------------

def test_tc27_clear_resets_memory_mode(lib, e_high):
    lib.add(e_high)
    lib.clear()
    assert lib.count() == 0


def test_tc28_clear_deletes_file(e_high):
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "patterns.jsonl"
        lib = PatternLibraryV2(path)
        lib.add(e_high)
        assert path.exists()
        lib.clear()
        assert not path.exists()


def test_tc29_invalid_threshold_raises_value_error():
    with pytest.raises(ValueError):
        PatternLibraryV2(":memory:", similarity_threshold=0.0)
    with pytest.raises(ValueError):
        PatternLibraryV2(":memory:", similarity_threshold=1.1)


# ---------------------------------------------------------------------------
# TC-30~33: 공개 API + 통합 시나리오
# ---------------------------------------------------------------------------

def test_tc30_public_api_pattern_entry_importable():
    from literary_system.constitution import PatternEntry
    assert PatternEntry is not None


def test_tc31_public_api_pattern_library_v2_importable():
    from literary_system.constitution import PatternLibraryV2
    assert PatternLibraryV2 is not None


def test_tc32_pattern_entry_to_dict_roundtrip(e_high):
    d = e_high.to_dict()
    e2 = PatternEntry.from_dict(d)
    assert e2.pattern_id == e_high.pattern_id
    assert e2.label == e_high.label
    assert e2.freq == e_high.freq
    assert e2.entropy_weight == pytest.approx(e_high.entropy_weight)
    assert e2.embedding == e_high.embedding


def test_tc33_integration_add_compress_rank(lib):
    """
    통합 시나리오:
    1. 10개 패턴 추가 (중 2쌍은 중복)
    2. compress() → 중복 제거
    3. rank(top_k=3) → 상위 3개 확인
    """
    patterns = []
    for i in range(10):
        # i=0,1 은 거의 동일한 벡터 (중복 쌍 1)
        if i == 0:
            emb = [1.0, 0.001, 0.0]
        elif i == 1:
            emb = [1.0, 0.001, 0.0]  # 동일
        elif i == 2:
            emb = [0.0, 1.0, 0.001]
        elif i == 3:
            emb = [0.0, 1.0, 0.001]  # 중복 쌍 2
        else:
            angle = i * 0.5
            emb = [math.cos(angle), math.sin(angle), 0.0]
        patterns.append(
            _entry(f"P{i}", freq=10 - i, entropy_weight=0.9, embedding=emb)
        )
    lib.add_many(patterns)
    assert lib.count() == 10

    before, after = lib.compress(similarity_threshold=0.90)
    assert before == 10
    assert after < 10  # 적어도 중복 2개 이상 제거

    top3 = lib.rank(top_k=3)
    assert len(top3) == 3
    # 상위는 freq가 높은 패턴들
    assert top3[0].freq >= top3[1].freq or top3[0].rank_score >= top3[1].rank_score
