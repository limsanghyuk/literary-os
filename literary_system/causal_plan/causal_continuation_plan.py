"""
V317: CausalContinuationPlanBuilder
GPT v1601 causal_continuation_deepening (phase49) 흡수 구현.

핵심 이론:
  "다음 화에 무엇이 일어나야 하는가"를
  인과 논리로 명시적으로 계획한다.

  3개 컴포넌트:
  1. CausalKnowledgeLedger    — 인물별 믿음 상태 (사실 / 오해 / 의무)
  2. PayoffPropagationReport  — 현재 화 이후 payoff 후보 우선순위
  3. CausalContinuationPlan   — 다음 화 연속화 계획 (act intent + 인과 후크)

GPT v1601 vs 우리 V315:
  V315 CausalChainPlanner: 예측 (if X learns Y → 압력 변화)
  V317 CausalContinuationPlan: 실행 계획 (다음 화 act intent + payoff 순서 + 인과 후크)

핵심 차이:
  V315: "예측 엔진" — 무엇이 일어날 수 있는가
  V317: "계획 엔진" — 무엇이 일어나야 하는가, 어떤 순서로

LLM 0회.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

from literary_system.world.knowledge_state_tracker import (
    KnowledgeStateTracker, KnowledgeStatus
)


@dataclass
class CharacterBeliefState:
    """인물의 믿음 상태."""
    known_facts: list[str] = field(default_factory=list)
    misconceptions: list[str] = field(default_factory=list)   # 잘못 알고 있는 것
    obligations: list[str] = field(default_factory=list)       # 해야 할 의무
    pressure: float = 0.0                                        # 총 압력 점수


@dataclass
class CausalKnowledgeLedger:
    """인과 지식 원장 — 화 간 인물 믿음 상태 추적."""
    project_id: str
    ledger_id: str
    source_episode_no: int
    target_episode_no: int
    states: dict[str, CharacterBeliefState] = field(default_factory=dict)
    causal_hotspots: list[str] = field(default_factory=list)


@dataclass
class PayoffCandidate:
    """payoff 후보 단일 항목."""
    residue: str              # residue ID 또는 이름
    setup_signal: str | None  # 어디서 심어졌는가
    payoff_window: str        # "next_episode" | "ep3_ep4" | "act2"
    priority: float           # [0, 1] — 높을수록 먼저 터뜨려야 함
    risk_if_unpaid: float     # payoff 안 하면 얼마나 위험한가


@dataclass
class PayoffPropagationReport:
    """payoff 전파 보고 — 어떤 것을 먼저 해소해야 하는가."""
    project_id: str
    report_id: str
    source_episode_no: int
    target_episode_no: int
    payoff_candidates: list[PayoffCandidate] = field(default_factory=list)
    deferred_payoffs: list[str] = field(default_factory=list)   # 다음 화로 미룬 것들


@dataclass
class CausalContinuationPlan:
    """
    다음 화 연속화 계획 — GPT v1601의 핵심 산출물.
    "다음 화는 이런 인과 흐름으로 진행해야 한다"
    """
    project_id: str
    plan_id: str
    source_episode_no: int
    target_episode_no: int
    recommended_next_act_intent: str
    carried_knowledge_asymmetry: dict[str, float]      # 인물별 압력
    preserved_misconceptions: dict[str, list[str]]     # 다음 화까지 유지할 오해
    prioritized_payoffs: list[str]                      # 다음 화 payoff 순서
    pressure_release_recommendation: float             # 얼마나 압력을 풀어야 하는가 [0, 1]
    continuation_hooks: list[str]                       # 다음 화 첫 씬 진입 후크


class CausalContinuationPlanBuilder:
    """
    KnowledgeStateTracker + PayoffPropagationReport
    → CausalContinuationPlan 생성.
    """

    def build_ledger(
        self,
        project_id: str,
        episode_no: int,
        tracker: KnowledgeStateTracker,
    ) -> CausalKnowledgeLedger:
        """현재 KnowledgeStateTracker에서 원장 추출."""
        import uuid
        states: dict[str, CharacterBeliefState] = {}
        causal_hotspots: list[str] = []

        for char_id, ck_dict in tracker.char_knowledge.items():
            known = [fid for fid, ck in ck_dict.items()
                     if ck.status == KnowledgeStatus.KNOWS]
            misconceptions = [
                f"{fid}:{ck.believed_value}"
                for fid, ck in ck_dict.items()
                if ck.status == KnowledgeStatus.MISBELIEVES
            ]
            obligations = []  # V315 확장 시 추가

            # 압력: 알고 있는 사실 수 × 0.12 + 오해 수 × 0.18
            pressure = round(
                min(1.0, len(known) * 0.12 + len(misconceptions) * 0.18), 4
            )

            states[char_id] = CharacterBeliefState(
                known_facts=known,
                misconceptions=misconceptions,
                obligations=obligations,
                pressure=pressure,
            )

            if pressure > 0.5:
                causal_hotspots.append(char_id)

        return CausalKnowledgeLedger(
            project_id=project_id,
            ledger_id=f"{project_id}_ledger_ep{episode_no:02d}_{uuid.uuid4().hex[:6]}",
            source_episode_no=episode_no,
            target_episode_no=episode_no + 1,
            states=states,
            causal_hotspots=causal_hotspots,
        )

    def build_payoff_report(
        self,
        project_id: str,
        episode_no: int,
        active_residues: dict[str, dict],  # {residue_id: {phase, setup_ep, ...}}
        knowledge_pressure: float = 0.5,
    ) -> PayoffPropagationReport:
        """현재 활성 residue → payoff 우선순위 계산."""
        import uuid
        candidates: list[PayoffCandidate] = []
        deferred: list[str] = []

        for rid, info in active_residues.items():
            phase = info.get("phase", "seed")
            seeded_ep = info.get("episode_seeded", 0)
            episodes_alive = episode_no - seeded_ep

            # priority 계산: 오래된 residue일수록 높음 + payoff 직전일수록 높음
            if phase == "payoff":
                priority = 0.90
                window = "next_episode"
            elif phase == "partial_open" and episodes_alive >= 3:
                priority = 0.72
                window = "next_episode"
            elif phase == "echo":
                priority = 0.50
                window = f"ep{episode_no+1}_ep{episode_no+2}"
            else:
                priority = 0.25
                window = "act2"
                deferred.append(rid)
                continue

            risk = round(min(0.95, priority + 0.10 * (episodes_alive / 6)), 4)

            candidates.append(PayoffCandidate(
                residue=rid,
                setup_signal=f"ep{seeded_ep:02d}",
                payoff_window=window,
                priority=round(priority, 4),
                risk_if_unpaid=risk,
            ))

        # 우선순위 정렬
        candidates.sort(key=lambda x: -x.priority)

        return PayoffPropagationReport(
            project_id=project_id,
            report_id=f"{project_id}_payoff_{uuid.uuid4().hex[:6]}",
            source_episode_no=episode_no,
            target_episode_no=episode_no + 1,
            payoff_candidates=candidates,
            deferred_payoffs=deferred,
        )

    def build_plan(
        self,
        project_id: str,
        source_episode_no: int,
        ledger: CausalKnowledgeLedger,
        payoff_report: PayoffPropagationReport,
        macroarc_total_episodes: int = 16,
    ) -> CausalContinuationPlan:
        """
        원장 + payoff 보고 → 다음 화 연속화 계획.
        이것이 V317의 핵심 산출물.
        """
        import uuid
        target_ep = source_episode_no + 1
        plan_id = f"{project_id}_plan_ep{source_episode_no:02d}to{target_ep:02d}_{uuid.uuid4().hex[:6]}"

        # 인물별 압력 정리
        asymmetry = {
            char_id: round(state.pressure, 4)
            for char_id, state in ledger.states.items()
        }

        # 다음 화까지 유지해야 할 오해 (압력이 높은 인물의 오해)
        preserved_misconceptions: dict[str, list[str]] = {}
        for char_id, state in ledger.states.items():
            if state.pressure > 0.35 and state.misconceptions:
                preserved_misconceptions[char_id] = state.misconceptions[:2]

        # payoff 순서
        prioritized_payoffs = [
            c.residue for c in payoff_report.payoff_candidates
            if c.payoff_window == "next_episode"
        ][:3]

        # 압력 해소 추천
        ep_ratio = source_episode_no / max(macroarc_total_episodes, 1)
        avg_pressure = sum(asymmetry.values()) / max(len(asymmetry), 1) if asymmetry else 0.5
        pressure_release = round(
            0.10 if ep_ratio < 0.3
            else 0.25 if ep_ratio < 0.6
            else 0.40 if avg_pressure > 0.6
            else 0.20,
            4
        )

        # act intent 추천
        act_intent = self._recommend_act_intent(
            source_episode_no, macroarc_total_episodes,
            avg_pressure, len(prioritized_payoffs)
        )

        # 연속화 후크
        hooks = self._build_hooks(ledger, payoff_report)

        return CausalContinuationPlan(
            project_id=project_id,
            plan_id=plan_id,
            source_episode_no=source_episode_no,
            target_episode_no=target_ep,
            recommended_next_act_intent=act_intent,
            carried_knowledge_asymmetry=asymmetry,
            preserved_misconceptions=preserved_misconceptions,
            prioritized_payoffs=prioritized_payoffs,
            pressure_release_recommendation=pressure_release,
            continuation_hooks=hooks,
        )

    def _recommend_act_intent(
        self,
        ep_no: int,
        total: int,
        avg_pressure: float,
        payoff_count: int,
    ) -> str:
        ratio = ep_no / max(total, 1)
        if ratio < 0.25:
            return "seed_conflict_and_expand_grid"
        elif ratio < 0.5:
            if avg_pressure > 0.6:
                return "raise_pressure_and_partial_reveal"
            return "deepen_knowledge_asymmetry"
        elif ratio < 0.75:
            if payoff_count > 0:
                return "selective_payoff_with_new_question"
            return "false_climax_and_relock"
        else:
            return "final_convergence_of_residues"

    def _build_hooks(
        self,
        ledger: CausalKnowledgeLedger,
        payoff: PayoffPropagationReport,
    ) -> list[str]:
        hooks = []
        # causal hotspot 인물이 처음 등장하는 씬 후크
        for char_id in ledger.causal_hotspots[:2]:
            hooks.append(f"{char_id}의 첫 등장 씬에서 misbelief 충돌 암시")

        # 가장 높은 priority payoff 후크
        if payoff.payoff_candidates:
            top = payoff.payoff_candidates[0]
            hooks.append(f"잔향 '{top.residue}' — 첫 씬 배경에 재등장 (window: {top.payoff_window})")

        if not hooks:
            hooks.append("이전 화 마지막 오브제로 첫 씬 열기")

        return hooks[:4]
