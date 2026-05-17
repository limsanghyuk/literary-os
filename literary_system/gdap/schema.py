"""V350: GDAP — Development Knowledge Graph 스키마 정의.

설계도 섹션 2 구현.
GitNexus LadybugDB 대응: Python dataclass + Enum 기반 경량 스키마.

노드 7종: FILE / MODULE / FUNCTION / CLASS / SCHEMA / TEST / CONFIG
엣지 9종: 의존 레이어(3) + 계약 레이어(2) + 검증 레이어(2) + 참조 레이어(2)
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


# ──────────────────────────────────────────────────────────────
#  해시 헬퍼
# ──────────────────────────────────────────────────────────────

def _sha256_short(text: str) -> str:
    """텍스트 SHA-256 앞 16자리."""
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16]


def _path_hash(path: str) -> str:
    """파일 경로 기반 해시 (내용 변경 감지용)."""
    try:
        import os
        stat = os.stat(path)
        key = f"{path}:{stat.st_size}:{stat.st_mtime}"
    except OSError:
        key = path
    return _sha256_short(key)


# ──────────────────────────────────────────────────────────────
#  노드 타입 (7종)
# ──────────────────────────────────────────────────────────────

class DKGNodeType(Enum):
    FILE     = "file"       # 소스 파일
    MODULE   = "module"     # 논리적 모듈/패키지
    FUNCTION = "function"   # 함수/메서드
    CLASS    = "class"      # 클래스/인터페이스
    SCHEMA   = "schema"     # 타입/인터페이스 계약
    TEST     = "test"       # 테스트 케이스
    CONFIG   = "config"     # 설정/환경 파일


# ──────────────────────────────────────────────────────────────
#  엣지 타입 (9종, 3레이어)
# ──────────────────────────────────────────────────────────────

class DKGEdgeType(Enum):
    # 의존 레이어 — 즉시 Dirty 전파
    IMPORTS      = "Imports"
    CALLS        = "Calls"
    INHERITS     = "Inherits"
    # 계약 레이어 — 스키마/타입 변경 시만 전파
    IMPLEMENTS   = "Implements"
    DEFINES_TYPE = "DefinesType"
    # 검증 레이어 — BUILD 후 전파
    TESTS        = "Tests"
    COVERS       = "Covers"
    # 참조 레이어 — 지연 전파
    REFERENCES   = "References"
    CONFIGURES   = "Configures"


# 레이어별 엣지 집합
DEPENDENCY_EDGES  = frozenset({"Imports", "Calls", "Inherits"})
CONTRACT_EDGES    = frozenset({"Implements", "DefinesType"})
VERIFICATION_EDGES = frozenset({"Tests", "Covers"})
REFERENCE_EDGES   = frozenset({"References", "Configures"})

# Dirty 전파 속도 분류
IMMEDIATE_PROPAGATION = frozenset({"Imports", "Calls", "Inherits"})  # 즉시
DEFERRED_PROPAGATION  = frozenset({"References", "Configures"})       # 지연
BUILD_PROPAGATION     = frozenset({"Tests", "Covers"})                # BUILD 후


# ──────────────────────────────────────────────────────────────
#  엣지 데이터클래스
# ──────────────────────────────────────────────────────────────

@dataclass
class DKGEdge:
    source_id: str
    target_id: str
    edge_type:  DKGEdgeType
    weight:     float = 1.0
    confidence: float = 1.0
    metadata:   Dict[str, Any] = field(default_factory=dict)

    def propagation_speed(self) -> str:
        et = self.edge_type.value
        if et in IMMEDIATE_PROPAGATION:
            return "immediate"
        if et in BUILD_PROPAGATION:
            return "build"
        if et in DEFERRED_PROPAGATION:
            return "deferred"
        return "schema_change"


# ──────────────────────────────────────────────────────────────
#  노드 데이터클래스
# ──────────────────────────────────────────────────────────────

@dataclass
class DKGFileNode:
    """FILE 노드 — 소스 파일. NKGEpisodeNode 대응."""
    path:         str
    lang:         str = "python"
    content_hash: str = field(init=False)

    def __post_init__(self) -> None:
        self.content_hash = _sha256_short(self.path)

    def node_id(self) -> str:
        return f"file:{self.path}"

    def is_stale(self, new_hash: str) -> bool:
        return new_hash != self.content_hash

    def refresh_hash(self) -> str:
        """파일 실제 상태로 해시 갱신."""
        self.content_hash = _path_hash(self.path)
        return self.content_hash


@dataclass
class DKGModuleNode:
    """MODULE 노드 — 논리 모듈/패키지. NKGArcNode 대응."""
    module_id: str
    package:   str = ""
    exports:   List[str] = field(default_factory=list)
    content_hash: str = field(init=False)

    def __post_init__(self) -> None:
        self.content_hash = _sha256_short(self.module_id)

    def node_id(self) -> str:
        return f"module:{self.module_id}"


@dataclass
class DKGFunctionNode:
    """FUNCTION 노드 — 함수/메서드. NKGSceneNode 대응."""
    func_id:    str
    file_path:  str
    signature:  str = ""
    is_async:   bool = False
    content_hash: str = field(init=False)

    def __post_init__(self) -> None:
        self.content_hash = _sha256_short(self.func_id + self.signature)

    def node_id(self) -> str:
        return f"function:{self.file_path}:{self.func_id}"

    def is_stale(self, new_signature: str) -> bool:
        return _sha256_short(self.func_id + new_signature) != self.content_hash


@dataclass
class DKGClassNode:
    """CLASS 노드 — 클래스/인터페이스. NKGCharacterNode 대응."""
    class_id:     str
    file_path:    str
    base_classes: List[str] = field(default_factory=list)
    content_hash: str = field(init=False)

    def __post_init__(self) -> None:
        self.content_hash = _sha256_short(self.class_id)

    def node_id(self) -> str:
        return f"class:{self.file_path}:{self.class_id}"


@dataclass
class DKGSchemaNode:
    """SCHEMA 노드 — 타입/인터페이스 계약. NKGForeshadowNode 대응."""
    schema_id:    str
    fields:       List[str] = field(default_factory=list)
    description:  str = ""
    content_hash: str = field(init=False)

    def __post_init__(self) -> None:
        key = self.schema_id + "|".join(sorted(self.fields))
        self.content_hash = _sha256_short(key)

    def node_id(self) -> str:
        return f"schema:{self.schema_id}"


@dataclass
class DKGTestNode:
    """TEST 노드 — 테스트 케이스. NKGEventNode 대응."""
    test_id:     str
    file_path:   str
    target_func: str = ""
    status:      str = "pending"  # pending / pass / fail
    content_hash: str = field(init=False)

    def __post_init__(self) -> None:
        self.content_hash = _sha256_short(self.test_id)

    def node_id(self) -> str:
        return f"test:{self.file_path}:{self.test_id}"


@dataclass
class DKGConfigNode:
    """CONFIG 노드 — 설정/환경 파일. NKGThemeNode 대응."""
    config_id:    str
    format:       str = "toml"  # toml / yaml / json / env
    content_hash: str = field(init=False)

    def __post_init__(self) -> None:
        self.content_hash = _sha256_short(self.config_id)

    def node_id(self) -> str:
        return f"config:{self.config_id}"


# ──────────────────────────────────────────────────────────────
#  유니온 타입
# ──────────────────────────────────────────────────────────────

DKGNode = (
    DKGFileNode | DKGModuleNode | DKGFunctionNode |
    DKGClassNode | DKGSchemaNode | DKGTestNode | DKGConfigNode
)

_NODE_TYPE_MAP: Dict[type, DKGNodeType] = {
    DKGFileNode:     DKGNodeType.FILE,
    DKGModuleNode:   DKGNodeType.MODULE,
    DKGFunctionNode: DKGNodeType.FUNCTION,
    DKGClassNode:    DKGNodeType.CLASS,
    DKGSchemaNode:   DKGNodeType.SCHEMA,
    DKGTestNode:     DKGNodeType.TEST,
    DKGConfigNode:   DKGNodeType.CONFIG,
}


def node_type_of(node: Any) -> DKGNodeType:
    """노드 객체로부터 DKGNodeType 반환."""
    return _NODE_TYPE_MAP.get(type(node), DKGNodeType.FILE)
