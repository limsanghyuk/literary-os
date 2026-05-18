"""
V562 MultiWorkCore — 작가별 N작품 동시 처리 코어
작품 ID 격리 + 공유 자산 관리 인터페이스

설계 원칙:
- 각 프로젝트는 독립된 project_id 네임스페이스로 격리
- 공유 자산(캐릭터, 월드)은 SharedCharacterDB/SharedWorldDB에서 관리 (V563-V564)
- 최대 동시 세션 수(MAX_CONCURRENT)를 초과하면 대기열 진입
- LLM-0: 외부 LLM 호출 없음 (ADR-015/031 준수)
"""

from __future__ import annotations

import uuid
import time
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any


class WorkStatus(Enum):
    """프로젝트 상태 FSM."""
    DRAFT = "draft"          # 초기 생성
    ACTIVE = "active"        # 세션 활성화
    PAUSED = "paused"        # 일시 정지
    COMPLETED = "completed"  # 완료
    ARCHIVED = "archived"    # 보관


class ProjectConflict(Exception):
    """프로젝트 충돌 예외 (중복 ID, 세션 한도 초과 등)."""
    pass


@dataclass
class WorkProject:
    """단일 작품/프로젝트 메타데이터.

    Attributes:
        project_id: 시스템 전역 고유 ID (UUID4)
        author_id:  작가 식별자
        title:      작품 제목
        genre:      장르 (drama, fantasy, romance, …)
        created_at: Unix 타임스탬프
        status:     WorkStatus FSM
        metadata:   자유 형식 확장 필드
    """
    project_id: str
    author_id: str
    title: str
    genre: str
    created_at: float = field(default_factory=time.time)
    status: WorkStatus = WorkStatus.DRAFT
    metadata: Dict[str, Any] = field(default_factory=dict)

    # 공유 자산 참조 (V563-V566에서 채워짐)
    shared_character_refs: List[str] = field(default_factory=list)
    shared_world_refs: List[str] = field(default_factory=list)

    def activate(self) -> None:
        """DRAFT → ACTIVE 전환."""
        if self.status not in (WorkStatus.DRAFT, WorkStatus.PAUSED):
            raise ProjectConflict(
                f"Cannot activate project in state {self.status.value}"
            )
        self.status = WorkStatus.ACTIVE

    def pause(self) -> None:
        """ACTIVE → PAUSED 전환."""
        if self.status != WorkStatus.ACTIVE:
            raise ProjectConflict(
                f"Cannot pause project in state {self.status.value}"
            )
        self.status = WorkStatus.PAUSED

    def complete(self) -> None:
        """ACTIVE/PAUSED → COMPLETED 전환."""
        if self.status not in (WorkStatus.ACTIVE, WorkStatus.PAUSED):
            raise ProjectConflict(
                f"Cannot complete project in state {self.status.value}"
            )
        self.status = WorkStatus.COMPLETED

    def archive(self) -> None:
        """COMPLETED → ARCHIVED 전환."""
        if self.status != WorkStatus.COMPLETED:
            raise ProjectConflict(
                f"Cannot archive project in state {self.status.value}"
            )
        self.status = WorkStatus.ARCHIVED


@dataclass
class WorkSession:
    """활성 작품 처리 세션 — 프로젝트 격리 컨텍스트.

    각 세션은 project_id에 바인딩되며 독립된 처리 상태를 유지한다.
    shared_assets는 MultiWorkCore가 관리하는 공유 자산에 대한
    읽기 전용 뷰를 제공한다.

    Attributes:
        session_id:    세션 고유 ID
        project_id:    연결된 프로젝트 ID
        author_id:     작가 ID
        started_at:    세션 시작 타임스탬프
        episode_count: 현재 세션에서 처리된 에피소드 수
        token_budget:  남은 토큰 예산 (-1 = 무제한)
        context:       세션 격리 컨텍스트 딕셔너리
    """
    session_id: str
    project_id: str
    author_id: str
    started_at: float = field(default_factory=time.time)
    episode_count: int = 0
    token_budget: int = -1
    context: Dict[str, Any] = field(default_factory=dict)

    def record_episode(self, tokens_used: int = 0) -> None:
        """에피소드 처리 기록."""
        self.episode_count += 1
        if self.token_budget > 0:
            self.token_budget -= tokens_used

    def is_budget_exhausted(self) -> bool:
        """토큰 예산 소진 여부."""
        return self.token_budget == 0

    def summary(self) -> Dict[str, Any]:
        """세션 요약 반환."""
        return {
            "session_id": self.session_id,
            "project_id": self.project_id,
            "author_id": self.author_id,
            "started_at": self.started_at,
            "episode_count": self.episode_count,
            "token_budget": self.token_budget,
        }


