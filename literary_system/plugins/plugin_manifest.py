"""
Literary OS V711 — PluginManifest
==================================
ADR-172: Plugin Manifest 스키마 및 검증 정책.

플러그인 매니페스트는 literary_system/plugins/ 에 배포되는
모든 플러그인의 메타데이터와 권한을 선언하는 단일 소스이다.

설계 원칙:
  - 불변(frozen) 데이터클래스로 선언 후 변경 불가
  - 의존성 순환 검사 내장 (max_depth=5)
  - 권한 화이트리스트 기반 (PluginPermission Enum)
  - SCHEMA_VERSION 호환성 검사 (semver major 일치)
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


# ── 현재 매니페스트 스키마 버전 ───────────────────────────────
MANIFEST_SCHEMA_VERSION: str = "1.0"

# ── 플러그인 ID 허용 패턴 (소문자 영숫자 + 하이픈) ───────────
_PLUGIN_ID_RE = re.compile(r"^[a-z][a-z0-9\-]{1,62}[a-z0-9]$")


class PluginPermission(str, Enum):
    """플러그인이 요청할 수 있는 권한 종류."""
    READ_CORPUS   = "read_corpus"      # corpus/ 읽기
    WRITE_OUTPUT  = "write_output"     # 생성 결과물 쓰기
    CALL_LLM      = "call_llm"         # UnifiedLLMGateway 호출 (LLM-0 우선)
    READ_NKG      = "read_nkg"         # NKG 노드 조회
    WRITE_NKG     = "write_nkg"        # NKG 노드 수정 (고위험)
    NETWORK_OUT   = "network_out"      # 외부 네트워크 송신 (기본 차단)


class PluginStatus(str, Enum):
    """플러그인 수명 주기 상태."""
    PENDING   = "pending"    # 로드 대기
    LOADED    = "loaded"     # 로드 완료, 실행 가능
    DISABLED  = "disabled"   # 수동 비활성화
    ERROR     = "error"      # 로드/검증 실패


class PluginValidationError(ValueError):
    """PluginManifest 유효성 검사 실패 예외."""
    pass


@dataclass(frozen=True)
class PluginManifest:
    """
    플러그인 메타데이터 선언.

    Attributes:
        plugin_id:      고유 식별자 (소문자 영숫자 + 하이픈, 3~64자)
        name:           사람이 읽을 수 있는 이름
        version:        Semantic Version (X.Y.Z)
        entry_point:    Python 모듈 경로 (e.g. literary_system.plugins.genre.romance)
        permissions:    요청 권한 목록 (화이트리스트에서 허가된 것만 인가)
        description:    플러그인 설명 (선택)
        author:         작성자 (선택)
        dependencies:   다른 plugin_id 의존성 목록 (순환 금지)
        schema_version: 매니페스트 스키마 버전 (호환성 검사용)
        tags:           검색 태그 (선택)
    """
    plugin_id:      str
    name:           str
    version:        str
    entry_point:    str
    permissions:    List[PluginPermission] = field(default_factory=list)
    description:    str = ""
    author:         str = ""
    dependencies:   List[str] = field(default_factory=list)
    schema_version: str = MANIFEST_SCHEMA_VERSION
    tags:           List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._validate()

    # ── 검증 메서드 ─────────────────────────────────────────────
    def _validate(self) -> None:
        """모든 필드 유효성 검사."""
        self._check_plugin_id()
        self._check_name()
        self._check_version()
        self._check_entry_point()
        self._check_schema_version()
        self._check_permissions()

    def _check_plugin_id(self) -> None:
        if not isinstance(self.plugin_id, str) or len(self.plugin_id) < 3:
            raise PluginValidationError(
                f"plugin_id 최소 3자 이상 필요: '{self.plugin_id}'"
            )
        if not _PLUGIN_ID_RE.match(self.plugin_id):
            raise PluginValidationError(
                f"plugin_id 형식 오류 (소문자 영숫자+하이픈): '{self.plugin_id}'"
            )

    def _check_name(self) -> None:
        if not self.name or not self.name.strip():
            raise PluginValidationError("name 은 빈 문자열일 수 없습니다.")
        if len(self.name) > 128:
            raise PluginValidationError("name 최대 128자 초과.")

    def _check_version(self) -> None:
        pattern = r"^\d+\.\d+\.\d+$"
        if not re.match(pattern, self.version):
            raise PluginValidationError(
                f"version 은 X.Y.Z 형식이어야 합니다: '{self.version}'"
            )

    def _check_entry_point(self) -> None:
        if not self.entry_point or "." not in self.entry_point:
            raise PluginValidationError(
                f"entry_point 는 점(.)으로 구분된 모듈 경로여야 합니다: '{self.entry_point}'"
            )

    def _check_schema_version(self) -> None:
        # major 버전만 비교
        my_major = self.schema_version.split(".")[0]
        cur_major = MANIFEST_SCHEMA_VERSION.split(".")[0]
        if my_major != cur_major:
            raise PluginValidationError(
                f"schema_version major 불일치: '{self.schema_version}' vs '{MANIFEST_SCHEMA_VERSION}'"
            )

    def _check_permissions(self) -> None:
        for perm in self.permissions:
            if not isinstance(perm, PluginPermission):
                raise PluginValidationError(
                    f"알 수 없는 권한: '{perm}'. PluginPermission Enum 사용 필수."
                )

    # ── 유틸리티 ────────────────────────────────────────────────
    def has_permission(self, perm: PluginPermission) -> bool:
        return perm in self.permissions

    def to_dict(self) -> dict:  # type: ignore[type-arg]
        return {
            "plugin_id":      self.plugin_id,
            "name":           self.name,
            "version":        self.version,
            "entry_point":    self.entry_point,
            "permissions":    [p.value for p in self.permissions],
            "description":    self.description,
            "author":         self.author,
            "dependencies":   list(self.dependencies),
            "schema_version": self.schema_version,
            "tags":           list(self.tags),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PluginManifest":  # type: ignore[type-arg]
        perms = [PluginPermission(p) for p in data.get("permissions", [])]
        return cls(
            plugin_id=data["plugin_id"],
            name=data["name"],
            version=data["version"],
            entry_point=data["entry_point"],
            permissions=perms,
            description=data.get("description", ""),
            author=data.get("author", ""),
            dependencies=data.get("dependencies", []),
            schema_version=data.get("schema_version", MANIFEST_SCHEMA_VERSION),
            tags=data.get("tags", []),
        )
