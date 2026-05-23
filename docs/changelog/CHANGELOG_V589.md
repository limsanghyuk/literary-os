# CHANGELOG — V589 (SP-A.2)

**버전**: 9.4.0  
**릴리즈일**: 2026-05-21  
**Gate**: G48 (PartialAvailabilityGate) — 10/10 PASS  
**ADR**: ADR-050  

---

## 변경 요약

### 신규 파일

| 파일 | 설명 |
|---|---|
| `literary_system/db/health_monitor.py` | BackendHealthMonitor (AvailabilityState, CircuitBreaker) |
| `docs/adr/ADR-050.md` | BackendHealthMonitor/PartialAvailability 설계 결정 |
| `tests/unit/test_health_monitor.py` | T1~T4 시나리오 25 PASS |

### 변경 파일

| 파일 | 변경 내용 |
|---|---|
| `literary_system/db/query_interface.py` | health_monitor 파라미터 추가, _get_available_backends() 폴백 로직 |
| `literary_system/rag/hybrid_retriever.py` | HybridRetrieverV2 클래스 추가 (기존 V438 보존) |
| `literary_system/db/__init__.py` | BackendHealthMonitor 등 4종 export 추가 |
| `literary_system/gates/release_gate.py` | Gate G48 (_gate_partial_availability_g48) 추가 |
| `literary_system/gates/gate_registry.py` | G48 등록 (ADR-050, V589, L1) |
| `pyproject.toml` | 9.3.0 → 9.4.0 |
| `MANIFEST.md` | V589 / 9.4.0 / 47 Gates 갱신 |

---

## Gate G48 체크포인트 (10/10 PASS)

PA-1 임포트 | PA-2 AvailabilityState 4종 | PA-3 CircuitState 3종
PA-4 빈모니터→OFFLINE | PA-5 T1 FULL | PA-6 T2 PARTIAL_DEGRADED
PA-7 T3 CRITICAL | PA-8 T4 OFFLINE | PA-9 QI 파라미터 | PA-10 LLM-0

---

## 수치 비교

| 항목 | V588 (9.3.0) | V589 (9.4.0) |
|---|---|---|
| Gates | 46/46 | **47/47** |
| ADR | ADR-001~049 | **ADR-001~050** |
| 신규 테스트 | — | **+25** |
| BackendHealthMonitor | 없음 | **구현 완료** |
| HybridRetrieverV2 | 없음 | **구현 완료** |
| T1~T4 시나리오 | — | **100% PASS** |

---

## 다음 단계

SP-A.3 (V590) — GPU Adapter (GPUAdapterContract ABC + RunPodAdapter + LambdaLabsAdapter + Gate G49 + ADR-051)
