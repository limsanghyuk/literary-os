# ADR-048 — Doc Consistency CI

**상태**: 승인  
**날짜**: 2026-05-20  
**버전**: V587 SP-α  
**작성자**: Claude (Literary OS 개발 모드)

---

## 문제 배경

V586 완료 시점에서 외부 관찰자가 GitHub 리포지토리를 보면 다음과 같은 불일치가 존재했다:

| 파일 | 표기 | 실제 |
|------|------|------|
| `.github/workflows/ci.yml` | "39 Gates" | 44 Gates |
| `CHANGELOG.md` | v7.7.1 (V571) | v9.1.0 (V586) |
| `tools/check_version_consistency.py` | 3파일 검사 | 실제 필요: 6파일 |
| GitHub Releases | 0건 | V572~V586 15버전 존재 |

이는 "내부 완성을 외부에서 신뢰할 수 없는 상태"로, V587의 핵심 문제로 진단되었다.

---

## 결정

**Single Source of Truth(SSoT)**: `pyproject.toml [project].version`

6개 파일이 이 SSoT와 항상 일치해야 한다:

| 검사 대상 | 검사 항목 |
|-----------|-----------|
| `README.md` | version 뱃지 + gate 뱃지 |
| `CHANGELOG.md` | 최상단 `## [X.Y.Z]` |
| `MANIFEST.md` | `버전: X.Y.Z` |
| `.github/workflows/ci.yml` | `Release Gate (N Gates)` |
| git tag | `vX.Y.Z-VNNN` (main 브랜치에서만) |
| live gate count | `run_release_gate()["total_gates"]` |

---

## 구현

### 1. `tools/check_version_consistency.py` 확장 (6파일)

```python
CHECKS = [
    README version badge   ← pyproject_ver
    README gate badge      ← live_gate_count
    CHANGELOG latest       ← pyproject_ver
    MANIFEST version       ← pyproject_ver
    ci.yml gate count      ← live_gate_count
    git tag                ← pyproject_ver (main only)
]
```

`--strict` 플래그: 불일치 시 exit(1) → CI에서 사용.
`--no-live-gate` 플래그: live gate 측정 생략 (pre-commit 빠른 모드).

### 2. `.pre-commit-config.yaml` 신규

커밋 전 자동으로 `check_version_consistency.py --strict --no-live-gate` 실행.

### 3. `.github/workflows/release.yml` 신규

`v*.*.*-V*` 태그 push 시 자동으로 GitHub Release를 생성.
`tools/extract_changelog_section.py`로 CHANGELOG에서 해당 버전 섹션을 추출해 Release body로 사용.

### 4. `tools/create_release.sh` 갱신

V571 하드코딩 제거. 인자 또는 최신 git tag를 자동 감지해 Release 생성.

---

## 결과

- `check_version_consistency.py` 실행 시 모든 파일 일치 → `✅ ALL CONSISTENT`
- 신규 태그 push → GitHub Release 자동 생성
- pre-commit hook → 커밋 전 정합성 강제

---

## 영향 범위

- 추가 의존성 없음 (표준 라이브러리만 사용)
- 기존 Gate 수 변경 없음 (ADR-048은 도구 레이어)
- 후방 호환: `--strict` 없이 실행하면 경고만 출력 (exit 0)
