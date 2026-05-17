"""
V317: PayoffScheduler
V315 CausalChainPlanner 고도화 + payoff 스케줄링 추가.

핵심 이론 (수석 아키텍트):
  "payoff는 즉흥이 아니다. 바둑의 '수읽기'처럼
   16화 전체에서 어느 화에 어떤 residue를 터뜨릴지
   미리 스케줄링해야 한다."

  V315 CausalChainPlanner의 predict_pressure_shift는
  "if A learns X → 어떤 압력 변화?" 를 예측하는 엔진이었다.

  V317 PayoffScheduler는:
  1. 전체 16화 payoff 스케줄 생성
  2. 각 화마다 어떤 residue를 얼마나 공개할지 예산 배분
  3. 빠른 payoff / 지연 payoff 전략 선택
  4. 실제 실행 이후 예산 추적

이것이 V317의 핵심 원리:
  "공개는 예산이다. 예산을 초과하면 반전이 사라진다."

LLM 0회.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class PayoffSlot:
    """단일 화의 payoff 예산."""
    episode_no: int
    allocated_residues: list[str]   # 이 화에서 공개할 residue들
    reveal_budget: float             # 이 화의 core_truth 공개 예산 [0, 1]
    pressure_target: float           # 이 화 목표 압력
    payoff_type: str                 # "full" | "partial" | "hint" | "none"
    strategic_note: str


@dataclass
class PayoffSchedule:
    """전체 시리즈 payoff 스케줄."""
    project_id: str
    total_episodes: int
    slots: dict[int, PayoffSlot]    # {episode_no: PayoffSlot}
    cumulative_reveal_curve: dict[int, float]  # {episode_no: 누적 공개량}
    strategy: str                    # "slow_burn" | "mid_explosion" | "distributed"


class PayoffScheduler:
    """
    전체 시리즈 payoff 스케줄 생성 + 실행 추적.

    3가지 전략:
    - slow_burn: 늦게 터뜨리기 (처음 70%는 힌트만, 후반 30%에 집중) [버그 2 수정: 0.55→0.70]
    - mid_explosion: 중반 터뜨리기 (50~70%에 메인 payoff)
    - distributed: 분산 터뜨리기 (균등 배분)
    """

    def generate_schedule(
        self,
        project_id: str,
        total_episodes: int,
        residue_ids: list[str],
        strategy: str = "slow_burn",
        macroarc_pressure_curve: list[float] | None = None,
    ) -> PayoffSchedule:
        """
        전체 payoff 스케줄 생성.
        residue_ids: 공개해야 할 residue 목록 (우선순위 순)
        """
        slots: dict[int, PayoffSlot] = {}
        cumulative: dict[int, float] = {}

        # 기본 압력 커브 (없으면 표준 상승 커브)
        if not macroarc_pressure_curve:
            macroarc_pressure_curve = [
                round(0.30 + 0.45 * (i / max(total_episodes - 1, 1)), 3)
                for i in range(total_episodes)
            ]

        # residue 배분 계획
        reveal_plan = self._plan_reveals(
            residue_ids, total_episodes, strategy
        )

        prev_cumulative = 0.0
        for ep_no in range(1, total_episodes + 1):
            ep_residues = reveal_plan.get(ep_no, [])
            ep_ratio = (ep_no - 1) / max(total_episodes - 1, 1)

            # 이 화의 reveal_budget
            if strategy == "slow_burn":
                reveal_budget = 0.05 if ep_ratio < 0.5 else round(0.10 + ep_ratio * 0.25, 3)
            elif strategy == "mid_explosion":
                reveal_budget = 0.05 if ep_ratio < 0.4 else (
                    0.35 if 0.5 < ep_ratio < 0.75 else 0.10
                )
            else:  # distributed
                reveal_budget = round(0.10 + ep_ratio * 0.10, 3)

            reveal_budget = min(0.50, reveal_budget)

            # payoff 타입
            if ep_residues and any(r in ["payoff_full"] for r in ep_residues):
                payoff_type = "full"
            elif ep_residues:
                payoff_type = "partial"
            elif reveal_budget > 0.20:
                payoff_type = "hint"
            else:
                payoff_type = "none"

            pressure_target = macroarc_pressure_curve[ep_no - 1]
            prev_cumulative += reveal_budget * 0.5
            cumulative[ep_no] = round(min(1.0, prev_cumulative), 4)

            strategic_note = self._generate_note(
                ep_no, total_episodes, ep_residues, payoff_type, ep_ratio
            )

            slots[ep_no] = PayoffSlot(
                episode_no=ep_no,
                allocated_residues=ep_residues,
                reveal_budget=reveal_budget,
                pressure_target=pressure_target,
                payoff_type=payoff_type,
                strategic_note=strategic_note,
            )

        return PayoffSchedule(
            project_id=project_id,
            total_episodes=total_episodes,
            slots=slots,
            cumulative_reveal_curve=cumulative,
            strategy=strategy,
        )

    def get_episode_brief(
        self,
        schedule: PayoffSchedule,
        episode_no: int,
    ) -> dict[str, Any]:
        """특정 화의 payoff 브리핑."""
        slot = schedule.slots.get(episode_no)
        if not slot:
            return {"error": f"Episode {episode_no} not in schedule"}

        prev_cumulative = schedule.cumulative_reveal_curve.get(episode_no - 1, 0.0)
        return {
            "episode_no": episode_no,
            "payoff_type": slot.payoff_type,
            "reveal_budget": slot.reveal_budget,
            "allocated_residues": slot.allocated_residues,
            "pressure_target": slot.pressure_target,
            "cumulative_reveal_before": prev_cumulative,
            "cumulative_reveal_after": schedule.cumulative_reveal_curve.get(episode_no, 0.0),
            "strategic_note": slot.strategic_note,
        }

    def check_budget_compliance(
        self,
        schedule: PayoffSchedule,
        episode_no: int,
        actual_reveal_amount: float,
    ) -> dict[str, Any]:
        """실제 공개량이 예산을 초과했는지 검사."""
        slot = schedule.slots.get(episode_no)
        if not slot:
            return {"ok": True}

        over_budget = actual_reveal_amount > slot.reveal_budget + 0.10
        return {
            "ok": not over_budget,
            "budget": slot.reveal_budget,
            "actual": actual_reveal_amount,
            "over_budget": over_budget,
            "warning": "공개 예산 초과 — 다음 화 반전 가능성 감소" if over_budget else None,
        }

    def rebalance(
        self,
        schedule: PayoffSchedule,
        executed_reveals: dict[int, float],  # {episode_no: 실제_공개량}
        from_episode: int,
    ) -> PayoffSchedule:
        """
        실제 실행 결과 기반 남은 화 재조정.
        너무 많이 공개됐으면 나머지 화 budget 낮추기.
        """
        total_executed = sum(v for ep, v in executed_reveals.items() if ep < from_episode)
        original_target = sum(
            schedule.slots[ep].reveal_budget
            for ep in range(1, from_episode)
            if ep in schedule.slots
        )

        surplus = total_executed - original_target
        if abs(surplus) < 0.05:
            return schedule  # 조정 불필요

        # 남은 화에서 surplus 흡수
        remaining_eps = [ep for ep in range(from_episode, schedule.total_episodes + 1)
                         if ep in schedule.slots]
        if not remaining_eps:
            return schedule

        adjustment = -surplus / max(len(remaining_eps), 1)
        for ep in remaining_eps:
            slot = schedule.slots[ep]
            new_budget = round(max(0.02, min(0.50, slot.reveal_budget + adjustment)), 4)
            schedule.slots[ep] = PayoffSlot(
                episode_no=slot.episode_no,
                allocated_residues=slot.allocated_residues,
                reveal_budget=new_budget,
                pressure_target=slot.pressure_target,
                payoff_type=slot.payoff_type,
                strategic_note=slot.strategic_note + " [재조정됨]",
            )

        return schedule

    # ── 내부 헬퍼 ─────────────────────────────────────────────
    def _plan_reveals(
        self,
        residue_ids: list[str],
        total_episodes: int,
        strategy: str,
    ) -> dict[int, list[str]]:
        """residue들을 화별로 배분."""
        plan: dict[int, list[str]] = {}
        if not residue_ids:
            return plan

        for idx, rid in enumerate(residue_ids):
            ratio_start = idx / max(len(residue_ids), 1)

            if strategy == "slow_burn":
                # 후반에 몰아서
                ep_target = max(1, int((0.70 + ratio_start * 0.25) * total_episodes))  # [버그 2 수정] slow_burn: 후반 70%~95%에 집중
            elif strategy == "mid_explosion":
                # 중반에 집중
                ep_target = max(1, int((0.45 + ratio_start * 0.20) * total_episodes))
            else:
                # 균등 분산
                ep_target = max(1, int((0.25 + ratio_start * 0.65) * total_episodes))

            ep_target = min(ep_target, total_episodes)
            plan.setdefault(ep_target, []).append(rid)

        return plan

    def _generate_note(
        self,
        ep_no: int,
        total: int,
        residues: list[str],
        payoff_type: str,
        ratio: float,
    ) -> str:
        if payoff_type == "full" and residues:
            return f"EP{ep_no:02d}: {residues[0]} 전체 공개 — 새 질문을 동시에 심어라"
        elif payoff_type == "partial" and residues:
            return f"EP{ep_no:02d}: {residues[0]} 부분 공개 — 핵심은 유보"
        elif payoff_type == "hint":
            return f"EP{ep_no:02d}: 잔향 암시만 — 직접 공개 금지"
        elif ratio > 0.85:
            return f"EP{ep_no:02d}: 최종 수렴 준비 — 미해결 잔향 목록 점검"
        else:
            return f"EP{ep_no:02d}: 압력 축적 — 공개 없음"
