"""
SP-C.2 V646 — DirectorAgent

씬 청사진(SceneBlueprint) 5요소를 생성하는 디렉터 에이전트.
ADR-106: Director is solely responsible for blueprint generation.
Agent Responsibility Matrix (C-M-09):
  - Director: 씬 청사진 5요소 | 단독 수정 권한 | round 1만 (재호출 없음)

LLM-0 원칙: 외부 LLM API 직접 호출 없음.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SceneBlueprint:
    """씬 청사진 5요소.

    Attributes:
        scene_id: 씬 식별자
        objective: 씬 목적 (등장인물 목표 + 갈등)
        setting: 배경 설명 (시간/공간/분위기)
        characters: 등장인물 목록 + 역할
        tone: 감정 톤 (e.g., 긴장, 로맨틱, 유머)
        constraints: 제약 조건 (C-M-09: 거부 권한 없음 원칙 포함)
    """
    scene_id: str
    objective: str
    setting: str
    characters: List[str] = field(default_factory=list)
    tone: str = "neutral"
    constraints: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scene_id": self.scene_id,
            "objective": self.objective,
            "setting": self.setting,
            "characters": self.characters,
            "tone": self.tone,
            "constraints": self.constraints,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "SceneBlueprint":
        return cls(
            scene_id=d.get("scene_id", ""),
            objective=d.get("objective", ""),
            setting=d.get("setting", ""),
            characters=d.get("characters", []),
            tone=d.get("tone", "neutral"),
            constraints=d.get("constraints", {}),
        )


class DirectorAgent:
    """씬 청사진 5요소 생성 에이전트.

    C-M-09: Director는 blueprint를 단독으로 수정하며 round 1에만 호출.
    재호출 없음 — AgentCoordinator가 round 1 종료 후 Script→Critic→Editor로 진행.
    """

    ROLE = "director"

    def __init__(self, scene_id_prefix: str = "scene") -> None:
        self._prefix = scene_id_prefix
        self._call_count = 0

    def generate_blueprint(
        self,
        manuscript_context: Optional[str] = None,
        episode_num: int = 1,
        scene_num: int = 1,
        tone: str = "neutral",
        characters: Optional[List[str]] = None,
        extra_constraints: Optional[Dict[str, Any]] = None,
    ) -> SceneBlueprint:
        """씬 청사진 5요소 생성.

        C-M-09: round 1에만 호출. AgentCoordinator가 이를 보장.
        """
        self._call_count += 1
        scene_id = f"{self._prefix}_ep{episode_num:02d}_sc{scene_num:02d}"

        # 컨텍스트 기반 청사진 구성 (LLM-0: 외부 호출 없음 — 규칙 기반)
        objective = self._derive_objective(manuscript_context, scene_num)
        setting = self._derive_setting(manuscript_context, episode_num)
        char_list = characters or ["주인공", "상대역"]

        constraints = {"editor_can_reject": False}  # C-M-09
        if extra_constraints:
            constraints.update(extra_constraints)

        return SceneBlueprint(
            scene_id=scene_id,
            objective=objective,
            setting=setting,
            characters=char_list,
            tone=tone,
            constraints=constraints,
        )

    def _derive_objective(self, ctx: Optional[str], scene_num: int) -> str:
        if ctx and len(ctx) > 20:
            snippet = ctx[:80].replace("\n", " ")
            return f"씬 {scene_num}: {snippet}... 에서의 갈등과 해소"
        return f"씬 {scene_num}: 등장인물 간 핵심 갈등 전개 및 목표 노출"

    def _derive_setting(self, ctx: Optional[str], episode_num: int) -> str:
        return f"에피소드 {episode_num}: 도심 배경, 낮 / 자연광, 감정적 긴장 고조"

    @property
    def call_count(self) -> int:
        return self._call_count
