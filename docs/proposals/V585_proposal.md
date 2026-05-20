# V585 제안서 — GraphRealAdapter (LOSDB Phase B 완료)

**버전:** 9.0.0  
**날짜:** 2026-05-20  
**ADR:** ADR-044  
**레이어:** L1 (DB 레이어)

## 1. 배경

LOSDB Phase B 최종 단계. SQL(V582)+Vector(V584) 완료 → Graph(V585) 완료로 Phase B 전체 완성.

## 2. 핵심 결정

- **networkx-optional**: networkx 설치 시 DiGraph 가속, 미설치 시 adjacency-dict fallback
- **GraphRecord**(노드) + **GraphEdgeRecord**(엣지) 데이터클래스
- **Migration.graph_ops**: op = add_node | add_edge | remove_node | remove_edge
- **JSON 영속화** + **rollback 스냅샷** (V584 패턴 계승)
- **Gate G44** (ADR-044, L1), **버전 9.0.0** (메이저 범프)

## 3. 구현 범위

신규: graph_real_adapter.py, test_v585_*, ADR-044, V585_design.md, CHANGELOG_V585.md  
수정: migration_manager.py(graph_ops), __init__.py, release_gate.py(G44), gate_registry.py, pyproject.toml(9.0.0)
