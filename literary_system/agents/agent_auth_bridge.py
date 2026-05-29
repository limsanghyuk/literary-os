"""
literary_system.agents.agent_auth_bridge
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
V722 — AgentAuthBridge: 에이전트 메시지 Zero-Trust 인증 브릿지 (ADR-183).

설계 원칙:
  - agents/ → security/ 단방향 의존 (역방향 금지, 순환 차단)
  - AgentBus 메시지 발송 전 ZeroTrust 토큰 검증
  - 에이전트별 테넌트 격리 보장
  - 인증 실패 시 메시지 드롭 (fail-closed)
  - G32: print() 금지
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional

from literary_system.security.zero_trust_token import (
    ZeroTrustTokenService,
    TokenClaims,
    TokenValidationError,
    TokenExpiredError,
)
from literary_system.security.tenant_authority import (
    TenantAuthority,
    AccessDecision,
)


# ── 인증 결과 열거 ─────────────────────────────────────────────────────────────

class AuthDecision(str, Enum):
    ALLOW   = "ALLOW"
    DENY    = "DENY"
    EXPIRED = "EXPIRED"
    INVALID = "INVALID"


# ── 브릿지 결과 DTO ───────────────────────────────────────────────────────────

@dataclass
class BridgeResult:
    """AgentAuthBridge.check() 반환 결과."""
    decision: AuthDecision
    claims: Optional[TokenClaims] = None
    reason: str = ""

    @property
    def allowed(self) -> bool:
        return self.decision == AuthDecision.ALLOW


# ── 에이전트 등록 레코드 ──────────────────────────────────────────────────────

@dataclass
class AgentAuthRecord:
    """등록된 에이전트의 인증 설정."""
    agent_id: str
    tenant_id: str
    required_role: Optional[str] = None
    active: bool = True


# ── 브릿지 본체 ───────────────────────────────────────────────────────────────

class AgentAuthBridge:
    """
    에이전트 메시지 발송 전 Zero-Trust 인증·인가를 수행하는 브릿지.

    Usage::

        bridge = AgentAuthBridge(token_svc, tenant_auth)
        bridge.register_agent("writer-A", tenant_id="tenant-1", required_role="writer")

        result = bridge.check(agent_id="writer-A", token_str="Bearer <token>")
        if not result.allowed:
            raise RuntimeError(result.reason)
    """

    def __init__(
        self,
        token_service: ZeroTrustTokenService,
        tenant_authority: TenantAuthority,
        *,
        fail_closed: bool = True,
    ) -> None:
        """
        Args:
            token_service:    ZeroTrustTokenService 인스턴스
            tenant_authority: TenantAuthority 인스턴스
            fail_closed:      True이면 미등록 에이전트도 DENY (기본값)
        """
        self._token_svc  = token_service
        self._tenant_auth = tenant_authority
        self._fail_closed = fail_closed
        self._agents: Dict[str, AgentAuthRecord] = {}
        self._audit_log: List[BridgeResult] = []

    # ── 에이전트 관리 ────────────────────────────────────────────────────────

    def register_agent(
        self,
        agent_id: str,
        tenant_id: str,
        required_role: Optional[str] = None,
    ) -> None:
        """에이전트 인증 설정 등록."""
        self._agents[agent_id] = AgentAuthRecord(
            agent_id=agent_id,
            tenant_id=tenant_id,
            required_role=required_role,
        )

    def deregister_agent(self, agent_id: str) -> bool:
        """에이전트 등록 해제. 없으면 False."""
        return self._agents.pop(agent_id, None) is not None

    def get_agent_record(self, agent_id: str) -> Optional[AgentAuthRecord]:
        return self._agents.get(agent_id)

    def list_agents(self) -> List[str]:
        return list(self._agents.keys())

    # ── 핵심 인증 ────────────────────────────────────────────────────────────

    def check(
        self,
        agent_id: str,
        token_str: str,
    ) -> BridgeResult:
        """
        에이전트의 발신 토큰을 검증하고 테넌트 권한을 확인한다.

        Args:
            agent_id:  발신 에이전트 ID
            token_str: Bearer 토큰 (Bearer 접두사 선택)

        Returns:
            BridgeResult(allowed=bool, claims=..., reason=...)
        """
        # 1. 에이전트 등록 확인
        record = self._agents.get(agent_id)
        if record is None:
            result = BridgeResult(
                decision=AuthDecision.DENY if self._fail_closed else AuthDecision.ALLOW,
                reason=f"Agent '{agent_id}' not registered",
            )
            self._audit_log.append(result)
            return result

        if not record.active:
            result = BridgeResult(
                decision=AuthDecision.DENY,
                reason=f"Agent '{agent_id}' is deactivated",
            )
            self._audit_log.append(result)
            return result

        # 2. 토큰 검증
        raw_token = token_str.removeprefix("Bearer ").strip()
        try:
            claims = self._token_svc.verify(raw_token)
        except TokenExpiredError as exc:
            result = BridgeResult(
                decision=AuthDecision.EXPIRED,
                reason=str(exc),
            )
            self._audit_log.append(result)
            return result
        except TokenValidationError as exc:
            result = BridgeResult(
                decision=AuthDecision.INVALID,
                reason=str(exc),
            )
            self._audit_log.append(result)
            return result

        # 3. 테넌트·역할 검증
        if record.required_role:
            decision: AccessDecision = self._tenant_auth.authorize(
                claims,
                required_role=record.required_role,
                target_tenant_id=record.tenant_id,
            )
            if not decision.granted:
                result = BridgeResult(
                    decision=AuthDecision.DENY,
                    claims=claims,
                    reason=decision.reason,
                )
                self._audit_log.append(result)
                return result
        else:
            # 역할 검사 생략, 테넌트 소속만 확인
            if claims.tenant_id != record.tenant_id:
                result = BridgeResult(
                    decision=AuthDecision.DENY,
                    claims=claims,
                    reason=(
                        f"Tenant mismatch: token.tenant_id={claims.tenant_id!r} "
                        f"≠ agent.tenant_id={record.tenant_id!r}"
                    ),
                )
                self._audit_log.append(result)
                return result

        result = BridgeResult(
            decision=AuthDecision.ALLOW,
            claims=claims,
            reason="OK",
        )
        self._audit_log.append(result)
        return result

    def check_batch(
        self,
        agent_id: str,
        tokens: List[str],
    ) -> List[BridgeResult]:
        """여러 토큰을 일괄 검증 (서로 다른 토큰이어야 함)."""
        return [self.check(agent_id, t) for t in tokens]

    # ── 감사 로그 ─────────────────────────────────────────────────────────────

    def audit_log(self) -> List[BridgeResult]:
        return list(self._audit_log)

    def clear_audit(self) -> None:
        self._audit_log.clear()

    # ── 통계 ─────────────────────────────────────────────────────────────────

    def stats(self) -> Dict[str, int]:
        """인증 결과별 카운트."""
        counts: Dict[str, int] = {d.value: 0 for d in AuthDecision}
        for r in self._audit_log:
            counts[r.decision.value] += 1
        return counts
