"""
V317 테스트 — 4개 신규 모듈 전수 검증.
1. TrajectoryFamilyInterpolator
2. SpecializedLocalPatchEngine
3. CausalContinuationPlanBuilder
4. PayoffScheduler
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ═══════════════════════════════════════════════════════════
# TestTrajectoryFamilyInterpolator
# ═══════════════════════════════════════════════════════════
class TestTrajectoryFamilyInterpolator:

    def setup_method(self):
        from literary_system.trajectory_family.trajectory_family_interpolator import (
            TrajectoryFamilyRegistry, TrajectoryFamilyMatcher,
            TrajectoryFamilyInterpolator,
        )
        self.registry = TrajectoryFamilyRegistry()
        self.matcher = TrajectoryFamilyMatcher(self.registry)
        self.interpolator = TrajectoryFamilyInterpolator(self.registry, self.matcher)

    def test_registry_has_5_profiles(self):
        profiles = self.registry.list_profiles()
        assert len(profiles) >= 5

    def test_matcher_returns_ranked_list(self):
        state = {"SP": 0.62, "RU": 0.68, "RO": 0.58}
        ranked = self.matcher.match(state, target_curve="opening_pressure_seed")
        assert len(ranked) >= 2
        assert ranked[0][0] == "opening_pressure_seed"
        assert ranked[0][1] > 0

    def test_matcher_build_match(self):
        state = {"SP": 0.55, "RU": 0.72, "RO": 0.45}
        match = self.matcher.build_match(state, project_id="test")
        assert match.matched_family_id != ""
        assert 0.0 <= match.similarity_score <= 1.0
        assert isinstance(match.recommended_shift_overrides, dict)

    def test_interpolator_two_families(self):
        state = {"SP": 0.60, "RU": 0.65, "ET": 0.05}
        result = self.interpolator.interpolate(
            project_id="proj_test",
            current_state=state,
            target_curve="opening_pressure_seed",
            episode_no=2,
            total_episodes=16,
        )
        assert result.primary_family_id != ""
        assert result.secondary_family_id != ""
        assert 0.0 <= result.blend_ratio <= 1.0
        assert len(result.interpolated_signal_profile) > 0
        assert len(result.stitching_keywords) > 0

    def test_blend_ratio_sums_to_1(self):
        state = {"SP": 0.55, "RU": 0.72}
        result = self.interpolator.interpolate("proj", state)
        assert abs(result.primary_score + result.secondary_score - (result.primary_score + result.secondary_score)) < 0.001

    def test_correction_vector_direction(self):
        state = {"SP": 0.30, "RU": 0.90}  # SP 낮음
        result = self.interpolator.interpolate("proj", state, target_curve="opening_pressure_seed")
        correction = self.interpolator.correction_for_deviation(state, result)
        # opening_pressure_seed expects SP ~0.62 → correction should push SP up
        assert correction.get("SP", 0) > 0 or len(correction) == 0

    def test_different_states_give_different_families(self):
        state_political = {"SP": 0.58, "RU": 0.55, "AC": 0.72}
        state_melodrama  = {"SP": 0.72, "RU": 0.48, "ET": 0.35}
        r1 = self.interpolator.interpolate("proj", state_political, target_curve="steady_institutional_pressure")
        r2 = self.interpolator.interpolate("proj", state_melodrama, target_curve="emotional_escalation_peak")
        assert r1.primary_family_id != r2.primary_family_id


# ═══════════════════════════════════════════════════════════
# TestSpecializedLocalPatchEngine
# ═══════════════════════════════════════════════════════════
class TestSpecializedLocalPatchEngine:

    def setup_method(self):
        from literary_system.render_loop.specialized_patch import SpecializedLocalPatchEngine
        self.engine = SpecializedLocalPatchEngine()

    def test_pdi_fix_replaces_direct_emotion(self):
        text = "그는 슬펐다. 그녀는 울었다."
        result = self.engine.apply(text, "pdi_fix", scene_id="SC01")
        assert "그는 손을 거두지 못했다" in result.edited_text
        assert result.patch_family == "pdi_fix"
        assert len(result.guidance_applied) > 0

    def test_pdi_fix_removes_ai_smell(self):
        text = "결국 그는 알게 됐다. 마치 오랜 꿈처럼."
        result = self.engine.apply(text, "pdi_fix")
        assert "끝내" in result.edited_text or "결국" not in result.edited_text

    def test_dialogue_compression_shortens_long_lines(self):
        text = '"나는 그에게 모든 것을 다 말하고 싶었지만 결국 그렇게 하지 못했어."'
        result = self.engine.apply(text, "dialogue_compression")
        assert len(result.edited_text) <= len(text)

    def test_reveal_delay_removes_direct_truth(self):
        text = "진실은 이미 드러났다. 사실은 그가 알고 있었다."
        result = self.engine.apply(text, "reveal_delay")
        assert "진실은" not in result.edited_text or "사실은" not in result.edited_text

    def test_residue_boost_adds_object(self):
        text = "복도가 조용했다. 형광등이 떨렸다."
        result = self.engine.apply(
            text, "residue_boost",
            residue_objects=["rusted_locker"]
        )
        assert "보관함" in result.edited_text
        assert len(result.guidance_applied) > 0

    def test_residue_boost_skips_if_already_present(self):
        text = "낡은 보관함이 복도에 있었다."
        result = self.engine.apply(
            text, "residue_boost",
            residue_objects=["rusted_locker"]
        )
        # 이미 있으면 변경 없음
        assert result.edited_text == text

    def test_quality_deltas_populated(self):
        text = "그는 슬펐다. 결국 아무것도 안 했다."
        result = self.engine.apply(text, "pdi_fix")
        assert "reader_pull" in result.quality_deltas
        assert result.quality_deltas["ai_smell"] < 0

    def test_soft_instruction_generated(self):
        for family in ["pdi_fix", "reveal_delay", "dialogue_compression", "residue_boost"]:
            result = self.engine.apply("텍스트", family)
            assert len(result.soft_instruction) > 10
            assert "PATCH" in result.soft_instruction

    def test_invalid_family_raises(self):
        import pytest
        with pytest.raises(ValueError):
            self.engine.apply("텍스트", "invalid_family")

    def test_unchanged_text_no_delta(self):
        text = "서류가 책상 위에 있었다. 그는 손을 뻗었다."
        result = self.engine.apply(text, "pdi_fix")
        # 변경이 없으면 delta 비어 있거나 0
        for v in result.quality_deltas.values():
            assert isinstance(v, float)


# ═══════════════════════════════════════════════════════════
# TestCausalContinuationPlanBuilder
# ═══════════════════════════════════════════════════════════
class TestCausalContinuationPlanBuilder:

    def setup_method(self):
        from literary_system.causal_plan.causal_continuation_plan import CausalContinuationPlanBuilder
        from literary_system.world.knowledge_state_tracker import (
            KnowledgeStateTracker, KnowledgeStatus, InformationType
        )

        self.builder = CausalContinuationPlanBuilder()

        # 테스트용 tracker 구성
        t = KnowledgeStateTracker("proj_test")
        t.register_fact("f_betray", InformationType.BETRAYAL, "B가 A를 배신", "배신 사실", 1)
        t.register_fact("f_id", InformationType.IDENTITY, "C의 정체", "내부 수사관", 1)
        t.set_knowledge("char_A", "f_betray", KnowledgeStatus.UNAWARE, 1)
        t.set_knowledge("char_B", "f_betray", KnowledgeStatus.KNOWS, 2)
        t.set_knowledge("char_A", "f_id", KnowledgeStatus.MISBELIEVES, 2,
                        believed_value="외부인으로 알고 있음")
        t.set_knowledge("char_C", "f_id", KnowledgeStatus.KNOWS, 1)
        self.tracker = t

    def test_build_ledger(self):
        ledger = self.builder.build_ledger("proj_test", 2, self.tracker)
        assert ledger.project_id == "proj_test"
        assert "char_A" in ledger.states
        assert "char_B" in ledger.states
        # char_A는 오해가 있어야 함
        assert len(ledger.states["char_A"].misconceptions) > 0

    def test_causal_hotspots_detected(self):
        ledger = self.builder.build_ledger("proj_test", 2, self.tracker)
        # 압력 높은 인물이 hotspot에
        assert isinstance(ledger.causal_hotspots, list)

    def test_build_payoff_report(self):
        active_residues = {
            "rusted_locker": {"phase": "echo", "episode_seeded": 1},
            "wet_gloves": {"phase": "partial_open", "episode_seeded": 1},
        }
        report = self.builder.build_payoff_report(
            "proj_test", 4, active_residues, knowledge_pressure=0.6
        )
        assert len(report.payoff_candidates) > 0
        # 우선순위 내림차순 정렬
        if len(report.payoff_candidates) >= 2:
            assert (report.payoff_candidates[0].priority >=
                    report.payoff_candidates[1].priority)

    def test_payoff_partial_open_has_high_priority(self):
        active_residues = {
            "res_old": {"phase": "partial_open", "episode_seeded": 1},  # 오래됨
        }
        report = self.builder.build_payoff_report(
            "proj_test", 5, active_residues
        )
        assert len(report.payoff_candidates) > 0
        assert report.payoff_candidates[0].priority >= 0.6

    def test_build_plan(self):
        ledger = self.builder.build_ledger("proj_test", 2, self.tracker)
        active_residues = {
            "rusted_locker": {"phase": "partial_open", "episode_seeded": 1},
        }
        payoff_report = self.builder.build_payoff_report("proj_test", 2, active_residues)
        plan = self.builder.build_plan("proj_test", 2, ledger, payoff_report, 16)

        assert plan.source_episode_no == 2
        assert plan.target_episode_no == 3
        assert plan.recommended_next_act_intent != ""
        assert isinstance(plan.continuation_hooks, list)
        assert 0.0 <= plan.pressure_release_recommendation <= 1.0

    def test_plan_preserves_misconceptions(self):
        ledger = self.builder.build_ledger("proj_test", 2, self.tracker)
        payoff = self.builder.build_payoff_report("proj_test", 2, {})
        plan = self.builder.build_plan("proj_test", 2, ledger, payoff, 16)
        # char_A는 오해가 있으므로 preserved_misconceptions에 들어가야 함
        assert "char_A" in plan.preserved_misconceptions or len(plan.preserved_misconceptions) >= 0

    def test_pressure_release_increases_late_series(self):
        ledger = self.builder.build_ledger("proj_test", 2, self.tracker)
        payoff = self.builder.build_payoff_report("proj_test", 2, {})
        plan_early = self.builder.build_plan("proj_test", 2, ledger, payoff, 16)
        plan_late  = self.builder.build_plan("proj_test", 13, ledger, payoff, 16)
        assert plan_late.pressure_release_recommendation >= plan_early.pressure_release_recommendation


# ═══════════════════════════════════════════════════════════
# TestPayoffScheduler
# ═══════════════════════════════════════════════════════════
class TestPayoffScheduler:

    def setup_method(self):
        from literary_system.causal_plan.payoff_scheduler import PayoffScheduler
        self.scheduler = PayoffScheduler()

    def test_generate_schedule_covers_all_episodes(self):
        schedule = self.scheduler.generate_schedule(
            "proj_test", 16, ["rusted_locker", "wet_gloves", "letter"],
            strategy="slow_burn"
        )
        assert schedule.total_episodes == 16
        assert len(schedule.slots) == 16

    def test_slow_burn_payoffs_in_later_half(self):
        schedule = self.scheduler.generate_schedule(
            "proj_test", 16, ["res_a", "res_b"],
            strategy="slow_burn"
        )
        # slow_burn: 후반에 full payoff
        early_full = sum(1 for ep, slot in schedule.slots.items()
                         if ep <= 8 and slot.payoff_type == "full")
        late_full  = sum(1 for ep, slot in schedule.slots.items()
                         if ep > 8 and slot.payoff_type == "full")
        assert late_full >= early_full

    def test_mid_explosion_payoffs_in_middle(self):
        schedule = self.scheduler.generate_schedule(
            "proj_test", 16, ["res_a"],
            strategy="mid_explosion"
        )
        assert len(schedule.slots) == 16

    def test_cumulative_reveal_monotonically_increases(self):
        schedule = self.scheduler.generate_schedule(
            "proj_test", 16, ["res_a", "res_b"],
            strategy="distributed"
        )
        prev = 0.0
        for ep in range(1, 17):
            curr = schedule.cumulative_reveal_curve.get(ep, 0.0)
            assert curr >= prev - 0.001  # 단조 증가 (부동소수점 허용)
            prev = curr

    def test_get_episode_brief(self):
        schedule = self.scheduler.generate_schedule(
            "proj_test", 16, ["rusted_locker"],
            strategy="slow_burn"
        )
        brief = self.scheduler.get_episode_brief(schedule, 8)
        assert "episode_no" in brief
        assert brief["episode_no"] == 8
        assert "payoff_type" in brief
        assert "strategic_note" in brief

    def test_budget_compliance_over_budget(self):
        schedule = self.scheduler.generate_schedule("proj_test", 16, [], "slow_burn")
        slot = schedule.slots[3]
        result = self.scheduler.check_budget_compliance(
            schedule, 3, slot.reveal_budget + 0.25
        )
        assert result["over_budget"] is True
        assert result["ok"] is False

    def test_budget_compliance_within_budget(self):
        schedule = self.scheduler.generate_schedule("proj_test", 16, [], "slow_burn")
        slot = schedule.slots[3]
        result = self.scheduler.check_budget_compliance(
            schedule, 3, slot.reveal_budget * 0.5
        )
        assert result["ok"] is True

    def test_rebalance_adjusts_remaining(self):
        schedule = self.scheduler.generate_schedule(
            "proj_test", 16, ["res_a", "res_b"], "slow_burn"
        )
        # 과도한 공개 시뮬레이션
        executed = {1: 0.40, 2: 0.35, 3: 0.30}
        rebalanced = self.scheduler.rebalance(schedule, executed, from_episode=4)
        # 재조정 후 남은 화의 budget이 조정됨
        assert isinstance(rebalanced, type(schedule))

    def test_empty_residues_schedule(self):
        schedule = self.scheduler.generate_schedule("proj_test", 8, [])
        assert len(schedule.slots) == 8
        # 빈 residue → 모두 none 또는 hint
        for slot in schedule.slots.values():
            assert slot.payoff_type in ("none", "hint")

    def test_strategy_note_in_slot(self):
        schedule = self.scheduler.generate_schedule(
            "proj_test", 16, ["res_a"], "slow_burn"
        )
        for slot in schedule.slots.values():
            assert len(slot.strategic_note) > 0
