"""
V566 ProjectIsolation — 프로젝트 격리 레이어

책임:
- 각 프로젝트의 사설 컨텍스트(private context) 보호
- 공유 자산 읽기 전용 접근 제어
- 프로젝트 간 데이터 누출 방지
- 격리 정책(IsolationPolicy) 정의 및 적용
- 접근 감사 로그

격리 모델:
- PRIVATE 키: project_id 네임스페이스로 격리, 타 프로젝트 접근 불가
- SHARED 키:  MultiWorkCore.shared_assets 경유 읽기 전용 접근 허용
- 쓰기:       항상 자기 프로젝트 컨텍스트에만 허용

LLM-0: 외부 LLM 호출 없음.
"""

from __future__ import annotations

import time
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Set


class AccessType(Enum):
    READ = "read"
    WRITE = "write"


class DataScope(Enum):
    PRIVATE = "private"    # 프로젝트 전용
    SHARED = "shared"      # 공유 (읽기 전용)


class IsolationViolation(Exception):
    """격리 정책 위반 예외."""
    pass


@dataclass
class IsolationPolicy:
    """프로젝트 격리 정책.

    Attributes:
        project_id:         적용 대상 프로젝트
        allow_shared_read:  공유 자산 읽기 허용 여부 (기본 True)
        blocked_keys:       접근 차단 키 목록 (블랙리스트)
        allowed_projects:   데이터 공유를 허용하는 타 프로젝트 ID (화이트리스트)
        audit_enabled:      접근 감사 활성화 여부
    """
    project_id: str
    allow_shared_read: bool = True
    blocked_keys: Set[str] = field(default_factory=set)
    allowed_projects: Set[str] = field(default_factory=set)
    audit_enabled: bool = True


@dataclass
class ProjectAuditEntry:
    """접근 감사 레코드."""
    entry_id: str
    project_id: str
    key: str
    access_type: AccessType
    scope: DataScope
    allowed: bool
    timestamp: float = field(default_factory=time.time)
    reason: str = ""


