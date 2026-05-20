# 세션 시작 가이드

> 집이든 회사든 **매 세션 첫 번째로** 이 내용을 Claude에게 전달하세요.

---

## 복사해서 사용하는 세션 시작 명령

```
세션을 다음 순서로 시작하라:

1. https://github.com/limsanghyuk/literary-os 최신 커밋·태그를 확인하라
2. SESSION_INIT.md 의 "현재 상태" 섹션을 읽어라
3. docs/sessions/2026-05-20_v581_integrity_audit.md 를 읽어라
4. docs/sessions/literary_os_v587_proposal.docx 와 literary_os_v587_blueprint.docx 를 읽어라
5. PREFLIGHT_GUIDE.md (15단계)를 수행한 후 V587 개발을 시작하라
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
| **최신 버전** | **V586 (9.1.0)** |
| **HEAD 커밋** | `7adfdf76` |
| **CI 상태** | ✅ ALL GREEN (5/5 jobs) |
| **게이트** | **44/44 PASS** (G1~G45) |
| **테스트** | 5,744+ PASS |
| **LOSDB Phase** | Phase C 완료 (LOSDBClient Facade) |
| **무결성 감사** | V581 완료 (B1~B4 수정) |
| **다음 버전** | **V587** — 개발 전 Preflight 15단계 필수 |

---

## V587 진입 전 필수 선행 사항

```
V587 개발 시작 전 반드시 아래를 수행하라:

1. git pull origin main
2. PREFLIGHT_GUIDE.md 15단계 전체 수행
3. docs/sessions/literary_os_v587_proposal.docx 확인 (6개 우선순위 항목)
4. docs/sessions/literary_os_v587_blueprint.docx 확인 (구현 설계 상세)
5. 15단계 완료 후 V587 개발 시작
```

> ⚠️ Preflight 없이 개발 진입 시 기준선 불일치(존재하지 않는 클래스명 참조, 게이트 수 불일치 등)가 반복됩니다.

---

## 표준 개발 사이클

```
[표준 개발 사이클]
Preflight 15단계 → 개발(코드+테스트) → 커밋·태그·푸시 → CI 확인 → 로직 무결성 감사 → 버그 수정 → CI 재확인
```

---

## V587 개요 (6개 우선순위 항목)

| 우선순위 | 항목 | 핵심 구현 | ADR |
|---------|------|-----------|-----|
| 1 | GitHub Releases 자동화 | create_release.sh v2 매개변수화 + CI release 잡 | — |
| 2 | CI 문서 정합성 강제 | check_version_consistency.py v2 + ci.yml "44 Gates" 수정 | — |
| 3 | E2E 산문 생성 테스트 | tests/test_v587_e2e_prose.py + Gate G46 | ADR-046 |
| 4 | 산문 벤치마크 | tools/benchmark_drama.py (씬·토큰·시간) | — |
| 5 | 사용자 CLI/API 문서 | docs/quickstart.md + docs/cli_reference.md | — |
| 6 | Gate 계층화 | L0+L1 fast-path(10개) / full(44개) 분리 | ADR-046 |

**V587 목표 수치**: 버전 9.2.0 · Gates 45/45 · 테스트 5,760+ · ADR-046 신설

---

## V581~V586 개발 이력 요약

| 버전 | 내용 | Gate | ADR |
|------|------|------|-----|
| V581 | SchemaRegistry + MigrationManager (MOCK) | G40 | ADR-040 |
| V582 | SQLiteRealAdapter (REAL) + LOSDB CLI | G41 | ADR-041 |
| V583 | MigrationEngine 통합 오케스트레이터 + 롤백 체이닝 | G42 | ADR-042 |
| V584 | VectorRealAdapter (numpy-optional) | G43 | ADR-043 |
| V585 | GraphRealAdapter (networkx-optional, BFS/DFS) | G44 | ADR-044 |
| V586 | LOSDBClient Facade + cross_query | G45 | ADR-045 |

---

## V587+ 로드맵 (Phase A 잔여)

```
V587: 품질 기반 강화 (CI·E2E·Gate Tiering·Docs)
V588: LOSDB QueryInterface + PartialAvailability (ADR-058, M-02)
V589: HybridSearchV2 + LOI 1차 합의
V591: MOCK↔REAL EquivalenceTester (ADR-059, M-06)
V594: 코퍼스 1차 입수 1만 씬
V595: Minimal-CLI v0.1 출시 + 베타 5명 (M-04)
```

Phase A 종료 KPI: Gate 45개 · 테스트 5,900+ · Minimal-CLI 베타 5명

---

## 개발자 최종 deliverable 위치

| 항목 | 위치 |
|------|------|
| 소스 코드 (단일 진실 원본) | `github.com/limsanghyuk/literary-os` main 브랜치 |
| V587 제안서 | `docs/sessions/literary_os_v587_proposal.docx` |
| V587 설계도 | `docs/sessions/literary_os_v587_blueprint.docx` |
| V581+ 장기 로드맵 제안서 (v2.0) | `docs/sessions/literary_os_v581_proposal_v2.docx` |
| V581+ 장기 설계도 (v2.0) | `docs/sessions/literary_os_v581_blueprint_v2.docx` |
| V581 무결성 감사 기록 | `docs/sessions/2026-05-20_v581_integrity_audit.md` |
