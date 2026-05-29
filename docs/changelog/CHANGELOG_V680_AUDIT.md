# CHANGELOG — V680-AUDIT (v12.0.1)

**날짜**: 2026-05-27
**버전**: 12.0.1
**태그**: v12.0.1, v12.0.1-V680-AUDIT
**기반**: V680 (v12.0.0, a1c391dd)

---

## 감사 개요

V680 전체 로직·알고리즘·무결성 정밀 감사 실시.
SP-C.4 Enterprise Layer (G73~G79) 6개 게이트 전수 점검.

---

## 발견된 결함 및 수정

### DEFECT-1 (P1) — `_get_total_tc()` JSON 키 오류 ✅ 수정

**파일**: `literary_system/enterprise/phase_c_exit_gate.py`

**증상**: `demo_run()` 직접 호출 시 `gate_passed=False, total_tc=0, overall_status=FAIL`.

**원인**: `_get_total_tc()`에서 `data.get("total", 0)` 사용.
`tools/test_inventory.json`의 실제 키는 `"test_count"`이며 `"total"` 키는 존재하지 않아 항상 0 반환.

**수정**: `data.get("test_count", data.get("total", 0))` — `test_count` 우선, `total` fallback.

**영향**: `release_gate.py`의 G79 함수는 `total_tc=8839`를 명시 주입하므로 원래 80/80 PASS였으나,
`demo_run()` 직접 호출 경로 및 독립 배포 환경에서 G79가 오동작함.

**수정 후 검증**:
```
demo_run() → gate_passed=True, total_tc=8845, tc_satisfied=True, overall_status=PASS ✅
```

---

## 추가 테스트 커버리지 (TestDemoRunGetTotalTc, +6 TC)

`tests/unit/test_v680_phase_c_exit.py`에 `TestDemoRunGetTotalTc` 클래스 추가:

| TC | 설명 |
|----|------|
| test_demo_run_gate_passed | demo_run() gate_passed=True 검증 |
| test_demo_run_total_tc_nonzero | demo_run() total_tc > 0 검증 |
| test_demo_run_tc_satisfies_minimum | tc_satisfied=True (MIN_TC=8500) |
| test_demo_run_overall_status_pass | overall_status=PASS |
| test_get_total_tc_returns_positive | _get_total_tc() > 0 |
| test_get_total_tc_matches_inventory | _get_total_tc() == test_inventory.json.test_count |

---

## 감사 결과 — 이상 없음 항목

| 모듈 | Gate | 결과 |
|------|------|------|
| slo.py | G73 | ✅ 로직 정상 — breach 기준 명확, demo_run PASS |
| revenue.py | G74 | ✅ TIERED 수식 수학적으로 정확 (3개 경계값 검증) |
| benchmark.py | G75-BM | ✅ P99 보수적 계산, demo_run all_passed=True |
| tenant_isolation.py | G76 | ✅ STRICT 규칙 2종 정상, violations=0 |
| cost_control.py | G77 | ⚠️ gate_passed 의도적 hardcoded True (설계 상 경보 전용) |
| compliance_audit.py | G78 | ⚠️ gate_passed 의도적 hardcoded True (보고 목적) |
| phase_c_exit_gate.py | G79 | ✅ DEFECT-1 수정 완료 |

> G77/G78의 hardcoded `gate_passed=True`는 ADR 설계 의도(경보/보고 전용)이며
> 기능 결함이 아님. 단, 향후 Phase D에서 강제 집행 모드 추가 권장.

---

## 메타데이터 갱신

| 항목 | V680 | V680-AUDIT |
|------|------|------------|
| 버전 | 12.0.0 | 12.0.1 |
| TC | 8839 | **8845** (+6) |
| Gates | 80/80 | **80/80** |
| 결함 수정 | 0 | **1 (P1)** |

---

## 파일 변경 목록

- `literary_system/enterprise/phase_c_exit_gate.py` — DEFECT-1 수정
- `tests/unit/test_v680_phase_c_exit.py` — TestDemoRunGetTotalTc +6 TC
- `tools/test_inventory.json` — 8845 TC, hash 갱신
- `pyproject.toml` — 12.0.0 → 12.0.1
- `docs/changelog/CHANGELOG_V680_AUDIT.md` — 본 파일
