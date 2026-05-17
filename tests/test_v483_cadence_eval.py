"""V483 테스트 — KoreanCadencePlanner + ModelEvalHarness BLEU smoothing."""
from __future__ import annotations
import pytest

from literary_system.prose.korean_cadence_planner import (
    KoreanCadencePlanner, CadencePlan, CadencePattern, DialogueDensity,
)
from literary_system.episode.episode_structure_calculator import (
    EpisodeStructureCalculator, EpisodeStructureConfig,
)
from literary_system.finetune.model_eval_harness import _bleu


# ── KoreanCadencePlanner ─────────────────────────────────────────

class TestKoreanCadencePlanner:
    def _make_planner(self):
        return KoreanCadencePlanner()

    def _make_structure(self, ep_idx=0):
        calc = EpisodeStructureCalculator()
        return calc.calculate(EpisodeStructureConfig(episode_idx=ep_idx))

    # 1. plan() 반환 타입
    def test_plan_returns_cadence_plan(self):
        planner = self._make_planner()
        structure = self._make_structure()
        plan = planner.plan(structure.scenes[0])
        assert isinstance(plan, CadencePlan)

    # 2. plan_episode() 씬 수 일치
    def test_plan_episode_count(self):
        planner = self._make_planner()
        structure = self._make_structure()
        plans = planner.plan_episode(structure)
        assert len(plans) == len(structure.scenes)

    # 3. 콜드 오픈 → STACCATO
    def test_cold_open_staccato(self):
        planner = self._make_planner()
        structure = self._make_structure()
        cold_scene = next(s for s in structure.scenes if s.role.value == "cold_open")
        plan = planner.plan(cold_scene)
        assert plan.cadence_pattern == CadencePattern.STACCATO

    # 4. denouement → REFRAIN
    def test_denouement_refrain(self):
        planner = self._make_planner()
        structure = self._make_structure()
        den_scenes = [s for s in structure.scenes if s.role.value == "denouement"]
        if den_scenes:
            plan = planner.plan(den_scenes[0])
            assert plan.cadence_pattern == CadencePattern.REFRAIN

    # 5. silence_ratio 범위 [0,1]
    def test_silence_ratio_in_range(self):
        planner = self._make_planner()
        structure = self._make_structure()
        for scene in structure.scenes:
            p = planner.plan(scene)
            assert 0.0 <= p.silence_ratio <= 1.0

    # 6. cut_speed_target 양수
    def test_cut_speed_positive(self):
        planner = self._make_planner()
        structure = self._make_structure()
        for scene in structure.scenes:
            p = planner.plan(scene)
            assert p.cut_speed_target > 0

    # 7. to_dict() 키 포함
    def test_to_dict_keys(self):
        planner = self._make_planner()
        structure = self._make_structure()
        p = planner.plan(structure.scenes[0])
        d = p.to_dict()
        for key in ("scene_idx", "cadence_pattern", "dialogue_density",
                    "avg_sentence_length", "cut_speed_target"):
            assert key in d

    # 8. high conflict → STACCATO
    def test_high_conflict_staccato(self):
        planner = self._make_planner()
        structure = self._make_structure()
        # climax 씬 찾기
        climax_scenes = [s for s in structure.scenes if s.role.value == "climax"]
        if climax_scenes:
            plan = planner.plan(climax_scenes[0])
            assert plan.cadence_pattern == CadencePattern.STACCATO

    # 9. cadence_summary() 반환
    def test_cadence_summary(self):
        planner = self._make_planner()
        structure = self._make_structure()
        plans = planner.plan_episode(structure)
        summary = planner.cadence_summary(plans)
        assert "total_scenes" in summary
        assert summary["total_scenes"] == len(plans)

    # 10. avg_sentence_length 양수
    def test_avg_sentence_length_positive(self):
        planner = self._make_planner()
        structure = self._make_structure()
        for scene in structure.scenes:
            p = planner.plan(scene)
            assert p.avg_sentence_length > 0

    # 11. rationale 비어있지 않음
    def test_rationale_not_empty(self):
        planner = self._make_planner()
        structure = self._make_structure()
        p = planner.plan(structure.scenes[0])
        assert len(p.rationale) > 0

    # 12. 마지막 화 (16화) 처리
    def test_final_episode_cadence(self):
        planner = self._make_planner()
        structure = self._make_structure(ep_idx=15)
        plans = planner.plan_episode(structure)
        assert len(plans) == len(structure.scenes)


# ── BLEU Smoothing 수정 확인 ──────────────────────────────────────

class TestBLEUSmoothing:

    # 13. 단문 non-zero BLEU (이전 버그: 0 반환)
    def test_short_text_nonzero_bleu(self):
        """2토큰 가설 — 이전 코드는 고차 n-gram=0으로 0.0 반환했음."""
        score = _bleu("사랑 해요", "사랑 해요")
        assert score > 0.0, "동일 문자열 BLEU가 0이면 smoothing 미적용"

    # 14. 완전 일치 BLEU ≈ 1.0 (BP=1.0)
    def test_perfect_match_bleu(self):
        ref = "사랑 해요 정말"
        score = _bleu(ref, ref)
        assert score >= 0.9, f"완전 일치 BLEU={score}"

    # 15. 완전 불일치 → 낮은 BLEU
    def test_no_match_low_bleu(self):
        score = _bleu("사랑 해요", "밥 먹었어 오늘")
        assert score < 0.5

    # 16. 빈 가설 → 0.0
    def test_empty_hypothesis_zero(self):
        score = _bleu("사랑 해요", "")
        assert score == 0.0

    # 17. 부분 일치 → 0 < BLEU < 1
    def test_partial_match_between_zero_one(self):
        score = _bleu("오늘 날씨 정말 좋다", "오늘 날씨 참 좋네")
        assert 0.0 < score < 1.0, f"BLEU={score}"

    # 18. 단어 순서 다름 → BLEU 감소
    def test_reordered_lower_bleu(self):
        score_same  = _bleu("가 나 다 라", "가 나 다 라")
        score_order = _bleu("가 나 다 라", "라 다 나 가")
        assert score_same > score_order

    # 19. 긴 문장 BLEU 계산 (성능 확인)
    def test_long_text_bleu(self):
        ref = " ".join(["단어"] * 50)
        hyp = " ".join(["단어"] * 48 + ["다른", "말"])
        score = _bleu(ref, hyp)
        assert 0.0 <= score <= 1.0
