# ADR-046 — Gate 계층화 (CI 티어 분리)

**상태**: 승인  
**날짜**: 2026-05-20  
**버전**: V587 SP-β  
**작성자**: Claude (Literary OS 개발 모드)

---

## 문제 배경

V586까지 `run_release_gate()` 는 44개 게이트를 순차 실행했다. PR 체크·pre-commit 단계에서도
전체 게이트를 돌리면 피드백 루프가 느려지고 CI 비용이 낭비된다.

**실측 (V587 기준):**
- 전체 44게이트: 약 120~180s (실환경 추정)
- L0+L1 fast-path 10게이트: **1.1s**

PR을 올릴 때마다 전체를 돌리는 것은 개발 속도와 CI 비용 모두에서 비합리적이다.

---

## 결정

게이트를 **4개 티어(L0~L3)**로 분류하고, CI 단계마다 해당 티어만 실행한다.

### 티어 정의

| 티어 | 실행 시점 | 목표 시간 | 포함 게이트 수 |
|------|-----------|-----------|--------------|
| L0 | pre-commit (로컬) | ≤ 5s | 3 |
| L1 | PR 체크 (fast-path) | ≤ 30s | 7 |
| L2 | main 병합 후 | ≤ 2m | 나머지 대다수 |
| L3 | 릴리즈 전 full | ≤ 5m | 전체 45게이트 |

> L1까지 총 10게이트, 실측 **1103.7ms** (목표 30s 대비 97% 여유).

### 티어 할당 기준

- **L0**: import/정적 분석, 인증 회귀 — 실행 비용 < 1ms
- **L1**: 어댑터 정합성, 중복 제로, 비동기 규율, 성능 기준, 주요 DB 어댑터 — 실행 비용 < 500ms
- **L2**: 나머지 단위·통합 게이트 (LOSDB 서브시스템, SLM, RAG, …)
- **L3**: E2E REAL LLM 포함 전체

### 게이트별 티어 할당 (V587 기준)

| 게이트 ID | 티어 | 근거 |
|-----------|------|------|
| `llm_zero` | L0 | 정적 분석, 즉시 |
| `llm0_static_analysis` | L0 | 정적 분석, < 100ms |
| `auth_regression_g34` | L0 | import 수준 |
| `adapter_canonical_g35` | L1 | 어댑터 존재 확인 |
| `duplicate_zero_g37` | L1 | 중복 클래스 스캔 |
| `async_discipline_g38` | L1 | AST 분석 |
| `performance_baseline_g39` | L1 | 마이크로 벤치마크 |
| `graph_real_adapter_g44` | L1 | NetworkX mock |
| `losdb_client_g45` | L1 | Facade 연결 확인 |
| `e2e_prose_g46` | L1 | MOCK 모드 E2E |
| 나머지 35게이트 | L2 | 통합·회귀 |

---

## 구현

### `run_release_gate_tiered(tiers=None)`

```python
# literary_system/gates/release_gate.py
def run_release_gate_tiered(tiers: list[str] | None = None) -> dict:
    """tiers=['L0','L1'] → fast-path 10게이트만 실행."""
    ...
```

- `tiers=None` → 전체 실행 (기존 `run_release_gate()` 동일)
- `tiers=['L0']` → pre-commit 3게이트
- `tiers=['L0','L1']` → PR fast-path 10게이트

### `_GATE_TIER` 딕셔너리

`release_gate.py` 내부에 각 게이트 ID → 티어 매핑 정의.  
`GateRegistryEntry.tier` 필드에도 동기화 (`gate_registry.py`).

### CI 워크플로 분리 (ADR-048 연계)

`.github/workflows/ci.yml` 4-job 구조:

```
precommit_gates   → tiers=[L0]
pr_check_gates    → tiers=[L0,L1]
main_merge_gates  → tiers=[L0,L1,L2]
release_full      → tiers=None (전체)
```

---

## 대안 고려

| 대안 | 기각 이유 |
|------|-----------|
| pytest mark으로만 분리 | gate 레지스트리와 이중 관리 |
| 게이트 수 줄이기 | 커버리지 손실 |
| 전체를 항상 실행 | PR 마다 120s+ CI 비용 |

---

## 영향

- **`gate_registry.py`**: `GateRegistryEntry.tier` 필드 추가 (breaking 아님, 기본값 `"L2"`)
- **`release_gate.py`**: `run_release_gate_tiered()` 추가, 기존 API 유지
- **`tools/measure_gate_time.py`**: `--quick` 플래그로 L0+L1 실측 지원
- **CI**: `.github/workflows/ci.yml` 4-job 분리 (ADR-048 연계)

---

## 결과

V587 기준 L0+L1 fast-path 실측: **1103.7ms** (10게이트, 목표 30s 대비 ✅ PASS).  
`docs/perf/gate_timings_v587.json` 에 측정 결과 저장.
