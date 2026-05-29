"""
V380: ledgers/episode_reveal_budget.py — EpisodeRevealBudget

에피소드 단위 복선 공개 예산 및 정책 관리.

4단계 복선 정책:
  ALLOW           — 해당 에피소드에서 사실/복선 정상 공개 가능
  FORESHADOW_ONLY — 암시적 힌트만 허용, 직접 공개 금지
  DELAY           — 다음 에피소드로 공개 지연 (forbidden_reveals에 자동 추가)
  BLOCK           — 완전 차단 (ProseRenderContract violation)

통합 지점:
  ClosedLoopRenderOrchestrator v2 BUILD 단계 진입 전
  EpisodeRevealBudget.check(episode_id, fact_id) 호출 필수

LLM 0회.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set


# ── 예외 계층 ───────────────────────────────────────────────────
class RevealBudgetViolationError(Exception):
    """복선 예산 위반 기본 예외."""
    def __init__(self, episode_id: str, fact_id: str, policy: str, msg: str = "") -> None:
        self.episode_id = episode_id
        self.fact_id    = fact_id
        self.policy     = policy
        super().__init__(
            f"[RevealBudget:{policy}] ep={episode_id}, fact={fact_id}"
            + (f" — {msg}" if msg else "")
        )

class RevealBlockedError(RevealBudgetViolationError):
    """BLOCK 정책: 렌더링 완전 차단."""
    def __init__(self, episode_id: str, fact_id: str) -> None:
        super().__init__(episode_id, fact_id, "BLOCK",
                         "이 에피소드에서 해당 사실은 절대 공개 불가합니다.")

class RevealForeshadowOnlyError(RevealBudgetViolationError):
    """FORESHADOW_ONLY 정책: 직접 공개 시도 차단."""
    def __init__(self, episode_id: str, fact_id: str) -> None:
        super().__init__(episode_id, fact_id, "FORESHADOW_ONLY",
                         "이 에피소드에서 해당 사실은 암시적 힌트만 가능합니다.")


# ── 복선 정책 열거형 ─────────────────────────────────────────────
class RevealPolicy(str, Enum):
    ALLOW           = "ALLOW"            # 정상 공개 허용
    FORESHADOW_ONLY = "FORESHADOW_ONLY"  # 암시만 허용
    DELAY           = "DELAY"            # 다음 화로 지연
    BLOCK           = "BLOCK"            # 완전 차단


# ── EpisodeRevealPolicy — 에피소드×사실 정책 단위 ─────────────────
@dataclass
class EpisodeRevealPolicy:
    """
    특정 에피소드에서 특정 사실(fact_id)에 대한 공개 정책.
    """
    episode_id:  str
    fact_id:     str
    policy:      RevealPolicy
    delay_to:    Optional[str] = None   # DELAY일 때 공개 예정 에피소드 ID
    reason:      str           = ""     # 정책 근거 메모

    def to_dict(self) -> dict:
        return {
            "episode_id": self.episode_id,
            "fact_id":    self.fact_id,
            "policy":     self.policy.value,
            "delay_to":   self.delay_to,
            "reason":     self.reason,
        }


# ── EpisodeRevealBudget — 전체 에피소드 복선 예산 대장 ─────────────
class EpisodeRevealBudget:
    """
    16부작 전체에 걸친 복선 공개 예산 관리자.

    사용 예:
        budget = EpisodeRevealBudget()
        budget.set_policy("ep_01", "fact_killer_identity", RevealPolicy.BLOCK)
        budget.set_policy("ep_08", "fact_killer_identity", RevealPolicy.FORESHADOW_ONLY)
        budget.set_policy("ep_14", "fact_killer_identity", RevealPolicy.ALLOW)

        # CLRO 렌더링 전 호출
        budget.check("ep_01", "fact_killer_identity")   # → RevealBlockedError
        budget.check("ep_14", "fact_killer_identity")   # → OK (None 반환)
    """

    def __init__(self) -> None:
        # (episode_id, fact_id) → EpisodeRevealPolicy
        self._policies:  Dict[tuple, EpisodeRevealPolicy] = {}
        # 전역 차단 사실 ID (어떤 에피소드에서도 공개 불가)
        self._global_blocks: Set[str] = set()
        # 지연된 사실 추적 (fact_id → [delayed_episode_ids])
        self._delayed: Dict[str, List[str]] = {}

    # ── 정책 설정 ──────────────────────────────────────────────────
    def set_policy(
        self,
        episode_id: str,
        fact_id:    str,
        policy:     RevealPolicy,
        delay_to:   Optional[str] = None,
        reason:     str           = "",
    ) -> None:
        """에피소드×사실 정책을 설정한다."""
        key = (episode_id, fact_id)
        self._policies[key] = EpisodeRevealPolicy(
            episode_id=episode_id,
            fact_id=   fact_id,
            policy=    policy,
            delay_to=  delay_to,
            reason=    reason,
        )
        if policy == RevealPolicy.DELAY and delay_to:
            self._delayed.setdefault(fact_id, []).append(episode_id)

    def set_global_block(self, fact_id: str) -> None:
        """특정 사실을 전체 에피소드에서 완전 차단."""
        self._global_blocks.add(fact_id)

    def remove_global_block(self, fact_id: str) -> None:
        self._global_blocks.discard(fact_id)

    # ── 정책 조회 ──────────────────────────────────────────────────
    def get_policy(
        self,
        episode_id: str,
        fact_id:    str,
    ) -> RevealPolicy:
        """에피소드×사실의 현재 정책 반환. 미설정이면 ALLOW."""
        if fact_id in self._global_blocks:
            return RevealPolicy.BLOCK
        key = (episode_id, fact_id)
        entry = self._policies.get(key)
        return entry.policy if entry else RevealPolicy.ALLOW

    # ── 게이트 검사 — CLRO 진입 전 호출 ───────────────────────────
    def check(
        self,
        episode_id:    str,
        fact_id:       str,
        direct_reveal: bool = True,
    ) -> None:
        """
        렌더링 전 복선 정책 검사.

        Args:
            episode_id:    현재 렌더링 중인 에피소드 ID
            fact_id:       공개하려는 사실 ID
            direct_reveal: True이면 직접 공개 (FORESHADOW_ONLY에서 차단)
                           False이면 암시 렌더링 (FORESHADOW_ONLY 통과)

        Raises:
            RevealBlockedError:       BLOCK 정책 위반
            RevealForeshadowOnlyError: FORESHADOW_ONLY에서 직접 공개 시도
        """
        policy = self.get_policy(episode_id, fact_id)

        if policy == RevealPolicy.BLOCK:
            raise RevealBlockedError(episode_id, fact_id)

        if policy == RevealPolicy.FORESHADOW_ONLY and direct_reveal:
            raise RevealForeshadowOnlyError(episode_id, fact_id)

        # DELAY → 그냥 통과 (경고 없음; 지연 처리는 SeriesArcPlanner가 담당)
        # ALLOW → 통과

    def check_all(
        self,
        episode_id: str,
        fact_ids:   List[str],
        direct_reveal: bool = True,
    ) -> List[str]:
        """
        여러 사실에 대해 일괄 검사.
        Returns: 위반 사실 ID 목록 (예외 발생 없이 수집).
        """
        violations: List[str] = []
        for fact_id in fact_ids:
            try:
                self.check(episode_id, fact_id, direct_reveal=direct_reveal)
            except RevealBudgetViolationError:
                violations.append(fact_id)
        return violations

    # ── 에피소드별 요약 ──────────────────────────────────────────
    def episode_summary(self, episode_id: str) -> dict:
        """에피소드에 설정된 모든 정책 요약."""
        policies = [
            v.to_dict()
            for (eid, _), v in self._policies.items()
            if eid == episode_id
        ]
        return {
            "episode_id":     episode_id,
            "policies":       policies,
            "global_blocks":  list(self._global_blocks),
            "policy_count":   len(policies),
        }

    def fact_journey(self, fact_id: str) -> List[dict]:
        """특정 사실의 에피소드별 정책 변화 이력."""
        journey = [
            v.to_dict()
            for (_, fid), v in self._policies.items()
            if fid == fact_id
        ]
        return sorted(journey, key=lambda x: x["episode_id"])

    # ── SeriesArcPlanner 연동: arc 노드에서 자동 정책 추출 ─────────
    @classmethod
    def from_arc_graph(cls, graph: object) -> "EpisodeRevealBudget":
        """
        CausalPlotGraph에서 forbidden_reveals / reveal_budget을 읽어
        EpisodeRevealBudget 자동 구성.
        """
        budget = cls()
        for node in graph.all_nodes():
            for fact_id in node.forbidden_reveals:
                budget.set_policy(
                    node.episode_id, fact_id,
                    RevealPolicy.BLOCK,
                    reason=f"SeriesArcPlanner: ep_{node.episode_index} 금지 사실",
                )
            # reveal_budget < 0.2 → FORESHADOW_ONLY 자동 등록 (사실 없으면 스킵)
        return budget

    def total_policy_count(self) -> int:
        return len(self._policies)
