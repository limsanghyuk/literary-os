# CHANGELOG — V640-PATCH (v11.11.0)

**릴리즈일**: 2026-05-26
**태그**: v11.11.0
**ADR**: ADR-100

## 개요
Phase C 본안 v1.2 §2.3 F9 의무 이행.
SP-C.1 자기학습 루프에서 생성되는 훈련 데이터(DataAugmentationController, FeedbackIntegrator 출처)의
안전 검증 공백을 해소하기 위한 사전 보강 패치.

## 신규 모듈
- `literary_system/safety/__init__.py` — safety 서브패키지 초기화
- `literary_system/safety/safety_regression_v2.py` — SafetyRegressionV2 4축 검증기
  - 4축: self_harm / hate_speech / PII / copyright
  - LLM-0 준수: regex 전용, 외부 API 호출 없음
  - 한국어 패턴: `\b` 미사용, 직접 매칭
  - SafetyRegressionViolation / SafetyRegressionReport 데이터클래스

## 신규 문서
- `docs/adr/ADR-100.md` — SafetyRegressionV2 설계 결정 기록

## 신규 테스트
- `tests/unit/test_v640patch_safety_regression_v2.py` — 33 TC (33/33 PASS)

## 변경 사항
- `tools/test_inventory.json` — 7577 TC (+ 33)
- 클래스명 정정: `SafetyViolation` → `SafetyRegressionViolation` (Gate G37 DuplicateZero 준수)

## Release Gate
- 61/61 PASS
