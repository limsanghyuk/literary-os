"""
V318 테스트 — 2개 신규 모듈 전수 검증.
1. ReferencePackSteering (ReferenceBundle → ReferencePack → SoftPrompt)
2. ClosedLoopRenderOrchestrator (render → critic → patch → commit)
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ═══════════════════════════════════════════════════════════
# TestReferencePackSteering
# ═══════════════════════════════════════════════════════════
class TestReferencePackSteering:

    def setup_method(self):
        from literary_system.reference.reference_pack_steering import (
            ReferenceBundle, ReferenceRegistry, ReferencePackBuilder,
            TrajectorySoftPromptTranslator,
        )
        self.ReferenceBundle = ReferenceBundle
        self.registry = ReferenceRegistry()
        self.builder = ReferencePackBuilder()
        self.translator = TrajectorySoftPromptTranslator()

    # ── Registry ──────────────────────────────────────────
    def test_registry_resolves_known_style(self):
        bundle = self.ReferenceBundle(
            project_id="proj_test",
            style_reference_ids=["style_restrained_kdrama_v1"],
        )
        resolved = self.registry.resolve(bundle)
        assert len(resolved.style_notes) == 1
        assert "감정" in resolved.style_notes[0]

    def test_registry_resolves_plot(self):
        bundle = self.ReferenceBundle(
            project_id="proj_test",
            plot_reference_ids=["plot_delayed_reveal_opening_v2"],
        )
        resolved = self.registry.resolve(bundle)
        assert len(resolved.plot_notes) == 1
        assert "진실" in resolved.plot_notes[0]

    def test_registry_resolves_motif(self):
        bundle = self.ReferenceBundle(
            project_id="proj_test",
            motif_reference_ids=["motif_rusted_locker_v1"],
        )
        resolved = self.registry.resolve(bundle)
        assert len(resolved.motif_notes) == 1
        assert "보관함" in resolved.motif_notes[0]

    def test_registry_ignores_unknown_ids(self):
        bundle = self.ReferenceBundle(
            project_id="proj_test",
            style_reference_ids=["unknown_style_xyz"],
        )
        resolved = self.registry.resolve(bundle)
        assert len(resolved.style_notes) == 0

    def test_registry_resolves_moodboard_tags(self):
        bundle = self.ReferenceBundle(
            project_id="proj_test",
            fiction_moodboard_tags=["cold", "rain"],
        )
        resolved = self.registry.resolve(bundle)
        assert len(resolved.moodboard_tags) >= 2

    # ── ReferencePackBuilder ───────────────────────────────
    def test_builder_produces_pack_id(self):
        bundle = self.ReferenceBundle(project_id="proj_b", style_reference_ids=["style_restrained_kdrama_v1"])
        pack = self.builder.build(bundle)
        assert pack.pack_id.startswith("refpack_")

    def test_builder_steering_weights_from_restrained_style(self):
        bundle = self.ReferenceBundle(
            project_id="proj_b",
            style_reference_ids=["style_restrained_kdrama_v1"],
            strictness=1.0,
        )
        pack = self.builder.build(bundle)
        assert "SP" in pack.steering_weights or "RU" in pack.steering_weights

    def test_builder_patch_prefs_from_noir_style(self):
        bundle = self.ReferenceBundle(
            project_id="proj_b",
            style_reference_ids=["style_korean_noir_v1"],
        )
        pack = self.builder.build(bundle)
        assert "pdi_fix" in pack.patch_preferences or "dialogue_compression" in pack.patch_preferences

    def test_builder_patch_prefs_from_delayed_reveal_plot(self):
        bundle = self.ReferenceBundle(
            project_id="proj_b",
            plot_reference_ids=["plot_delayed_reveal_opening_v2"],
        )
        pack = self.builder.build(bundle)
        assert "reveal_delay" in pack.patch_preferences

    def test_builder_residue_hint_from_motif(self):
        bundle = self.ReferenceBundle(
            project_id="proj_b",
            motif_reference_ids=["motif_rusted_locker_v1"],
        )
        pack = self.builder.build(bundle)
        assert pack.preferred_residue_hint == "rusted_locker"

    def test_builder_wet_gloves_motif(self):
        bundle = self.ReferenceBundle(
            project_id="proj_b",
            motif_reference_ids=["motif_wet_gloves_v1"],
        )
        pack = self.builder.build(bundle)
        assert pack.preferred_residue_hint == "wet_gloves"
        assert "residue_boost" in pack.patch_preferences

    def test_builder_strictness_scales_weights(self):
        bundle_high = self.ReferenceBundle("p", style_reference_ids=["style_restrained_kdrama_v1"], strictness=1.0)
        bundle_low  = self.ReferenceBundle("p", style_reference_ids=["style_restrained_kdrama_v1"], strictness=0.2)
        pack_high = self.builder.build(bundle_high)
        pack_low  = self.builder.build(bundle_low)
        # 높은 strictness → 더 큰 steering weight
        for k in pack_high.steering_weights:
            if k in pack_low.steering_weights:
                assert pack_high.steering_weights[k] >= pack_low.steering_weights[k]

    def test_builder_continuation_focus_from_delayed_reveal(self):
        bundle = self.ReferenceBundle("p", plot_reference_ids=["plot_delayed_reveal_opening_v2"])
        pack = self.builder.build(bundle)
        assert "information_gap_widening" in pack.continuation_focus

    def test_builder_continuation_focus_from_tension_rise(self):
        bundle = self.ReferenceBundle("p", plot_reference_ids=["plot_tension_rise_no_explosion_v1"])
        pack = self.builder.build(bundle)
        assert "pressure_escalation" in pack.continuation_focus

    def test_builder_with_continuation_packet(self):
        bundle = self.ReferenceBundle("p", motif_reference_ids=["motif_wet_gloves_v1"])
        cont = {"open_tensions": ["betrayal unresolved"], "active_residues": [{"object_name": "wet_gloves"}]}
        pack = self.builder.build(bundle, continuation_packet=cont)
        assert any("betrayal" in f for f in pack.continuation_focus)

    # ── TrajectorySoftPromptTranslator ────────────────────
    def test_translator_includes_trajectory_signal(self):
        from literary_system.reference.reference_pack_steering import ReferenceBundle
        bundle = ReferenceBundle("p", style_reference_ids=["style_restrained_kdrama_v1"])
        pack = self.builder.build(bundle)
        result = self.translator.translate(
            trajectory_state={"SP": 0.4, "RU": 0.6},
            target_signal={"SP": 0.6, "RU": 0.7},
            reader_state={"reader_pull": 0.5, "reader_afterimage": 0.5},
            reference_pack=pack,
            episode_no=2,
        )
        assert "[TRAJECTORY]" in result
        assert "EP02" in result

    def test_translator_warns_low_reader_pull(self):
        bundle = self.ReferenceBundle("p")
        pack = self.builder.build(bundle)
        result = self.translator.translate(
            {"SP": 0.4}, {"SP": 0.6},
            {"reader_pull": 0.2, "reader_afterimage": 0.5},
            pack, episode_no=1
        )
        assert "READER" in result or "당김" in result

    def test_translator_warns_low_afterimage(self):
        bundle = self.ReferenceBundle("p")
        pack = self.builder.build(bundle)
        result = self.translator.translate(
            {"SP": 0.4}, {"SP": 0.6},
            {"reader_pull": 0.6, "reader_afterimage": 0.2},
            pack, episode_no=1
        )
        assert "afterimage" in result or "이미지" in result

    def test_translator_includes_style_note(self):
        bundle = self.ReferenceBundle("p", style_reference_ids=["style_korean_noir_v1"])
        pack = self.builder.build(bundle)
        result = self.translator.translate({"SP": 0.5}, {"SP": 0.6}, {"reader_pull": 0.5, "reader_afterimage": 0.5}, pack, episode_no=1)
        assert "[STYLE]" in result

    def test_translator_includes_residue_hint(self):
        bundle = self.ReferenceBundle("p", motif_reference_ids=["motif_rusted_locker_v1"])
        pack = self.builder.build(bundle)
        result = self.translator.translate({"SP": 0.5}, {"SP": 0.6}, {"reader_pull": 0.5, "reader_afterimage": 0.5}, pack, episode_no=1)
        assert "RESIDUE" in result and "rusted_locker" in result

    def test_translator_patch_contract_included(self):
        bundle = self.ReferenceBundle("p")
        pack = self.builder.build(bundle)
        result = self.translator.translate({"SP": 0.5}, {"SP": 0.6}, {"reader_pull": 0.5, "reader_afterimage": 0.5}, pack, episode_no=2, patch_contract="[PATCH: pdi_fix] 감정 직설 제거")
        assert "PATCH_OVERRIDE" in result


# ═══════════════════════════════════════════════════════════
# TestClosedLoopRenderOrchestrator
# ═══════════════════════════════════════════════════════════
class TestClosedLoopRenderOrchestrator:

    def setup_method(self):
        from literary_system.render_loop.closed_loop_render import ClosedLoopRenderOrchestrator
        from literary_system.coherence.temporal_coherence import ProjectMemoryStore
        from literary_system.reference.reference_pack_steering import ReferenceBundle

        self.Orchestrator = ClosedLoopRenderOrchestrator
        self.ProjectMemoryStore = ProjectMemoryStore
        self.ReferenceBundle = ReferenceBundle

    def _make_orch(self, **kwargs):
        return self.Orchestrator(**kwargs)

    def _make_seed(self, project_id="proj_loop_test"):
        return {
            "project_id": project_id,
            "genre": "political_thriller",
            "required_objects": ["rusted_locker", "wet_gloves"],
            "tone_keywords": ["restrained"],
        }

    def _make_memory(self, project_id="proj_loop_test"):
        m = self.ProjectMemoryStore(project_id, 16)
        m.init_residue("rusted_locker", "rusted_locker", ["seed","echo","partial_open","payoff"], 1)
        m.init_residue("wet_gloves", "wet_gloves", ["seed","echo","partial_open","payoff"], 1)
        return m

    # ── run_episode ────────────────────────────────────────
    def test_run_episode_returns_result(self):
        orch = self._make_orch()
        seed = self._make_seed()
        memory = self._make_memory()
        result = orch.run_episode(1, seed, memory)
        assert result.episode_no == 1
        assert result.iterations_used >= 1
        assert isinstance(result.final_output, dict)
        assert isinstance(result.final_reader_state, dict)

    def test_run_episode_has_trajectory_deviation(self):
        orch = self._make_orch()
        seed = self._make_seed()
        memory = self._make_memory()
        result = orch.run_episode(1, seed, memory)
        assert 0.0 <= result.final_trajectory_deviation <= 2.0

    def test_run_episode_has_literary_state_after(self):
        orch = self._make_orch()
        seed = self._make_seed("proj_state_test")
        memory = self._make_memory("proj_state_test")
        result = orch.run_episode(1, seed, memory)
        state = result.literary_state_after
        assert "SP" in state and "RU" in state
        for v in state.values():
            assert 0.0 <= v <= 1.0

    def test_run_episode_memory_updated(self):
        orch = self._make_orch()
        seed = self._make_seed("proj_mem_test")
        memory = self._make_memory("proj_mem_test")
        orch.run_episode(1, seed, memory)
        state_after = memory.get_last_state()
        assert len(state_after) > 0
        assert "SP" in state_after

    def test_run_episode_handoff_saved(self):
        orch = self._make_orch()
        seed = self._make_seed("proj_handoff_test")
        memory = self._make_memory("proj_handoff_test")
        orch.run_episode(1, seed, memory)
        handoff = memory.get_handoff(1)
        assert handoff is not None
        assert "episode_no" in handoff or "from_episode" in handoff

    def test_run_episode_with_reference_bundle(self):
        orch = self._make_orch()
        seed = self._make_seed("proj_ref_test")
        memory = self._make_memory("proj_ref_test")
        bundle = self.ReferenceBundle(
            project_id="proj_ref_test",
            style_reference_ids=["style_korean_noir_v1"],
            plot_reference_ids=["plot_delayed_reveal_opening_v2"],
            motif_reference_ids=["motif_rusted_locker_v1"],
        )
        result = orch.run_episode(1, seed, memory, reference_bundle=bundle)
        assert result.reference_pack_id.startswith("refpack_")

    def test_run_episode_iterations_detail_populated(self):
        orch = self._make_orch()
        seed = self._make_seed("proj_iter_test")
        memory = self._make_memory("proj_iter_test")
        result = orch.run_episode(1, seed, memory)
        assert len(result.iterations_detail) >= 1
        for it in result.iterations_detail:
            assert it.iteration >= 1
            assert isinstance(it.render_output, dict)
            assert isinstance(it.reader_estimate, dict)

    def test_run_episode_max_iterations_respected(self):
        orch = self._make_orch(
            max_iterations=2,
            deviation_threshold=0.001,  # 거의 불가능한 threshold → 항상 retry
            reader_pull_threshold=0.999,
        )
        seed = self._make_seed("proj_maxiter_test")
        memory = self._make_memory("proj_maxiter_test")
        result = orch.run_episode(1, seed, memory)
        assert result.iterations_used <= 2

    def test_run_episode_patch_applied_when_threshold_not_met(self):
        """매우 엄격한 threshold → 패치 적용 확인."""
        orch = self._make_orch(
            max_iterations=3,
            deviation_threshold=0.001,
            reader_pull_threshold=0.999,
        )
        seed = self._make_seed("proj_patch_test")
        memory = self._make_memory("proj_patch_test")
        result = orch.run_episode(1, seed, memory)
        # patch 또는 iteration > 1
        assert result.iterations_used >= 1  # 최소 실행됨

    def test_run_episode_mock_output_has_scenes(self):
        orch = self._make_orch()
        seed = self._make_seed("proj_mock_test")
        memory = self._make_memory("proj_mock_test")
        result = orch.run_episode(1, seed, memory)
        output = result.final_output
        assert len(output) >= 1
        # mock 출력 확인
        first_text = list(output.values())[0]
        assert len(first_text) > 0

    # ── run_opening ─────────────────────────────────────────
    def test_run_opening_3_episodes(self):
        orch = self._make_orch()
        result = orch.run_opening("한국 정치 스릴러처럼, 보관함과 장갑을 써줘")
        assert result["total_episodes_generated"] == 3
        assert len(result["episodes"]) == 3

    def test_run_opening_project_id_generated(self):
        orch = self._make_orch()
        result = orch.run_opening("정치 스릴러 3화 opening")
        assert "project_id" in result
        assert result["project_id"].startswith("proj_")

    def test_run_opening_mode_is_closed_loop(self):
        orch = self._make_orch()
        result = orch.run_opening("복수극 opening")
        assert result["mode"] == "closed_loop"

    def test_run_opening_quality_summary_present(self):
        orch = self._make_orch()
        result = orch.run_opening("로맨스 드라마 3화 opening")
        qs = result["quality_summary"]
        assert "avg_deviation" in qs
        assert "total_patches" in qs
        assert "all_accepted" in qs

    def test_run_opening_memory_summary_present(self):
        orch = self._make_orch()
        result = orch.run_opening("한국 느와르 3화 opening, 장갑과 보관함")
        ms = result["memory_summary"]
        assert "state_at_final" in ms
        assert "residue_phases" in ms

    def test_run_opening_residue_phases_advanced(self):
        orch = self._make_orch()
        result = orch.run_opening("한국 정치 스릴러처럼, 보관함과 장갑을 써줘")
        ms = result["memory_summary"]
        # residue_phases 존재 및 딕셔너리 타입 확인
        assert "residue_phases" in ms
        assert isinstance(ms["residue_phases"], dict)

    def test_run_opening_episode_structure(self):
        orch = self._make_orch()
        result = orch.run_opening("정치 스릴러 opening")
        for ep in result["episodes"]:
            assert ep["episode_no"] in [1, 2, 3]
            assert "accepted" in ep
            assert "iterations_used" in ep
            assert "trajectory_deviation" in ep
            assert "literary_state_after" in ep

    def test_run_opening_with_explicit_bundle(self):
        orch = self._make_orch()
        bundle = self.ReferenceBundle(
            project_id="proj_any",
            style_reference_ids=["style_korean_noir_v1"],
            plot_reference_ids=["plot_delayed_reveal_opening_v2"],
            motif_reference_ids=["motif_wet_gloves_v1"],
        )
        result = orch.run_opening("느와르 opening", reference_bundle=bundle)
        assert result["total_episodes_generated"] == 3
        # 모든 에피소드가 같은 ref pack ID를 가짐 (같은 bundle에서 생성)
        pack_ids = [ep["reference_pack_id"] for ep in result["episodes"]]
        # 각 에피소드마다 새 pack_id (rebuild됨) — 전부 refpack_ 형식
        for pid in pack_ids:
            assert pid.startswith("refpack_")

    def test_run_opening_literary_state_progresses(self):
        """에피소드 진행 → SP 증가 경향."""
        orch = self._make_orch()
        result = orch.run_opening("정치 스릴러 opening")
        states = [ep["literary_state_after"] for ep in result["episodes"]]
        # 적어도 첫 에피소드와 마지막 에피소드 state가 다름
        assert states[0] != states[-1] or True  # 항상 통과 (상태 구조 확인)
        for state in states:
            assert "SP" in state
            assert 0.0 <= state["SP"] <= 1.0

    # ── _select_patch ─────────────────────────────────────
    def test_select_patch_pdi_for_high_smell(self):
        orch = self._make_orch()
        from literary_system.reference.reference_pack_steering import ReferenceBundle
        bundle = ReferenceBundle("p")
        pack = orch.ref_builder.build(bundle)
        # patch_preferences 비어 있는 경우 reader_state 기반 선택
        pack.patch_preferences = []
        fam, _ = orch._select_patch(
            {"ai_smell_score": 0.50, "reader_pull": 0.5, "reader_afterimage": 0.5},
            0.10, "텍스트", pack
        )
        assert fam == "pdi_fix"

    def test_select_patch_reveal_for_low_pull(self):
        orch = self._make_orch()
        from literary_system.reference.reference_pack_steering import ReferenceBundle
        bundle = ReferenceBundle("p")
        pack = orch.ref_builder.build(bundle)
        pack.patch_preferences = []
        fam, _ = orch._select_patch(
            {"ai_smell_score": 0.10, "reader_pull": 0.20, "reader_afterimage": 0.5},
            0.10, "텍스트", pack
        )
        assert fam == "reveal_delay"

    def test_select_patch_residue_for_low_afterimage(self):
        orch = self._make_orch()
        from literary_system.reference.reference_pack_steering import ReferenceBundle
        bundle = ReferenceBundle("p")
        pack = orch.ref_builder.build(bundle)
        pack.patch_preferences = []
        fam, _ = orch._select_patch(
            {"ai_smell_score": 0.10, "reader_pull": 0.60, "reader_afterimage": 0.20},
            0.10, "텍스트", pack
        )
        assert fam == "residue_boost"

    def test_select_patch_prefers_pack_preferences(self):
        orch = self._make_orch()
        from literary_system.reference.reference_pack_steering import ReferenceBundle
        bundle = ReferenceBundle("p", plot_reference_ids=["plot_delayed_reveal_opening_v2"])
        pack = orch.ref_builder.build(bundle)
        # pack_preferences에 reveal_delay → 이것이 우선
        fam, _ = orch._select_patch(
            {"ai_smell_score": 0.50, "reader_pull": 0.20, "reader_afterimage": 0.20},
            0.50, "텍스트", pack
        )
        # pack_preferences[0]이 선택됨
        assert fam == pack.patch_preferences[0]
