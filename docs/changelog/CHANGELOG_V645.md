# CHANGELOG — V645

## 버전
v11.16.0

## 날짜
2026-05-26

## 요약
SP-C.1 최종 완료 게이트 G63 (SelfLearningGate) 신설. MetaLearnerCycle 4사이클(V641~V644)
완주 후 오염 0% / KL<0.05 / Krippendorff α≥0.70 세 축을 자동 검증하는 릴리즈 게이트.
Release Gate 62/62 PASS, SP-C.1 완전 종료.

## 변경 내용

### 신규 모듈
- `literary_system/gates/self_learning_gate.py`
  - `_kl_divergence_from_uniform()` — KL(w||uniform) 계산
  - `SLGAxisResult` — 단일 평가 축 결과 (axis_name/value/threshold/passed/detail)
  - `SelfLearningGateReport` — G63 게이트 보고서 (JSONL 영속화)
  - `SelfLearningGate` — 게이트 클래스 (in-memory / file 모드)
  - `run_g63_gate()` — 7체크포인트 통합 실행

### 수정 모듈
- `literary_system/gates/release_gate.py` — G63 등록 (62번째 게이트)
- `literary_system/gates/__init__.py` — SelfLearningGate 심볼 공개
- `literary_system/constitution/__init__.py` — MetaLearnerCycle 심볼 공개

### 테스트
- `tests/unit/test_v645_self_learning_gate.py` — 33 TC (33/33 PASS)
  - TC-001~005: 상수 검증
  - TC-006~012: KL 발산 수식 검증
  - TC-013~018: AxisResult 데이터클래스
  - TC-019~025: SelfLearningGateReport
  - TC-026~031: SelfLearningGate 클래스
  - TC-032~033: run_g63_gate 통합

### 문서
- `docs/adr/ADR-105.md` — G63 SelfLearningGate 결정 기록

## 테스트 현황
- 전체: 7742+ PASS (≥7709 + 33)
- Release Gate: 62/62 PASS

## 마일스톤
- **SP-C.1 완료** (V641~V645, MetaLearnerCycle 4사이클 + G63)
- Phase C 이행 준비 완료