class MultiWorkCore:
    """작가별 N작품 동시 처리 코어.

    핵심 책임:
    1. 프로젝트 등록 / 조회 / 상태 전환
    2. 세션 생성 및 격리 보장 (project_id 네임스페이스)
    3. 동시 세션 수 제한 (MAX_CONCURRENT)
    4. 공유 자산 참조 등록 인터페이스 (V563-V566 확장점)
    5. Thread-safe 연산 (RLock)

    LLM-0: 외부 LLM 호출 없음.
    """

    MAX_CONCURRENT: int = 10  # 동시 활성 세션 최대 수

    def __init__(self, max_concurrent: int = MAX_CONCURRENT) -> None:
        self._max_concurrent = max_concurrent
        self._projects: Dict[str, WorkProject] = {}          # project_id → WorkProject
        self._sessions: Dict[str, WorkSession] = {}          # session_id → WorkSession
        self._project_session: Dict[str, str] = {}           # project_id → session_id
        self._shared_assets: Dict[str, Any] = {}             # asset_key → asset_value
        self._lock = threading.RLock()

    # ------------------------------------------------------------------ #
    # 프로젝트 관리
    # ------------------------------------------------------------------ #

    def register_project(
        self,
        author_id: str,
        title: str,
        genre: str,
        project_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> WorkProject:
        """새 프로젝트 등록.

        Args:
            author_id:  작가 ID
            title:      작품 제목
            genre:      장르
            project_id: 외부 지정 ID (None이면 UUID4 자동 생성)
            metadata:   추가 메타데이터

        Returns:
            등록된 WorkProject 인스턴스

        Raises:
            ProjectConflict: project_id 중복
        """
        with self._lock:
            pid = project_id or str(uuid.uuid4())
            if pid in self._projects:
                raise ProjectConflict(f"Project already registered: {pid}")
            proj = WorkProject(
                project_id=pid,
                author_id=author_id,
                title=title,
                genre=genre,
                metadata=metadata or {},
            )
            self._projects[pid] = proj
            return proj

    def get_project(self, project_id: str) -> Optional[WorkProject]:
        """프로젝트 조회."""
        return self._projects.get(project_id)

    def list_projects(
        self,
        author_id: Optional[str] = None,
        status: Optional[WorkStatus] = None,
    ) -> List[WorkProject]:
        """프로젝트 목록 반환 (필터 옵션)."""
        with self._lock:
            result = list(self._projects.values())
            if author_id is not None:
                result = [p for p in result if p.author_id == author_id]
            if status is not None:
                result = [p for p in result if p.status == status]
            return result

    def remove_project(self, project_id: str) -> bool:
        """프로젝트 제거 (DRAFT/ARCHIVED 상태만 허용).

        Returns:
            제거 성공 여부
        """
        with self._lock:
            proj = self._projects.get(project_id)
            if proj is None:
                return False
            if proj.status not in (WorkStatus.DRAFT, WorkStatus.ARCHIVED):
                raise ProjectConflict(
                    f"Cannot remove project in state {proj.status.value}"
                )
            # 세션도 함께 정리
            sid = self._project_session.pop(project_id, None)
            if sid:
                self._sessions.pop(sid, None)
            del self._projects[project_id]
            return True

    # ------------------------------------------------------------------ #
    # 세션 관리
    # ------------------------------------------------------------------ #

    def open_session(
        self,
        project_id: str,
        token_budget: int = -1,
    ) -> WorkSession:
        """프로젝트 활성 세션 오픈.

        Args:
            project_id:   세션을 열 프로젝트 ID
            token_budget: 세션 토큰 예산 (-1 = 무제한)

        Returns:
            새 WorkSession

        Raises:
            ProjectConflict: 프로젝트 미존재, 이미 세션 존재, 동시 한도 초과
        """
        with self._lock:
            proj = self._projects.get(project_id)
            if proj is None:
                raise ProjectConflict(f"Project not found: {project_id}")

            if project_id in self._project_session:
                raise ProjectConflict(
                    f"Session already open for project: {project_id}"
                )

            active_count = len(self._project_session)
            if active_count >= self._max_concurrent:
                raise ProjectConflict(
                    f"Max concurrent sessions reached: {self._max_concurrent}"
                )

            proj.activate()
            sid = str(uuid.uuid4())
            session = WorkSession(
                session_id=sid,
                project_id=project_id,
                author_id=proj.author_id,
                token_budget=token_budget,
            )
            self._sessions[sid] = session
            self._project_session[project_id] = sid
            return session

    def get_session(self, project_id: str) -> Optional[WorkSession]:
        """프로젝트 현재 세션 조회."""
        with self._lock:
            sid = self._project_session.get(project_id)
            return self._sessions.get(sid) if sid else None

    def close_session(
        self,
        project_id: str,
        mark_completed: bool = False,
    ) -> Optional[WorkSession]:
        """세션 종료.

        Args:
            project_id:     세션을 닫을 프로젝트
            mark_completed: True이면 프로젝트를 COMPLETED로 전환, 아니면 PAUSED

        Returns:
            닫힌 WorkSession (없으면 None)
        """
        with self._lock:
            sid = self._project_session.pop(project_id, None)
            if sid is None:
                return None
            session = self._sessions.pop(sid, None)
            proj = self._projects.get(project_id)
            if proj:
                if mark_completed:
                    proj.complete()
                else:
                    proj.pause()
            return session

    def active_session_count(self) -> int:
        """현재 활성 세션 수."""
        return len(self._project_session)

    # ------------------------------------------------------------------ #
    # 공유 자산 인터페이스 (V563-V566 확장점)
    # ------------------------------------------------------------------ #

    def register_shared_asset(self, asset_key: str, asset_value: Any) -> None:
        """공유 자산 등록.

        V563 SharedCharacterDB, V564 SharedWorldDB에서
        캐릭터/월드 객체를 등록할 때 사용.
        """
        with self._lock:
            self._shared_assets[asset_key] = asset_value

    def get_shared_asset(self, asset_key: str) -> Optional[Any]:
        """공유 자산 조회."""
        return self._shared_assets.get(asset_key)

    def list_shared_asset_keys(self) -> List[str]:
        """등록된 공유 자산 키 목록."""
        return list(self._shared_assets.keys())

    def link_asset_to_project(
        self,
        project_id: str,
        asset_key: str,
        asset_type: str = "character",
    ) -> None:
        """공유 자산을 프로젝트에 연결.

        Args:
            project_id: 대상 프로젝트
            asset_key:  공유 자산 키
            asset_type: 'character' | 'world'
        """
        with self._lock:
            proj = self._projects.get(project_id)
            if proj is None:
                raise ProjectConflict(f"Project not found: {project_id}")
            if asset_key not in self._shared_assets:
                raise ProjectConflict(f"Shared asset not found: {asset_key}")
            if asset_type == "character":
                if asset_key not in proj.shared_character_refs:
                    proj.shared_character_refs.append(asset_key)
            elif asset_type == "world":
                if asset_key not in proj.shared_world_refs:
                    proj.shared_world_refs.append(asset_key)
            else:
                raise ValueError(f"Unknown asset_type: {asset_type}")

    # ------------------------------------------------------------------ #
    # 통계 / 상태
    # ------------------------------------------------------------------ #

    def stats(self) -> Dict[str, Any]:
        """코어 통계 반환."""
        with self._lock:
            by_status: Dict[str, int] = {}
            for proj in self._projects.values():
                key = proj.status.value
                by_status[key] = by_status.get(key, 0) + 1
            return {
                "total_projects": len(self._projects),
                "active_sessions": len(self._project_session),
                "max_concurrent": self._max_concurrent,
                "shared_assets": len(self._shared_assets),
                "by_status": by_status,
            }
