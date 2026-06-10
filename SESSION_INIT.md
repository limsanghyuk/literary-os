# 세션 시작 가이드 (V745 / v13.0.0)

> 집이든 회사든 **매 세션 첫 번째로** 이 내용을 Claude에게 전달하세요.

---

## 정본 진입 순서 (이 순서대로 로드)

```
1. https://github.com/limsanghyuk/literary-os 최신 커밋·태그 확인 (git pull origin main)
2. docs/sessions/INDEX.md (전체 색인·정본 읽는 순서)
3. docs/sessions/2026-06-07_MASTER_synthesis_priorities.md (현 시점 단일 종합·우선순위)
4. docs/sessions/2026-06-07_home_handoff_v3.md (집 이어작업 정본)
5. CLAUDE.md (RULE-0 + 개발 프로토콜) · docs/workflow/DEV_PROTOCOL_v3.0.md
6. 개발 착수 시: python3 tools/run_preflight.py (RULE-0, 13단계 PASS 후에만 구현)
```

---

## 현재 상태 (2026-06-09 기준)

| 항목 | 값 |
|------|-----|
| **최신 버전** | **V745 (v13.0.0) — Phase D 완전 종료 (Phase D Exit G95)** |
| **공개 main HEAD** | github.com/limsanghyuk/literary-os (로컬과 동일) |
| **릴리즈 게이트** | **97 등록** · Phase D Exit G95 8/8 PASS |
| **테스트** | **10,788 PASS** |
| **고립 패키지** | **0개** (85개 전체 연결, ADR-128 G_CONNECTIVITY) |
| **Preflight** | 13단계 (DEV_PROTOCOL_v3.0, RULE-0) |
| **최신 ADR** | ADR-208 |
| **태그/릴리즈** | 220 태그 · 30 릴리즈 (최신 v13.0.0) |
| **현재 단계** | Phase D 완료 → **Phase E 기획 중** (검증 우선 · LLM-0→2.5 점진 완화) |
| **최우선 작업** | SP-E.0 무결성 실행 · 데이터(Gold 대본집)+공식 검증 · critic/·orchestration/ 구현 |

---

## 세션 종료 명령

```
1. docs/sessions/YYYY-MM-DD_[home|company]_[작업요약].md 작성
2. 변경사항 커밋 → GitHub main push (DEV_PROTOCOL_v3.0 §5)
3. docs/sessions/INDEX.md 와 MASTER 문서 갱신
```

---

## 표준 개발 사이클 (DEV_PROTOCOL_v3.0 + RULE-0)

```
[RULE-0] V(N) 시작 전 → python3 tools/run_preflight.py → PASS 확인
[1] 구현 (신규파일 + tests/unit/test_vNNN_*.py 33TC 이상)
[2] pytest → generate_test_inventory.py → run_release_gate.py (97 PASS)
[3] commit → push → Release 태그 → ZIP 패키징
[RULE-0] V(N+1) 시작 전 → run_preflight.py 재실행 → PASS 확인
```

> ⚠️ Preflight 없이 개발 진입 시 기준선 불일치(존재하지 않는 클래스명 참조, 게이트 수 불일치 등)가 반복됩니다.
