# Literary OS 개발 통합 프로토콜 v2.0

**버전**: 2.1  
**최초 제정**: 2026-05-26 (v2.0)  
**개정**: 2026-05-27 (v2.1 — 버전 경계 자동 Preflight 강제 규칙 추가)  
**적용 대상**: Phase C V638 이후 **모든** 개발 이터레이션 (절대 필수)

---

## 🚨 [RULE-0] 버전 경계 자동 Preflight 강제 집행 (절대 불변)

> **개발자가 별도로 지시하지 않아도, Claude(AI 개발 에이전트)가 자동으로 집행한다.**
> CLAUDE.md에 동일 규칙이 선언되어 있으며, 두 문서가 서로를 강제한다.

### 규칙 본문

```
V(N) 개발 시작 전:
  필수 → python3 tools/run_preflight.py
  조건 → PREFLIGHT PASS 확인 후에만 구현 착수
  위반 → 구현 코드 작성 즉시 중단, Preflight 실행 후 재시작

V(N) 개발 완료 후, V(N+1) 시작 전:
  필수 → python3 tools/run_preflight.py 재실행 (변경사항 반영)
  조건 → PREFLIGHT PASS + Release Gate PASS 동시 확인
  위반 → V(N+1) 구현 착수 금지
```

### 적용 사례 (예시)

| 상황 | Claude 자동 행동 |
|------|-----------------|
| "V667 진행해" | Preflight 13단계 먼저 실행 → PASS 후 V667 구현 |
| V667 구현 완료 후 | Preflight 재실행 → PASS 후 V668 착수 |
| "668 해줘" / "계속 개발" | 직전 Preflight PASS 여부 확인 → 미확인 시 재실행 |
| "SP-C.4 진행해" | V667 Preflight 먼저 실행 후 착수 |

### 이 규칙이 존재하는 이유

V631~V636: DEV_PROTOCOL_v2.0이 있었으나 Preflight를 건너뜀.  
원인: 문서가 "참조하라"만 명시하고 자동 집행 메커니즘이 없었음.  
결과: SP-C.1 전체에서 연결성 검사 누락 → V666에서 고립 패키지 10개 발견.  
해결: RULE-0을 CLAUDE.md + 이 문서 양쪽에 박아 상호 강제.

---

## ⚠️ 최우선 원칙

> **개발·설계·수정 착수 전 반드시 Preflight 13단계를 실행한다.**  
> 이 원칙을 건너뛴 커밋은 릴리즈 승인 대상이 아니다.

---

## 전체 개발 흐름 (MUST FOLLOW)

```
┌────────────────────────────────────────────────────────────┐
│  [RULE-0] V(N) 시작 전                                     │  ← 자동 집행
│      python3 tools/run_preflight.py → PASS 확인            │
├────────────────────────────────────────────────────────────┤
│  [0] 세션 시작 — GitHub clone & 최신 상태 확인             │
├────────────────────────────────────────────────────────────┤
│  [1] PREFLIGHT 13단계 실행 (§1 참조)                       │  ← 절대 필수
│      python3 tools/run_preflight.py                        │
├────────────────────────────────────────────────────────────┤
│  [2] 구현 (§2 개발 표준 준수)                              │
│      신규 파일 → 테스트(33 TC) → __init__ 공개             │
├────────────────────────────────────────────────────────────┤
│  [3] 검증 (§3)                                             │
│      pytest → generate_test_inventory → run_release_gate   │
├────────────────────────────────────────────────────────────┤
│  [4] GitHub 배포 (§4)                                      │
│      commit → push → Release 태그                          │
├────────────────────────────────────────────────────────────┤
│  [5] ZIP 패키징 + 7/7 검증 + 이전 버전 비교 (§5)          │
├────────────────────────────────────────────────────────────┤
│  [6] 메모리 업데이트 (§6)                                  │
├────────────────────────────────────────────────────────────┤
│  [RULE-0] V(N+1) 시작 전                                   │  ← 자동 집행
│      python3 tools/run_preflight.py 재실행 → PASS 확인     │
│      → 그 이후에만 V(N+1) 구현 시작                        │
└────────────────────────────────────────────────────────────┘
```

