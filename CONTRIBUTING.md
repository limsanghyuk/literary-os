# Contributing & 버전 계보 관리

## 브랜치 전략

```
main                ← 릴리즈 전용 (보호 브랜치)
feat/V572-<name>    ← 기능 개발
fix/V572-<bug>      ← 버그픽스
release/v7.8.0      ← 릴리즈 준비
```

## 버전-태그 매핑

| Git 태그 | Literary OS 버전 |
|----------|-----------------|
| v7.7.1-V571 | V571 — 현재 |
| v7.8.0-V58x | V572~V58x |
| v8.0.0-V6xx | Phase 7 |

## 커밋 메시지 컨벤션

```
feat(V572): <기능 설명>
fix(V572): <버그 설명>
test(V572): <테스트 설명>
gate(G32): <게이트 설명>
adr(032): ADR-032 — <정책 제목>
```

## 릴리즈 절차

1. `feat/V5xx` 브랜치 개발 + `pytest tests/ -q` PASS
2. `pyproject.toml` · `MANIFEST_Vxxx.md` · `CLAUDE.md` 버전 갱신
3. PR → main 머지
4. `git tag -a vX.Y.Z-Vxxx -m "..."` → `git push origin --tags`
5. GitHub Actions Release 워크플로우 자동 실행
