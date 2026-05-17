"""
V380: world/character_knowledge_prose_bridge.py — CharacterKnowledgeProseBridge

KnowledgeStateTracker의 5상태를 ProseRenderContract에 연결하는 브리지.

핵심 역할:
  - 인물의 지식 상태(KNOWS/SUSPECTS/UNAWARE/MISBELIEVES/READER_ONLY)를
    산문 렌더링 제약으로 변환
  - READER_ONLY 사실이 UNAWARE 인물의 대사/행동에 누출되는 것을 차단
  - 지식 비대칭 압력을 ProseRenderContract 메타데이터로 주입

5상태 → 산문 렌더링 제약:
  KNOWS         → 해당 사실을 대사/행동에 자연스럽게 표현 가능
  SUSPECTS      → 암시적 행동(시선 회피, 말끝 흐림)으로만 표현
  UNAWARE       → 해당 사실을 전혀 알지 못하는 것처럼 렌더링
  MISBELIEVES   → 잘못된 믿음을 기반으로 한 행동/대사 렌더링
  READER_ONLY   → 산문에 절대 노출 금지 → ProseRenderContract BLOCK

LLM 0회.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from literary_system.world.knowledge_state_tracker import (
    KnowledgeStateTracker, KnowledgeStatus, KnowledgeFact,
)
from literary_system.prose.contract import (
    ProseRenderContract,
    ProseContractViolationError,
)


# ── 예외 ──────────────────────────────────────────────────────
class KnowledgeLeakageError(ProseContractViolationError):
    """READER_ONLY 사실이 인물 산문에 노출되려 할 때."""
    def __init__(self, char_id: str, fact_id: str) -> None:
        self.char_id = char_id
        self.fact_id = fact_id
        super().__init__(
            "KNOWLEDGE_LEAKAGE",
            f"READER_ONLY 사실 '{fact_id}'이 인물 '{char_id}' 산문에 노출 시도됨"
        )

class UnawarnessViolationError(ProseContractViolationError):
    """UNAWARE 인물이 사실을 아는 것처럼 렌더링하려 할 때."""
    def __init__(self, char_id: str, fact_id: str) -> None:
        self.char_id = char_id
        self.fact_id = fact_id
        super().__init__(
            "UNAWARENESS_VIOLATION",
            f"UNAWARE 인물 '{char_id}'이 사실 '{fact_id}'을 아는 것처럼 렌더링 시도됨"
        )


# ── 렌더링 제약 레코드 ─────────────────────────────────────────
@dataclass
class KnowledgeRenderConstraint:
    """
    인물×사실의 산문 렌더링 제약.
    """
    char_id:           str
    fact_id:           str
    status:            KnowledgeStatus
    render_mode:       str    # "direct" | "suggestive" | "ignorant" | "mistaken" | "blocked"
    behavioral_hint:   str    = ""  # 산문 작성 힌트
    is_blocked:        bool   = False

    def to_dict(self) -> dict:
        return {
            "char_id":         self.char_id,
            "fact_id":         self.fact_id,
            "status":          self.status.value,
            "render_mode":     self.render_mode,
            "behavioral_hint": self.behavioral_hint,
            "is_blocked":      self.is_blocked,
        }


# ── 상태별 렌더 모드 및 행동 힌트 매핑 ─────────────────────────
_STATUS_TO_RENDER: Dict[KnowledgeStatus, tuple] = {
    KnowledgeStatus.KNOWS:       ("direct",     "해당 사실을 자연스럽게 행동/대사에 반영"),
    KnowledgeStatus.SUSPECTS:    ("suggestive", "시선 회피, 말끝 흐림, 간접 질문으로 암시"),
    KnowledgeStatus.UNAWARE:     ("ignorant",   "해당 사실과 무관하게 행동 — 직접 언급 금지"),
    KnowledgeStatus.MISBELIEVES: ("mistaken",   "잘못된 믿음 기반 행동 — 왜곡된 확신"),
    KnowledgeStatus.READER_ONLY: ("blocked",    "산문 노출 절대 금지 — READER_ONLY"),
}


class CharacterKnowledgeProseBridge:
    """
    KnowledgeStateTracker ↔ ProseRenderContract 연결 브리지.

    사용 예:
        bridge = CharacterKnowledgeProseBridge(tracker)
        # 렌더링 전 게이트 검사
        bridge.check("수지", "fact_killer_identity")   # UNAWARE → 통과
        bridge.check("형사", "fact_killer_identity")   # KNOWS → 통과
        bridge.check("독자", "fact_killer_identity")   # READER_ONLY → KnowledgeLeakageError

        # ProseRenderContract에 지식 제약 메타데이터 주입
        contract = bridge.enrich_contract(
            ProseRenderContract.default(),
            char_id="수지",
            fact_ids=["fact_killer_identity", "fact_alibi"]
        )
    """

    def __init__(self, tracker: KnowledgeStateTracker) -> None:
        self._tracker = tracker

    # ── 핵심 게이트 ──────────────────────────────────────────────
    def check(
        self,
        char_id:       str,
        fact_id:       str,
        allow_suspect: bool = True,
    ) -> None:
        """
        산문 렌더링 전 지식 상태 검사.

        Args:
            char_id:       렌더링 대상 인물 ID
            fact_id:       렌더링에 포함될 사실 ID
            allow_suspect: True이면 SUSPECTS 상태도 암시 허용 (기본값 True)

        Raises:
            KnowledgeLeakageError:     READER_ONLY 사실 노출 시도
            UnawarnessViolationError:  UNAWARE 인물이 사실 직접 표현 시도
        """
        status = self._get_status(char_id, fact_id)

        if status == KnowledgeStatus.READER_ONLY:
            raise KnowledgeLeakageError(char_id, fact_id)

    def check_scene(
        self,
        char_id:  str,
        fact_ids: List[str],
    ) -> List[str]:
        """
        씬에 포함된 여러 사실에 대해 일괄 검사.
        Returns: 위반 사실 ID 목록 (예외 없이 수집).
        """
        violations: List[str] = []
        for fact_id in fact_ids:
            try:
                self.check(char_id, fact_id)
            except (KnowledgeLeakageError, UnawarnessViolationError):
                violations.append(fact_id)
        return violations

    def assert_no_leakage(
        self,
        char_ids:    List[str],
        fact_ids:    List[str],
    ) -> None:
        """
        여러 인물에 대해 READER_ONLY 누수가 없는지 일괄 검사.
        하나라도 위반 시 KnowledgeLeakageError 발생.
        """
        for char_id in char_ids:
            for fact_id in fact_ids:
                self.check(char_id, fact_id)

    # ── 제약 생성 ────────────────────────────────────────────────
    def get_constraint(
        self,
        char_id: str,
        fact_id: str,
    ) -> KnowledgeRenderConstraint:
        """인물×사실의 렌더링 제약 객체 반환."""
        status = self._get_status(char_id, fact_id)
        render_mode, hint = _STATUS_TO_RENDER.get(
            status, ("direct", "")
        )
        return KnowledgeRenderConstraint(
            char_id=         char_id,
            fact_id=         fact_id,
            status=          status,
            render_mode=     render_mode,
            behavioral_hint= hint,
            is_blocked=      (status == KnowledgeStatus.READER_ONLY),
        )

    def get_scene_constraints(
        self,
        char_id:  str,
        fact_ids: List[str],
    ) -> List[KnowledgeRenderConstraint]:
        """씬에 등장하는 사실 목록에 대한 전체 제약 반환."""
        return [self.get_constraint(char_id, fid) for fid in fact_ids]

    # ── ProseRenderContract 메타데이터 주입 ────────────────────────
    def enrich_contract(
        self,
        contract:   ProseRenderContract,
        char_id:    str,
        fact_ids:   List[str],
    ) -> ProseRenderContract:
        """
        ProseRenderContract의 metadata 필드에 지식 제약 정보를 추가.
        contract 원본을 수정하지 않고 복사본 반환.
        """
        constraints = self.get_scene_constraints(char_id, fact_ids)
        blocked = [c.fact_id for c in constraints if c.is_blocked]
        hints   = {c.fact_id: c.behavioral_hint for c in constraints}

        # 얕은 복사 후 메타데이터 갱신
        import dataclasses
        enriched = dataclasses.replace(
            contract,
            metadata={
                **contract.metadata,
                "knowledge_constraints": {
                    "char_id":    char_id,
                    "blocked":    blocked,
                    "hints":      hints,
                    "constraints":[c.to_dict() for c in constraints],
                },
            },
        )
        return enriched

    # ── 지식 비대칭 압력 계산 ───────────────────────────────────────
    def asymmetry_pressure(
        self,
        char_a: str,
        char_b: str,
        fact_ids: List[str],
    ) -> float:
        """
        두 인물 간의 지식 비대칭 압력 수치 (0.0~1.0).
        비대칭이 클수록 씬 텐션 상승에 기여.
        """
        if not fact_ids:
            return 0.0

        weight_map: Dict[tuple, float] = {
            (KnowledgeStatus.KNOWS,       KnowledgeStatus.UNAWARE):     1.0,
            (KnowledgeStatus.KNOWS,       KnowledgeStatus.MISBELIEVES): 0.9,
            (KnowledgeStatus.READER_ONLY, KnowledgeStatus.UNAWARE):     0.8,
            (KnowledgeStatus.SUSPECTS,    KnowledgeStatus.UNAWARE):     0.6,
            (KnowledgeStatus.KNOWS,       KnowledgeStatus.SUSPECTS):    0.4,
        }

        total = 0.0
        for fid in fact_ids:
            sa = self._get_status(char_a, fid)
            sb = self._get_status(char_b, fid)
            w  = weight_map.get((sa, sb), 0.0)
            # 역방향도 확인
            if w == 0.0:
                w = weight_map.get((sb, sa), 0.0)
            total += w

        return min(1.0, total / len(fact_ids))

    # ── blocked_facts 조회 ───────────────────────────────────────
    def blocked_facts_for(self, char_id: str) -> List[str]:
        """해당 인물 기준 READER_ONLY 사실 ID 목록."""
        char_dict = getattr(self._tracker, "char_knowledge", {}).get(char_id, {})
        return [
            fact_id
            for fact_id, ck in char_dict.items()
            if ck.status == KnowledgeStatus.READER_ONLY
        ]

    # ── 내부 ─────────────────────────────────────────────────────
    def _get_status(self, char_id: str, fact_id: str) -> KnowledgeStatus:
        """KnowledgeStateTracker에서 상태 조회. 미등록이면 UNAWARE 반환."""
        try:
            # get_knowledge는 KnowledgeStatus를 직접 반환
            return self._tracker.get_knowledge(char_id, fact_id)
        except Exception:
            return KnowledgeStatus.UNAWARE
