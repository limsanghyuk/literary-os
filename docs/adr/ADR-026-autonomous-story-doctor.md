# ADR-026: Autonomous Story Doctor (ASD) — Phase 5 SP1

**Status:** Accepted  
**Date:** 2026-05-17  
**Version:** 5.5.0 (V541~V545)

## Context

Phase 4 GIG(Graph Intelligence Gate, V526~V540)는 서사 지식 그래프를 구축하고
씬 변경 전 영향 반경을 계산하는 수동 검사 체계를 완성했다.
그러나 기존 그래프에 누적된 서사 부채(narrative debt)를 자동으로 탐지·진단·수리하는
능동적 메커니즘이 없었다.

## Decision

Phase 5 ASD를 5개 모듈(V541~V545)로 구현한다.

### 모듈 구성

| 버전 | 모듈 | 역할 |
|------|------|------|
| V541 | `NarrativeDebtDetector` | 3종 서사 부채 탐지 |
| V542 | `ArcConsistencyChecker` | 4종 캐릭터 아크 일관성 검증 |
| V543 | `StoryDoctorOrchestrator` | 우선순위 수리 추천 엔진 |
| V544 | `AutoRepairExecutor` | PlanBuildProtocol 경유 안전 수리 실행 |
| V545 | `Gate28` | StoryQualityGate — 서사 품질 승인 게이트 |

### 서사 부채 분류 (NarrativeDebtDetector)

| 부채 유형 | 탐지 기준 | 기본 심각도 |
|-----------|-----------|-------------|
| UNRESOLVED_SECRET | SECRET → REVEALS 엣지 없음 | 0.70 |
| BROKEN_FORESHADOW | FORESHADOWS 대상 씬 없음/비씬/고아 씬 | 0.60 |
| ABANDONED_THREAD | CHARACTER 나가는 엣지 없음 | 0.50 |

### 아크 일관성 검사 (ArcConsistencyChecker)

| 검사 | 기준 | 기본 심각도 |
|------|------|-------------|
| AC-1 ARC_NOT_TRACKED | 감정 압력 추적 없음 | 0.45 |
| AC-2 ARC_POST_DEATH_EDGE | episode_last 이후 관계 노드 존재 | 0.80 |
| AC-3 ARC_CONTRADICTION_OVERFLOW | 캐릭터 쌍 CONTRADICTS ≥ 2 | 0.65 |
| AC-4 ARC_EPISODE_INVERSION | episode_first > episode_last | 0.90 |

### 우선순위 공식 (StoryDoctorOrchestrator)

```
priority_score = min(severity × (1 + blast_weight × blast_ratio), 1.0)

blast_ratio = len(affected_scenes) / max(total_scenes, 1)
blast_weight = 1.5 (기본)
```

### Gate28 임계값

| 게이트 | 지표 | 임계값 |
|--------|------|--------|
| G28-1 | debt_score | ≤ 0.50 |
| G28-2 | arc_score | ≤ 0.40 |
| G28-3 | high_priority_cnt | ≤ 5 |
| G28-4 | combined_quality | ≤ 0.45 |

```
combined_quality = min(debt_score × 0.55 + arc_score × 0.45, 1.0)
```

## LLM-0 준수

ASD 전체 패키지(`literary_system/graph_intelligence/asd/`)는 외부 LLM 호출이 없는
순수 그래프 탐색 기반 알고리즘으로 구성된다(ADR-015 LLM-0 정책 준수).

## 결과

- 5210 PASS / 20 SKIP (기준선 5157 대비 +53)
- 신규 파일 5종: `narrative_debt_detector.py`, `arc_consistency_checker.py`,
  `story_doctor_orchestrator.py`, `auto_repair_executor.py`, `gate28.py`
- 테스트: `tests/test_v541_v545_phase5_asd.py` (53 tests)
