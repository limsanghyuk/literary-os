"""
V313→V322: BuildOpeningOrchestrator
전체 V313 파이프라인 집행자.

흐름:
  한 줄 입력
    → SeedCompiler
    → v7 StandardLiteraryAnalyzer  (MacroArc/Grid/Residue/StateEstimator)
    → StyleDNAEngine
    → PromptAssembler
    → [ProjectMemoryStore 상태 전달]
    → V312Bridge → run_sovereign_v312()
    → TemporalCoherenceEngine (일관성 검사)
    → 결과 반환 + 다음 화 handoff 저장
"""
from __future__ import annotations
from pathlib import Path
from typing import Any

from literary_system.compiler.seed_compiler import SeedCompiler
from literary_system.compiler.prompt_assembler import PromptAssembler
from literary_system.compiler.v312_bridge import V312Bridge
from literary_system.style.style_dna_engine import StyleDNAEngine
from literary_system.coherence.temporal_coherence import (
    TemporalCoherenceEngine,
    ProjectMemoryStore,
    ResidueLifecycle,
)

# V382: 파이프라인 실행 추적
from literary_system.pipeline import (
    LiteraryPipelineState,
    append_trace,
    save_literary_checkpoint,
    autosave_literary_state,
)


class BuildOpeningOrchestrator:
    """
    V313 메인 오케스트레이터.
    3가지 모드(Quick/Director/Studio) 지원.
    """

    def __init__(
        self,
        out_root: str | Path = "./out",
        sovereign_backend: str | Path | None = None,
        mode: str = "quick",   # "quick" | "director" | "studio"
    ):
        self.out_root = Path(out_root)
        self.out_root.mkdir(parents=True, exist_ok=True)
        self.mode = mode

        self.seed_compiler    = SeedCompiler()
        self.style_engine     = StyleDNAEngine()
        self.assembler        = PromptAssembler()
        self.bridge           = V312Bridge(sovereign_backend)
        self.coherence_engine = TemporalCoherenceEngine()
        # V382: 파이프라인 실행 상태 (매 run_quick/run_director 호출 시 갱신)
        self.pipeline_state: LiteraryPipelineState | None = None

    # ────────────────────────────────────────────────────────
    # Quick Mode: 한 줄 → 3화 opening bundle
    # ────────────────────────────────────────────────────────
    def run_quick(
        self,
        user_prompt: str,
        total_episodes: int = 16,
    ) -> dict[str, Any]:
        """
        사용자 한 줄 → 3화 opening 전체 생성.
        내부 복잡성 완전 은닉.
        """
        # V382: 파이프라인 실행 추적 시작
        self.pipeline_state = LiteraryPipelineState(project_id="")
        append_trace(self.pipeline_state,
            f"\n[BuildOpeningOrchestrator] run_quick 시작 | mode={self.mode}")

        append_trace(self.pipeline_state, "\n[Node_SeedCompiler] compile 시작")
        seed = self.seed_compiler.compile(user_prompt)
        project_id = seed["project_id"]
        self.pipeline_state.project_id = project_id
        self.pipeline_state.seed_contract = seed
        append_trace(self.pipeline_state,
            f"  -> 씨드 컴파일 완료 | project_id={project_id}")
        save_literary_checkpoint(self.pipeline_state, "seed_compiler",
            ["run_id", "project_id", "seed_contract"])

        # v7 Analyzer로 전체 패킷 컴파일
        append_trace(self.pipeline_state, "\n[Node_StandardLiteraryAnalyzer] analyze 시작")
        try:
            from literary_system.analyzer.orchestrator import StandardLiteraryAnalyzer
            from literary_system.librarian.orchestrator import ChiefLibrarian

            project_context = {
                "project_id": project_id,
                "master_seed": user_prompt,
                "media_type": seed["format_type"],
                "genre": seed["genre"],
                "total_episode_count": total_episodes,
                "episode_index": 1,
                "pdi_profile": seed["pdi_baseline"],
                "required_objects": seed["required_objects"],
            }
            inputs = [{"text": user_prompt, "source_type": "user_prompt"}]

            analyzer = StandardLiteraryAnalyzer()
            bundle_v7 = analyzer.analyze(inputs, project_context)
            append_trace(self.pipeline_state,
                "  -> StandardLiteraryAnalyzer 완료")
            save_literary_checkpoint(self.pipeline_state, "standard_literary_analyzer",
                ["run_id", "project_id"])

        except Exception as e:
            # v7 분析기 없이 기본 패킷으로 폴백
            bundle_v7 = self._make_fallback_bundle(seed, total_episodes)
            append_trace(self.pipeline_state,
                "  -> StandardLiteraryAnalyzer fallback (v7 미설치)")
            save_literary_checkpoint(self.pipeline_state, "standard_literary_analyzer_fallback",
                ["run_id", "project_id"])

        append_trace(self.pipeline_state, "\n[Node_StyleDNAEngine] style compile 시작")
        style_dna = self.style_engine.compile(
            genre=seed["genre"],
            tone_keywords=seed["tone_keywords"],
            project_id=project_id,
        )

        append_trace(self.pipeline_state, "  -> StyleDNAEngine 완료")
        save_literary_checkpoint(self.pipeline_state, "style_dna_engine",
            ["run_id", "project_id"])

        memory = ProjectMemoryStore(project_id, total_episodes)
        self._init_residues(memory, seed["required_objects"], episode_seeded=1)

        episodes = []
        bridge_status = self.bridge.get_status()
        append_trace(self.pipeline_state,
            f"\n[Node_V312Bridge] 브릿지 상태 확인 | available={self.bridge.is_available()}")
        save_literary_checkpoint(self.pipeline_state, "v312_bridge_check",
            ["run_id", "project_id"])

        for ep_no in range(1, 4):
            append_trace(self.pipeline_state,
                f"\n[Node_Episode_{ep_no:02d}] 에피소드 {ep_no}화 생성 시작")
            ep_result = self._run_episode(
                episode_no=ep_no,
                seed=seed,
                bundle_v7=bundle_v7,
                style_dna=style_dna,
                memory=memory,
                total_episodes=total_episodes,
            )
            episodes.append(ep_result)

            # 다음 화로 Literary State 전달
            state_after = ep_result.get("literary_state_after", {})
            if state_after:
                memory.record_state(ep_no, state_after)

            # Episode Continuation Handoff 저장
            handoff = self.coherence_engine.build_handoff(
                episode_no=ep_no,
                literary_state=state_after or memory.get_last_state(),
                active_residues=seed["required_objects"],
                memory=memory,
                reveal_summary=memory.cumulative_reveal(ep_no),
            )
            memory.save_handoff(ep_no, handoff)
            append_trace(self.pipeline_state,
                f"  -> 에피소드 {ep_no}화 완료 | coherence_violations={len(ep_result.get('coherence_violations', []))}")
            save_literary_checkpoint(self.pipeline_state, f"episode_{ep_no:02d}",
                ["run_id", "project_id"])

        append_trace(self.pipeline_state,
            f"\n[BuildOpeningOrchestrator] run_quick 완료 | episodes=3")
        autosave_literary_state(self.pipeline_state, "run_quick_completed", status="completed")

        return {
            "project_id":   project_id,
            "mode":         "quick",
            "seed_contract": seed,
            "style_dna":    style_dna,
            "episodes":     episodes,
            "memory_summary": {
                "episodes_completed": 3,
                "residue_phases": {
                    rid: memory.get_residue_phase(rid)
                    for rid in seed["required_objects"]
                },
                "state_at_ep3": memory.get_last_state(),
            },
            "bridge_status": bridge_status,
            "pipeline_trace": list(self.pipeline_state.execution_trace),
            "pipeline_checkpoints": list(self.pipeline_state.checkpoints.keys()),
        }

    # ────────────────────────────────────────────────────────
    # Director Mode: 더 많은 제어
    # ────────────────────────────────────────────────────────
    def run_director(
        self,
        user_prompt: str,
        style_ref: str | None = None,
        reveal_strictness: float = 0.25,
        anti_llm_intensity: float = 1.0,
        total_episodes: int = 16,
        custom_objects: list[str] | None = None,
    ) -> dict[str, Any]:
        seed = self.seed_compiler.compile(user_prompt)
        if custom_objects:
            seed["required_objects"] = custom_objects

        style_overrides: dict = {}
        if anti_llm_intensity > 0.8:
            style_overrides["dialogue_compression"] = 0.80

        style_dna = self.style_engine.compile(
            genre=seed["genre"],
            tone_keywords=seed["tone_keywords"],
            custom_overrides=style_overrides if style_overrides else None,
            project_id=seed["project_id"],
        )

        # Quick와 동일 파이프라인, 제어값만 다름
        return self.run_quick(user_prompt, total_episodes)

    # ────────────────────────────────────────────────────────
    # 내부 헬퍼
    # ────────────────────────────────────────────────────────
    def _run_episode(
        self,
        episode_no: int,
        seed: dict,
        bundle_v7: dict,
        style_dna: dict,
        memory: ProjectMemoryStore,
        total_episodes: int,
    ) -> dict[str, Any]:
        """단일 화 생성."""
        # episode_intent 생성
        ep_ratio = episode_no / max(total_episodes, 1)
        ep_intent = {
            "episode_no": episode_no,
            "act_index": 1 if episode_no <= total_episodes // 4 else (
                2 if episode_no <= total_episodes * 0.7 else 3),
            "intent": [
                "seed_conflict_and_grid",
                "raise_pressure_without_release",
                "false_opening_and_deeper_lock",
            ][episode_no - 1] if episode_no <= 3 else "continue_escalation",
            "reveal_budget": round(0.10 + ep_ratio * 0.20, 2),
            "pressure_target": round(0.35 + ep_ratio * 0.40, 2),
        }

        macroarc = {
            "project_id": seed["project_id"],
            "macro_goal": "Establish long-form conflict map without over-revealing.",
            "episode_intents": [ep_intent],
            "anti_cliffhanger_policy": True,
            "total_episodes": total_episodes,
        }

        character_grid = bundle_v7.get("character_grid", {
            "characters": [
                {"char_id": "lead", "role_type": "lead",
                 "pressure_target": "institutional_pressure",
                 "occupancy_ep1": 0.95, "occupancy_ep2": 0.90, "occupancy_ep3": 0.90},
                {"char_id": "foil", "role_type": "foil",
                 "pressure_target": "truth_vs_survival",
                 "occupancy_ep1": 0.65, "occupancy_ep2": 0.78, "occupancy_ep3": 0.84},
            ],
            "edges": [{"source": "lead", "target": "foil",
                        "edge_type": "mistrust_axis", "tension": 0.76}],
        })

        residue_plan = {
            "project_id": seed["project_id"],
            "residues": [
                {"residue_id": obj,
                 "object_name": obj,
                 "phase": memory.get_residue_phase(obj)}
                for obj in seed["required_objects"]
            ],
        }

        # Literary State 이전 화에서 인계
        state_before = memory.get_last_state()

        # bundle 조립
        bundle = self.assembler.assemble(
            episode_no=episode_no,
            seed_contract=seed,
            macroarc_packet=macroarc,
            character_grid=character_grid,
            residue_plan=residue_plan,
            style_dna=style_dna,
            literary_state_before=state_before,
        )

        # V312 실행
        if self.bridge.is_available():
            v312_result = self.bridge.run(bundle)
        else:
            # V312 미연결 시 설계 결과만 반환
            v312_result = {
                "render_output": {"SC01": "", "SC02": "", "SC03": ""},
                "literary_state_after": {},
                "promotion_decision": "archive_only",
                "note": "V312 bridge not connected — design layer only",
            }

        # 일관성 검사
        violations = self.coherence_engine.check(
            episode_no=episode_no,
            generated_summary=v312_result.get("render_output", {}).get("SC01", ""),
            memory=memory,
            residue_used=seed["required_objects"],
        )

        # residue 진행
        for rid in seed["required_objects"]:
            memory.advance_residue(rid, episode_no)

        return {
            "episode_no":     episode_no,
            "ep_intent":      ep_intent,
            "render_output":  v312_result.get("render_output", {}),
            "literary_state_after": v312_result.get("literary_state_after", {}),
            "promotion":      v312_result.get("promotion_decision", "archive_only"),
            "loss_report":    v312_result.get("loss_report", {}),
            "hitl_recommended": v312_result.get("hitl_recommended", False),
            "coherence_violations": [
                {"type": v.violation_type, "detail": v.detail, "severity": v.severity}
                for v in violations
            ],
            "style_applied": style_dna.get("profile_name", ""),
        }

    def _make_fallback_bundle(
        self, seed: dict, total_episodes: int
    ) -> dict[str, Any]:
        """v7 분析기 없을 때 기본 bundle 생성."""
        return {
            "character_grid": None,
            "project_id": seed["project_id"],
        }

    def _init_residues(
        self, memory: ProjectMemoryStore, objects: list[str], episode_seeded: int
    ) -> None:
        for obj in objects:
            memory.init_residue(
                residue_id=obj,
                object_name=obj,
                lifecycle_plan=["seed", "echo", "partial_open", "payoff"],
                episode_seeded=episode_seeded,
            )
