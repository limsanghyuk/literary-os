"""
literary_system/core/__init__.py
================================
V686 — Core 공통 타입 패키지 (ADR-148)

literary_system 전체에서 공통으로 사용하는
TypeVar, Protocol, TypeAlias를 중앙 집중 관리한다.
"""
from literary_system.core.type_stubs import (
    JSON,
    TenantId,
    GateId,
    Score,
    LiteraryCoreProtocol,
    GateProtocol,
    SerializableProtocol,
    AnalyzerProtocol,
)

__all__ = [
    "JSON",
    "TenantId",
    "GateId",
    "Score",
    "LiteraryCoreProtocol",
    "GateProtocol",
    "SerializableProtocol",
    "AnalyzerProtocol",
]
