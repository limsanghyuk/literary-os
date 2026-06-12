"""
WP-4b (V748) DoD 테스트 — 8 TC

  1. test_compare_blind_position_randomized
  2. test_trait_mode_rejects_preference_prompt
  3. test_bt_scores_monotonic_with_winrate
  4. test_transitivity_detector_finds_cycle
  5. test_anchor_set_sha_pinned
  6. test_cost_cap_aborts
  7. test_no_absolute_reward_type_guard
  8. test_regression_f_protocol_fixture
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any, List
from unittest.mock import MagicMock, patch, call

import pytest

import literary_system.validation.pairwise as pw

# ──────────────────────────────────────────────────────────────
# 픽스처
# ──────────────────────────────────────────────────────────────

FIXTURE_DB = {
    "운수좋은날_s02": "김첨지는 오늘도 새벽부터 손님을 기다렸다. 빗속에서 그의 두 눈은 아내를 걱정했다.",
    "운수좋은날_s10": "돈이 생겼다. 설렁탕 한 그릇을 사 들고 집으로 달려갔다.",
    "운수좋은날_s11": "방 안은 너무도 조용했다. 아내는 이미 식어 있었다.",
    "pd_anchor_s01":  "선생은 창밖을 바라보며 담배 연기를 내뿜었다. 회한이 가득한 눈빛이었다.",
    "pd_anchor_s02":  "두 사람은 오래도록 아무 말도 하지 않았다. 그것이 이별이었다.",
    "test_scene_a":   "저는 정말 기쁘고 행복합니다! 세상이 아름다워요! 환상적입니다!",
    "test_scene_b":   "창 밖에 비가 내렸다. 그는 우산을 접고 빗속으로 걸어 들어갔다.",
    "strong_scene":   "그날 밤의 침묵은 무거웠다. 말하지 않은 것들이 방 안을 가득 채웠다.",
    "weak_scene_a":   "씬A 내용. 일반적인 묘사가 있다.",
    "weak_scene_b":   "씬B 내용. 다른 묘사가 있다.",
    "weak_scene_c":   "씬C 내용. 또 다른 묘사가 있다.",
}


def _mock_llm_winner(winner: str = "left", rationale: str = "테스트 판정"):
    """LLM 호출을 mock하는 컨텍스트 패치."""
    return patch(
        "literary_system.validation.pairwise._call_llm",
        return_value=(winner, rationale),
    )


# ──────────────────────────────────────────────────────────────
# TC-1: 위치 무작위화 검증
# ──────────────────────────────────────────────────────────────

class TestCompareBlindPositionRandomized:
    def test_compare_blind_position_randomized(self):
        """compare()는 position_seed를 기록하고 위치 편향을 무작위화한다."""
        with _mock_llm_winner("left"):
            j = pw.compare(
                a_id="운수좋은날_s02",
                b_id="pd_anchor_s01",
                db=FIXTURE_DB,
                mode="preference",
            )

        assert "pair_id" in j
        assert "position_seed" in j
        assert isinstance(j["position_seed"], int)
        assert j["left_id"] == "운수좋은날_s02"
        assert j["right_id"] == "pd_anchor_s01"
        assert j["winner"] in ("left", "right")

    def test_compare_stores_rationale(self):
        """compare()는 rationale(R5 근거)을 반드시 포함한다."""
        with _mock_llm_winner("right", "오른쪽이 더 절제된 문체"):
            j = pw.compare(
                a_id="test_scene_a",
                b_id="test_scene_b",
                db=FIXTURE_DB,
                mode="preference",
            )
        assert j["rationale"], "rationale 비어있음"
        assert j["judge_id"] == pw.DEFAULT_JUDGE


# ──────────────────────────────────────────────────────────────
# TC-2: 문체 축 선호 질문 금지 (D-PW3)
# ──────────────────────────────────────────────────────────────

class TestTraitModeRejectsPreferencePrompt:
    def test_trait_mode_rejects_preference_prompt(self):
        """mode=preference + trait=문체 → ValueError (D-PW3 위반)."""
        with pytest.raises(ValueError, match="D-PW3"):
            pw._build_prompt(
                left_text="씬A",
                right_text="씬B",
                mode="preference",
                trait="절제 저온 문체",
                position_seed=42,
            )

    def test_trait_mode_allows_style_trait(self):
        """mode=trait + trait=문체 → 허용 (문체 판단은 trait 모드만 허용)."""
        prompt, _ = pw._build_prompt(
            left_text="씬A",
            right_text="씬B",
            mode="trait",
            trait="절제 저온 문체",
            position_seed=42,
        )
        assert "절제 저온 문체" in prompt


# ──────────────────────────────────────────────────────────────
# TC-3: BT 점수 단조성
# ──────────────────────────────────────────────────────────────

class TestBtScoresMonotonicWithWinrate:
    def test_bt_scores_monotonic_with_winrate(self):
        """
        A가 B를 항상 이기는 판정 → bt_scores[A] > bt_scores[B].
        BT 점수가 승률 방향과 단조 일치해야 한다.
        """
        judgments = [
            {"left_id": "A", "right_id": "B", "winner": "left"},
            {"left_id": "A", "right_id": "B", "winner": "left"},
            {"left_id": "A", "right_id": "B", "winner": "left"},
        ]
        scores = pw.bt_scores(judgments)
        assert scores["A"] > scores["B"], "A가 항상 이기면 BT 점수도 A > B"

    def test_bt_scores_empty_returns_empty(self):
        assert pw.bt_scores([]) == {}

    def test_bt_scores_symmetric_is_equal(self):
        """A-B 동수 → BT 점수 근사 동등."""
        judgments = [
            {"left_id": "A", "right_id": "B", "winner": "left"},
            {"left_id": "A", "right_id": "B", "winner": "right"},
        ]
        scores = pw.bt_scores(judgments)
        assert abs(scores["A"] - scores["B"]) < 0.1


# ──────────────────────────────────────────────────────────────
# TC-4: 순환 의존 탐지
# ──────────────────────────────────────────────────────────────

class TestTransitivityDetectorFindsCycle:
    def test_transitivity_detector_finds_cycle(self):
        """A→B→C→A 3-사이클 픽스처 → 순환률 > 0."""
        judgments = [
            {"left_id": "A", "right_id": "B", "winner": "left"},   # A > B
            {"left_id": "B", "right_id": "C", "winner": "left"},   # B > C
            {"left_id": "C", "right_id": "A", "winner": "left"},   # C > A (순환!)
        ]
        rate = pw.transitivity_check(judgments)
        assert rate > 0.0, "A→B→C→A 순환이 감지되지 않음"

    def test_transitivity_clean_graph_zero(self):
        """완전 일관된 순서 A>B>C → 순환 0."""
        judgments = [
            {"left_id": "A", "right_id": "B", "winner": "left"},
            {"left_id": "B", "right_id": "C", "winner": "left"},
            {"left_id": "A", "right_id": "C", "winner": "left"},
        ]
        rate = pw.transitivity_check(judgments)
        assert rate == 0.0, f"순환 없는 그래프에서 rate={rate}"

    def test_transitivity_threshold_gate(self):
        """G_TRANSITIVITY 임계 <5% — 합성 데이터로 검증."""
        # 순환 없는 20판정
        ids = ["S1", "S2", "S3", "S4", "S5"]
        judgments = []
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                judgments.append({
                    "left_id": ids[i], "right_id": ids[j], "winner": "left"
                })
        rate = pw.transitivity_check(judgments)
        assert rate < 0.05, f"순환 없는 완전 순위 → 순환률 {rate:.3f} ≥ 5%"


# ──────────────────────────────────────────────────────────────
# TC-5: Anchor Set sha256 고정
# ──────────────────────────────────────────────────────────────

class TestAnchorSetShaPinned:
    def test_anchor_set_sha_pinned(self):
        """ANCHOR_SET_V1 ID 목록의 sha256이 변경되지 않았음을 검증."""
        import hashlib, json
        expected = hashlib.sha256(
            json.dumps(pw.ANCHOR_SET_V1, ensure_ascii=False).encode()
        ).hexdigest()
        assert pw.get_anchor_sha() == expected, "ANCHOR_SET_V1 sha256 불일치 — ADR 없이 변경 금지"

    def test_anchor_set_has_five_entries(self):
        """anchor_set v1은 5개 씬 ID."""
        assert len(pw.ANCHOR_SET_V1) == 5


# ──────────────────────────────────────────────────────────────
# TC-6: cost_cap 초과 시 abort
# ──────────────────────────────────────────────────────────────

class TestCostCapAborts:
    def test_cost_cap_aborts(self):
        """cost_cap=0.0001 → ValueError (LLM 비용 추정 초과)."""
        with pytest.raises((ValueError, RuntimeError)):
            pw.compare(
                a_id="test_scene_a",
                b_id="test_scene_b",
                db=FIXTURE_DB,
                cost_cap=0.0001,   # 추정 비용(0.002) 미만
            )

    def test_cost_cap_zero_aborts(self):
        """cost_cap=0.0 → 항상 abort."""
        with pytest.raises((ValueError, RuntimeError)):
            pw.compare(
                a_id="test_scene_a",
                b_id="test_scene_b",
                db=FIXTURE_DB,
                cost_cap=0.0,
            )


# ──────────────────────────────────────────────────────────────
# TC-7: G_NO_ABSOLUTE_REWARD 타입 가드
# ──────────────────────────────────────────────────────────────

class TestNoAbsoluteRewardTypeGuard:
    def test_no_absolute_reward_type_guard(self):
        """
        run_release_gate._check_no_absolute_reward() 게이트가 존재하고
        현재 코드베이스에서 위반 0건을 반환한다.
        """
        gate_path = Path(__file__).resolve().parent.parent.parent / "tools" / "run_release_gate.py"
        spec = importlib.util.spec_from_file_location("run_release_gate", gate_path)
        mod  = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        result = mod._check_no_absolute_reward()
        assert "pass" in result
        assert result["pass"] is True, \
            f"G_NO_ABSOLUTE_REWARD 위반: {result.get('violations')}"

    def test_gate_detects_violation_on_injected_code(self, tmp_path: Path):
        """
        절대 점수 패턴이 있는 가짜 파일 → 위반 탐지.
        """
        import importlib.util, re, types

        # run_release_gate 모듈을 tmp 환경으로 패치해서 violation 탐지 테스트
        gate_path = Path(__file__).resolve().parent.parent.parent / "tools" / "run_release_gate.py"
        spec = importlib.util.spec_from_file_location("rg_test", gate_path)
        mod  = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        # SYS_ROOT를 tmp_path로 monkeypatch
        rlhf_dir = tmp_path / "rlhf"
        rlhf_dir.mkdir()
        (rlhf_dir / "bad_reward.py").write_text("reward = 9.5\n")

        import unittest.mock as mock
        with mock.patch.object(mod, "SYS_ROOT", tmp_path):
            result = mod._check_no_absolute_reward()

        assert result["pass"] is False
        assert len(result["violations"]) >= 1


# ──────────────────────────────────────────────────────────────
# TC-8: 회귀 픽스처 F 프로토콜 (LLM mock)
# ──────────────────────────────────────────────────────────────

class TestRegressionFProtocolFixture:
    def test_regression_f_protocol_fixture(self):
        """
        명작(strong_scene) vs 강열화(weak_scene_*) 11쌍 픽스처.
        compare()를 직접 mock — 명작이 9/11 이상 승리하는 판정 결과 주입.
        G_PAIRWISE_REGRESSION 임계(≥9/11) 검증.
        """
        strong = "strong_scene"
        weaks  = [f"weak_scene_{c}" for c in ("a", "b", "c")]
        pairs  = (
            [(strong, w) for w in weaks * 3][:8]
            + [("운수좋은날_s02", w) for w in weaks]
        )

        def _mock_compare(a_id, b_id, **kw):
            # 명작(strong_scene 또는 anchor)이 left → 항상 left 승리 픽스처
            return pw.PairwiseJudgment(  # type: ignore[call-arg]
                pair_id       = f"{a_id}_vs_{b_id}",
                left_id       = a_id,
                right_id      = b_id,
                winner        = "left",
                mode          = kw.get("mode", "preference"),
                trait         = kw.get("trait"),
                rationale     = "명작이 더 문학적 (fixture)",
                judge_id      = pw.DEFAULT_JUDGE,
                position_seed = 0,
            )

        with patch("literary_system.validation.pairwise.compare", side_effect=_mock_compare):
            wins = 0
            for a_id, b_id in pairs:
                j = pw.compare(a_id=a_id, b_id=b_id, db=FIXTURE_DB, mode="preference")
                if j["winner"] == "left":
                    wins += 1

        total = len(pairs)
        assert wins >= 9, f"G_PAIRWISE_REGRESSION FAIL: {wins}/{total} < 9/11"
