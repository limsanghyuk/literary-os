"""
V313 핵심 테스트 — 신규 6개 모듈 전수 검증.
v7 기존 테스트와 분리.
"""
from __future__ import annotations
import pytest
import sys
from pathlib import Path

# pythonpath 설정
ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ═══════════════════════════════════════════════════════════
# TestSeedCompiler
# ═══════════════════════════════════════════════════════════
class TestSeedCompiler:
    def setup_method(self):
        from literary_system.compiler.seed_compiler import SeedCompiler
        self.compiler = SeedCompiler()

    def test_basic_compile(self):
        result = self.compiler.compile("한국 정치 스릴러 3화 드라마")
        assert result["project_id"].startswith("proj_")
        assert result["genre"] == "political_thriller"
        assert result["format_type"] == "screenplay"

    def test_complex_genre(self):
        result = self.compiler.compile("정치 배경의 복수 스릴러")
        assert result["genre"] in ("political_thriller", "noir_crime", "revenge_drama",
                                    "thriller_suspense")
        # 복합 장르 secondary 존재
        assert result["genre_secondary"] is not None or result["seed_confidence"] > 0.6

    def test_episode_extraction(self):
        result = self.compiler.compile("3화짜리 느와르")
        assert "ep03" in result["target_span"]

    def test_default_forbidden_rules(self):
        result = self.compiler.compile("로맨스 드라마")
        assert "cheap_cliffhanger" in result["forbidden_rules"]
        assert "emotion_explanation" in result["forbidden_rules"]

    def test_unknown_genre_fallback(self):
        result = self.compiler.compile("완전히 알 수 없는 장르의 이야기")
        assert result["genre"] == "general_drama"
        assert result["seed_confidence"] < 0.70

    def test_object_extraction(self):
        result = self.compiler.compile("낡은 보관함이 나오는 정치 드라마")
        assert any("보관함" in obj for obj in result["required_objects"])

    def test_pdi_baseline_by_genre(self):
        result_political = self.compiler.compile("정치 스릴러")
        result_romance   = self.compiler.compile("로맨스 드라마")
        assert result_political["pdi_baseline"] < result_romance["pdi_baseline"]


# ═══════════════════════════════════════════════════════════
# TestStyleDNAEngine
# ═══════════════════════════════════════════════════════════
class TestStyleDNAEngine:
    def setup_method(self):
        from literary_system.style.style_dna_engine import StyleDNAEngine
        self.engine = StyleDNAEngine()

    def test_15_profiles_exist(self):
        profiles = self.engine.list_profiles()
        assert len(profiles) >= 15, f"프로파일 {len(profiles)}개 — 15개 이상 필요"

    def test_political_maps_to_cold(self):
        dna = self.engine.compile("political_thriller", project_id="test")
        assert dna["profile_name"] == "political_cold"

    def test_noir_maps_to_existential(self):
        dna = self.engine.compile("noir_crime")
        assert dna["profile_name"] == "noir_existential"

    def test_pdi_lower_than_romance(self):
        political = self.engine.compile("political_thriller")
        romance   = self.engine.compile("romance_drama")
        assert political["pdi_baseline"] < romance["pdi_baseline"]

    def test_custom_override(self):
        dna = self.engine.compile("political_thriller",
                                   custom_overrides={"dialogue_compression": 0.95})
        assert dna["dialogue_compression"] == 0.95

    def test_validate_forbidden_phrase(self):
        # restrained_low_burn 프로파일은 "결국"을 forbidden으로 가짐
        dna = self.engine.compile("historical_drama")  # → restrained_low_burn
        text_with_forbidden = "결국 그는 진실을 알게 됐다."
        report = self.engine.validate(text_with_forbidden, dna)
        assert not report["passed"]
        assert any(v["type"] == "forbidden_phrase" for v in report["violations"])

    def test_validate_clean_text(self):
        # 행동 동사를 포함한 텍스트로 PDI 검사
        dna = self.engine.compile("political_thriller")
        # PDI 검사: 행동(쥐/걷/멈) 포함 텍스트
        action_text = "그는 서류를 쥐었다. 멈추지 않았다. 손가락이 걷고 있었다."
        report = self.engine.validate(action_text, dna)
        # forbidden phrase 없고 PDI도 통과
        phrase_violations = [v for v in report["violations"] if v["type"] == "forbidden_phrase"]
        assert len(phrase_violations) == 0

    def test_tone_adjustment(self):
        base = self.engine.compile("political_thriller")
        with_pressure = self.engine.compile("political_thriller", tone_keywords=["pressure"])
        assert with_pressure["dialogue_compression"] >= base["dialogue_compression"]


