"""
V327 P3 — BOOToSGOAdapter
BuildOpeningOrchestrator 출력 bundle → SceneGenerationOrchestrator 입력으로 변환.

책임:
  1. BOO bundle에서 character_states 추출 → SGO.run_episode() 입력
  2. BOO bundle에서 KnowledgeStateTracker 초기화 및 반환
  3. BOO bundle project_id 추출
"""
from __future__ import annotations

from typing import Any


class BOOToSGOAdapter:
    """
    BuildOpeningOrchestrator 결과 bundle을
    SceneGenerationOrchestrator 호환 입력으로 변환한다.

    Usage::

        adapter = BOOToSGOAdapter(bundle)
        char_states = adapter.character_states
        tracker     = adapter.knowledge_tracker  # KnowledgeStateTracker
        project_id  = adapter.project_id
    """

    def __init__(self, bundle: dict[str, Any]) -> None:
        self._bundle = bundle

    # ── 공개 프로퍼티 ──────────────────────────────────────────

    @property
    def project_id(self) -> str:
        """bundle에서 project_id 추출."""
        return self._bundle.get("project_id", "unknown_project")

    @property
    def character_states(self) -> dict[str, Any]:
        """
        bundle의 character_grid → SGO character_states 포맷 변환.

        SGO character_states 포맷::
            {
                "캐릭터명": {
                    "intent":   str,
                    "location": str,
                    "emotion":  str,
                    "role":     str,
                }
            }
        """
        return self._extract_character_states(self._bundle)

    @property
    def knowledge_tracker(self) -> Any:
        """
        bundle의 character_grid와 seed_contract로
        KnowledgeStateTracker를 초기화하여 반환.

        KnowledgeStateTracker 없는 환경이면 None 반환.
        """
        return self._build_knowledge_tracker(self._bundle)

    @property
    def seed_contract(self) -> dict[str, Any]:
        """원본 seed_contract 반환."""
        return self._bundle.get("seed_contract", {})

    @property
    def memory_summary(self) -> dict[str, Any]:
        """BOO가 생성한 메모리 요약."""
        return self._bundle.get("memory_summary", {})

    # ── 내부 변환 로직 ─────────────────────────────────────────

    @staticmethod
    def _extract_character_states(bundle: dict[str, Any]) -> dict[str, Any]:
        """
        character_grid → character_states.

        character_grid 구조::
            {
                "characters": [
                    {"char_id": "lead", "role_type": "lead",
                     "pressure_target": "...", ...},
                    ...
                ],
                "edges": [{"source": ..., "target": ..., "tension": 0.76}]
            }
        """
        # seed_contract에서 최종 literary state 가져오기 (있으면)
        memory = bundle.get("memory_summary", {})
        state_at_ep3: dict = memory.get("state_at_ep3", {}) or {}

        # episode 목록에서 character_grid 탐색
        episodes: list[dict] = bundle.get("episodes", [])
        char_grid: dict | None = None
        for ep in reversed(episodes):          # 최신 화 우선
            grid = ep.get("character_grid")
            if grid:
                char_grid = grid
                break

        # fallback: seed_contract의 기본 캐릭터
        seed: dict = bundle.get("seed_contract", {})
        if char_grid is None:
            char_grid = {
                "characters": [
                    {"char_id": "lead", "role_type": "lead",
                     "pressure_target": seed.get("genre", "갈등"), },
                    {"char_id": "foil", "role_type": "foil",
                     "pressure_target": "진실 vs 생존", },
                ],
                "edges": [],
            }

        char_states: dict[str, Any] = {}
        for char in char_grid.get("characters", []):
            cid = char.get("char_id", "unknown")
            # literary_state_after에서 각 인물의 마지막 상태 추출 (있으면)
            char_last = state_at_ep3.get(cid, {})
            char_states[cid] = {
                "intent":   char_last.get("intent",
                                char.get("pressure_target", "")),
                "location": char_last.get("location",
                                char.get("last_location", "미정")),
                "emotion":  char_last.get("emotion",
                                char.get("emotional_state", "긴장")),
                "role":     char.get("role_type", "unknown"),
            }
        return char_states

    @staticmethod
    def _build_knowledge_tracker(bundle: dict[str, Any]) -> Any:
        """
        KnowledgeStateTracker 초기화.
        literary_state / seed_contract의 잠복 정보들을 facts로 등록.
        """
        try:
            from literary_system.world.knowledge_state_tracker import (
                InformationType,
                KnowledgeStateTracker,
            )
        except ImportError:
            return None

        project_id = bundle.get("project_id", "unknown")
        tracker = KnowledgeStateTracker(project_id=project_id)

        seed: dict = bundle.get("seed_contract", {})
        required_objects: list[str] = seed.get("required_objects", [])

        # required_objects → 숨겨진 사실 등록
        for obj in required_objects:
            tracker.register_fact(
                fact_id=f"object_{obj}",
                fact_type=InformationType.OBJECT,
                description=f"극 중 핵심 오브젝트: {obj}",
                true_value=obj,
                episode_revealed_at=1,
                reader_knows=True,
            )

        # 인물별 기본 지식 상태: lead는 자신의 목표만, foil은 모름
        memory_summary: dict = bundle.get("memory_summary", {})
        residue_phases: dict = memory_summary.get("residue_phases", {})

        char_states = BOOToSGOAdapter._extract_character_states(bundle)
        for char_id in char_states:
            for obj in required_objects:
                fact_id = f"object_{obj}"
                # 잔류물 phase에 따라 지식 상태 결정
                phase = residue_phases.get(obj, "latent")
                if phase in ("active", "revealed"):
                    status = "knows"
                elif char_id == "lead":
                    status = "suspects"
                else:
                    status = "unaware"
                try:
                    tracker.set_knowledge(char_id, fact_id, status, episode_no=1)
                except Exception:
                    pass  # 지식 상태 설정 실패는 무시

        return tracker
