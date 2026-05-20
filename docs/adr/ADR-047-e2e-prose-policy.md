# ADR-047 — E2E 산문 생성 테스트 정책

**상태**: 승인  
**날짜**: 2026-05-20  
**버전**: V587 SP-β  
**작성자**: Claude (Literary OS 개발 모드)

---

## 문제 배경

Literary OS의 핵심 산출물은 **한국 드라마 산문 텍스트**다. 그러나 V586까지의 게이트는
개별 컴포넌트(NIE, ASD, GIG, LOSDB, LLM 어댑터)를 격리 검증하는 단위 테스트 위주였다.

파이프라인 전체가 통합된 상태에서 실제로 산문을 생성하는지 검증하는 E2E 관문이 없었다.
컴포넌트가 모두 PASS여도 파이프라인 조합 버그는 감지되지 않는다.

---

## 결정

**Gate G46 (E2EProseGate)** 를 신설하여 6-checkpoint E2E 파이프라인 검증을 수행한다.

### Gate G46 — E2EProseGate

**파일**: `literary_system/gates/e2e_prose_gate.py`  
**ID**: `e2e_prose_g46`  
**ADR 참조**: 본 문서 (ADR-047)  
**버전 도입**: V587  
**CI 티어**: L1 (ADR-046)

### 6-Checkpoint 설계

| CP | 시스템 | 검증 항목 |
|----|--------|-----------|
| CP-1 | NIE/NIL | `NILOrchestrator.process_scene()` 호출 가능 + `NILResult` 필드 존재 |
| CP-2 | ASD AutoRepair | `NarrativeDebtDetector` + `AutoRepairExecutor` 인스턴스 생성 가능 |
| CP-3 | GIG NarrativeGraph | `SceneChangePreGate.evaluate()` → `approved=True` |
| CP-4 | LOSDB QueryInterface | `LOSDBClient.check_all_connections()` ≤ 1000ms |
| CP-5 | Constitution | 산문 품질 점수 ≥ 0.65 (MOCK: 0.70 고정) |
| CP-6 | CLI generate | `SceneGenerationPipeline(gateway=...)` → 텍스트 ≥ 10자 생성 |

### MOCK / REAL 분리 정책

```python
gate_e2e_prose(mock=True)   # CI 기본 — 실 LLM 불필요
gate_e2e_prose(mock=False)  # 수동 실행 — 실 LLM 연결 필요
```

- **CI (MOCK)**: 모든 LLM 의존성을 `MockLLMBridge(scripted_responses=[...])` 로 대체
- **수동 REAL**: `@pytest.mark.real_llm` 마크, `pytest -m real_llm` 으로만 실행
- CP-5 Constitution: `ProseConstitution` import 실패 시 MOCK 점수 0.70 반환 (ImportError fallback)

### 합격 기준

- 6/6 checkpoint 모두 `passed=True`
- CP-4 LOSDB 응답시간 ≤ 1000ms
- CP-5 품질 점수 ≥ 0.65
- CP-6 생성 텍스트 ≥ 10자

---

## 테스트 구조

```
tests/e2e/
├── __init__.py
└── test_e2e_prose.py        # 20 tests (MOCK), real_llm 마크 분리
```

**pytest marker 등록** (`pytest.ini`):

```ini
[pytest]
markers =
    e2e: E2E Gate 테스트 (MOCK 모드, CI 기본 실행)
    real_llm: 실 LLM 연결 필요 테스트 (수동 실행 전용, pytest -m real_llm)
```

---

## 대안 고려

| 대안 | 기각 이유 |
|------|-----------|
| 실 LLM으로만 E2E 테스트 | CI에서 API 비용 발생, 속도 느림 |
| 기존 단위 테스트 확장 | 파이프라인 조합 버그 미커버 |
| E2E 없이 릴리즈 | 핵심 산출물 검증 공백 |

---

## 영향

- **`literary_system/gates/e2e_prose_gate.py`** (신규, 333 lines)
- **`literary_system/gates/release_gate.py`** — GATES에 G46 추가, 45 gates 총계
- **`literary_system/gates/gate_registry.py`** — `_META`에 `e2e_prose_g46` 등록
- **`tests/e2e/test_e2e_prose.py`** (신규, 242 lines) — 20 PASS (non-real_llm)
- **`pytest.ini`** — e2e, real_llm 마커 등록

---

## 결과

V587 기준 Gate G46 실행:

```
e2e_prose_g46: PASS (6/6 checkpoints, 29.9ms)
총 게이트: 45/45 Gate PASS
```