---

## §1. PREFLIGHT 13단계 (개발 착수 전 필수 실행)

> **실행 명령 (1개로 13단계 전부 자동 실행)**
> ```bash
> python3 tools/run_preflight.py
> ```
> 소요 시간: 약 30~60초. 개발자 개입 불필요.

| Step | 확인 항목 | 실패 시 조치 |
|---|---|---|
| 1 | 모듈/심볼 수 이전 버전 대비 ± 확인 | 급격한 감소 시 파일 삭제 여부 점검 |
| 2 | 변경 예정 심볼의 현재 importer 목록 | 영향 범위 사전 파악 |
| 3 | depth-1/2/3 영향 계산 | High 위험 시 Step 1~13 전부 재실행 |
| 4 | LLM-0 위반 패턴 검사 | `corpus/`, `constitution/`, `finetune/` 내 외부 LLM 호출 |
| 5 | DEV_MODE=True 패턴 검사 | 발견 시 즉시 제거 |
| 6 | G32 위반 검사 (print() 무분별 사용) | 제거 후 재실행 |
| 7 | 생존 매트릭스 — 22개 핵심 심볼 전원 존재 | 누락 시 개발 중단 후 원인 파악 |
| 8 | Gate 연결 계보 (G62 → release_gate) | 단절 시 연결 복원 |
| 9 | `constitution/__init__.py` 공개 API 스키마 | 누락 심볼 추가 |
| 10 | 위험도 분류 (🔴/🟡/🟢) | 🔴 High 시 Step 1~13 전부 |
| 11 | `python3 tools/run_release_gate.py` | FAIL 시 개발 중단 |
| 12 | 순환 의존 탐지 | 신규 순환 시 아키텍처 검토 |
| **13** | **G_CONNECTIVITY — 고립 패키지 검사 (ADR-128)** | **고립 발견 시 즉시 연결 복원** |

### 위험도 분류 기준

| 위험도 | 해당 변경 | 필수 Step |
|---|---|---|
| 🔴 High | `release_gate.py` 수정, Gate 추가/삭제, `__init__.py` 대규모 변경 | Step 1~13 전부 |
| 🟡 Medium | 기존 모듈에 메서드 추가, 소규모 export 추가 | Step 7~13 |
| 🟢 Low | 독립 신규 모듈 추가, 테스트 파일, 문서 | Step 10, 11, 13 |

---

## §2. 구현 표준

### 2.1 버전 명명

| 항목 | 규칙 |
|---|---|
| 버전 번호 | `vMAJOR.MINOR.PATCH` (pyproject.toml 단일 소스) |
| V번호 | 개발 이터레이션 번호 (V667, V668, ...) |
| CHANGELOG | `docs/changelog/CHANGELOG_VXXX.md` |
| MANIFEST | `manifests/MANIFEST_VXXX.md` |

### 2.2 ADR 작성 표준

```markdown
# ADR-XXX: [제목]

**날짜**: YYYY-MM-DD
**상태**: Accepted
**구현**: VXXX (vXX.X.X)

## 컨텍스트
## 결정
## 결과
```

### 2.3 테스트 파일 표준

- 파일명: `tests/unit/test_vXXX_[기능명].py`
- TC 수: **최소 33개** (TC-01~TC-33)
- LLM-0: 테스트 내 외부 LLM 호출 절대 금지

### 2.4 신규 패키지 추가 시 필수 (ADR-128)

```
[ ] 해당 패키지 __init__.py에 공개 심볼 추가 (__all__ 포함)
[ ] 연결 계획 선언: 어떤 상위 패키지가 이 패키지를 import하는지 PR에 명시
[ ] Preflight Step 13 G_CONNECTIVITY PASS 확인
[ ] 클래스명 중복 없음 확인 (duplicate_zero G37)
[ ] LLM-0 원칙 준수 확인
```

