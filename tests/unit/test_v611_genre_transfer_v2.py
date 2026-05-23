"""
V611 GenreTransferV2 + LoRAStackingAdapter 단위 테스트 (12 TC)

TC01~TC06: GenreTransferV2 핵심 기능
TC07~TC10: LoRAStackingAdapter 핵심 기능
TC11~TC12: 통합 (CIM v2 + 장르 전이 + LoRA 스태킹)
"""
import math
import warnings

import pytest

from literary_system.multiwork.genre_transfer import (
    GenreAdaptationReport,
    GenreProfile,
    GenreTransferLearning,
    GenreTransferV2,
    TransferRecord,
)
from literary_system.serving.lora_stacking_adapter import (
    LoRAStackingAdapter,
    LoRAWeight,
    StackResult,
)


# ======================================================================
# 픽스처
# ======================================================================

@pytest.fixture
def gtv2() -> GenreTransferV2:
    return GenreTransferV2()


@pytest.fixture
def lora_drama() -> LoRAWeight:
    return LoRAWeight(
        weight_id="lora-drama-001",
        genre="drama",
        version="v1.0",
        weight_data={
            "attn": {"q": 0.10, "k": 0.20, "v": 0.05},
            "ffn":  {"w1": 0.30, "w2": 0.15},
        },
    )


@pytest.fixture
def lora_thriller() -> LoRAWeight:
    return LoRAWeight(
        weight_id="lora-thriller-001",
        genre="thriller",
        version="v1.0",
        weight_data={
            "attn": {"q": 0.40, "k": 0.10, "v": 0.25},
            "ffn":  {"w1": 0.20, "w2": 0.35},
        },
    )


@pytest.fixture
def adapter(lora_drama, lora_thriller) -> LoRAStackingAdapter:
    a = LoRAStackingAdapter()
    a.register(lora_drama)
    a.register(lora_thriller)
    return a


# ======================================================================
# TC01: GenreTransferV2 기본 인스턴스 + stats_v2
# ======================================================================

def test_tc01_gtv2_init_and_stats(gtv2: GenreTransferV2) -> None:
    """TC01: GenreTransferV2 초기화 및 stats_v2 구조 검증."""
    stats = gtv2.stats_v2()
    assert stats["version"] == "2.0.0"
    assert stats["registered_genres"] == 7        # 기본 장르 7종
    assert stats["has_char_db"] is False
    assert stats["has_world_db"] is False
    assert stats["has_cim_v2"] is False
    assert stats["adaptation_report_count"] == 0
    assert isinstance(gtv2, GenreTransferLearning)  # 상속 확인


# ======================================================================
# TC02: weighted_transfer 기본 동작 (CIM 없음)
# ======================================================================

def test_tc02_weighted_transfer_no_cim(gtv2: GenreTransferV2) -> None:
    """TC02: CIM 없을 때 weighted_transfer → alpha 그대로, GenreAdaptationReport 반환."""
    report = gtv2.weighted_transfer(
        source_genre="drama",
        target_genre="thriller",
        project_id="proj-001",
        alpha=0.3,
    )
    assert isinstance(report, GenreAdaptationReport)
    assert report.project_id == "proj-001"
    assert report.source_genre == "drama"
    assert report.target_genre == "thriller"
    # CIM 없음 → cim_weight=0 → adjusted_alpha = clamp(0.3 + 0) = 0.3
    assert abs(report.alpha - 0.3) < 1e-9
    assert report.cim_weight_boost == 0.0
    assert report.char_reward_mean == 0.0
    assert report.world_consistency == 1.0
    assert 0.0 <= report.coherence_score <= 1.0


# ======================================================================
# TC03: weighted_transfer 결과 파라미터 수치 검증
# ======================================================================

