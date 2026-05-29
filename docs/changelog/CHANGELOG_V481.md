# CHANGELOG — Literary OS V481 (Hotfix)

**릴리즈 일자:** 2026-05-16  
**기준선:** V480 (literary_os_v480_FINAL2.zip)  
**유형:** Hotfix — 4개 버그 클러스터 수정 + 인프라 정비

---

## 버그 수정

### H4 — ProviderHealthMonitor._do_check() return 누락 (Bug A)
- **파일:** `literary_system/llm_bridge/health/provider_health_monitor.py`
- **증상:** `force_check()` 호출 시 항상 `None` 반환 → 건강 상태 강제 갱신 불가
- **원인:** `_do_check()` 메서드에 `return ok` 누락 (Python 암묵적 None 반환)
- **수정:** `return ok` 명시 추가 + `get_status()`, `check_all()`, `force_check()` public API 복원

### H5 — TaskRouter._is_tier_healthy 설계 결정 확정 (Bug B 관련)
- **파일:** `literary_system/llm_bridge/routing/task_router.py`
- **현황:** `get_provider_id()` 방식으로 tier → provider_id 변환 후 health 조회
- **확정:** Blueprint의 "tier 직접 조회" 문구는 이 간접 변환을 포함한 의미임을 ADR 주석으로 명문화
- **근거:** `ProviderHealthMonitor`는 `provider_id` 기반 키 ("ollama"/"haiku"/"sonnet"), tier 이름 ("local"/"speed"/"quality")과 다름. `get_provider_id()` 변환이 필수 설계.
- **검증:** `test_v411f_unified_gateway.py` 전체 통과 확인

### H6 — make_default_gateway() return 누락 (Bug C)
- **파일:** `literary_system/llm_bridge/gateway/unified_llm_gateway.py`
- **증상:** `make_default_gateway()` 호출 시 항상 `None` 반환 → 모든 gateway 생성 실패
- **수정:** `return UnifiedLLMGateway(task_router=router, health_monitor=health)` 추가

### H7 — LLMNodeRouter.stats() public API 누락 (Bug D)
- **파일:** `literary_system/llm_bridge/llm_node_router.py`
- **증상:** 외부에서 노드별 호출 통계 접근 불가
- **수정:** `stats() -> dict` 메서드 추가 (calls, errors 노드별 반환)

---

## 인프라 정비

### H1 — pyproject.toml 버전 갱신
- `version`: `4.8.0` → `4.8.1`
- `description`: `Literary OS V480` → `Literary OS V481`

### H2 — tests/ 디렉토리 패키징 포함 확인
- `literary_os_v480_FINAL2.zip` 내 tests/ 181개 파일 전체 포함 확인 완료

### H3 — manifests/live_core_manifest.json V481 갱신
- `version`: `V382` → `V481`
- `test_pass`: `2015` → `4452`
- `release_date`: `2026-05-16`
- SP3/SP4/SP5 gate 항목, 12개 core_module 경로 추가

### OTel tracer 초기화 수정
- **파일:** `apps/studio_api/otel/setup.py`
- **증상:** pytest 종료 후 `ValueError: I/O operation on closed file` 반복 출력
- **원인:** `PeriodicExportingMetricReader(ConsoleMetricExporter(), export_interval_millis=60_000)` — 60초 백그라운드 스레드가 pytest teardown 후 닫힌 stdout에 write 시도
- **수정:** 프로덕션 exporter(`OTEL_PROMETHEUS_PORT`, `OTEL_EXPORTER_OTLP_ENDPOINT`)가 없을 때 `PeriodicExportingMetricReader` 미등록. `MeterProvider`는 reader 없이 초기화 (수집 가능, export 없음).

---

## 테스트 결과

```
4452 passed, 18 skipped
```

- PASS: 4452 (이전 동일)
- FAIL: 0
- SKIP: 18 (외부 서비스 의존 — OTel OTLP, live Stripe 등)
- OTel teardown I/O 경고: 제거됨 (PeriodicExportingMetricReader 미등록)

---

## 파일 목록 (변경)

| 파일 | 변경 유형 |
|------|---------|
| `pyproject.toml` | 버전 갱신 |
| `manifests/live_core_manifest.json` | V481 갱신 |
| `literary_system/llm_bridge/health/provider_health_monitor.py` | Bug H4 수정 |
| `literary_system/llm_bridge/routing/task_router.py` | H5 ADR 주석 추가 |
| `literary_system/llm_bridge/gateway/unified_llm_gateway.py` | Bug H6 수정 |
| `literary_system/llm_bridge/llm_node_router.py` | Bug H7 수정 |
| `apps/studio_api/otel/setup.py` | OTel teardown 수정 |
