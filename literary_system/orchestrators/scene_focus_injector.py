"""
V325 - SceneFocusInjector  (Phase 3)
씬별 압축 컨텍스트 조립기.

설계 원칙 (P2 외과적 통합):
  - Temporal Delta: 씬 진행도 기반 시간 압력
  - Emotional Pressure: tension_target + 씬 내 위치 가중치
  - Hidden Intent: 캐릭터 상태 dict에서 목적 추출
  - LibrarianRAGBridge 선택적 연동 (None이면 RAG 생략)
  - LLM 0회 — 완전 로컬
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ────────────────────────────────────────────────────────────────
# SceneFocusContext 데이터클래스
# ────────────────────────────────────────────────────────────────

@dataclass
class SceneFocusContext:
    """씬 생성 직전 조립된 압축 컨텍스트."""
    scene_id:           str
    temporal_delta:     float          # 0.0~1.0 시간 진행도
    emotional_pressure: float          # 0.0~1.0 감정 압력
    hidden_intent:      str            # 핵심 캐릭터 숨은 목적
    retrieved_docs:     list[dict]     # RAG 검색 결과 (없으면 [])
    micro_context:      str            # 최종 조립 컨텍스트 문자열

    def to_dict(self) -> dict[str, Any]:
        return {
            "scene_id":           self.scene_id,
            "temporal_delta":     round(self.temporal_delta, 4),
            "emotional_pressure": round(self.emotional_pressure, 4),
            "hidden_intent":      self.hidden_intent,
            "retrieved_docs":     self.retrieved_docs,
            "micro_context":      self.micro_context,
        }


# ────────────────────────────────────────────────────────────────
# SceneFocusInjector
# ────────────────────────────────────────────────────────────────

class SceneFocusInjector:
    """
    SequencePlan + 씬 인덱스 → SceneFocusContext 조립.

    사용 예:
        injector = SceneFocusInjector(rag_bridge=bridge)
        ctx = injector.build(
            seq_plan, scene_index=3,
            total_scenes_in_seq=10,
            character_states={"고애신": {"intent": "탈출"}}
        )
    """

    def __init__(
        self,
        rag_bridge: Any | None = None,    # LibrarianRAGBridge | None
        rag_top_k: int = 5,
    ) -> None:
        self._rag   = rag_bridge
        self._top_k = rag_top_k

    # ── 공개 API ─────────────────────────────────────────────────

    def build(
        self,
        seq_plan: Any,                       # SequencePlan
        scene_index: int,                    # 시퀀스 내 씬 순번 (0-based)
        total_scenes_in_seq: int,            # 시퀀스 내 전체 씬 수
        character_states: dict[str, Any] | None = None,
        scene_id: str | None = None,
    ) -> SceneFocusContext:
        """
        씬별 SceneFocusContext 생성.

        Args:
            seq_plan:           SequencePlan 인스턴스
            scene_index:        시퀀스 내 씬 순번 (0-based)
            total_scenes_in_seq: 시퀀스 내 전체 씬 수
            character_states:   {캐릭터명: {intent, location, emotion, ...}}
            scene_id:           None이면 자동 생성

        Returns:
            SceneFocusContext
        """
        if scene_id is None:
            seq_id   = getattr(seq_plan, "seq_id", "seq00")
            scene_id = f"{seq_id}_sc{scene_index+1:03d}"

        temporal   = self._calc_temporal_delta(seq_plan, scene_index, total_scenes_in_seq)
        emotional  = self._calc_emotional_pressure(seq_plan, scene_index, total_scenes_in_seq)
        intent_str = self._extract_hidden_intent(character_states or {})
        docs       = self._retrieve_docs(seq_plan, scene_id, character_states)
        micro      = self._assemble_micro_context(
            seq_plan, temporal, emotional, intent_str, docs
        )

        return SceneFocusContext(
            scene_id           = scene_id,
            temporal_delta     = temporal,
            emotional_pressure = emotional,
            hidden_intent      = intent_str,
            retrieved_docs     = docs,
            micro_context      = micro,
        )

    # ── 내부 헬퍼 ────────────────────────────────────────────────

    def _calc_temporal_delta(
        self,
        seq_plan: Any,
        scene_index: int,
        total: int,
    ) -> float:
        """
        시간 진행도 = 에피소드 전체 기준 현재 씬 위치.
        pct_start ~ pct_end 구간 내 씬 인덱스 비율.
        """
        pct_start = getattr(seq_plan, "pct_start", 0.0)
        pct_end   = getattr(seq_plan, "pct_end",   1.0)
        span      = pct_end - pct_start
        if total <= 1:
            return round(pct_start + span * 0.5, 4)
        local_frac = scene_index / (total - 1)
        return round(pct_start + span * local_frac, 4)

    def _calc_emotional_pressure(
        self,
        seq_plan: Any,
        scene_index: int,
        total: int,
    ) -> float:
        """
        감정 압력 = tension_target × (1 + 씬 내 진행 보정).
        씬이 후반부일수록 tension_target에 수렴.
        """
        tension = getattr(seq_plan, "tension_target", 0.5)
        if total <= 1:
            return round(min(1.0, tension), 4)
        progress = scene_index / (total - 1)
        # 앞부분은 tension의 70%, 뒷부분은 100%
        weight   = 0.70 + 0.30 * progress
        return round(min(1.0, tension * weight), 4)

    def _extract_hidden_intent(
        self,
        character_states: dict[str, Any],
    ) -> str:
        """
        캐릭터 상태에서 숨은 목적(intent) 추출.
        여러 캐릭터가 있으면 '|'로 구분.
        """
        intents: list[str] = []
        for char_name, state in character_states.items():
            if isinstance(state, dict):
                intent = state.get("intent") or state.get("hidden_intent", "")
                if intent:
                    intents.append(f"{char_name}: {intent}")
        return " | ".join(intents) if intents else "명시된 숨은 의도 없음"

    def _retrieve_docs(
        self,
        seq_plan: Any,
        scene_id: str,
        character_states: dict[str, Any] | None,
    ) -> list[dict]:
        """LibrarianRAGBridge가 있으면 관련 문서 검색."""
        if self._rag is None:
            return []
        query_parts: list[str] = []
        goal = getattr(seq_plan, "goal", "")
        if goal:
            query_parts.append(goal)
        if character_states:
            query_parts.extend(list(character_states.keys())[:3])

        query = " ".join(query_parts) or scene_id
        try:
            docs = self._rag.retrieve_for_scene(query, k=self._top_k)
            return [
                {"doc_id": d.doc_id, "content": d.content, "score": round(d.score, 4)}
                for d in docs
            ]
        except Exception:
            return []

    def _assemble_micro_context(
        self,
        seq_plan: Any,
        temporal: float,
        emotional: float,
        intent: str,
        docs: list[dict],
    ) -> str:
        """
        최종 Micro-Context 문자열 조립.
        PromptAssembler의 context 파라미터로 직접 전달 가능.
        """
        goal     = getattr(seq_plan, "goal", "")
        act_idx  = getattr(seq_plan, "act_index", 0)
        act_name = {1: "기(起)", 2: "승(承)", 3: "전(轉)", 4: "결(結)"}.get(act_idx, "")

        lines = [
            f"[시퀀스 목표] {goal}",
            f"[막 위치] {act_name}  [시간진행도] {temporal:.2f}  [감정압력] {emotional:.2f}",
            f"[숨은 의도] {intent}",
        ]

        if docs:
            refs = "  /  ".join(d["content"][:40] for d in docs[:3])
            lines.append(f"[참조 문서] {refs}")

        return "\n".join(lines)