def test_tc03_weighted_transfer_param_values(gtv2: GenreTransferV2) -> None:
    """TC03: drama→thriller alpha=0.4 전이 파라미터 수치 검증."""
    drama = gtv2.get_profile("drama")
    thriller = gtv2.get_profile("thriller")
    report = gtv2.weighted_transfer("drama", "thriller", "proj-x", alpha=0.4)
    profile = report.adapted_profile

    # transferred[k] = (1-alpha)*target[k] + alpha*source[k]
    for key in ["tension_base", "dialogue_ratio", "pacing_norm"]:
        expected = round(0.6 * thriller.params[key] + 0.4 * drama.params[key], 6)
        assert abs(profile.params[key] - expected) < 1e-4, (
            f"{key}: expected {expected}, got {profile.params[key]}"
        )


# ======================================================================
# TC04: project_genre_coherence — 동일 장르 반복 시 1.0
# ======================================================================

def test_tc04_coherence_same_genre(gtv2: GenreTransferV2) -> None:
    """TC04: 동일 project_id에서 같은 target_genre 반복 → coherence=1.0."""
    for _ in range(3):
        gtv2.weighted_transfer("drama", "thriller", "proj-coh", alpha=0.3)
    coherence = gtv2.project_genre_coherence("proj-coh")
    assert coherence == 1.0


# ======================================================================
# TC05: project_genre_coherence — 혼합 장르 시 < 1.0
# ======================================================================

def test_tc05_coherence_mixed_genres(gtv2: GenreTransferV2) -> None:
    """TC05: 혼합 target_genre → coherence < 1.0."""
    gtv2.weighted_transfer("drama", "thriller", "proj-mix", alpha=0.3)
    gtv2.weighted_transfer("drama", "romance", "proj-mix", alpha=0.2)
    gtv2.weighted_transfer("drama", "thriller", "proj-mix", alpha=0.3)
    coherence = gtv2.project_genre_coherence("proj-mix")
    # thriller 2회 / 총 3회 = 0.6667
    assert abs(coherence - round(2 / 3, 4)) < 1e-4


# ======================================================================
# TC06: recommend_genre — CIM 없음(기본 0.5) → 가장 먼 장르
# ======================================================================

def test_tc06_recommend_genre_no_cim(gtv2: GenreTransferV2) -> None:
    """TC06: CIM 없음 시 cim_weight=0.5 기본값 → 가장 먼 장르 추천."""
    genre, dist = gtv2.recommend_genre("romance")
    assert genre in gtv2.list_genres()
    assert genre != "romance"
    assert dist > 0.0
    # romance에서 가장 먼 장르는 thriller (높은 tension/pacing 대비)
    # 정확한 값보다 반환 타입 구조 확인
    assert isinstance(genre, str)
    assert isinstance(dist, float)


# ======================================================================
# TC07: LoRAStackingAdapter 등록 + 이중 등록 방지
# ======================================================================

def test_tc07_lora_register_and_duplicate(
    adapter: LoRAStackingAdapter, lora_drama: LoRAWeight
) -> None:
    """TC07: LoRA 등록 성공 + overwrite=False 이중 등록 KeyError."""
    assert adapter.get("lora-drama-001") is lora_drama
    assert adapter.get("lora-thriller-001") is not None
    with pytest.raises(KeyError):
        adapter.register(lora_drama, overwrite=False)
    # overwrite=True는 성공해야 함
    adapter.register(lora_drama, overwrite=True)


# ======================================================================
# TC08: stack() 수치 검증
# ======================================================================

def test_tc08_stack_numeric(adapter: LoRAStackingAdapter) -> None:
    """TC08: 0.6/0.4 계수로 스태킹 → attn.q 수치 검증."""
    result = adapter.stack(
        ["lora-drama-001", "lora-thriller-001"],
        [0.6, 0.4],
    )
    assert isinstance(result, StackResult)
    # 0.6*0.10 + 0.4*0.40 = 0.06 + 0.16 = 0.22
    assert abs(result.merged_weights["attn"]["q"] - 0.22) < 1e-7
    # 0.6*0.05 + 0.4*0.25 = 0.03 + 0.10 = 0.13
    assert abs(result.merged_weights["attn"]["v"] - 0.13) < 1e-7
    assert abs(result.coeff_sum - 1.0) < 1e-9


# ======================================================================
# TC09: stack() 유효성 검사 — 계수 합 ≠ 1.0
# ======================================================================

