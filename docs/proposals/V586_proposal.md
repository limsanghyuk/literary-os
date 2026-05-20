# V586 제안서 — LOSDBClient: LOSDB 통합 Facade

**버전**: 9.1.0  
**날짜**: 2026-05-20  
**ADR**: ADR-045  
**Gate**: G45  
**레이어**: L1  

---

## 배경

V585로 LOSDB Phase B (REAL 구현 3종: SQLiteRealAdapter / VectorRealAdapter / GraphRealAdapter) 가 완료되었다. 그러나 세 어댑터는 각자 독립적으로 존재하며 통합 진입점이 없다. 사용자는 세 어댑터를 직접 인스턴스화하고 각각의 API를 따로 학습해야 한다.

## 목표

1. **단일 진입점**: `LOSDBClient` 하나로 SQL/Vector/Graph 백엔드를 통합 관리
2. **cross_query**: 복수 백엔드에서 label 기반 조회 후 결과 병합
3. **옵셔널 백엔드**: 어댑터 미제공 시 해당 백엔드 비활성 (부분 설치 지원)
4. **Gate G45**: LOSDBClient 통합 검증 8체크포인트

## 비범위 (V587+)

- 쿼리 옵티마이저 (비용 기반 백엔드 선택)
- 트랜잭션 분산 커밋
- 스키마 자동 마이그레이션

## 결정

ADR-045: `LOSDBClient` Facade 패턴으로 세 어댑터를 통합.

## 리스크

- 낮음: 기존 어댑터를 변경하지 않으므로 기존 테스트 영향 없음
- 낮음: 어댑터 독립 유지로 결합도 증가 없음
