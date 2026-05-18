"""
V568 AuthorLicenseAPI — 작가 라이선스 관리 API

책임:
- 작가별 라이선스 등록·조회·만료 관리
- 프로젝트별 허용 작업 범위 정의 (스코프)
- 라이선스 유효성 검증 (만료·스코프 위반 감지)
- 사용량 추적 (작품 수, 씬 수, 토큰 수)
- CorpusValidator ALLOWED_LICENSES와 정합 유지

허용 라이선스 유형 (ADR-031 준수):
    PERSONAL, COMMERCIAL, ENTERPRISE, RESEARCH

LLM-0: 외부 LLM 호출 없음.
"""

from __future__ import annotations

import time
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Any


class LicenseType(Enum):
    PERSONAL = "personal"        # 개인 비상업 목적
    COMMERCIAL = "commercial"    # 상업 출판 허용
    ENTERPRISE = "enterprise"    # 다중 사용자·멀티 프로젝트
    RESEARCH = "research"        # 연구 목적 (제한적 상업화)


class LicenseScope(Enum):
    """허용 작업 스코프."""
    GENERATE = "generate"        # 콘텐츠 생성
    EXPORT = "export"            # 원고 내보내기
    FINE_TUNE = "fine_tune"      # 파인튜닝 데이터셋 사용
    MULTI_WORK = "multi_work"    # 멀티워크 기능
    API_ACCESS = "api_access"    # API 직접 접근


class LicenseViolation(Exception):
    """라이선스 정책 위반 예외."""
    pass


# 라이선스 유형별 기본 스코프
_DEFAULT_SCOPES: Dict[LicenseType, Set[LicenseScope]] = {
    LicenseType.PERSONAL: {
        LicenseScope.GENERATE,
        LicenseScope.EXPORT,
    },
    LicenseType.COMMERCIAL: {
        LicenseScope.GENERATE,
        LicenseScope.EXPORT,
        LicenseScope.MULTI_WORK,
        LicenseScope.API_ACCESS,
    },
    LicenseType.ENTERPRISE: {
        LicenseScope.GENERATE,
        LicenseScope.EXPORT,
        LicenseScope.FINE_TUNE,
        LicenseScope.MULTI_WORK,
        LicenseScope.API_ACCESS,
    },
    LicenseType.RESEARCH: {
        LicenseScope.GENERATE,
        LicenseScope.EXPORT,
        LicenseScope.FINE_TUNE,
    },
}

# 라이선스 유형별 최대 동시 작품 수 (-1 = 무제한)
_MAX_CONCURRENT_PROJECTS: Dict[LicenseType, int] = {
    LicenseType.PERSONAL: 3,
    LicenseType.COMMERCIAL: 10,
    LicenseType.ENTERPRISE: -1,
    LicenseType.RESEARCH: 5,
}


@dataclass
class AuthorLicense:
    """작가 라이선스.

    Attributes:
        license_id:    라이선스 고유 ID
        author_id:     작가 ID
        license_type:  라이선스 종류
        issued_at:     발급 타임스탬프
        expires_at:    만료 타임스탬프 (-1 = 영구)
        scopes:        허용 스코프 집합
        max_projects:  최대 동시 작품 수
        usage:         사용량 카운터 딕셔너리
    """
    license_id: str
    author_id: str
    license_type: LicenseType
    issued_at: float = field(default_factory=time.time)
    expires_at: float = -1.0          # -1 = 만료 없음
    scopes: Set[LicenseScope] = field(default_factory=set)
    max_projects: int = 3
    usage: Dict[str, int] = field(default_factory=lambda: {
        "projects_created": 0,
        "scenes_generated": 0,
        "tokens_used": 0,
    })

    def is_active(self) -> bool:
        """라이선스 활성 여부 (만료 검사)."""
        if self.expires_at < 0:
            return True
        return time.time() < self.expires_at

    def has_scope(self, scope: LicenseScope) -> bool:
        """스코프 허용 여부."""
        return scope in self.scopes

    def can_create_project(self) -> bool:
        """신규 프로젝트 생성 가능 여부."""
        if self.max_projects < 0:
            return True
        return self.usage["projects_created"] < self.max_projects

    def record_project_created(self) -> None:
        self.usage["projects_created"] += 1

    def record_scene_generated(self, tokens: int = 0) -> None:
        self.usage["scenes_generated"] += 1
        self.usage["tokens_used"] += tokens


