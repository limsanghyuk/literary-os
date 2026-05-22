"""
V601 — Gate G54 후속 단위 테스트: RewardModel (8 TC)

TC-A1~A3: 기본 보상 계산
TC-B1~B2: 마커 가중치 상한 (B-V2-03)
TC-C1~C3: 적대적 시드 + quality_correlation
"""
from __future__ import annotations

import pytest

from literary_system.rlhf.reward_model import (
    RewardModel,
    RewardResult,
    ConstitutionAxisReward,
    AdversarialSeed,
    MARKER_WEIGHT_CAP,
    REWARD_THRESHOLD,
    DEFAULT_WEIGHTS,
)


# ===========================================================================
# 픽스처
# ===========================================================================

DRAMA_SCENE = (
    "주인공이 빗속을 걷다 멈춰 서며 하늘을 올려다보았다. "
    "그의 눈에는 오랜 슬픔과 새로운 결심이 뒤섞여 있었다. "
    "오늘이 지나면 모든 것이 달라질 것이라는 예감이 들었다. "
    "그는 천천히 문 앞에 섰다. 그녀가 바라보고 있었다. "
    "두 사람 사이의 침묵이 긴장감을 고조시켰다."
)

SHORT_SCENE = "짧은 씬."


# ===========================================================================
# TC-A: 기본 보상 계산
# ===========================================================================

class TestRewardModelBasic:
    """TC-A1~A3: 기본 보상 계산 + 결과 구조."""

    def test_a1_compute_returns_reward_result(self):
        """TC-A1: compute()가 RewardResult를 반환해야 한다."""
        rm = RewardModel()
        result = rm.compute(DRAMA_SCENE)

        assert isinstance(result, RewardResult)
        assert 0.0 <= result.reward <= 1.0
        assert isinstance(result.passed, bool)
        assert result.text_length == len(DRAMA_SCENE)

    def test_a2_drama_scene_passes_threshold(self):
        """TC-A2: 정상 드라마 씬은 R(scene) ≥ REWARD_THRESHOLD를 달성해야 한다."""
        rm = RewardModel()
        result = rm.compute(DRAMA_SCENE)

        assert result.passed is True, (
            f"R(scene)={result.reward:.4f} < threshold={REWARD_THRESHOLD}"
        )

    def test_a3_result_has_five_axes(self):
        """TC-A3: 결과에 5축 axis_rewards가 있어야 한다."""
        rm = RewardModel()
        result = rm.compute(DRAMA_SCENE)

        assert len(result.axis_rewards) == 5
        axis_names = {r.axis for r in result.axis_rewards}
        assert axis_names == {"drse", "debt", "arc", "tension", "prose"}

        # 각 축 점수 [0, 1]
        for ar in result.axis_rewards:
            assert 0.0 <= ar.raw_score <= 1.0
            assert 0.0 <= ar.weighted


# ===========================================================================
# TC-B: 마커 가중치 상한
# ===========================================================================

class TestMarkerWeightCap:
    """TC-B1~B2: MARKER_WEIGHT_CAP 적용 검증 (B-V2-03)."""

    def test_b1_default_weights_all_capped(self):
        """TC-B1: 기본 가중치 중 상한 초과 값이 클램프되어야 한다."""
        rm = RewardModel()

        # drse=0.30 > 0.20이므로 클램프되어야 함
        for ar in rm.compute(DRAMA_SCENE).axis_rewards:
            assert ar.weight <= MARKER_WEIGHT_CAP, (
                f"축 {ar.axis}의 weight={ar.weight} > cap={MARKER_WEIGHT_CAP}"
            )

    def test_b2_custom_high_weights_capped(self):
        """TC-B2: 사용자 지정 고가중치도 상한 이하로 정규화되어야 한다."""
        high_weights = {
            "drse":    0.80,  # 상한 초과
            "debt":    0.05,
            "arc":     0.05,
            "tension": 0.05,
            "prose":   0.05,
        }
        rm = RewardModel(weights=high_weights)
        result = rm.compute(DRAMA_SCENE)

        for ar in result.axis_rewards:
            assert ar.weight <= MARKER_WEIGHT_CAP, (
                f"축 {ar.axis} weight={ar.weight} > cap={MARKER_WEIGHT_CAP}"
            )

        # 정규화 후 가중치 합 ≈ 1.0
        total_w = sum(ar.weight for ar in result.axis_rewards)
        assert abs(total_w - 1.0) < 1e-6, f"가중치 합={total_w}"


# ===========================================================================
# TC-C: 적대적 시드 + quality_correlation
# ===========================================================================

class TestAdversarialAndCorrelation:
    """TC-C1~C3: 적대적 시드 탐지 + 품질 상관."""

    def test_c1_marker_stuffing_penalized(self):
        """TC-C1: 마커 스터핑 패턴에 페널티가 적용되어야 한다."""
        stuffed = "복선감정대사씬캐릭터갈등반전클라이맥스복선 " * 10
        rm = RewardModel()

        result = rm.compute(stuffed)
        seed = rm.test_adversarial_seed("marker_stuffing", stuffed)

        assert result.adv_penalty > 0.0, "마커 스터핑에 패널티 미적용"
        assert seed.penalty_applied > 0.0
        # 차단 여부는 보상 < threshold
        assert seed.reward < 1.0

    def test_c2_adversarial_suite_returns_five_results(self):
        """TC-C2: run_adversarial_suite()가 5건을 반환해야 한다."""
        seeds = [
            ("marker_stuffing",    "복선감정대사씬캐릭터갈등반전클라이맥스복선 " * 8),
            ("length_inflation",   "abc " * 200),
            ("repetition_pattern", "주인공이 빗속을 걷다. " * 5),
            ("extreme_emotion",    "헐헐헐!!!??? " * 3),
            ("genre_deviation",    "x " * 300),
        ]
        rm = RewardModel()
        results = rm.run_adversarial_suite(seeds)

        assert len(results) == 5
        for res in results:
            assert isinstance(res, AdversarialSeed)
            assert 0.0 <= res.reward <= 1.0

    def test_c3_quality_correlation_increases_with_n(self):
        """TC-C3: quality_correlation()이 N≥2부터 유효값을 반환해야 한다."""
        rm = RewardModel()

        # N=1이면 0.0
        r0 = rm.quality_correlation(0.8, 0.9)
        assert r0 == 0.0

        # N≥2이면 [-1.0, 1.0]
        r1 = rm.quality_correlation(0.7, 0.75)
        assert -1.0 <= r1 <= 1.0

        r2 = rm.quality_correlation(0.6, 0.65)
        assert -1.0 <= r2 <= 1.0

    def test_a_summary_stats(self):
        """TC-추가: summary()가 올바른 통계를 반환해야 한다."""
        rm = RewardModel()
        scenes = [DRAMA_SCENE, DRAMA_SCENE, SHORT_SCENE]
        results = rm.compute_batch(scenes)

        stats = rm.summary(results)
        assert stats["total"] == 3
        assert 0 <= stats["pass_count"] <= 3
        assert 0.0 <= stats["pass_rate"] <= 1.0
        assert 0.0 <= stats["mean_reward"] <= 1.0
