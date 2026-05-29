# CHANGELOG V722

**날짜**: 2026-05-29  
**버전**: v12.3.6  
**단계**: SP-D.3 Zero-Trust agents 통합

## 신규

| 파일 | 설명 |
|------|------|
| `literary_system/agents/agent_auth_bridge.py` | AgentAuthBridge + BridgeResult + AuthDecision + AgentAuthRecord |
| `tests/unit/test_v722_agent_auth_bridge.py` | 33 TC PASS |
| `docs/adr/ADR-183.md` | 설계 결정 |

## 수정

`literary_system/agents/__init__.py` — AgentAuthBridge 4종 export 추가
