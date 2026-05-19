# CHANGELOG V580 — Async + Performance (8.5.0)

**날짜**: 2026-05-19  
**버전**: 8.5.0  
**이전**: V579 (8.4.0) → **이번**: V580 (8.5.0)  
**테스트**: 25 TC PASS (test_v580_async_performance.py)  
**Gates**: 38 PASS (G38 AsyncDiscipline + G39 PerformanceBaseline 신설)

---

## 핵심 변경사항

### 1. AsyncDiscipline (ADR-036, Gate G38)

`asyncio.get_event_loop()`는 Python 3.10+ deprecated. AST 기반 탐지로 코드베이스 전체 스캔.

**수정 파일**: `literary_system/orchestrators/character_intent_agent.py`
- `async def decide()`: `get_event_loop()` → `get_running_loop()` (항상 async 컨텍스트에서 실행)
- `def collect_sync()`: `get_running_loop()` + `RuntimeError` 예외 처리 패턴 (루프 없는 환경 대응)

**Gate G38**: `_gate_async_discipline_g38()` — AST Walk 기반, 문자열/주석 내 패턴 무시

### 2. PerformanceBaseline (ADR-039, Gate G39)

핵심 순수 Python 연산 3종의 성능 기준선 수립 및 회귀 방지.

| 벤치마크 | 반복 | 기준 | 허용 편차 |
|---------|------|------|---------|
| JSON 직렬화/역직렬화 | 1,000회 | 500ms | +30% |
| SHA-256 해시 | 10,000회 | 200ms | +30% |
| 정규식 컴파일+매칭 | 5,000회 | 300ms | +30% |

**Gate G39**: `_gate_performance_baseline_g39()` — 외부 의존성 없음, LLM-0 원칙 준수

### 3. ADR 신설

- `docs/adr/ADR-036.md` — AsyncDiscipline: `get_event_loop()` 금지
- `docs/adr/ADR-039.md` — PerformanceBaseline: 핵심 연산 기준선

### 4. Gate Registry 갱신

```python
"async_discipline_g38":    ("ADR-036", "V580", "L1")
"performance_baseline_g39": ("ADR-039", "V580", "L1")
```

### 5. V579 테스트 호환성 수정

G38/G39 추가로 Gates 수가 36→38로 증가. `test_v579_duplicate_zero.py` TC-20/24/25 조건 갱신.

---

## V575→V580 로드맵 완료 현황

| 버전 | 제목 | Gate | 상태 |
|-----|------|------|------|
| V575 | Security & Hygiene | G32 LoggingDiscipline | ✅ |
| V576 | Test Fortification | G33 SchemaRoundTrip, G34 AuthRegression | ✅ |
| V577 | LLM Adapter Consolidation | G35 AdapterCanonical | ✅ |
| V578 | Gate Registry & ADR | G36 GateRegistry | ✅ |
| V579 | Duplicate Resolution | G37 DuplicateZero | ✅ |
| **V580** | **Async + Performance** | **G38 AsyncDiscipline, G39 PerformanceBaseline** | ✅ |

**V574 Critical 결함 해소 현황**:
- CR-1 DEV_MODE 기본값=true → ✅ V574.1/V575
- CR-2 LLM 어댑터 4세대 공존 → ✅ V577
- CR-3 0% 커버리지 21파일 → ✅ V576
- CR-4 중복 클래스 88개 → ✅ V579 (0건)