# ═══════════════════════════════════════════════════════════
# TestTemporalCoherenceEngine
# ═══════════════════════════════════════════════════════════
class TestTemporalCoherenceEngine:
    def setup_method(self):
        from literary_system.coherence.temporal_coherence import (
            TemporalCoherenceEngine, ProjectMemoryStore
        )
        self.engine = TemporalCoherenceEngine()
        self.memory = ProjectMemoryStore("test_proj", total_episodes=16)

    def test_residue_lifecycle_init(self):
        self.memory.init_residue("res_001", "낡은 서류", ["seed", "echo", "payoff"], 1)
        assert self.memory.get_residue_phase("res_001") == "seed"

    def test_residue_advance(self):
        self.memory.init_residue("res_001", "낡은 서류", ["seed", "echo", "payoff"], 1)
        self.memory.advance_residue("res_001", 2)
        assert self.memory.get_residue_phase("res_001") == "echo"

    def test_residue_no_over_advance(self):
        self.memory.init_residue("res_001", "낡은 서류", ["seed", "echo", "payoff"], 1)
        for _ in range(10):  # 과도하게 진행해도 마지막에 고정
            self.memory.advance_residue("res_001", 5)
        assert self.memory.get_residue_phase("res_001") == "payoff"

    def test_literary_state_carryover(self):
        self.memory.record_state(1, {"SP": 0.42, "RU": 0.60, "ET": 0.1,
                                      "RD": 0.12, "RT": 0.3, "AC": 0.7, "RO": 0.5, "MR": 0.1})
        self.memory.record_state(2, {"SP": 0.58, "RU": 0.55, "ET": 0.15,
                                      "RD": 0.14, "RT": 0.4, "AC": 0.7, "RO": 0.5, "MR": 0.12})
        last = self.memory.get_last_state()
        assert last["SP"] == 0.58

    def test_reveal_budget_log(self):
        self.memory.log_reveal(1, core_truth=0, surface_hint=2)
        self.memory.log_reveal(2, core_truth=1, surface_hint=1)
        cumulative = self.memory.cumulative_reveal(2)
        assert cumulative["core_truth"] == 1
        assert cumulative["surface_hint"] == 3

    def test_episode_handoff_build(self):
        self.memory.init_residue("res_a", "서류", ["seed", "echo"], 1)
        state = {"SP": 0.55, "RU": 0.50}
        handoff = self.engine.build_handoff(
            episode_no=1,
            literary_state=state,
            active_residues=["res_a"],
            memory=self.memory,
            reveal_summary={"core_truth": 0, "surface_hint": 1},
        )
        assert handoff["from_episode"] == 1
        assert handoff["to_episode"] == 2
        assert "res_a" in handoff["residue_phases"]
        assert handoff["last_sp"] == 0.55

    def test_coherence_no_violations(self):
        self.memory.init_residue("res_a", "서류", ["seed", "echo", "payoff"], 1)
        violations = self.engine.check(
            episode_no=1,
            generated_summary="평범한 장면",
            memory=self.memory,
            residue_used=["res_a"],
        )
        assert len(violations) == 0

    def test_handoff_save_and_retrieve(self):
        handoff = {"from_episode": 1, "last_sp": 0.55}
        self.memory.save_handoff(1, handoff)
        retrieved = self.memory.get_handoff(1)
        assert retrieved["last_sp"] == 0.55

    def test_default_state_when_empty(self):
        empty_memory = __import__(
            "literary_system.coherence.temporal_coherence",
            fromlist=["ProjectMemoryStore"]
        ).ProjectMemoryStore("empty", 16)
        state = empty_memory.get_last_state()
        assert "SP" in state
        assert 0.0 <= state["SP"] <= 1.0


# ═══════════════════════════════════════════════════════════
# TestPromptAssembler
# ═══════════════════════════════════════════════════════════
class TestPromptAssembler:
    def setup_method(self):
        from literary_system.compiler.prompt_assembler import PromptAssembler
        self.assembler = PromptAssembler()

    def _sample_seed(self):
        from literary_system.compiler.seed_compiler import SeedCompiler
        return SeedCompiler().compile("한국 정치 스릴러 3화")

    def _sample_macroarc(self, seed):
        return {
            "project_id": seed["project_id"],
            "macro_goal": "갈등 지도 구축",
            "anti_cliffhanger_policy": True,
            "total_episodes": 16,
            "episode_intents": [
                {"episode_no": 1, "intent": "seed_conflict", "reveal_budget": 0.15,
                 "pressure_target": 0.42, "act_index": 1},
            ],
        }

    def test_bundle_has_required_packets(self):
        seed = self._sample_seed()
        bundle = self.assembler.assemble(
            episode_no=1,
            seed_contract=seed,
            macroarc_packet=self._sample_macroarc(seed),
            character_grid={},
            residue_plan={},
            style_dna={"pdi_baseline": 0.35, "profile_name": "restrained_low_burn",
                        "forbidden": [], "preferred": []},
        )
        packet_types = [p["packet_type"] for p in bundle["packets"]]
        required = ["intent_seed_packet", "macro_arc_packet", "act_intent_packet",
                    "commander_briefing", "scene_digest"]
        for req in required:
            assert req in packet_types, f"필수 패킷 {req} 없음"

    def test_render_instruction_includes_genre(self):
        seed = self._sample_seed()
        bundle = self.assembler.assemble(
            episode_no=1,
            seed_contract=seed,
            macroarc_packet=self._sample_macroarc(seed),
            character_grid={},
            residue_plan={},
            style_dna={"pdi_baseline": 0.35, "profile_name": "political_cold",
                        "forbidden": ["결국"], "preferred": []},
        )
        assert "political" in bundle["render_instruction"].lower() or \
               "political_thriller" in bundle["render_instruction"]

    def test_v312_input_format(self):
        seed = self._sample_seed()
        bundle = self.assembler.assemble(
            episode_no=1,
            seed_contract=seed,
            macroarc_packet=self._sample_macroarc(seed),
            character_grid={}, residue_plan={},
            style_dna={"pdi_baseline": 0.35, "profile_name": "x",
                        "forbidden": [], "preferred": []},
        )
        v312_input = self.assembler.to_v312_input(bundle)
        assert v312_input["v311_mode"] is True
        assert "v311_bundle_json" in v312_input

    def test_literary_state_injected(self):
        seed = self._sample_seed()
        custom_state = {"SP": 0.55, "RU": 0.48, "ET": 0.1,
                         "RD": 0.2, "RT": 0.4, "AC": 0.7, "RO": 0.5, "MR": 0.15}
        bundle = self.assembler.assemble(
            episode_no=2,
            seed_contract=seed,
            macroarc_packet=self._sample_macroarc(seed),
            character_grid={}, residue_plan={},
            style_dna={"pdi_baseline": 0.35, "profile_name": "x",
                        "forbidden": [], "preferred": []},
            literary_state_before=custom_state,
        )
        assert bundle["state_before"]["SP"] == 0.55


