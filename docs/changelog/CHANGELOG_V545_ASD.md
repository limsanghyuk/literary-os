# CHANGELOG — V545 Phase 5 ASD SP1

**Release:** 5.5.0 (2026-05-17)  
**Tests:** 5210 PASS / 20 SKIP  
**Baseline:** 5157 PASS (V540) → +53

## New Modules

### V541 — NarrativeDebtDetector
`literary_system/graph_intelligence/asd/narrative_debt_detector.py`
- DebtType: UNRESOLVED_SECRET / BROKEN_FORESHADOW / ABANDONED_THREAD
- severity 파라미터화 (secret 0.70, foreshadow 0.60, thread 0.50)
- NarrativeDebtReport: total_debts, overall_debt_score

### V542 — ArcConsistencyChecker
`literary_system/graph_intelligence/asd/arc_consistency_checker.py`
- AC-1 arc_not_tracked, AC-2 arc_post_death_edge
- AC-3 arc_contradiction_overflow (기준 2건)
- AC-4 arc_episode_inversion (episode_first > episode_last)
- ArcConsistencyReport: overall_score

### V543 — StoryDoctorOrchestrator
`literary_system/graph_intelligence/asd/story_doctor_orchestrator.py`
- priority_score = severity × (1 + 1.5 × blast_ratio)
- DoctorReport: high / medium / low priority 분류
- 내장 NarrativeDebtDetector + ArcConsistencyChecker + NarrativeImpactAnalyzer

### V544 — AutoRepairExecutor
`literary_system/graph_intelligence/asd/auto_repair_executor.py`
- PlanBuildProtocol(Gate26 + Gate27) 경유 안전 수리
- ExecutionStatus: APPROVED / DRY_RUN / GATE_FAIL / PLAN_ABORT / ERROR
- execute() + execute_batch() API

### V545 — Gate28 (StoryQualityGate)
`literary_system/graph_intelligence/asd/gate28.py`
- G28-1 debt_score ≤ 0.50
- G28-2 arc_score ≤ 0.40
- G28-3 high_priority_cnt ≤ 5
- G28-4 combined_quality ≤ 0.45 (debt×0.55 + arc×0.45)

## ADR
- ADR-026: Autonomous Story Doctor 아키텍처 결정 기록

## LLM-0
전체 ASD 패키지 외부 LLM 호출 없음 (ADR-015 준수)
