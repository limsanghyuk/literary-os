"""
V318: ClosedLoopRenderOrchestrator
GPT v1500 closed_loop_render_orchestrator + policy_conditioned_recovery 흡수.

핵심 이론 (수석 아키텍트):
  단일 패스 렌더링은 충분하지 않다.
  "좋은 씬이 나왔다" ≠ "Literary State 목표를 달성했다"

  ClosedLoop = render → critic → patch → re-evaluate → commit/retry

  GPT v1500의 핵심 혁신:
  1. 렌더링 후 즉각 critic 평가
  2. critic 실패 → specialized patch 자동 선택
  3. patch 후 reader_state 재평가
  4. 재평가 후 trajectory deviation 재계산
  5. deviation 허용 범위 내 → commit, 아니면 retry

우리 V313과의 차이:
  V313 BuildOpeningOrchestrator:
    run_quick() → for ep in range(1,4): V312Bridge.run(bundle) → 결과
    → 단일 패스. 실패해도 그냥 진행.

  V318 ClosedLoopRenderOrchestrator:
    for ep: render → critic → if fail: specialized_patch → re-render
    → max_iterations 제한
    → trajectory_deviation 추적
    → reference_pack steering 통합

이것이 V1500이 V1402보다 품질이 높은 이유.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from literary_system.coherence.temporal_coherence import ProjectMemoryStore, TemporalCoherenceEngine
from literary_system.compiler.seed_compiler import SeedCompiler
from literary_system.reference.reference_pack_steering import (
    ReferenceBundle,
    ReferencePack,
    ReferencePackBuilder,
    TrajectorySoftPromptTranslator,
)
from literary_system.render_loop.specialized_patch import SpecializedLocalPatchEngine
from literary_system.trajectory.narrative_trajectory import TrajectoryEngine, TrajectoryPoint
from literary_system.trajectory.reader_simulator import ReaderSimulator


@dataclass
class RenderIteration:
    """단일 렌더링 반복 결과."""
    iteration: int
    render_output: dict[str, str]
    reader_estimate: dict[str, float]
    trajectory_deviation: float
    patch_applied: str | None    # 적용된 patch family
    soft_instruction_used: str
    accepted: bool
    reason: str


@dataclass
class ClosedLoopResult:
    """ClosedLoop 단일 에피소드 결과."""
    episode_no: int
    final_output: dict[str, str]
    final_reader_state: dict[str, float]
    final_trajectory_deviation: float
    iterations_used: int
    iterations_detail: list[RenderIteration]
    patches_applied: list[str]
    literary_state_after: dict[str, float]
    trajectory_shape: str
    reference_pack_id: str
    accepted: bool


class ClosedLoopRenderOrchestrator:
    """
    ClosedLoop 렌더링 집행자.

    흐름:
      seed + reference_bundle + memory
        → TrajectoryFamilyInterpolator (목표 신호)
        → TrajectorySoftPromptTranslator (soft instruction)
        → V312Bridge (렌더링) [or mock]
        → ReaderSimulator (독자 상태 평가)
        → NarrativeTrajectory (deviation 계산)
        → if deviation > threshold:
            SpecializedLocalPatchEngine (자동 패치)
            → 재렌더링 (max 3회)
        → commit to ProjectMemoryStore
    """

    def __init__(
        self,
        sovereign_backend: str | None = None,
        max_iterations: int = 3,
        deviation_threshold: float = 0.18,
        reader_pull_threshold: float = 0.35,
    ):
        self.sovereign_backend = sovereign_backend
        self.max_iterations = max_iterations
        self.deviation_threshold = deviation_threshold
        self.reader_pull_threshold = reader_pull_threshold

        self.seed_compiler      = SeedCompiler()
        self.traj_engine        = TrajectoryEngine()
        self.reader_sim         = ReaderSimulator()
        self.patch_engine       = SpecializedLocalPatchEngine()
        self.ref_builder        = ReferencePackBuilder()
        self.soft_translator    = TrajectorySoftPromptTranslator()
        self.coherence_engine   = TemporalCoherenceEngine()

    def run_episode(
        self,
        episode_no: int,
        seed_contract: dict[str, Any],
        memory: ProjectMemoryStore,
        reference_bundle: ReferenceBundle | None = None,
        total_episodes: int = 16,
        genre: str = "political_thriller",
    ) -> ClosedLoopResult:
        """
        단일 에피소드 closed-loop 렌더링.
        """
        project_id = seed_contract.get("project_id", "proj_unknown")

        # ① Reference Pack 구성
        if reference_bundle is None:
            reference_bundle = ReferenceBundle(
                project_id=project_id,
                style_reference_ids=["style_restrained_kdrama_v1"],
                plot_reference_ids=["plot_delayed_reveal_opening_v2"],
                motif_reference_ids=self._infer_motif_ids(seed_contract),
                strictness=0.6,
            )
        ref_pack = self.ref_builder.build(reference_bundle)

        # ② 궤도 생성 (NarrativeTrajectory)
        trajectory = self.traj_engine.create(project_id, genre, total_episodes)
        state_before = memory.get_last_state()

        # ③ 목표 신호 (trajectory target + reference steering)
        target_signal = self._compute_target_signal(
            episode_no, trajectory, ref_pack, total_episodes
        )

        # ④ ClosedLoop
        iterations: list[RenderIteration] = []
        current_output: dict[str, str] = {}
        current_reader: dict[str, float] = {}
        current_deviation = 1.0
        patches_applied: list[str] = []

        for iteration in range(1, self.max_iterations + 1):
            # soft instruction 조립
            soft_instr = self.soft_translator.translate(
                trajectory_state=state_before,
                target_signal=target_signal,
                reader_state=current_reader or {"reader_pull": 0.5, "reader_afterimage": 0.5},
                reference_pack=ref_pack,
                episode_no=episode_no,
                patch_contract=iterations[-1].soft_instruction_used if iterations else None,
            )

            # 렌더링 (V312 Bridge or mock)
            raw_output = self._render(seed_contract, soft_instr, episode_no)

            # 독자 상태 평가
            all_text = " ".join(raw_output.values())
            reader_est = self.reader_sim.estimate(all_text, state_before)
            reader_dict = {
                "reader_pull": reader_est.reader_pull,
                "reader_afterimage": reader_est.reader_afterimage,
                "reader_uncertainty": reader_est.reader_uncertainty,
                "ai_smell_score": reader_est.ai_smell_score,
            }

            # Literary State 추정 (rule-based)
            state_after = self._estimate_state_after(state_before, reader_est, episode_no, total_episodes)

            # 궤도에 기록 + deviation 계산
            trajectory = self.traj_engine.ingest_episode_result(
                trajectory, episode_no, state_after
            )
            deviation = trajectory.total_deviation(episode_no)

            # 수락 여부 판단
            pull_ok = reader_dict["reader_pull"] >= self.reader_pull_threshold
            dev_ok  = deviation <= self.deviation_threshold
            smell_ok = reader_dict["ai_smell_score"] <= 0.40
            accepted = pull_ok and dev_ok and smell_ok

            # 어떤 패치가 필요한가?
            patch_applied = None
            patch_instruction = None
            if not accepted and iteration < self.max_iterations:
                patch_applied, patch_instruction = self._select_patch(
                    reader_dict, deviation, all_text, ref_pack
                )
                if patch_applied:
                    patch_result = self.patch_engine.apply(
                        all_text, patch_applied,
                        scene_id=f"EP{episode_no:02d}",
                        residue_objects=seed_contract.get("required_objects", []),
                    )
                    # 패치된 텍스트로 output 업데이트
                    raw_output = {"SC01_patched": patch_result.edited_text}
                    patches_applied.append(patch_applied)

            iterations.append(RenderIteration(
                iteration=iteration,
                render_output=raw_output,
                reader_estimate=reader_dict,
                trajectory_deviation=round(deviation, 4),
                patch_applied=patch_applied,
                soft_instruction_used=soft_instr[:200],
                accepted=accepted,
                reason=self._reason(pull_ok, dev_ok, smell_ok),
            ))

            current_output = raw_output
            current_reader = reader_dict
            current_deviation = deviation

            if accepted:
                break

        # 수락 여부 (max iteration 도달해도 최선 결과 반환)
        final_accepted = iterations[-1].accepted if iterations else False

        # memory에 Literary State 기록
        final_state = self._estimate_state_after(state_before, reader_est if iterations else None,
                                                   episode_no, total_episodes)
        memory.record_state(episode_no, final_state)

        # Episode Handoff 저장
        handoff = self.coherence_engine.build_handoff(
            episode_no=episode_no,
            literary_state=final_state,
            active_residues=seed_contract.get("required_objects", []),
            memory=memory,
            reveal_summary=memory.cumulative_reveal(episode_no),
        )
        memory.save_handoff(episode_no, handoff)

        return ClosedLoopResult(
            episode_no=episode_no,
            final_output=current_output,
            final_reader_state=current_reader,
            final_trajectory_deviation=round(current_deviation, 4),
            iterations_used=len(iterations),
            iterations_detail=iterations,
            patches_applied=patches_applied,
            literary_state_after=final_state,
            trajectory_shape=trajectory.shape_name,
            reference_pack_id=ref_pack.pack_id,
            accepted=final_accepted,
        )

    def run_opening(
        self,
        user_prompt: str,
        reference_bundle: ReferenceBundle | None = None,
        total_episodes: int = 16,
        episode_count: int = 3,
    ) -> dict[str, Any]:
        """
        3화 오프닝 ClosedLoop 생성.
        V313 run_quick()의 ClosedLoop 업그레이드 버전.
        """
        seed = self.seed_compiler.compile(user_prompt)
        project_id = seed["project_id"]
        genre = seed["genre"]
        memory = ProjectMemoryStore(project_id, total_episodes)

        # residue 초기화
        for obj in seed["required_objects"]:
            memory.init_residue(
                obj, obj, ["seed", "echo", "partial_open", "payoff"], 1
            )

        episodes: list[ClosedLoopResult] = []
        for ep_no in range(1, episode_count + 1):
            result = self.run_episode(
                episode_no=ep_no,
                seed_contract=seed,
                memory=memory,
                reference_bundle=reference_bundle,
                total_episodes=total_episodes,
                genre=genre,
            )
            episodes.append(result)

            # residue 진행
            for obj in seed["required_objects"]:
                memory.advance_residue(obj, ep_no)

        total_iterations = sum(r.iterations_used for r in episodes)
        all_patches = [p for r in episodes for p in r.patches_applied]

        return {
            "project_id": project_id,
            "mode": "closed_loop",
            "seed_contract": seed,
            "total_episodes_generated": episode_count,
            "total_iterations": total_iterations,
            "episodes": [
                {
                    "episode_no": r.episode_no,
                    "accepted": r.accepted,
                    "iterations_used": r.iterations_used,
                    "patches_applied": r.patches_applied,
                    "trajectory_deviation": r.final_trajectory_deviation,
                    "trajectory_shape": r.trajectory_shape,
                    "reference_pack_id": r.reference_pack_id,
                    "literary_state_after": r.literary_state_after,
                    "reader_state": r.final_reader_state,
                }
                for r in episodes
            ],
            "quality_summary": {
                "avg_deviation": round(
                    sum(r.final_trajectory_deviation for r in episodes) / max(len(episodes), 1), 4
                ),
                "total_patches": len(all_patches),
                "patch_breakdown": {p: all_patches.count(p) for p in set(all_patches)},
                "all_accepted": all(r.accepted for r in episodes),
            },
            "memory_summary": {
                "state_at_final": memory.get_last_state(),
                "residue_phases": {
                    obj: memory.get_residue_phase(obj)
                    for obj in seed["required_objects"]
                },
            },
        }

    # ── 내부 헬퍼 ─────────────────────────────────────────────
    def _render(
        self,
        seed_contract: dict,
        soft_instruction: str,
        episode_no: int,
    ) -> dict[str, str]:
        """V312 Bridge 또는 mock 렌더링."""
        try:
            from literary_system.compiler.v312_bridge import V312Bridge
            bridge = V312Bridge(self.sovereign_backend)
            if bridge.is_available():
                bundle = {
                    "render_instruction": soft_instruction,
                    "project_id": seed_contract.get("project_id", ""),
                    "episode_no": episode_no,
                    "state_before": {},
                }
                result = bridge.run(bundle)
                return result.get("render_output", {"SC01": ""})
        except Exception:
            pass

        # Mock 렌더링 — 설계층 결과만 반환
        genre = seed_contract.get("genre", "drama")
        objects = seed_contract.get("required_objects", [])
        obj_hint = f"녹슨 {objects[0]}이 복도에 있었다." if objects else "빈 복도."
        return {
            "SC01": f"[EP{episode_no:02d} | {genre} | MOCK] {obj_hint}",
            "SC02": f"[EP{episode_no:02d} | 압력 상승] 침묵이 먼저 움직였다.",
            "SC03": f"[EP{episode_no:02d} | 열리지 않은 문] {obj_hint} 바람이 한 번 지나갔다.",
        }

    def _compute_target_signal(
        self,
        episode_no: int,
        trajectory: Any,
        ref_pack: ReferencePack,
        total_episodes: int,
    ) -> dict[str, float]:
        """궤도 목표 + 참조팩 steering 합산."""
        target = {
            "SP": trajectory.target_at(episode_no, "SP"),
            "RU": trajectory.target_at(episode_no, "RU"),
            "ET": trajectory.target_at(episode_no, "ET"),
        }
        for k, delta in ref_pack.steering_weights.items():
            if k in target:
                target[k] = round(min(1.0, max(0.0, target[k] + delta)), 4)
        return target

    def _estimate_state_after(
        self,
        state_before: dict[str, float],
        reader_est: Any | None,
        episode_no: int,
        total_episodes: int,
    ) -> dict[str, float]:
        """독자 상태에서 Literary State 변화 추정."""
        ep_ratio = episode_no / max(total_episodes, 1)
        pull = reader_est.reader_pull if reader_est else 0.5
        uncertainty = reader_est.reader_uncertainty if reader_est else 0.5
        return {
            "SP": round(min(1.0, state_before.get("SP", 0.30) + ep_ratio * 0.04 + pull * 0.02), 3),
            "RU": round(max(0.0, state_before.get("RU", 0.60) - ep_ratio * 0.03 + uncertainty * 0.02), 3),
            "ET": round(min(1.0, state_before.get("ET", 0.00) + ep_ratio * 0.02), 3),
            "RD": round(state_before.get("RD", 0.12) + 0.01, 3),
            "RT": round(state_before.get("RT", 0.30) + 0.02, 3),
            "AC": round(state_before.get("AC", 0.70), 3),
            "RO": round(state_before.get("RO", 0.50), 3),
            "MR": round(state_before.get("MR", 0.10) + 0.01, 3),
        }

    def _select_patch(
        self,
        reader_state: dict[str, float],
        deviation: float,
        text: str,
        ref_pack: ReferencePack,
    ) -> tuple[str | None, str | None]:
        """어떤 특화 패치가 필요한가."""
        # ref_pack의 patch_preferences를 먼저 확인
        if ref_pack.patch_preferences:
            pref = ref_pack.patch_preferences[0]
            profile = self.patch_engine.FAMILY_PROFILES.get(pref)
            if profile:
                return pref, profile.guidance_notes[0] if profile.guidance_notes else pref

        # reader_state 기반 자동 선택
        ai_smell = reader_state.get("ai_smell_score", 0.0)
        pull = reader_state.get("reader_pull", 0.5)
        afterimage = reader_state.get("reader_afterimage", 0.5)

        if ai_smell > 0.35:
            return "pdi_fix", None
        if pull < 0.35:
            return "reveal_delay", None
        if afterimage < 0.30:
            return "residue_boost", None
        if deviation > self.deviation_threshold * 1.5:
            return "dialogue_compression", None

        return None, None

    def _reason(self, pull_ok: bool, dev_ok: bool, smell_ok: bool) -> str:
        reasons = []
        if not pull_ok:  reasons.append("reader_pull 부족")
        if not dev_ok:   reasons.append("trajectory deviation 초과")
        if not smell_ok: reasons.append("AI smell 과다")
        return "ACCEPTED" if not reasons else f"REJECTED: {', '.join(reasons)}"

    def _infer_motif_ids(self, seed: dict) -> list[str]:
        objects = seed.get("required_objects", [])
        motif_map = {
            "rusted_locker": "motif_rusted_locker_v1",
            "wet_gloves": "motif_wet_gloves_v1",
        }
        return [motif_map[o] for o in objects if o in motif_map]