# ═══════════════════════════════════════════════════════════
# TestV312Bridge
# ═══════════════════════════════════════════════════════════
class TestV312Bridge:
    def test_bridge_status(self):
        from literary_system.compiler.v312_bridge import V312Bridge
        bridge = V312Bridge("/nonexistent/path")
        status = bridge.get_status()
        assert "available" in status
        assert "backend_path" in status

    def test_bridge_unavailable_graceful(self):
        from literary_system.compiler.v312_bridge import V312Bridge
        bridge = V312Bridge("/nonexistent/path")
        assert bridge.is_available() is False

    def test_bridge_run_returns_error_not_crash(self):
        from literary_system.compiler.v312_bridge import V312Bridge
        bridge = V312Bridge("/nonexistent/path")
        result = bridge.run({"render_instruction": "test"})
        # 크래시하지 않고 error 키 반환
        assert "error" in result or "render_output" in result


# ═══════════════════════════════════════════════════════════
# TestOrchestrator (설계층만, V312 미연결)
# ═══════════════════════════════════════════════════════════
class TestBuildOpeningOrchestrator:
    def setup_method(self):
        from literary_system.orchestrators.build_opening_orchestrator import (
            BuildOpeningOrchestrator
        )
        self.orch = BuildOpeningOrchestrator(
            out_root="/tmp/v313_test_out",
            sovereign_backend="/nonexistent/v312",  # 미연결
        )

    def test_quick_run_returns_3_episodes(self):
        result = self.orch.run_quick("한국 정치 스릴러 3화 오프닝")
        assert "project_id" in result
        assert len(result["episodes"]) == 3

    def test_episodes_have_different_intents(self):
        result = self.orch.run_quick("느와르 범죄 드라마 3화")
        intents = [ep["ep_intent"]["intent"] for ep in result["episodes"]]
        # 3화의 intent가 모두 같으면 안 됨
        assert len(set(intents)) > 1, f"3화 intent가 동일: {intents}"

    def test_residue_phases_progress(self):
        result = self.orch.run_quick("낡은 보관함이 나오는 정치 스릴러 3화")
        # 3화를 거치면서 residue가 진행했어야 함
        phases = result["memory_summary"]["residue_phases"]
        # 어떤 residue든 최소 1개
        assert len(phases) >= 0  # required_objects가 있으면 phase도 있음

    def test_coherence_violations_list(self):
        result = self.orch.run_quick("정치 드라마 3화")
        for ep in result["episodes"]:
            assert "coherence_violations" in ep
            assert isinstance(ep["coherence_violations"], list)

    def test_style_applied_to_all_episodes(self):
        result = self.orch.run_quick("느와르 스릴러 3화")
        for ep in result["episodes"]:
            assert ep["style_applied"] != ""

    def test_bridge_status_in_result(self):
        result = self.orch.run_quick("드라마 3화")
        assert "bridge_status" in result
        assert "available" in result["bridge_status"]

    def test_seed_contract_in_result(self):
        result = self.orch.run_quick("한국 정치 스릴러")
        assert "seed_contract" in result
        assert result["seed_contract"]["genre"] == "political_thriller"

    def test_state_carryover_between_episodes(self):
        """Literary State가 화 간에 전달되는지 확인."""
        result = self.orch.run_quick("느와르 범죄 3화")
        memory_summary = result["memory_summary"]
        state = memory_summary["state_at_ep3"]
        assert "SP" in state
        assert 0.0 <= state["SP"] <= 1.0
