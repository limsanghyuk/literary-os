# 세션 시작 가이드

> 집이든 회사든 **매 세션 첫 번째로** 이 내용을 Claude/GPT에게 전달하세요.

---

## 복사해서 사용하는 세션 시작 명령

```
세션을 다음 순서로 시작하라:

1. https://github.com/limsanghyuk/literary-os 최신 커밋·태그를 확인하라
2. https://github.com/limsanghyuk/v1700-literary-os 최신 커밋을 확인하라
3. literary-os/docs/sessions/ 폴더의 최근 세션 기록을 읽어라
4. 현재 개발 가능한 다음 버전을 보고하고 작업을 시작하라
```

---

## 세션 종료 명령

```
세션을 다음과 같이 마무리하라:

1. docs/sessions/YYYY-MM-DD_[home|company]_[작업요약].md 를 작성하라
2. 모든 변경사항을 커밋하고 GitHub main에 push하라
3. 다음 세션 시작 시 알아야 할 내용을 3줄로 요약하라
```

---

## 현재 버전
- literary-os: **V580** (8.5.0) — CI GREEN, Gate 38/38, 5529+ PASS
- v1700-literary-os: **Stage130** — Gate 20/20 PASS
- 상세 워크플로우: `docs/workflow/WORKFLOW.md`

## V581+ 진화 로드맵 v2.0 (2026-05-19 확정)
- 핵심 문서: `docs/sessions/literary_os_v581_proposal_v2.docx` (제안서)
- 핵심 문서: `docs/sessions/literary_os_v581_blueprint_v2.docx` (설계도)
- 핸드오프: `docs/sessions/2026-05-19_home_proposals_v2_handoff.md`
- 5-Phase: A(LOSDB+CLI V581~595) → B(LoRA+B2B V596~610) → C(RLHF V611~630) → D(SDK V631~660) → E(에코시스템 V661+)
- 다음 개발: V581 SchemaRegistry + Multi-backend MigrationManager (ADR-040)
- 시작 전: `git pull origin main` → Preflight Guide 15단계
