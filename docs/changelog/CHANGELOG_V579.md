# CHANGELOG V579 — Duplicate Resolution + Gate G37

**버전**: 8.4.0 (V579)  
**날짜**: 2026-05-19  
**테스트**: 5,604 PASS / 36 Gates PASS  

## 변경 개요

CR-4 중복 클래스 88개(실측 36종) → **0건** 해소.  
Gate G37 DuplicateZero 신설로 CI 강제.

## 핵심 변경

### 중복 클래스 해소 (36종)

| 구분 | 처리 방식 | 대표 클래스 |
|------|---------|------------|
| Rename + alias | 23종 | GateResult→PhysicsGateResult/EnduranceGateResult 등 |
| Rename + alias | 8종 | RelationType→NarrativeRelationType/CharacterRelationType 등 |
| Rename + alias | 5종 | SearchResult→QdrantSearchResult/BGESearchResult 등 |

**원칙**: 리네임 후 `OldName = NewName` backward-compat alias 추가.  
기존 임포트 코드 변경 불필요.

### Gate G37 DuplicateZero (ADR-033)
- `_gate_duplicate_zero_g37()`: literary_system/ AST 스캔
- 이종 파일 간 동일 class명 0건 강제
- GATE_REGISTRY 등록: adr_ref=ADR-033, version_added=V579, layer=L1

### 기타
- gate_registry.py _META: G36, G37 항목 추가
- tests/test_v579_duplicate_zero.py: 25 TC PASS
- pyproject.toml: 8.3.0 → 8.4.0

## 수치 현황

| 항목 | V578 | V579 |
|------|------|------|
| 중복 클래스 | 36종 | **0종** |
| Gates | 35 | **36** |
| 테스트 PASS | 5,579 | **5,604** |
| 버전 | 8.3.0 | **8.4.0** |

## ADR 참조

- ADR-033: DuplicateZero — 클래스명 단일 위치 원칙 (V579 신설)