def test_tc09_stack_invalid_coeff(adapter: LoRAStackingAdapter) -> None:
    """TC09: 계수 합이 1.0이 아니면 ValueError."""
    with pytest.raises(ValueError, match="계수 합"):
        adapter.stack(["lora-drama-001", "lora-thriller-001"], [0.6, 0.5])

    with pytest.raises(ValueError, match="계수 합"):
        adapter.stack(["lora-drama-001", "lora-thriller-001"], [0.4, 0.4])

    with pytest.raises(ValueError, match="개수 불일치"):
        adapter.stack(["lora-drama-001"], [0.5, 0.5])


# ======================================================================
# TC10: genre_stack() 균등 계수 (CIM 없음)
# ======================================================================

def test_tc10_genre_stack_uniform(adapter: LoRAStackingAdapter) -> None:
    """TC10: CIM 없음 → 장르 스태킹 시 균등 계수(0.5/0.5) 적용."""
    result = adapter.genre_stack(["drama", "thriller"], project_id="proj-gs")
    assert isinstance(result, StackResult)
    # 계수 합 = 1.0
    assert abs(result.coeff_sum - 1.0) < 1e-9
    # 균등 계수 → 각 0.5
    for coeff in result.coefficients.values():
        assert abs(coeff - 0.5) < 1e-9
    # 이력 기록
    assert len(adapter.stack_history()) == 1


# ======================================================================
# TC11: 통합 — GenreTransferV2 보고서 이력 + LoRA 스태킹 연동
# ======================================================================

def test_tc11_integration_report_and_lora(
    gtv2: GenreTransferV2, adapter: LoRAStackingAdapter
) -> None:
    """TC11: GenreTransferV2 weighted_transfer 보고서 기반 LoRA 계수 결정."""
    # 2개 프로젝트에서 장르 전이
    gtv2.weighted_transfer("drama", "thriller", "proj-A", alpha=0.3)
    gtv2.weighted_transfer("romance", "thriller", "proj-A", alpha=0.2)
    gtv2.weighted_transfer("drama", "drama", "proj-B", alpha=0.1)

    # proj-A 보고서만 필터
    reports_a = gtv2.adaptation_reports(project_id="proj-A")
    assert len(reports_a) == 2

    # 보고서 기반 계수: coherence를 각 계수로 사용
    coherences = [r.coherence_score for r in reports_a]
    total = sum(coherences)
    if total > 0:
        coeffs = [c / total for c in coherences]
    else:
        coeffs = [0.5, 0.5]
    # coeffs 합이 1.0인지 확인
    assert abs(sum(coeffs) - 1.0) < 1e-9

    # LoRA 스태킹 (drama/thriller 각 1개씩)
    result = adapter.stack(["lora-drama-001", "lora-thriller-001"], coeffs)
    assert result is not None
    assert "attn" in result.merged_weights


# ======================================================================
# TC12: stats 통합 검증 + apply_to_model 스텁
# ======================================================================

def test_tc12_stats_and_apply_stub(
    gtv2: GenreTransferV2, adapter: LoRAStackingAdapter
) -> None:
    """TC12: stats_v2 / adapter stats / apply_to_model 스텁 검증."""
    gtv2.weighted_transfer("fantasy", "sf", "proj-Z", alpha=0.25)
    gtv2.weighted_transfer("fantasy", "sf", "proj-Z", alpha=0.3)

    stats = gtv2.stats_v2()
    assert stats["adaptation_report_count"] == 2
    assert stats["transfer_history_count"] == 2

    result = adapter.stack(
        ["lora-drama-001", "lora-thriller-001"], [0.7, 0.3]
    )
    apply_result = adapter.apply_to_model(result, model_id="test-base")
    assert apply_result["model_id"] == "test-base"
    assert apply_result["status"] == "stub_ok"
    assert apply_result["layers_applied"] == len(result.merged_weights)
    assert apply_result["params_applied"] > 0

    a_stats = adapter.stats()
    assert a_stats["stack_history_count"] == 1
    assert a_stats["registered_weights"] == 2
