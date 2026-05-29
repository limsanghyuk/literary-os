"""
V649 — EditorAgent (SP-C.2 Multi-Agent Ensemble).
C-M-09: Editor는 최종 통합 담당 — 거부권 없음(editor_can_reject=False).
KoreanCadencePlanner 폴리시 적용 (cadence 교정).
LLM-0: 외부 API 직접 호출 없음.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class EditedScene:
    """편집 완료 씬 — EditorAgent 최종 산출물."""
    scene_id: str
    final_text: str
    cadence_applied: bool
    polish_notes: List[str] = field(default_factory=list)
    source_draft_attempt: int = 1


class EditorAgent:
    """
    최종 통합·교정 에이전트 (C-M-09).

    - Blueprint constraints["editor_can_reject"] == False 준수.
    - 거부 없이 항상 최선의 편집본 반환.
    - KoreanCadencePlanner 있으면 적용, 없으면 기본 교정.
    """

    ROLE = "editor"

    def __init__(
        self,
        cadence_planner: Optional[Any] = None,
    ) -> None:
        self._cadence_planner = cadence_planner

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def finalize(
        self,
        draft_dict: Dict[str, Any],
        blueprint_dict: Optional[Dict[str, Any]] = None,
        critic_report_dict: Optional[Dict[str, Any]] = None,
    ) -> EditedScene:
        """
        초안을 최종 편집.

        C-M-09: 거부권 없음 — 어떤 초안도 최선으로 편집해 반환.

        Args:
            draft_dict:          ScriptDraft 딕셔너리 (draft_text 포함).
            blueprint_dict:      원본 Blueprint (제약 검증용, 선택).
            critic_report_dict:  CriticReport 딕셔너리 (제안 참조, 선택).

        Returns:
            EditedScene
        """
        # C-M-09: editor_can_reject 무시 — 항상 처리
        scene_id: str = draft_dict.get("scene_id", "unknown")
        draft_text: str = draft_dict.get("draft_text", "")
        attempt_num: int = draft_dict.get("attempt_num", 1)

        polish_notes: List[str] = []

        # 1. Critic 제안 반영 메모
        if critic_report_dict:
            suggestions = critic_report_dict.get("suggestions", [])
            for sug in suggestions:
                polish_notes.append(f"[편집 반영] {sug}")

        # 2. KoreanCadencePlanner 적용
        final_text, cadence_applied = self._apply_cadence(
            draft_text, blueprint_dict, polish_notes
        )

        return EditedScene(
            scene_id=scene_id,
            final_text=final_text,
            cadence_applied=cadence_applied,
            polish_notes=polish_notes,
            source_draft_attempt=attempt_num,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------
    def _apply_cadence(
        self,
        text: str,
        blueprint_dict: Optional[Dict[str, Any]],
        polish_notes: List[str],
    ) -> tuple[str, bool]:
        """KoreanCadencePlanner 적용 또는 기본 교정."""
        if self._cadence_planner is not None:
            try:
                result = self._cadence_planner.apply(text, blueprint_dict or {})
                polished = str(result)
                polish_notes.append("KoreanCadencePlanner 적용 완료")
                return polished, True
            except Exception as e:
                polish_notes.append(f"KoreanCadencePlanner 예외 ({e}) — 기본 교정 적용")

        # 기본 교정: 앞뒤 공백 제거 + 연속 빈줄 1개로 압축
        lines = text.split("\n")
        condensed: List[str] = []
        blank_count = 0
        for line in lines:
            stripped = line.rstrip()
            if stripped == "":
                blank_count += 1
                if blank_count <= 1:
                    condensed.append("")
            else:
                blank_count = 0
                condensed.append(stripped)
        final = "\n".join(condensed).strip()
        polish_notes.append("기본 공백 교정 적용")
        return final, False
