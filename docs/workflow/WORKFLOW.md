# 개발 워크플로우 — 두 컴퓨터 환경 동기화

> **집 컴퓨터 (Cowork + Claude)** ↔ **회사 컴퓨터 (Claude Code / GPT + GitNexus)**  
> GitHub가 단일 진실 원천(Single Source of Truth)

---

## 핵심 원칙

1. **세션 시작 전 항상 pull** — 어느 컴퓨터에서든 최신 상태를 먼저 확인
2. **설계서·제안서·로드맵도 GitHub에** — Google Drive 대신 `docs/` 폴더에 커밋
3. **브랜치로 환경 구분** — 집/회사 작업이 서로 충돌하지 않음
4. **세션 종료 시 항상 push** — 다음 세션(어느 환경이든)이 최신 상태에서 시작

---

## 브랜치 전략

```
main ─────────────────────────────── (CI 통과, 릴리즈 기준선)
  └─ dev-home ──────────────────────  (집 컴퓨터 / Cowork + Claude)
  └─ dev-company ───────────────────  (회사 컴퓨터 / Claude Code + GitNexus)
  └─ feature/V574-xxx ──────────────  (특정 기능 개발 시 별도 브랜치)
```

---

## 세션 시작 프로토콜 (어느 환경이든 동일)

### Claude / GPT에게 첫 메시지로 전달할 내용:

```
아래 순서로 세션을 시작하라:

1. https://github.com/limsanghyuk/literary-os 최신 커밋과 태그를 확인하라
2. https://github.com/limsanghyuk/v1700-literary-os 최신 커밋을 확인하라
3. docs/sessions/ 폴더의 최근 세션 기록을 읽어 이전 작업 맥락을 파악하라
4. 현재 브랜치 상태(dev-home / dev-company)를 보고하라
5. 위 확인이 끝나면 개발 작업을 시작하라
```

---

## 세션 종료 프로토콜

세션 종료 전 Claude / GPT에게:

```
이번 세션 작업을 다음과 같이 마무리하라:

1. 이번 세션에서 진행한 내용을 docs/sessions/YYYY-MM-DD_[환경]_[주요내용].md 로 저장하라
2. 설계서·제안서가 있으면 docs/proposals/ 또는 docs/blueprints/에 커밋하라
3. 모든 변경사항을 커밋하고 GitHub에 push하라
4. 다음 세션에서 이어받아야 할 내용을 한 문단으로 요약하라
```

---

## 문서 폴더 구조

```
docs/
├── sessions/          ← 세션 기록 (날짜_환경_내용.md/.docx)
├── workflow/          ← 이 파일 (워크플로우 가이드)
├── proposals/         ← 제안서 (설계 결정 전)
├── blueprints/        ← 설계도 (구현 기준)
├── adr/               ← Architecture Decision Records
├── changelog/         ← 버전별 변경 이력
└── history/           ← 구버전 문서 아카이브
```

---

## 양쪽 환경의 AI 도구 차이

| 항목 | 집 (Cowork) | 회사 (Claude Code / GPT) |
|------|-------------|--------------------------|
| AI | Claude (Cowork) | Claude Code CLI / GPT-4o |
| GitNexus | bash CLI 방식 | MCP 서버 직접 연결 |
| 파일 접근 | C:\claude\ 마운트 | 로컬 파일시스템 직접 |
| CI/CD | GitHub Actions (자동) | GitHub Actions (자동) |
| 기준선 | GitHub main | GitHub main |

**공통점**: 둘 다 `git pull → 작업 → git push` 흐름으로 통일

---

## 현재 레포지토리 상태 (2026-05-19 기준)

| 레포 | 현재 버전 | 위치 |
|------|-----------|------|
| literary-os | V573 (7.8.1) | https://github.com/limsanghyuk/literary-os |
| v1700-literary-os | Stage130 (1.30.0) | https://github.com/limsanghyuk/v1700-literary-os |

