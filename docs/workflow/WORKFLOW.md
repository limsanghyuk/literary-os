# 개발 워크플로우 — 집/회사 로컬 환경 동기화

> **집 컴퓨터 (Cowork + Claude)** ↔ **회사 컴퓨터 (Claude Code / GPT)**  
> GitHub가 단일 진실 원천(Single Source of Truth)  
> **최신 버전: V655 / v11.28.0 / 2026-05-27**

---

## ⚠️ 환경 설정 — 로컬 클론 후 1회만 실행

```bash
# 저장소 클론
git clone https://github.com/limsanghyuk/literary-os.git
cd literary-os

# 의존성 설치
pip install -e ".[dev]"

# Git Hook 설치 (커밋 전 프로토콜 자동 검사)
bash tools/install_hooks.sh

# 설치 확인
python3 tools/session_start.py
```

> `tools/install_hooks.sh`는 `.git/hooks/pre-commit`을 설치하여  
> **커밋 시 LLM-0 위반 / Gate FAIL / DEV_MODE=True를 자동 차단**합니다.

---

## 핵심 원칙

1. **세션 시작 전 항상 pull** — 어느 환경이든 최신 상태 먼저 확인
2. **`python3 tools/session_start.py` 필수 실행** — Preflight Step 1+12 자동화
3. **설계서·제안서·로드맵도 GitHub에** — `docs/` 폴더에 커밋
4. **세션 종료 시 항상 push** — 다음 세션이 최신 상태에서 시작

---

## 세션 시작 프로토콜 (어느 환경이든 동일)

```bash
# 1. 최신 상태 pull
git pull origin main

# 2. 세션 시작 스크립트 실행 (Preflight Step 1+7+12 자동)
python3 tools/session_start.py

# 3. 최근 세션 기록 확인 (docs/sessions/ 최신 파일)
# 4. 개발 착수
```

**Claude / GPT에게 첫 메시지로 전달할 내용:**

```
아래 순서로 세션을 시작하라:

1. https://github.com/limsanghyuk/literary-os 최신 커밋과 태그를 확인하라
2. https://github.com/limsanghyuk/v1700-literary-os 최신 커밋을 확인하라
3. docs/sessions/ 폴더의 최근 세션 기록을 읽어 이전 작업 맥락을 파악하라
4. python3 tools/session_start.py 결과를 확인하라 (Gate PASS 필수)
5. 위 확인이 끝나면 CLAUDE.md를 읽고 개발 작업을 시작하라
```

---

## 세션 종료 프로토콜

```bash
# 1. 세션 기록 저장
# docs/sessions/YYYY-MM-DD_[환경]_[주요내용].md

# 2. 설계/제안서 저장
# docs/proposals/ 또는 docs/blueprints/

# 3. 커밋 + push (pre-commit hook이 자동 검사)
git add -A
git commit -m "VXXX: [핵심 변경 1줄 설명]"
git push origin main

# 4. 다음 세션 인수인계 요약 작성
```

---

## pre-commit Hook 검사 항목

커밋 시 자동으로 아래 4가지를 검사하고 위반 시 커밋을 차단합니다:

| 검사 | 내용 | 위반 시 |
|------|------|---------|
| [1] test_inventory | Python 변경 시 inventory 갱신 여부 | 커밋 차단 |
| [2] LLM-0 | corpus/constitution/finetune 내 LLM API 호출 | 커밋 차단 |
| [3] DEV_MODE | DEV_MODE=True 코드 존재 여부 | 커밋 차단 |
| [4] Gate | Python 5개↑ 변경 시 run_release_gate PASS | 커밋 차단 |

---

## 브랜치 전략

```
main ──────────────────── (CI 통과, 릴리즈 기준선)
  └─ dev-home ───────────  (집 / Cowork + Claude)
  └─ dev-company ────────  (회사 / Claude Code)
  └─ feature/VXXX-xxx ──  (특정 기능 개발)
```

---

## 양쪽 환경의 AI 도구 차이

| 항목 | 집 (Cowork) | 회사 (Claude Code) |
|------|-------------|---------------------|
| AI | Claude (Cowork) | Claude Code CLI |
| 세션 시작 | python3 tools/session_start.py | python3 tools/session_start.py |
| 파일 접근 | C:\claude\ 마운트 | 로컬 파일시스템 |
| CI/CD | GitHub Actions | GitHub Actions |
| 기준선 | GitHub main | GitHub main |

**공통점**: `git pull → session_start.py → 작업 → git push` 흐름 통일

---

## 현재 레포지토리 상태 (2026-05-27)

| 레포 | 현재 버전 | URL |
|------|-----------|-----|
| literary-os | **V655 (v11.28.0)** | https://github.com/limsanghyuk/literary-os |
| v1700-literary-os | Stage 144 | https://github.com/limsanghyuk/v1700-literary-os |

---

## 문서 폴더 구조

```
docs/
├── sessions/          ← 세션 기록 (날짜_환경_내용.md)
├── workflow/          ← 이 파일 + DEV_PROTOCOL + PREFLIGHT + BRANCH + PACKAGING
├── proposals/         ← 제안서 + 설계 문서
├── adr/               ← Architecture Decision Records (ADR-001~115)
├── phase/             ← Phase 설계도 + 본안
└── history/           ← 구버전 문서 아카이브
```
