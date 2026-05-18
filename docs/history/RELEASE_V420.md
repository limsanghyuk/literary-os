# Literary OS V420 — Release Notes

## 릴리즈 정보
- **버전**: V420
- **빌드 날짜**: 2026-05-14
- **기반**: V411 (2,897 PASSED baseline)
- **테스트**: 2,935 PASSED (+38 신규), 2 skipped, 0 failed

## 변경 사항 요약

### [NEW] apps/studio_api/ 완전 재구조화
V316 단일 파일 → 모듈형 서브패키지 아키텍처

```
apps/studio_api/
├── main.py               V420 (V316 역호환 심 포함)
├── main_v316.py          V316 원본 보존
├── schema/mapper.py      Pydantic v2 스키마 + SchemaMapper
├── auth/middleware.py    JWT 인증 + RBAC (DEV_MODE bypass)
├── ratelimit/bucket.py   토큰 버킷 Rate Limiter
├── jobs/queue.py         비동기 Job Queue (인메모리 stub)
├── otel/setup.py         OpenTelemetry span + SLO 측정
├── resilience/circuit_breaker.py  Circuit Breaker (CLOSED/OPEN/HALF_OPEN)
├── middleware/idempotency.py      Idempotency-Key 미들웨어
├── routers/
│   ├── analyze.py        /analyze, /gate, /nkg/{id}, /voice/analyze
│   ├── io.py             /import, /export
│   ├── cost.py           /cost/ledger, /cost/summary
│   ├── jobs.py           /jobs/{id} GET/DELETE
│   └── generate.py       /generate, /edit, /export/traces, /status/{id} (V316 마이그레이션)
└── ws/energy.py          WebSocket /ws/energy/{series_id}
```

### [NEW] 신규 엔드포인트 9개
| 경로 | 메서드 | 설명 |
|------|--------|------|
| /api/v1/analyze | POST | DRSE 씬 분석 |
| /api/v1/gate | POST | EnduranceGate 실행 |
| /api/v1/nkg/{series_id} | GET | NKG 그래프 조회 (페이지네이션) |
| /api/v1/voice/analyze | POST | VoiceManifold 13D 분석 |
| /api/v1/import | POST | 원고 임포트 |
| /api/v1/export | POST | 원고 내보내기 |
| /api/v1/cost/ledger | POST | 비용 기록 |
| /api/v1/cost/summary | GET | 비용 집계 |
| /api/v1/jobs/{id} | GET/DELETE | 비동기 작업 상태/취소 |
| /ws/energy/{series_id} | WS | 에너지 스트림 |

### [NEW] 미들웨어 스택
1. CORS (화이트리스트: localhost:3000, localhost:8080, literary-os.dev)
2. IdempotencyMiddleware — POST 재시도 보호 (24h TTL)
3. RateLimitMiddleware — 토큰 버킷 (rate=10, burst=20)
4. OtelMiddleware — 모든 요청 span + SLO 위반 감지

### [NEW] Circuit Breaker
- `drse_engine`: threshold=5, recovery=30s
- `nkg_store`: threshold=5, recovery=30s
- `endurance_gate`: threshold=3, recovery=60s
- `voice_manifold`: threshold=5, recovery=30s

## ADR 준수 현황
- ADR-001 (7-Layer): SchemaMapper 경유 L4↔L2 접근 ✅
- ADR-002 (OAuth 2.1): JWT 인증 + DEV_MODE bypass ✅ (완전 구현은 V421)
- ADR-003 (OTel): SLO 측정 /analyze<1.5s /generate<30s /gate<5s ✅
- ADR-004 (Tiered Model): Stub 구현, V435 RAG 연결 예정 ✅
- ADR-005 (Test Policy): baseline 2,897 → 2,935 (+38) ✅

## V421 예정
- OAuth 2.1 + OIDC 완전 구현 (pyjwt → python-jose 교체)
- OpenTelemetry SDK 실 연결 (OTLP exporter)
- Prometheus 메트릭 엔드포인트 /metrics
