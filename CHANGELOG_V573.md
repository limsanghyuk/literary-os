# CHANGELOG V573 — Hotfix: Gate28 이중 무력화 버그 수정

**버전**: v7.8.1-V573  
**날짜**: 2026-05-18  
**분류**: Hotfix (CRITICAL + HIGH + MEDIUM)  
**기준**: V572 (v7.8.0) 감사 보고서 literary_os_v572_audit_proposal.docx

---

## 수정 내역

### BUG-1 (CRITICAL) — Gate28Result 속성 오독 수정
- **파일**: `literary_system/gates/release_gate.py`
- **위치**: L498 (구 L482)
- **변경**: `getattr(result, "overall_passed", True)` → `result.approved`
- **영향**: `Gate28Result`에 `overall_passed` 속성 없음 → `getattr` fallback True로 항상 통과
  → Gate28이 실질적으로 작동하지 않던 문제 수정

### BUG-2 (HIGH) — 존재하지 않는 타입명 Import 수정
- **파일**: `literary_system/gates/release_gate.py`
- **변경**:
  - `DebtReport` → `NarrativeDebtReport` (import + 생성자)
  - `ArcReport` → `ArcConsistencyReport` (import + 생성자)
  - `NarrativeDebtReport` 생성자: `total_debts`, `unresolved_secrets`, `broken_foreshadows`, `abandoned_threads`, `overall_debt_score` 필드로 교체
  - `ArcConsistencyReport` 생성자: `total_issues`, `not_tracked`, `post_death_edges`, `contradiction_flows`, `episode_inversions`, `overall_score` 필드로 교체
  - `DoctorReport` 생성자: `work_id` 제거, `total_issues`, `high_priority`, `medium_priority`, `low_priority` 추가
- **영향**: `ImportError` 발생 → Gate28 except 분기 항상 실행 → Gate28 로직 미실행

### BUG-3 (MEDIUM) — ToolUseParser 타입명 오염 수정
- **파일**: 
  - `literary_system/llm_bridge/openai_compatible_adapter.py`
  - `literary_system/llm_bridge/llm_node_router.py`
  - `literary_system/llm_bridge/physics_aware_router.py`
- **변경**: `ActionPacketParser` → `ToolUseParser` (tool_use_parser 모듈 내 실제 클래스명)
- **영향**: `ImportError` → try/except에서 None 반환 → tool_use 기능 무음 비활성화

---

## 수정 파일 목록

| 파일 | 변경 유형 | 버그 |
|------|-----------|------|
| `literary_system/gates/release_gate.py` | 수정 | BUG-1, BUG-2 |
| `literary_system/llm_bridge/openai_compatible_adapter.py` | 수정 | BUG-3 |
| `literary_system/llm_bridge/llm_node_router.py` | 수정 | BUG-3 |
| `literary_system/llm_bridge/physics_aware_router.py` | 수정 | BUG-3 |
| `CHANGELOG_V573.md` | 신설 | — |

---

## 검증

- 전체 테스트 스위트: **5456 PASS / 0 FAIL / 20 SKIP** (V572 대비 동일)
- Gate28 실제 로직 활성화 확인: `result.approved` 정상 참조
- ToolUseParser 정상 임포트 확인

---

## ADR 참조

- **ADR-032** (Preflight Step 13): 이번 버그들은 Step 13이 탐지 범위에 포함되지 않은 Gate 함수 내 타입명까지 다루지 못한 사례 → **Preflight Step 14 (Gate 함수 타입 AST 대조)** 필요성 확인
