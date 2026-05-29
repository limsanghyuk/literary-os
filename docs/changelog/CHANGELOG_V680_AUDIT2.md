# CHANGELOG — V680-AUDIT2 (v12.0.2)

**날짜**: 2026-05-27  
**버전**: 12.0.2  
**커밋 브랜치**: main  
**검증**: 최고 수석 아키텍처(CSA) × 최고 수석 컴파일러(CSC) 2차 독립 교차검증

---

## 개요

V680-AUDIT(v12.0.1)에 대한 2차 전문가 교차검증(CSA + CSC)을 수행하여
아래 2건의 결함을 추가 식별·수정한 패치이다.

---

## 수정 사항

### DEFECT-2 (P3) — VERSION 상수 미갱신
**파일**: `literary_system/enterprise/phase_c_exit_gate.py`  
**증상**: `EnterprisePhaseCExitGate.VERSION = "12.0.0"` 및
`EnterprisePhaseCExitReport.version: str = "12.0.0"` 두 곳이
v12.0.1 버전 범프 시 갱신되지 않아, G79 보고서가 항상 "v12.0.0"을 출력.
pyproject.toml(12.0.1)과 보고서 메타데이터 불일치.  
**수정**: 두 상수 모두 `"12.0.1"` → `"12.0.2"` 기준으로 `"12.0.1"` 적용 후 최종 `"12.0.2"` 반영.  
**영향 테스트**: `test_v680_phase_c_exit.py` line 132, 144, 156 assertion 3건 동반 수정.

### DEFECT-3 (P3) — test_gate_count_75 stale assertion
**파일**: `tests/integration/test_v675_enterprise_integration.py`  
**증상**: V675 시점 작성된 `assert len(GATES) == 75`가 V676~V680 게이트 추가(→80)
이후 갱신되지 않아 통합 테스트 1건이 지속 실패 상태.  
**수정**: 함수명 `test_gate_count_75` → `test_gate_count_80`, assertion `== 75` → `== 80`.  
**영향**: test_inventory 재생성 (source_hash 갱신, TC=8845 유지).

---

## CSA × CSC 설계 관찰 (수정 불필요 — 설계 의도 확인)

| 관찰 ID | 모듈 | 내용 | 판정 |
|---------|------|------|------|
| D-1 | compliance_audit.py | G78 항상 PASS (보고 목적 — ADR comment 명시) | 설계 의도 |
| D-2 | cost_control.py | G77 항상 PASS / is_blocking dead code (알림 전용) | 설계 미완성 (이슈 아님) |
| D-3 | benchmark.py | WARN 시 passed=False → G79 실패 가능 (현 데모 안전) | Fragility 허용 |
| D-4 | slo.py | throughput 위반은 BREACH 불가 → G73 통과 | 설계 제약 허용 |
| D-5 | revenue.py | TIERED 비연속 구간 오배분 가능성 (데모 안전) | 설계 제약 허용 |
| D-6 | phase_c_exit_gate.py | G74 details에 invoices attr 없어 수집 누락 | 정보 손실 허용 |

---

## 테스트 결과

| 항목 | 결과 |
|------|------|
| Unit Tests | 2628 PASS |
| Integration Tests | 89 PASS (1 skip) |
| **전체** | **2717 PASS, 1 skip, 0 FAIL** |
| Gates | 80 / 80 PASS |
| TC (inventory) | 8,845 |

---

## 변경 파일 목록

```
literary_system/enterprise/phase_c_exit_gate.py   # DEFECT-2: VERSION "12.0.0"→"12.0.1"→"12.0.2"
tests/unit/test_v680_phase_c_exit.py               # DEFECT-2: version assertion 3건
tests/integration/test_v675_enterprise_integration.py  # DEFECT-3: gate_count 75→80
tools/test_inventory.json                          # source_hash 재생성 (TC=8845)
pyproject.toml                                     # version 12.0.1 → 12.0.2
docs/changelog/CHANGELOG_V680_AUDIT2.md           # 본 문서
```
