# 세션 시작 가이드

> 집이든 회사든 **매 세션 첫 번째로** 이 내용을 Claude에게 전달하세요.

---

## 복사해서 사용하는 세션 시작 명령

```
세션을 다음 순서로 시작하라:

1. https://github.com/limsanghyuk/literary-os 최신 커밋·태그를 확인하라
2. SESSION_INIT.md 의 "현재 상태" 섹션을 읽어라
3. docs/sessions/2026-05-20_v581_integrity_audit.md 를 읽어라
4. PREFLIGHT_GUIDE.md (15단계)를 수행한 후 V584 개발을 시작하라
```

---

## 세션 종료 명령

```
세션을 다음과 같이 마무리하라:

1. docs/sessions/YYYY-MM-DD_[home|company]_[작업요약].md 를 작성하라
2. 모든 변경사항을 커밋하고 GitHub main에 push하라
3. SESSION_INIT.md 의 "현재 상태" 섹션을 업데이트하라
```

---

## 현재 상태 (2026-05-20 기준)

| 항목 | 값 |
|------|-----|
| **최신 버전** | V584 (8.9.0) |
| **HEAD 커밋** | `8a9a58e8` |
| **CI 상태** | ✅ ALL GREEN (5/5 jobs) |
| **게이트** | 40/40 PASS (G1~G40, 일부 번호 병합) |
| **테스트** | 5529+ PASS |
| **무결성 감사** | V584 완료 (B1~B4 수정) |
| **다음 버전** | **V584** (개발 전 Preflight 15단계 필수) |

---

## V584 진입 전 필수 선행 사항

```
V584 개발 시작 전 반드시 아래를 수행하라:

1. git pull origin main
2. PREFLIGHT_GUIDE.md 15단계 전체 수행
3. 15단계 완료 후 V584 개발 시작
```

> ⚠️ Preflight 없이 개발 진입 시 기준선 불일치(존재하지 않는 클래스명 참조, 게이트 수 불일치 등)가 반복됩니다.

---

## V584 개발 프로세스 요약 (표준 절차로 채택)

```
[표준 개발 사이클]
Preflight 15단계 → 개발(코드+테스트) → 커밋·태그·푸시 → CI 확인 → 로직 무결성 감사 → 버그 수정 → CI 재확인
```

### V584에서 수행한 전체 과정

1. **Preflight 15단계** — V580 기준선 확인
2. **V584 개발** — `literary_system/db/` 패키지 신설 (SchemaRegistry + MigrationManager)
3. **커밋 `8c66156d`** — Gate G40 + ADR-040 + 테스트 35종 + version 8.9.0
4. **CI 수정** — Ruff I001 auto-fix, ProvenanceLedger→RAGProvenanceLedger, fetch-depth:0
5. **CI 그린** — 커밋 `421305d1` (test_tc25 38→39 수정 포함)
6. **로직 무결성 감사** — 소스 전수 읽기 + 교차검증 → B1~B4 발견
7. **버그 수정** — 커밋 `8a9a58e8` (B1~B4 수정 + T1 회귀 테스트)
8. **CI 재확인** — 전 잡 그린 ✅

---

## 개발자에게 제공되는 최종 deliverable

| 항목 | 위치 |
|------|------|
| 소스 코드 (단일 진실 원본) | `github.com/limsanghyuk/literary-os` main 브랜치 |
| 제안서 | `docs/sessions/literary_os_v581_proposal_v2.docx` |
| 설계도 | `docs/sessions/literary_os_v581_blueprint_v2.docx` |
| Handoff 문서 | `docs/sessions/2026-05-19_home_proposals_v2_handoff.md` |
| 무결성 감사 기록 | `docs/sessions/2026-05-20_v581_integrity_audit.md` |

---

## V584+ 진화 로드맵 v2.0

- 5-Phase: A(LOSDB+CLI V584~595) → B(LoRA+B2B V596~610) → C(RLHF V611~630) → D(SDK V631~660) → E(에코시스템 V661+)
- Phase A 다음 목표: V584 — SchemaRegistry CLI 인터페이스 또는 SQL REAL 어댑터 연결 시작
- 핵심 문서: `docs/sessions/literary_os_v581_proposal_v2.docx` (제안서)
- 핵심 문서: `docs/sessions/literary_os_v581_blueprint_v2.docx` (설계도)
