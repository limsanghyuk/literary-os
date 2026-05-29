# CHANGELOG V744 — SP-D.4 보조 게이트 3종 (G92·G93·G94)

**날짜**: 2026-05-29  
**버전**: v12.6.0 (12.5.10 → 12.6.0)  
**태그**: `v12.6.0`, `v12.6.0-V744`  
**ADR**: ADR-205, ADR-206, ADR-207  

## 요약

V744에서 SP-D.4 보조 게이트 3종(G92·G93·G94)을 구현한다. 각 게이트는 Phase D에서 도입한 핵심 레이어(성능 SLO, 보안 태세, 관측성 완결성)를 자동 검증하며, `release_gate.py` GATES에 등록되어 릴리즈 승인 흐름에 통합된다.

## 신규 파일

| 파일 | 내용 |
|------|------|
| `literary_system/gates/spd4_aux_gates.py` | G92·G93·G94 보조 게이트 구현 (616 LOC) |
| `tests/unit/test_v744_spd4_aux_gates.py` | 72 TC 단위 테스트 |
| `docs/adr/ADR-205.md` | G92 Phase D Performance SLO Gate |
| `docs/adr/ADR-206.md` | G93 Security Posture Gate |
| `docs/adr/ADR-207.md` | G94 Observability Completeness Gate |

## 변경 파일

| 파일 | 변경 내용 |
|------|-----------|
| `literary_system/gates/release_gate.py` | G92·G93·G94 GATES 등록 (총 96 gates) |
| `tools/run_preflight.py` | SURVIVAL_SYMBOLS SP-D.4 심볼 6종 추가, 기준 V744로 갱신 |
| `pyproject.toml` | version 12.5.10 → 12.6.0 |

## Gate 상세

### G92 — Performance SLO Gate (ADR-205)
| 체크 | 검증 내용 | 결과 |
|------|-----------|------|
| PS-1 | AgentBus 임포트 | ✅ PASS |
| PS-2 | CircuitBreaker CLOSED→OPEN 전환 | ✅ PASS |
| PS-3 | SLO 상수 (P99≤200ms, RTT≤50ms) | ✅ PASS |
| PS-4 | P99 분위수 정확도 | ✅ PASS |
| PS-5 | DRBackup 생성 지연 ≤100ms | ✅ PASS |

### G93 — Security Posture Gate (ADR-206)
| 체크 | 검증 내용 | 결과 |
|------|-----------|------|
| SP-1 | ZeroTrustTokenService 임포트 | ✅ PASS |
| SP-2 | TokenClaims tenant_id 필드 | ✅ PASS |
| SP-3 | PluginWhitelist approve/deny 메서드 | ✅ PASS |
| SP-4 | TenantAuthority 격리 차단 | ✅ PASS |
| SP-5 | ZeroTrustAuditLog 구조 | ✅ PASS |

### G94 — Observability Completeness Gate (ADR-207)
| 체크 | 검증 내용 | 결과 |
|------|-----------|------|
| OC-1 | OtelSdkAdapter 스팬 생성/종료 | ✅ PASS |
| OC-2 | TraceContext W3C 왕복 | ✅ PASS |
| OC-3 | PrometheusExporter 스냅샷 | ✅ PASS |
| OC-4 | PhaseEManifestValidator 8/8 (deploy/ 연결) | ✅ PASS |
| OC-5 | DR E2E 관측성 (backup+restore) | ✅ PASS |

## ADR-128 해소

OC-4 체크에서 `literary_system.deploy.PhaseEManifestValidator`를 직접 임포트함으로써 GitNexus가 식별한 `deploy/` 패키지의 G_CONNECTIVITY 단절(0 in/0 out)을 해소한다.

## 테스트 결과

```
72 passed in 0.19s
SP-D.4 보조 게이트 PASS: 15/15 checks passed (G92=PASS, G93=PASS, G94=PASS)
```

## 다음 단계

V745 — Phase D Exit Gate G95 (8축 SC-1~SC-8) + v13.0.0 릴리즈
