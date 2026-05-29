# ADR-028: Gate 계층 L1~L4 통합 카탈로그

Status: Accepted

## 문제
Gate25~28이 release_gate.py GATES 목록에 미등록 (P3).
21개 게이트 우선순위·중복·실행 순서 정책 부재.

## 결정
GateHierarchyManager로 L1~L4 계층 정의:
- L1: Gate1~24 (release_gate.py 기존)
- L2: Gate25 (NIE 수렴)
- L3: Gate26·27 (GIG 서사/코드)
- L4: Gate28 (ASD 품질)

release_gate.py GATES 목록에 Gate25~28 4개 추가.

## 근거
P3 해소. 모든 게이트가 단일 실행 경로로 통합됨.
