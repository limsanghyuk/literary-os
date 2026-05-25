# CHANGELOG V630

**버전**: v11.0.0  
**릴리즈 날짜**: 2026-05-25  
**기반 버전**: V629 (v10.34.0)  
**Phase**: Phase B 완전 종료

---

## 개요

V630은 Literary OS Phase B의 최종 릴리즈이다.  
G61 Phase B Exit Gate를 7축으로 강화하고, Phase B 전 기간에 걸쳐 축적된 인터페이스 추적 요구사항을 Exit Gate 수준에서 공식 검증한다.  
버전이 v10.x → v11.0.0으로 major 범프되며, Phase B가 공식 종료된다.

---

## 변경 사항

### 신규 기능

#### C7 InterfaceTrace (phase_b_exit_gate.py)

- `P_IF_TRACE_REQUIRED` 상수: P-IF-01~05 5건 정의
- `verify_interfaces_trace()` 함수 신설: 동적 importlib 기반 검증, override 지원
- `run_phase_b_exit_gate()` C7 체크포인트 추가
- `_if_trace_override` 파라미터 추가 (테스트 주입용)
- `run_g61_gate()` gate_name "SP-B 7축 완료 판정 (V630)" 업데이트

#### MIN_TESTS 상향 (6700 → 7000)

- C6 판정 기준이 tests ≥ 7000으로 강화됨
- Phase B V621~V630 누적 테스트 수 7000+ 달성 반영

### 문서

- `docs/adr/ADR-097.md` 신설 (supersedes ADR-080)
- `docs/changelog/CHANGELOG_V630.md` 신설 (본 파일)

### 버전 범프

- `pyproject.toml`: 10.34.0 → **11.0.0**
- `live_core_manifest.json`: V629 → **V630**, v10.34.0 → **v11.0.0**
- `literary_system/gates/release_gate.py`: "V629" → **"V630"**

---

## 테스트

| 파일 | TC 수 | 결과 |
|------|-------|------|
| `tests/unit/test_v630_phase_b_exit_v2.py` | 60 | 60/60 PASS |

---

## ADR 참조

- ADR-097: G61 Phase B Exit Gate 7축 강화 (본 버전)
- ADR-080: Superseded by ADR-097

---

## Phase B 종료 선언

V620~V630에 걸쳐 수행된 Phase B 작업이 완료되었다:

- **SP-B.1** (V596~V600): LoRA Fine-tuning Pipeline (Gate G54)
- **SP-B.2** (V601~V621): RLHF 루프 + 인터페이스 추적 (Gate G56/G57)
- **SP-B.3** (V607~V622): MultiWork 협업 7모듈 (Gate G59)
- **SP-B.4** (V614~V620): PerformanceSLO (Gate G60)
- **Exit Gate** (V620/V630): G61 7축 판정 (ADR-097)

Phase C 이행 준비 완료.