### 2.5 Phase C 절대 원칙 (불변)

| 원칙 | 내용 |
|---|---|
| **LLM-0** | `corpus/`, `constitution/`, `finetune/` 에서 외부 LLM 호출 절대 금지 |
| **LLM-1** | PROMOTED 단계 모델만 서빙 (AutoPromotionGate G62 통과 필수) |
| **DEV_MODE** | 항상 `false` 기본값 유지 (ADR-034) |
| **GPU SLO** | 재학습 최소 간격 7일, 월 최대 $200 (ADR-051) |
| **G_CONNECTIVITY** | 고립 패키지 2버전 연속 금지 (ADR-128) |

---

## §3. 검증 체크리스트 (커밋 전 필수)

```bash
# [1] 전체 테스트
python3 -m pytest tests/unit/ -q --tb=short 2>&1 | tail -5

# [2] test_inventory 갱신
python3 tools/generate_test_inventory.py

# [3] Release Gate PASS 확인 (G_PREFLIGHT + G_CONNECTIVITY + 66 Gates)
python3 tools/run_release_gate.py
```

**Gate FAIL 시 절대 커밋하지 않는다.**

---

## §4. GitHub 배포 절차

```bash
git add -A
git commit -m "V{N}: [핵심 변경 1줄] (ADR-XXX, v{SEMVER})"
git push origin main
git tag v{SEMVER}
git push origin v{SEMVER}
# GitHub Release API로 릴리즈 생성
```

---

## §5. ZIP 패키징 + 이전 버전 비교 검증

```bash
zip -r /tmp/literary-os-vXXX.zip . \
    --exclude ".git/*" --exclude "*/__pycache__/*" --exclude "*.pyc" -q

# 7/7 검증 항목
# [1] 총 파일 수 ≥ 1200
# [2] .gitignore 포함
# [3] .github/workflows/ ≥ 4개
# [4] .git/ 없음
# [5] __pycache__ 없음
# [6] pyproject.toml 포함
# [7] tests/ 파일 ≥ 100개

# 이전 버전 대비 파일 수 감소 100개 이상 시 경고
cp /tmp/literary-os-vXXX.zip /sessions/.../mnt/claude/literary-os-vXXX.zip
```

---

## §6. 메모리 업데이트

```
[ ] memory/project_vXXX_state.md 작성
[ ] memory/MEMORY.md 인덱스 항목 추가
```

---

## §7. 최종 인도 전 체크리스트

```
개발 전
[✓] RULE-0: Preflight 13단계 실행 완료
[✓] Step 13 G_CONNECTIVITY PASS

구현 중
[✓] LLM-0 원칙 준수
[✓] ADR-128: 신규 패키지 연결 계획 선언
[✓] 클래스명 중복 없음

배포 전
[✓] pytest PASS
[✓] generate_test_inventory.py 실행
[✓] run_release_gate.py PASS (G_PREFLIGHT + G_CONNECTIVITY + 66 Gates)

패키징
[✓] 7/7 검증 항목 PASS
[✓] 이전 버전 대비 파일 수 비교 정상
[✓] C:\claude 복사 완료

RULE-0 (V(N+1) 시작 전)
[✓] Preflight 재실행 → PASS 확인 후 다음 버전 착수
```

---

## §8. 버전 이력

| 버전 | 날짜 | 변경 내용 |
|---|---|---|
| v1.0 | 2026-05-26 | PACKAGING_PROTOCOL_v1.0 최초 제정 |
| v2.0 | 2026-05-26 | 전면 개정 — Preflight §1 필수화, 결함 4종 해소 |
| **v2.1** | **2026-05-27** | **RULE-0 추가 — 버전 경계 자동 Preflight 강제 집행 (CLAUDE.md 연동)** |
