"""literary_system/llm_bridge/agent_envelope.py

AgentEnvelope (P-IF-01) + RoutingPolicy 4축 확장 — V621, ADR-088.

LLM-0 원칙: 실 API 호출 없음. 인터페이스 정의 전용.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional, Any


class AgentRole(Enum):
    """에이전트 역할 열거형 (P-IF-01, ADR-088).

    Phase B는 SCENE_WRITER 단일 사용. Phase C+에서 다중 역할 활성화.
    """
    SCENE_WRITER  = "scene_writer"    # Phase B 기본
    CRITIC        = "critic"          # Phase C+ — 씬 비평
    EDITOR        = "editor"          # Phase C+ — 편집
    HISTORIAN     = "historian"       # Phase C+ — 서사 역사 추적
    READER_VOICE  = "reader_voice"    # Phase C+ — 독자 시점


@dataclass
class AgentEnvelope:
    """LLM 요청 봉투 (P-IF-01, ADR-088).

    Phase B: agent_id='default', role=SCENE_WRITER 단일 사용.
    Phase C+: 다중 에이전트 오케스트레이션 확장.

    Args:
        agent_id:        에이전트 식별자 (기본 'default').
        role:            에이전트 역할 (기본 SCENE_WRITER).
        prompt:          LLM 입력 프롬프트.
        context:         추가 컨텍스트 딕셔너리.
        parent_agent_id: 부모 에이전트 ID (멀티 에이전트 체인).
        session_id:      세션 식별자.
        metadata:        임의 메타데이터.
    """
    agent_id:        str           = "default"
    role:            AgentRole     = AgentRole.SCENE_WRITER
    prompt:          str           = ""
    context:         Dict[str, Any] = field(default_factory=dict)
    parent_agent_id: Optional[str] = None
    session_id:      Optional[str] = None
    metadata:        Dict[str, Any] = field(default_factory=dict)


class RoutingDecision(Enum):
    """라우팅 결정 상수."""
    LOCAL_LORA  = "local_lora"
    EXTERNAL_LLM = "external_llm"
    CASCADE     = "cascade"


@dataclass
class RoutingPolicy:
    """4축 라우팅 정책 (ADR-088 확장, 기존 3축 → 4축).

    4축:
      cost_weight:    비용 우선 가중치
      latency_weight: 지연시간 우선 가중치
      quality_weight: 품질 우선 가중치
      role_weight:    역할 기반 라우팅 우선 가중치 (신규 4축)

    agent_routing: 에이전트 ID 또는 역할 이름 → RoutingDecision 매핑.
    """
    cost_weight:    float = 0.3
    latency_weight: float = 0.3
    quality_weight: float = 0.3
    role_weight:    float = 0.1  # 4축 (V621 신규)
    agent_routing:  Dict[str, RoutingDecision] = field(default_factory=dict)

    def __post_init__(self) -> None:
        total = self.cost_weight + self.latency_weight + self.quality_weight + self.role_weight
        if abs(total - 1.0) > 1e-6:
            raise ValueError(
                f"RoutingPolicy 4축 가중치 합이 1.0이어야 합니다. 현재: {total:.4f}"
            )

    def decide_for_agent(self, env: AgentEnvelope) -> RoutingDecision:
        """에이전트 봉투 기반 라우팅 결정.

        우선순위:
          1. agent_id 직접 매핑
          2. role.value 매핑
          3. 기본 LOCAL_LORA (Phase B)
        """
        if env.agent_id in self.agent_routing:
            return self.agent_routing[env.agent_id]
        role_key = env.role.value
        if role_key in self.agent_routing:
            return self.agent_routing[role_key]
        return RoutingDecision.LOCAL_LORA
