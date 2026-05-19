# literary-os 브랜치 전략 및 릴리즈 워크플로

> 기준 버전: V580 (8.5.0) | 최종 수정: 2026-05-19

---

## 핵심 원칙

```
GitHub main   = 최신 안정 기준선 (항상 GREEN)
CI            = 검증의 유일한 기준
Release tag   = 공식 버전 기준
ZIP + SHA256  = 보관/배포용 산출물
```

---

## 브랜치 구조

| 브랜치 | 용도 | 생명주기 |
|--------|------|---------|
| `main` | 최신 안정 기준선 | 영구 |
| `develop` | 다음 릴리즈 통합 (선택) | 영구 |
| `581-async-fix` | 기능/스테이지 개발 | PR merge 후 삭제 |
| `582-perf-gate` | 기능/스테이지 개발 | PR merge 후 삭제 |

### 브랜치 명명 규칙

```
/<버전번호>-<주제>
예: /581-coverage-95
    /582-studio-skip-zero
    /hotfix-devmode-regression
```

---

## 개발 → 릴리즈 플로

```
1. main에서 브랜치 생성
   git checkout -b 581-coverage-95

2. 개발 + 로컬 테스트
   pytest tests/ -q
   python -c "from literary_system.gates.release_gate import run_release_gate; ..."

3. push → CI 자동 실행
   git push origin 581-coverage-95
   (GitHub Actions: lint → version-check → preflight → test → Gates)

4. CI GREEN 확인 후 PR 생성 → main merge

5. main에서 tag 생성
   git tag v8.6.0-V581
   git push origin v8.6.0-V581

6. Release 워크플로 자동 실행
   → literary-os-8.6.0-V581.zip 생성
   → literary-os-8.6.0-V581.zip.sha256 생성
   → GitHub Release 페이지에 게시
```

---

## CI 체크 항목 (4단계)

| 단계 | 체크 | 실패시 |
|------|------|--------|
| lint | Ruff E/F/W/I | PR merge 차단 |
| version-check | pyproject.toml ↔ git tag 일치 | PR merge 차단 |
| preflight | Step 13/14/15 통과 | PR merge 차단 |
| test | pytest + 38 Gates PASS | PR merge 차단 |
| security-quick | DEV_MODE=false 회귀 방지 (PR 전용) | PR merge 차단 |

---

## 릴리즈 산출물 3종

개발자에게 제공하는 공식 산출물:

1. **GitHub commit / branch / PR** — 변경 이력의 원본
2. **개발자 handoff 문서** — `CHANGELOG_V<번호>.md` + ADR
3. **GitHub Release ZIP + SHA256** — 보관 및 배포용

### SHA256 검증 방법
```bash
sha256sum -c literary-os-8.5.0-V580.zip.sha256
```

---

## 태그 명명 규칙

```
v<major>.<minor>.<patch>-V<버전번호>
예: v8.5.0-V580
    v8.6.0-V581
```

- `major.minor.patch` — pyproject.toml `version` 값과 동일
- `V<번호>` — literary-os 내부 버전 번호

---

## 긴급 핫픽스

```
1. main에서 hotfix 브랜치 생성
   git checkout -b hotfix-devmode-regression

2. 최소 수정 + 테스트 통과

3. main에 직접 merge (PR 권장)

4. 패치 버전 bump + tag
   git tag v8.5.1-V580-hf
```
