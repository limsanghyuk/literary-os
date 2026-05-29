# 세션 기록 — 2026-05-19 (집 컴퓨터 / Cowork + Claude)

## 환경
- 컴퓨터: 집
- AI: Claude (Cowork 모드)
- 시작 기준선: V571 ZIP 업로드 → GitHub 신규 Push

## 이번 세션에서 완료한 작업

### 1. literary-os 레포 구축 및 정리
- V571 ZIP → GitHub literary-os 레포 최초 Push
- 레포 클린업: `.gitignore` 신설, `.claude/` / `__pycache__` 추적 해제
- `README.md` V571 기준 완전 재작성 (기존 V430 내용)
- `MANIFEST.md` V571 기준 교체 (기존 V328 내용)
- `CHANGELOG.md` 신설 (루트), 구버전 CHANGELOG 16개 → `docs/changelog/`
- 구버전 MANIFEST 13개 → `docs/history/`

### 2. v1700-literary-os 레포 구축
- V1700 Stage128 ZIP → GitHub v1700-literary-os 최초 Push
- `README.md` Stage128 기준 완전 재작성 (기존 Stage112 내용)
- `pyproject.toml` v1.28.0·Stage128 설명 갱신

### 3. 두 컴퓨터 환경 동기화 구조 수립
- `docs/workflow/WORKFLOW.md` 신설 — 세션 시작/종료 프로토콜 포함
- `docs/sessions/` 폴더 신설 — 세션 기록 보관 시작
- 회사 컴퓨터 작업 기록 docx → `docs/sessions/2026-05-19_company_github_strategy.docx`

## 현재 GitHub 상태
- literary-os: V573 (회사에서 V572·V573 + CI/CD 구축 완료)
- v1700-literary-os: Stage130 (회사에서 Stage129·130 머지 완료)

## 다음 세션에서 이어받을 내용
- literary-os: V574 개발 시작 가능 (V573 Preflight 통과 상태)
- v1700-literary-os: Stage131 GIG / Gate26 Advisory Absorption 개발
- 세션 시작 시 반드시 `docs/sessions/` 최근 파일 확인 후 맥락 파악

## 확인된 구조적 사실
- 집 컴퓨터(Cowork)와 회사 컴퓨터(Claude Code+GPT+GitNexus)가 
  각자 독립적으로 같은 GitHub 레포에 Push하고 있음
- Stage129·130은 회사 컴퓨터에서 이번 세션 중에 Push된 것으로 확인됨
- Google Drive → GitHub docs/ 전환으로 동기화 문제 해결 가능
