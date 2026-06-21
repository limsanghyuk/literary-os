"""V793 — strategies 후보 생성기 실구현 (p1/p2/p3/p4 포팅, gen_p3·gen_p2 기반).

전략 스텁이 description만 갖던 것을 실제 generate()로 격상. 생성물은
process_candidate(길이매칭→E4) 파이프라인을 우회하지 않음(설계 C3 보존).
"""
import random
import pytest

from literary_system.learning.pairing.strategies import (
    P1GradedDegradation, P2OnPolicy, P3AntiLLM, P4Ties,
    process_candidate, STRATEGIES)
from literary_system.learning.pairing.strategies.base import (
    parse_two_version, RawPair)
from literary_system.learning.pairing.strategies.p1 import degrade
from literary_system.learning.pairing.tokenizer import WhitespaceTokenizer


def _fake_two(a, b, chars=400):
    body = "가 " * chars
    return lambda prompt: f"{a}\n{body}\n{b}\n{body}"


# ---- 공통: parse_two_version ----
def test_parse_two_version_ok():
    a, b = parse_two_version("[SHOW]\nX[TELL]\nY", "[SHOW]", "[TELL]")
    assert a == "X" and b == "Y"

def test_parse_two_version_fail():
    a, b = parse_two_version("no markers", "[SHOW]", "[TELL]")
    assert a is None and b is None


# ---- P3 anti-LLM ----
def test_p3_generate_count_and_strategy():
    pairs = P3AntiLLM().generate(5, generator=_fake_two("[SHOW]", "[TELL]"),
                                 rng=random.Random(1))
    assert len(pairs) == 5
    assert all(p.strategy == "p3" for p in pairs)
    assert all(p.chosen_text and p.rejected_text for p in pairs)

def test_p3_short_output_discarded():
    pairs = P3AntiLLM().generate(2, generator=_fake_two("[SHOW]", "[TELL]", chars=10),
                                 rng=random.Random(1))
    assert pairs == []   # <MIN_LEN → 전량 폐기

def test_p3_generator_exception_skipped():
    def boom(prompt):
        raise RuntimeError("api down")
    pairs = P3AntiLLM().generate(2, generator=boom, rng=random.Random(1))
    assert pairs == []

def test_p3_equal_length_passes_pipeline():
    pairs = P3AntiLLM().generate(1, generator=_fake_two("[SHOW]", "[TELL]"),
                                 rng=random.Random(1))
    v = process_candidate(pairs[0], WhitespaceTokenizer())
    assert v.accept is True and v.drop_reason is None


# ---- P2 on-policy ----
def test_p2_generate_markers():
    pairs = P2OnPolicy().generate(3, generator=_fake_two("[GOOD]", "[WEAK]"),
                                  rng=random.Random(2))
    assert len(pairs) == 3 and all(p.strategy == "p2" for p in pairs)


# ---- P1 graded degradation (결정론) ----
def test_p1_degrade_length_neutral_axes():
    src = "그래서 흐느꼈다 손목시계"
    out = degrade(src, ("break_causality", "flatten_affect", "generic_swap"))
    assert "그래서" not in out and "흐느꼈다" not in out and "손목시계" not in out

def test_p1_generate_chosen_is_source():
    src = "그는 손목시계를 보며 흐느꼈다. 그래서 골목길로 나섰다. " * 4
    pairs = P1GradedDegradation().generate(2, sources=[src], rng=random.Random(3))
    assert len(pairs) == 2
    assert all(p.chosen_text == src for p in pairs)
    assert all(p.rejected_text != p.chosen_text for p in pairs)

def test_p1_no_substitution_discarded():
    pairs = P1GradedDegradation().generate(1, sources=["평범한 문장 " * 20],
                                           rng=random.Random(3))
    assert pairs == []   # 열화 훅 없음 → 폐기

def test_p1_empty_sources():
    assert P1GradedDegradation().generate(3, sources=[]) == []


# ---- P4 ties ----
def test_p4_tie_meta():
    src = "그는 말했다… 그리고  떠났다—끝. " * 8
    pairs = P4Ties().generate(2, sources=[src], rng=random.Random(4))
    assert len(pairs) == 2 and all(p.meta.get("tie") for p in pairs)


# ---- 레지스트리 정합 ----
def test_registry_has_all_four_with_generate():
    assert set(STRATEGIES) == {"p1", "p2", "p3", "p4"}
    for s in STRATEGIES.values():
        assert hasattr(s, "generate")