class ProjectIsolationManager:
    """프로젝트 격리 관리자.

    - 격리 정책 등록·조회
    - 컨텍스트 읽기/쓰기 접근 제어
    - 감사 로그 관리
    - Thread-safe (RLock)
    """

    def __init__(self) -> None:
        self._policies: Dict[str, IsolationPolicy] = {}
        self._private_ctx: Dict[str, Dict[str, Any]] = {}   # project_id → {key: value}
        self._audit_log: List[AuditEntry] = []
        self._audit_counter = 0
        self._lock = threading.RLock()

    # ------------------------------------------------------------------ #
    # 정책 관리
    # ------------------------------------------------------------------ #

    def register_policy(self, policy: IsolationPolicy) -> None:
        """격리 정책 등록.

        Raises:
            KeyError: 이미 정책이 등록된 프로젝트
        """
        with self._lock:
            if policy.project_id in self._policies:
                raise KeyError(
                    f"Policy already registered for: {policy.project_id}"
                )
            self._policies[policy.project_id] = policy
            self._private_ctx[policy.project_id] = {}

    def update_policy(self, project_id: str, **kwargs: Any) -> None:
        """정책 필드 업데이트."""
        with self._lock:
            policy = self._policies.get(project_id)
            if policy is None:
                raise KeyError(f"Policy not found: {project_id}")
            for k, v in kwargs.items():
                if hasattr(policy, k):
                    setattr(policy, k, v)

    def get_policy(self, project_id: str) -> Optional[IsolationPolicy]:
        return self._policies.get(project_id)

    # ------------------------------------------------------------------ #
    # 컨텍스트 접근 제어
    # ------------------------------------------------------------------ #

    def write(self, project_id: str, key: str, value: Any) -> None:
        """프로젝트 사설 컨텍스트 쓰기.

        Args:
            project_id: 쓰기 주체 프로젝트
            key:        컨텍스트 키
            value:      저장할 값

        Raises:
            IsolationViolation: 정책에 의해 차단된 키
            KeyError:           미등록 프로젝트
        """
        with self._lock:
            policy = self._policies.get(project_id)
            if policy is None:
                raise KeyError(f"Project not registered: {project_id}")

            if key in policy.blocked_keys:
                self._audit(project_id, key, AccessType.WRITE,
                            DataScope.PRIVATE, allowed=False,
                            reason="blocked_key")
                raise IsolationViolation(
                    f"Write to blocked key '{key}' denied for {project_id}"
                )

            self._private_ctx[project_id][key] = value
            self._audit(project_id, key, AccessType.WRITE,
                        DataScope.PRIVATE, allowed=True)

    def read_private(
        self, project_id: str, key: str, default: Any = None
    ) -> Any:
        """자기 프로젝트 사설 컨텍스트 읽기.

        Raises:
            KeyError:           미등록 프로젝트
            IsolationViolation: 차단된 키
        """
        with self._lock:
            policy = self._policies.get(project_id)
            if policy is None:
                raise KeyError(f"Project not registered: {project_id}")

            if key in policy.blocked_keys:
                self._audit(project_id, key, AccessType.READ,
                            DataScope.PRIVATE, allowed=False,
                            reason="blocked_key")
                raise IsolationViolation(
                    f"Read blocked key '{key}' denied for {project_id}"
                )

            value = self._private_ctx[project_id].get(key, default)
            self._audit(project_id, key, AccessType.READ,
                        DataScope.PRIVATE, allowed=True)
            return value

    def read_shared(
        self,
        project_id: str,
        key: str,
        shared_assets: Dict[str, Any],
    ) -> Any:
        """공유 자산 읽기 (격리 정책 검사 후).

        Args:
            project_id:    요청 프로젝트
            key:           공유 자산 키
            shared_assets: MultiWorkCore._shared_assets 딕셔너리

        Returns:
            공유 자산 값 (없으면 None)

        Raises:
            IsolationViolation: 공유 읽기가 허용되지 않은 경우
        """
        with self._lock:
            policy = self._policies.get(project_id)
            if policy is None:
                raise KeyError(f"Project not registered: {project_id}")

            if not policy.allow_shared_read:
                self._audit(project_id, key, AccessType.READ,
                            DataScope.SHARED, allowed=False,
                            reason="shared_read_disabled")
                raise IsolationViolation(
                    f"Shared read disabled for project: {project_id}"
                )

            if key in policy.blocked_keys:
                self._audit(project_id, key, AccessType.READ,
                            DataScope.SHARED, allowed=False,
                            reason="blocked_key")
                raise IsolationViolation(
                    f"Blocked key '{key}' denied for {project_id}"
                )

            value = shared_assets.get(key)
            self._audit(project_id, key, AccessType.READ,
                        DataScope.SHARED, allowed=True)
            return value

    def cross_project_read(
        self,
        requester_id: str,
        owner_id: str,
        key: str,
    ) -> Any:
        """타 프로젝트의 사설 컨텍스트에서 허가된 키 읽기.

        allowed_projects 화이트리스트에 owner_id가 있어야 허용.

        Raises:
            IsolationViolation: 화이트리스트 미등록 or 차단 키
        """
        with self._lock:
            req_policy = self._policies.get(requester_id)
            if req_policy is None:
                raise KeyError(f"Requester not registered: {requester_id}")
            if owner_id not in req_policy.allowed_projects:
                self._audit(requester_id, key, AccessType.READ,
                            DataScope.PRIVATE, allowed=False,
                            reason=f"cross_project_not_allowed:{owner_id}")
                raise IsolationViolation(
                    f"Cross-project read from {owner_id} not allowed "
                    f"for {requester_id}"
                )
            owner_ctx = self._private_ctx.get(owner_id, {})
            value = owner_ctx.get(key)
            self._audit(requester_id, key, AccessType.READ,
                        DataScope.PRIVATE, allowed=True,
                        reason=f"cross_project:{owner_id}")
            return value

    # ------------------------------------------------------------------ #
    # 감사 로그
    # ------------------------------------------------------------------ #

    def _audit(
        self,
        project_id: str,
        key: str,
        access_type: AccessType,
        scope: DataScope,
        allowed: bool,
        reason: str = "",
    ) -> None:
        """내부 감사 기록 (정책의 audit_enabled 확인)."""
        policy = self._policies.get(project_id)
        if policy and not policy.audit_enabled:
            return
        self._audit_counter += 1
        entry = AuditEntry(
            entry_id=f"audit-{self._audit_counter:06d}",
            project_id=project_id,
            key=key,
            access_type=access_type,
            scope=scope,
            allowed=allowed,
            reason=reason,
        )
        self._audit_log.append(entry)

    def get_audit_log(
        self,
        project_id: Optional[str] = None,
        allowed: Optional[bool] = None,
        limit: int = 100,
    ) -> List[AuditEntry]:
        """감사 로그 조회 (최신순)."""
        with self._lock:
            result = list(self._audit_log)
            if project_id:
                result = [e for e in result if e.project_id == project_id]
            if allowed is not None:
                result = [e for e in result if e.allowed == allowed]
            return result[-limit:]

    def violation_count(self, project_id: Optional[str] = None) -> int:
        """정책 위반 횟수."""
        logs = self.get_audit_log(project_id=project_id, allowed=False,
                                  limit=100000)
        return len(logs)

    # ------------------------------------------------------------------ #
    # 통계
    # ------------------------------------------------------------------ #

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "registered_projects": len(self._policies),
                "total_audit_entries": len(self._audit_log),
                "violations": self.violation_count(),
                "private_ctx_keys": {
                    pid: len(ctx)
                    for pid, ctx in self._private_ctx.items()
                },
            }

AuditEntry = ProjectAuditEntry  # V579 backward-compat alias
