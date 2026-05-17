"""
V313→V322: TemporalCoherenceEngine
화 간 일관성 추적 — V313의 핵심 신규 모듈.
인물 속성, residue 생애, reveal_budget 누적, 지식 상태를 타임라인으로 관리.
LLM 0회.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CharacterState:
    """화 단위 인물 상태 스냅샷."""
    char_id: str
    episode_no: int
    knowledge: dict[str, str] = field(default_factory=dict)
    # key: 사실_id, value: "knows"|"suspects"|"unaware"
    active: bool = True
    tension_axis: str = ""


@dataclass
class ResidueLifecycle:
    """residue 생애 추적."""
    residue_id: str
    object_name: str
    lifecycle_plan: list[str]   # ["seed","echo","partial_open","payoff"]
    current_phase: int = 0      # lifecycle_plan의 현재 인덱스
    episode_seeded: int = 0
    episode_last_seen: int = 0


@dataclass
class CoherenceViolation:
    violation_type: str
    episode_no: int
    detail: str
    severity: str   # "critical" | "warning" | "info"


class ProjectMemoryStore:
    """
    프로젝트 수준 기억 저장소.
    화 간 상태를 누적하며 일관성을 추적.
    """

    def __init__(self, project_id: str, total_episodes: int = 16):
        self.project_id = project_id
        self.total_episodes = total_episodes

        # 인물 상태 타임라인: {episode_no: {char_id: CharacterState}}
        self.character_timeline: dict[int, dict[str, CharacterState]] = {}

        # residue 생애: {residue_id: ResidueLifecycle}
        self.residue_lifecycles: dict[str, ResidueLifecycle] = {}

        # reveal_budget 누적: {episode_no: {"core_truth": int, "surface_hint": int}}
        self.reveal_log: dict[int, dict[str, int]] = {}

        # Literary State 타임라인: {episode_no: dict}
        self.state_timeline: dict[int, dict[str, float]] = {}

        # 화 종료 패킷 (Episode Continuation)
        self.episode_handoffs: dict[int, dict[str, Any]] = {}

    # ── 인물 상태 ─────────────────────────────────────────
    def set_character_state(self, episode_no: int, state: CharacterState) -> None:
        if episode_no not in self.character_timeline:
            self.character_timeline[episode_no] = {}
        self.character_timeline[episode_no][state.char_id] = state

    def get_character_state(self, episode_no: int, char_id: str) -> CharacterState | None:
        return self.character_timeline.get(episode_no, {}).get(char_id)

    def get_latest_character_state(self, char_id: str) -> CharacterState | None:
        for ep in sorted(self.character_timeline.keys(), reverse=True):
            st = self.character_timeline[ep].get(char_id)
            if st:
                return st
        return None

    # ── residue 생애 ──────────────────────────────────────
    def init_residue(self, residue_id: str, object_name: str,
                     lifecycle_plan: list[str], episode_seeded: int) -> None:
        self.residue_lifecycles[residue_id] = ResidueLifecycle(
            residue_id=residue_id,
            object_name=object_name,
            lifecycle_plan=lifecycle_plan,
            current_phase=0,
            episode_seeded=episode_seeded,
            episode_last_seen=episode_seeded,
        )

    def advance_residue(self, residue_id: str, episode_no: int) -> str | None:
        rl = self.residue_lifecycles.get(residue_id)
        if not rl:
            return None
        rl.current_phase = min(rl.current_phase + 1, len(rl.lifecycle_plan) - 1)
        rl.episode_last_seen = episode_no
        return rl.lifecycle_plan[rl.current_phase]

    def get_residue_phase(self, residue_id: str) -> str:
        rl = self.residue_lifecycles.get(residue_id)
        if not rl:
            return "unknown"
        return rl.lifecycle_plan[rl.current_phase]

    # ── Literary State ────────────────────────────────────
    def record_state(self, episode_no: int, state: dict[str, float]) -> None:
        self.state_timeline[episode_no] = dict(state)

    def get_last_state(self) -> dict[str, float]:
        if not self.state_timeline:
            return {"SP": 0.30, "RU": 0.55, "ET": 0.0, "RD": 0.12,
                    "RT": 0.30, "AC": 0.70, "RO": 0.50, "MR": 0.10}
        last_ep = max(self.state_timeline.keys())
        return self.state_timeline[last_ep]

    # ── Episode Handoff ───────────────────────────────────
    def save_handoff(self, episode_no: int, handoff: dict[str, Any]) -> None:
        self.episode_handoffs[episode_no] = handoff

    def get_handoff(self, episode_no: int) -> dict[str, Any]:
        return self.episode_handoffs.get(episode_no, {})

    # ── reveal_budget 누적 ────────────────────────────────
    def log_reveal(self, episode_no: int, core_truth: int = 0, surface_hint: int = 0) -> None:
        self.reveal_log[episode_no] = {
            "core_truth": core_truth,
            "surface_hint": surface_hint,
        }

    def cumulative_reveal(self, up_to_episode: int) -> dict[str, int]:
        ct = sum(v["core_truth"]   for ep, v in self.reveal_log.items() if ep <= up_to_episode)
        sh = sum(v["surface_hint"] for ep, v in self.reveal_log.items() if ep <= up_to_episode)
        return {"core_truth": ct, "surface_hint": sh}


class TemporalCoherenceEngine:
    """
    화 간 일관성 검사 엔진.
    ProjectMemoryStore를 참조해 일관성 위반을 감지.
    """

    def check(
        self,
        episode_no: int,
        generated_summary: str,
        memory: ProjectMemoryStore,
        reveal_budget: dict[str, int] | None = None,
        residue_used: list[str] | None = None,
    ) -> list[CoherenceViolation]:
        violations: list[CoherenceViolation] = []

        # ① reveal_budget 초과 검사
        if reveal_budget:
            cumulative = memory.cumulative_reveal(episode_no - 1)
            ct_budget   = reveal_budget.get("core_truth_total", 999)
            sh_budget   = reveal_budget.get("surface_hint_total", 999)
            if cumulative["core_truth"] > ct_budget:
                violations.append(CoherenceViolation(
                    violation_type="reveal_budget_exceeded",
                    episode_no=episode_no,
                    detail=f"core_truth 누적 {cumulative['core_truth']} > 예산 {ct_budget}",
                    severity="critical",
                ))

        # ② residue 생애 순서 검사
        for rid in (residue_used or []):
            rl = memory.residue_lifecycles.get(rid)
            if not rl:
                continue
            expected_phase = rl.lifecycle_plan[min(rl.current_phase, len(rl.lifecycle_plan)-1)]
            # "payoff"는 seed 없이 불가
            if expected_phase == "payoff" and rl.episode_seeded == 0:
                violations.append(CoherenceViolation(
                    violation_type="residue_premature_payoff",
                    episode_no=episode_no,
                    detail=f"{rid} — seed 없이 payoff 시도",
                    severity="critical",
                ))

        # ③ 장기 미등장 인물 갑작스러운 재등장 (단순 탐지)
        for char_id, rl_data in memory.character_timeline.get(episode_no, {}).items():
            last = memory.get_latest_character_state(char_id)
            if last and last.episode_no < episode_no - 3:
                violations.append(CoherenceViolation(
                    violation_type="character_sudden_return",
                    episode_no=episode_no,
                    detail=f"{char_id} — {last.episode_no}화 이후 {episode_no - last.episode_no}화 만에 재등장",
                    severity="warning",
                ))

        return violations

    def build_handoff(
        self,
        episode_no: int,
        literary_state: dict[str, float],
        active_residues: list[str],
        memory: ProjectMemoryStore,
        reveal_summary: dict[str, int],
    ) -> dict[str, Any]:
        """화 종료 시 다음 화로 전달할 Episode Continuation Packet."""
        residue_phases = {
            rid: memory.get_residue_phase(rid)
            for rid in active_residues
        }
        return {
            "from_episode": episode_no,
            "to_episode":   episode_no + 1,
            "literary_state_carry": literary_state,
            "active_residues": active_residues,
            "residue_phases": residue_phases,
            "cumulative_reveal": reveal_summary,
            "last_sp": literary_state.get("SP", 0.0),
            "last_ru": literary_state.get("RU", 0.0),
        }