class AuthorLicenseAPI:
    """작가 라이선스 관리 API.

    - 라이선스 발급·조회·만료
    - 스코프 검증
    - 사용량 추적
    - Thread-safe (RLock)
    """

    def __init__(self) -> None:
        self._licenses: Dict[str, AuthorLicense] = {}    # license_id → License
        self._author_licenses: Dict[str, List[str]] = {} # author_id → [license_id]
        self._lock = threading.RLock()

    # ------------------------------------------------------------------ #
    # 라이선스 발급
    # ------------------------------------------------------------------ #

    def issue_license(
        self,
        license_id: str,
        author_id: str,
        license_type: LicenseType,
        expires_in_days: float = -1,
        extra_scopes: Optional[Set[LicenseScope]] = None,
    ) -> AuthorLicense:
        """라이선스 발급.

        Args:
            license_id:      고유 ID
            author_id:       작가 ID
            license_type:    유형
            expires_in_days: 만료 일수 (-1 = 영구)
            extra_scopes:    추가 스코프

        Returns:
            발급된 AuthorLicense

        Raises:
            KeyError: license_id 중복
        """
        with self._lock:
            if license_id in self._licenses:
                raise KeyError(f"License already exists: {license_id}")

            expires_at = -1.0
            if expires_in_days > 0:
                expires_at = time.time() + expires_in_days * 86400

            scopes = set(_DEFAULT_SCOPES.get(license_type, set()))
            if extra_scopes:
                scopes |= extra_scopes

            lic = AuthorLicense(
                license_id=license_id,
                author_id=author_id,
                license_type=license_type,
                expires_at=expires_at,
                scopes=scopes,
                max_projects=_MAX_CONCURRENT_PROJECTS[license_type],
            )
            self._licenses[license_id] = lic
            self._author_licenses.setdefault(author_id, []).append(license_id)
            return lic

    # ------------------------------------------------------------------ #
    # 조회
    # ------------------------------------------------------------------ #

    def get_license(self, license_id: str) -> Optional[AuthorLicense]:
        return self._licenses.get(license_id)

    def get_active_license(self, author_id: str) -> Optional[AuthorLicense]:
        """작가의 가장 최근 활성 라이선스 반환."""
        with self._lock:
            ids = self._author_licenses.get(author_id, [])
            for lid in reversed(ids):
                lic = self._licenses.get(lid)
                if lic and lic.is_active():
                    return lic
            return None

    def list_licenses(
        self,
        author_id: Optional[str] = None,
        active_only: bool = False,
    ) -> List[AuthorLicense]:
        with self._lock:
            result = list(self._licenses.values())
            if author_id:
                result = [l for l in result if l.author_id == author_id]
            if active_only:
                result = [l for l in result if l.is_active()]
            return result

    # ------------------------------------------------------------------ #
    # 검증
    # ------------------------------------------------------------------ #

    def validate_scope(self, author_id: str, scope: LicenseScope) -> None:
        """작가의 활성 라이선스가 주어진 스코프를 허용하는지 검증.

        Raises:
            LicenseViolation: 라이선스 없음, 만료, 스코프 미허용
        """
        lic = self.get_active_license(author_id)
        if lic is None:
            raise LicenseViolation(
                f"No active license for author: {author_id}"
            )
        if not lic.has_scope(scope):
            raise LicenseViolation(
                f"Scope '{scope.value}' not allowed under "
                f"{lic.license_type.value} license"
            )

    def validate_project_creation(self, author_id: str) -> None:
        """신규 프로젝트 생성 권한 검증.

        Raises:
            LicenseViolation: 프로젝트 한도 초과
        """
        lic = self.get_active_license(author_id)
        if lic is None:
            raise LicenseViolation(f"No active license for: {author_id}")
        if not lic.can_create_project():
            raise LicenseViolation(
                f"Project limit ({lic.max_projects}) reached for {author_id}"
            )

    # ------------------------------------------------------------------ #
    # 사용량 기록
    # ------------------------------------------------------------------ #

    def record_project_created(self, author_id: str) -> None:
        """프로젝트 생성 기록 (활성 라이선스에 반영)."""
        lic = self.get_active_license(author_id)
        if lic:
            lic.record_project_created()

    def record_scene_generated(self, author_id: str, tokens: int = 0) -> None:
        """씬 생성 기록."""
        lic = self.get_active_license(author_id)
        if lic:
            lic.record_scene_generated(tokens)

    # ------------------------------------------------------------------ #
    # 만료 처리
    # ------------------------------------------------------------------ #

    def revoke_license(self, license_id: str) -> bool:
        """라이선스 즉시 만료 처리.

        Returns:
            성공 여부
        """
        with self._lock:
            lic = self._licenses.get(license_id)
            if lic is None:
                return False
            lic.expires_at = time.time() - 1  # 과거 시각으로 설정
            return True

    # ------------------------------------------------------------------ #
    # 통계
    # ------------------------------------------------------------------ #

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            active = [l for l in self._licenses.values() if l.is_active()]
            return {
                "total_licenses": len(self._licenses),
                "active_licenses": len(active),
                "authors": len(self._author_licenses),
                "by_type": {
                    lt.value: sum(
                        1 for l in active if l.license_type == lt
                    )
                    for lt in LicenseType
                },
            }
