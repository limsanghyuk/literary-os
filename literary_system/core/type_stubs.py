"""
literary_system/core/type_stubs.py
====================================
V686 — 공통 타입 정의 및 Protocol 스텁 (ADR-148, D-M-07)

literary_system 전체 패키지에서 재사용하는
TypeAlias, TypeVar, Protocol을 한 곳에서 정의한다.

설계 원칙:
  - 외부 LLM 호출 없음 (LLM-0 준수)
  - mypy --strict 호환 (strict=True 설정과 함께 사용)
  - Python 3.10+ 지원 (Union[X,Y] 대신 X|Y 사용 가능)
"""
from __future__ import annotations

from typing import (
    Any,
    Dict,
    List,
    Optional,
    Protocol,
    TypeVar,
    Union,
    runtime_checkable,
)

# ---------------------------------------------------------------------------
# TypeAlias
# ---------------------------------------------------------------------------

# JSON 직렬화 가능 타입
JSON = Union[
    Dict[str, Any],
    List[Any],
    str,
    int,
    float,
    bool,
    None,
]

# 테넌트 식별자 (문자열)
TenantId = str

# Gate 식별자 (예: "G81", "G77")
GateId = str

# 0.0~1.0 점수
Score = float


# ---------------------------------------------------------------------------
# TypeVar
# ---------------------------------------------------------------------------

T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)
ReportT = TypeVar("ReportT")


# ---------------------------------------------------------------------------
# Protocols — 런타임 체크 지원
# ---------------------------------------------------------------------------

@runtime_checkable
class LiteraryCoreProtocol(Protocol):
    """literary_system 핵심 컴포넌트 공통 인터페이스."""

    @property
    def component_id(self) -> str:
        """컴포넌트 식별자."""
        ...

    def health_check(self) -> bool:
        """컴포넌트 상태 확인 — True: 정상, False: 비정상."""
        ...


@runtime_checkable
class GateProtocol(Protocol):
    """Gate 컴포넌트 공통 인터페이스."""

    GATE_ID: str

    def run(self) -> dict[str, Any]:
        """Gate 실행 — 결과 딕셔너리 반환."""
        ...


@runtime_checkable
class SerializableProtocol(Protocol):
    """직렬화 가능한 객체 인터페이스."""

    def to_dict(self) -> Dict[str, JSON]:
        """딕셔너리로 직렬화."""
        ...

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SerializableProtocol":
        """딕셔너리에서 역직렬화."""
        ...


@runtime_checkable
class AnalyzerProtocol(Protocol):
    """분석기 공통 인터페이스."""

    def analyze(self, text: str) -> Dict[str, Any]:
        """텍스트 분석 — 결과 딕셔너리 반환."""
        ...

    def score(self, text: str) -> Score:
        """분석 점수 (0.0~1.0) 반환."""
        ...


# ---------------------------------------------------------------------------
# 유틸리티 함수
# ---------------------------------------------------------------------------

def clamp_score(value: float, lo: float = 0.0, hi: float = 1.0) -> Score:
    """점수를 [lo, hi] 범위로 클램핑."""
    return max(lo, min(hi, value))


def is_valid_gate_id(gate_id: str) -> bool:
    """Gate ID 형식 검증 — 'G' + 숫자."""
    return gate_id.startswith("G") and gate_id[1:].isdigit() and len(gate_id) >= 2


def is_valid_tenant_id(tenant_id: str) -> bool:
    """테넌트 ID 비어 있지 않음 검증."""
    return bool(tenant_id and tenant_id.strip())
