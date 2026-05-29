# CHANGELOG V546 — Phase 6 Stage A: Cleanup & Foundation

**릴리즈:** V546  
**날짜:** 2025-01-01  
**단계:** Phase 6 Stage A  
**상태:** 완료 (PASS)

---

## 개요

V546은 Phase 6의 첫 번째 단계로, V545까지 누적된 8개의 기술 부채(P1~P8)를 해결하고 ADR-027~031을 신설하는 Cleanup & Foundation 릴리즈입니다.

---

## 해결된 문제 (P1~P8)

### P1: LLM-0 정책 위반 정리
- `multiwork/` 내 직접 LLM 호출 제거
- ADR-015/031 준수 강화

### P2: StoryDoctorOrchestrator 우선순위 정렬
- 수리 추천 우선순위 정렬 로직 수정
- 동점 처리 안정화

### P3: ArcConsistencyChecker 임계값 조정
- 일관성 점수 임계값 0.7 → 0.75 상향
- 경계 케이스 처리 개선

### P4: AutoRepairExecutor 안전성 강화
- 최대 수리 시도 횟수 제한 추가
- 롤백 메커니즘 구현

### P5: NarrativeDebtDetector 성능 최적화
- O(n²) → O(n log n) 알고리즘 개선
- 대규모 씬 그래프 처리 속도 향상

### P6: Gate28 판정 기준 명확화
- StoryQualityGate 판정 조건 문서화
- 엣지 케이스 처리 추가

### P7: 테스트 격리 강화
- 테스트 간 상태 공유 제거
- 각 테스트 독립성 보장

### P8: 소급 설계 문서 작성
- ADR-027~031 신설
- 레거시 결정 사항 문서화

---

## 신규 ADR

| ADR | 제목 |
|-----|------|
| ADR-027 | LLM-0 Policy — multiwork 모듈 LLM 호출 금지 |
| ADR-028 | StoryDoctor 우선순위 정렬 정책 |
| ADR-029 | ArcConsistency 임계값 정책 (0.75) |
| ADR-030 | AutoRepair 안전 실행 정책 |
| ADR-031 | Cleanup 소급 설계 문서화 정책 |

---

## 테스트 결과

- **PASS:** 5,210+  
- **FAIL:** 0  
- **SKIP:** 20  

---

## 다음 버전

→ V547: Phase 6 Stage B (PNE — Proactive Narrative Engine) 시작
