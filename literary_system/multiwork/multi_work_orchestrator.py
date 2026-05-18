"""
V570 MultiWorkOrchestrator — Stage C 최상위 오케스트레이터

V562~V568 모든 컴포넌트를 조율:
  MultiWorkCore + SharedCharacterDB + SharedWorldDB +
  GenreTransferLearning + ProjectIsolationManager +
  MultiWorkCIM + AuthorLicenseAPI

책임:
- 작가 등록부터 작품 완료까지 생명주기 조율
- 씬 처리 이벤트 라우팅 (CIM 기록, 아크 기록, 격리 컨텍스트 업데이트)
- 라이선스 검증 통합 (모든 주요 작업 전 검증)
- 통합 상태 스냅샷 제공

LLM-0: 외부 LLM 호출 없음.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

from .multi_work_core import MultiWorkCore, WorkProject, WorkSession, ProjectConflict
from .shared_character_db import SharedCharacterDB
from .shared_world_db import SharedWorldDB
from .genre_transfer import GenreTransferLearning
from .project_isolation import ProjectIsolationManager, IsolationPolicy
from .multi_work_cim import MultiWorkCIM
from .author_license_api import AuthorLicenseAPI, LicenseType, LicenseScope


@dataclass
class SceneProcessEvent:
    """씬 처리 이벤트 — 오케스트레이터에 전달되는 데이터."""
    project_id: str
    scene_id: str
    characters_present: List[str]          # 씬에 등장하는 캐릭터 ID 목록
    arc_deltas: Dict[str, float] = field(default_factory=dict)   # char_id → delta
    tokens_used: int = 0
    context_updates: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OrchestratorSnapshot:
    """오케스트레이터 전체 상태 스냅샷."""
    core_stats: Dict[str, Any]
    cim_stats: Dict[str, Any]
    char_db_stats: Dict[str, Any]
    world_db_stats: Dict[str, Any]
    gtl_stats: Dict[str, Any]
    iso_stats: Dict[str, Any]
    license_stats: Dict[str, Any]
    total_scenes_processed: int


class MultiWorkOrchestrator:
    """Stage C MultiWorkOrchestrator.

    Usage:
        orch = MultiWorkOrchestrator()
        orch.register_author("alice", LicenseType.COMMERCIAL)
        proj = orch.create_project("alice", "내 드라마", "drama")
        session = orch.open_session("alice", proj.project_id)
        orch.process_scene(SceneProcessEvent(
            project_id=proj.project_id,
            scene_id="s-001",
            characters_present=["hero", "villain"],
            arc_deltas={"hero": 0.2, "villain": -0.1},
            tokens_used=500,
        ))
        orch.close_session("alice", proj.project_id, mark_completed=True)
    """

    def __init__(
        self,
        max_concurrent: int = 10,
        cim_decay: float = 0.95,
    ) -> None:
        self.core = MultiWorkCore(max_concurrent=max_concurrent)
        self.char_db = SharedCharacterDB()
        self.world_db = SharedWorldDB()
        self.gtl = GenreTransferLearning()
        self.iso = ProjectIsolationManager()
        self.cim = MultiWorkCIM(decay=cim_decay)
        self.license_api = AuthorLicenseAPI()
        self._total_scenes: int = 0
        self._lock = threading.RLock()

    # ------------------------------------------------------------------ #
    # 작가 등록
    # ------------------------------------------------------------------ #

    def register_author(
        self,
        author_id: str,
        license_type: LicenseType = LicenseType.PERSONAL,
        expires_in_days: float = -1,
    ) -> None:
        """작가 등록 및 라이선스 발급."""
        self.license_api.issue_license(
            license_id=f"lic-{author_id}",
            author_id=author_id,
            license_type=license_type,
            expires_in_days=expires_in_days,
        )

    # ------------------------------------------------------------------ #
    # 프로젝트 생명주기
    # ------------------------------------------------------------------ #

    def create_project(
        self,
        author_id: str,
        title: str,
        genre: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> WorkProject:
        """프로젝트 생성 (라이선스 검증 포함).

        .. note::
            **COMMERCIAL 이상 라이선스 필요.**
            PERSONAL 라이선스는 MULTI_WORK 스코프를 포함하지 않으므로
            이 메서드 호출 시 LicenseViolation이 발생합니다.
            register_author() 시 LicenseType.COMMERCIAL 이상을 사용하세요.

        Raises:
            LicenseViolation: MULTI_WORK 스코프 없음, 라이선스 없음, 프로젝트 한도 초과
        """
        self.license_api.validate_scope(author_id, LicenseScope.MULTI_WORK)
        self.license_api.validate_project_creation(author_id)

        proj = self.core.register_project(author_id, title, genre, metadata=metadata)
        self.license_api.record_project_created(author_id)
        return proj

    def open_session(self, author_id: str, project_id: str) -> WorkSession:
        """세션 오픈 + 격리 정책 등록."""
        self.license_api.validate_scope(author_id, LicenseScope.GENERATE)

        # 격리 정책 등록 (이미 있으면 skip)
        if self.iso.get_policy(project_id) is None:
            self.iso.register_policy(IsolationPolicy(project_id=project_id))

        # CIM 초기화
        if self.cim.get_project_cim(project_id) is None:
            self.cim.init_project(project_id)

        session = self.core.open_session(project_id)
        return session

    def close_session(
        self,
        author_id: str,
        project_id: str,
        mark_completed: bool = False,
    ) -> Optional[WorkSession]:
        """세션 종료."""
        return self.core.close_session(project_id, mark_completed=mark_completed)

    # ------------------------------------------------------------------ #
    # 씬 처리
    # ------------------------------------------------------------------ #

    def process_scene(self, event: SceneProcessEvent) -> None:
        """씬 처리 이벤트 라우팅.

        1. 세션 에피소드 기록
        2. CIM 상호작용 기록 (등장 캐릭터 쌍 전체)
        3. 캐릭터 아크 델타 기록
        4. 격리 컨텍스트 업데이트

        Raises:
            ProjectConflict: 세션 없는 프로젝트
        """
        with self._lock:
            session = self.core.get_session(event.project_id)
            if session is None:
                raise ProjectConflict(
                    f"No active session for project: {event.project_id}"
                )

            # 1. 세션 기록
            session.record_episode(tokens_used=event.tokens_used)
            self._total_scenes += 1

            # 2. CIM 기록 (등장 캐릭터 쌍)
            chars = event.characters_present
            project_cim = self.cim.get_project_cim(event.project_id)
            if project_cim:
                for i in range(len(chars)):
                    for j in range(i + 1, len(chars)):
                        project_cim.record_interaction(chars[i], chars[j])

            # 3. 아크 델타 기록
            for char_id, delta in event.arc_deltas.items():
                if self.char_db.get_character(char_id) is not None:
                    self.char_db.record_arc(char_id, event.scene_id, delta)

            # 4. 격리 컨텍스트 업데이트
            if self.iso.get_policy(event.project_id) and event.context_updates:
                for key, val in event.context_updates.items():
                    self.iso.write(event.project_id, key, val)

    # ------------------------------------------------------------------ #
    # 장르 전이
    # ------------------------------------------------------------------ #

    def apply_genre_transfer(
        self,
        author_id: str,
        project_id: str,
        source_genre: str,
        alpha: float = 0.3,
    ) -> Dict[str, float]:
        """장르 전이 결과를 프로젝트 세션 컨텍스트에 저장.

        Returns:
            전이된 스타일 파라미터 딕셔너리
        """
        proj = self.core.get_project(project_id)
        if proj is None:
            raise ProjectConflict(f"Project not found: {project_id}")

        transferred = self.gtl.transfer(
            source_genre, proj.genre, alpha=alpha, project_id=project_id
        )

        session = self.core.get_session(project_id)
        if session:
            session.context["style_params"] = transferred.params

        return transferred.params

    # ------------------------------------------------------------------ #
    # 상태 스냅샷
    # ------------------------------------------------------------------ #

    def snapshot(self) -> OrchestratorSnapshot:
        """현재 전체 시스템 상태 스냅샷."""
        return OrchestratorSnapshot(
            core_stats=self.core.stats(),
            cim_stats=self.cim.stats(),
            char_db_stats=self.char_db.stats(),
            world_db_stats=self.world_db.stats(),
            gtl_stats=self.gtl.stats(),
            iso_stats=self.iso.stats(),
            license_stats=self.license_api.stats(),
            total_scenes_processed=self._total_scenes,
        )
