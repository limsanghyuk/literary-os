# ADR-073: Phase B 시스템 통합 테스트 전략

**Status**: Accepted  
**Date**: 2026-05-23  
**Version**: V613 (v10.18.0)  
**Author**: Literary OS Team

## Context

SP-B.1 (LoRA Fine-tuning), SP-B.2 (RLHF 루프), SP-B.3 (MultiWork 협업) 세 서브페이즈가
각각 독립 개발 및 Gate 검증을 완료했다. SP-B.4 진입 전에 세 서브페이즈 간의
엔드-투-엔드 파이프라인 연결성을 단일 통합 테스트 파일로 검증할 필요가 있다.

## Decision

`tests/integration/test_system_integration.py`를 신설하여 Phase B 전체의
크로스-서브페이즈 통합을 검증한다.

### 테스트 구조 (4 클래스, 31 TC)

| 클래스 | 대상 | TC 수 |
|--------|------|-------|
| `TestSPB1Integration` | SP-B.1 LoRA 파이프라인 (G53/G54) | 7 |
| `TestSPB2Integration` | SP-B.2 RLHF 루프 (G55/G56/G57) | 10 |
| `TestSPB3Integration` | SP-B.3 MultiWork 협업 (G58/G59) | 9 |
| `TestPhaseBCrossIntegration` | 크로스 서브페이즈 + 전체 Gate | 5 |

### 검증 원칙

1. **실제 인터페이스 기반**: 각 클래스의 실제 시그니처를 기준으로 TC 작성
2. **Gate 직접 실행**: 유닛 TC에 더해 G53~G59 7개 Gate를 직접 호출하여 PASS 확인
3. **병존 검증**: 서브페이즈 간 의존성 없이 독립 인스턴스화 가능함을 증명
4. **데이터 흐름 검증**: add→get, register→stack 등 상태 변환 흐름 포함

## Consequences

- **긍정**: SP-B.4 PerformanceOptimizer 개발 전에 Phase B 전체 기준선 확보
- **긍정**: 31 TC 추가로 6527 → 6558 PASS (테스트 밀도 향상)
- **중립**: integration/ 폴더에 두 번째 파일 추가 (qdrant_live.py 기존 파일과 공존)
- **부정**: Gate 직접 실행이 포함되어 통합 테스트 시간이 단위 테스트보다 길다

## Relationship

- Supersedes: 없음 (신규)
- Depends on: ADR-056~072 (SP-B.1~B.3 전체 ADR)
- Enables: ADR-074 (V614 PerformanceOptimizer)
