# CHANGELOG V573 — Gate28 이중 무력화 완전 수정 + Preflight Step14 + 테스트 보강

**버전**: v7.8.1-V573  
**날짜**: 2026-05-18  
**분류**: Hotfix (CRITICAL + HIGH + MEDIUM) + 예방 인프라 강화  
**기준**: V572 (v7.8.0) 감사 보고서 literary_os_v572_audit_proposal.docx  
**설계도**: literary_os_v573_blueprint.docx  
**테스트**: 5465 PASS / 0 FAIL / 20 SKIP (V572 대비 +9)

---

## 수정 내역

### BUG-1 (CRITICAL) — Gate28Result 속성 오독 수정
- **파일**: `literary_system/gates/release_gate.py`
- **변경**: `getattr(result, "overall_passed", True)` → `result.approved`
- **영향**: Gate28이 항상 True를 반환하던 실질적 무력화 수정

### BUG-2 (HIGH) — 존재하지 않는 타입명 Import 수정
- **파일**: `literary_system/gates/release_gate.py`
- **변경**:
  - `DebtReport` → `NarrativeDebtReport` (import + 생성자 전면)
  - `ArcReport` → `ArcConsistencyReport` (import + 생성자 전면)
  - `NarrativeDebtReport` 생성자: `total_debts`, `unresolved_secrets`, `broken_foreshadows`, `abandoned_threads`, `overall_debt_score`
  - `ArcConsistencyReport` 생성자: `total_issues`, `not_tracked`, `post_death_edges`, `contradiction_flows`, `episode_inversions`, `overall_score`
  - `DoctorReport` 생성자: `work_id` 제거 → `total_issues`, `high_priority`, `medium_priority`, `low_priority` 추가
- **영향**: `ImportError` → except 분기만 실행하던 Gate28 로직 정상화

### BUG-3 (MEDIUM) — ToolUseParser 타입명 오염 수정
- **파일**: 3개 llm_bridge 파일
  - `literary_system/llm_bridge/openai_compatible_adapter.py`
  - `literary_system/llm_bridge/llm_node_router.py`
  - `literary_system/llm_bridge/physics_aware_router.py`
- **변경**: `ActionPacketParser` → `ToolUseParser`
- **영향**: tool_use 기능 무음 비활성화 해소

---

## 예방 인프라 (신설)

### ADR-033 — Preflight Step14: Gate-Type AST 대조
- **파일**: `docs/adr/ADR-033.md`
- **내용**: Gate 함수 내 import 타입명을 AST로 자동 대조하는 방침 수립

### tools/preflight_step14.py (신설)
- `release_gate.py` 내 `_gate_*` 함수의 alias 없는 `from X import Y` 수집
- 대상 모듈의 실제 class + function 명칭과 대조
- `--strict`: 불일치 시 exit(1) — CI 블로킹
- V573 기준: 29개 Gate 함수, 55개 타입 import, **불일치 0건**

### .github/workflows/ci.yml (수정)
- `preflight-step14` 잡 추가 (preflight 잡 직후 실행)
- test 잡: `needs: [preflight, preflight-step14]` — Step14 FAIL 시 테스트 블로킹
- CI 체계: 5잡 (preflight → preflight-step14 → test×2 → integrity)

---

## 테스트 보강

### tests/test_gate28_unit.py (신설)
Gate28 직접 테스트 — TC-01~05 5케이스
- TC-01: 빈 보고서 → approved=True
- TC-02: debt 임계값 초과 → approved=False
- TC-03: arc 임계값 초과 → approved=False
- TC-04: combined_quality 수식 (debt×0.55 + arc×0.45) 정확도 검증
- TC-05: Gate28Result.approved 속성 + BUG-1/2 회귀 검증

### tests/test_tool_use_parser.py (신설)
ToolUseParser 직접 테스트 — TC-01~04 4케이스
- TC-01: tool_use_parser 모듈 + 3개 어댑터 임포트 성공 (BUG-3 회귀 방지)
- TC-02: parse_tool_input 정상 파싱
- TC-03: parse_raw_response dict 형태 파싱
- TC-04: tool_use 없을 때 fallback ActionPacket 반환

---

## 변경 파일 목록

| 파일 | 변경 | 항목 |
|------|------|------|
| `literary_system/gates/release_gate.py` | 수정 | BUG-1, BUG-2 |
| `literary_system/llm_bridge/openai_compatible_adapter.py` | 수정 | BUG-3 |
| `literary_system/llm_bridge/llm_node_router.py` | 수정 | BUG-3 |
| `literary_system/llm_bridge/physics_aware_router.py` | 수정 | BUG-3 |
| `tools/preflight_step14.py` | 신설 | ADR-033 |
| `.github/workflows/ci.yml` | 수정 | CI Step14 잡 |
| `docs/adr/ADR-033.md` | 신설 | ADR-033 |
| `tests/test_gate28_unit.py` | 신설 | TC-01~05 |
| `tests/test_tool_use_parser.py` | 신설 | TC-01~04 |
| `CHANGELOG_V573.md` | 수정 | 릴리즈 |
| `literary_os_v573_blueprint.docx` (workspace) | 신설 | 설계도 |

---

## ADR 참조

- **ADR-032** (Preflight Step13): 테스트 의존성 대조 — V572에서 신설
- **ADR-033** (Preflight Step14): Gate 함수 타입명 AST 대조 — **V573 신설**

---

*Literary OS Claude v7.8.1-V573 | 2026-05-18*
