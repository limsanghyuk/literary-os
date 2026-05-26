# 통합 레포지토리 패키징 프로토콜 v1.0

> **제정**: 2026-05-26 (V633 ZIP 누락 사고 이후 제정)  
> **목적**: 개발 완료 시 ZIP 패키지 품질을 표준화하고, 매번 동일한 결과가 보장되도록 한다.  
> **적용 범위**: 모든 버전 ZIP 패키징 (개발자 인도, 릴리즈, 아카이빙)

---

## 1. 사고 경위 (Why This Protocol Exists)

V631~V633 개발 과정에서 ZIP 패키지를 생성할 때 `--exclude "*.git*"` glob 패턴을 사용했다.  
이 패턴은 `.git/` 뿐 아니라 `.gitignore`와 `.github/workflows/` 전체를 함께 제외했다.  
결과적으로 CI 워크플로우 6개 파일(`.github/workflows/*.yml`)과 `.gitignore`가 누락되었다.  
패키징 시 검증을 수행하지 않아 여러 버전에 걸쳐 동일한 오류가 반복되었다.

**교훈**: 패키징 명령어 오류는 코드 오류보다 발견이 어렵다. 반드시 자동 검증을 실행한다.

---

## 2. 표준 ZIP 명령어

### 2.1 올바른 명령어 (필수)

```bash
# 레포지토리 루트에서 실행
cd /path/to/repo

zip -r /tmp/literary-os-vXXX.zip . \
  --exclude ".git/*" \        # .git/ 내부만 제외 (← MUST: *.git* 사용 금지)
  --exclude "*/__pycache__/*" \
  --exclude "*.pyc" \
  -q

# C:\claude 로 복사
cp /tmp/literary-os-vXXX.zip /sessions/amazing-kind-pasteur/mnt/claude/literary-os-vXXX.zip
```

### 2.2 절대 사용 금지 패턴

```bash
# ❌ 금지: .gitignore, .github/ 까지 제외됨
--exclude "*.git*"

# ❌ 금지: .gitignore 포함 불가
--exclude ".git*"
```

---

## 3. 패키징 후 의무 검증 체크리스트

ZIP 생성 직후 아래 검증을 반드시 실행한다. **모든 항목이 PASS여야 인도 가능하다.**

```bash
ZIP=/tmp/literary-os-vXXX.zip   # 검증 대상 경로

echo "=== PACKAGING VALIDATION ==="

# [1] 파일 수 확인 (2,500 이상)
FILE_COUNT=$(unzip -l $ZIP | tail -1 | awk '{print $2}')
echo "[1] 총 파일 수: $FILE_COUNT"
[ "$FILE_COUNT" -ge 2500 ] && echo "    ✅ PASS" || echo "    ❌ FAIL — 파일 수 부족"

# [2] .gitignore 포함 확인
GI_COUNT=$(unzip -l $ZIP | grep -c '^\s*[0-9].*\.gitignore$')
echo "[2] .gitignore (루트): $GI_COUNT"
[ "$GI_COUNT" -ge 1 ] && echo "    ✅ PASS" || echo "    ❌ FAIL — .gitignore 누락"

# [3] .github/workflows/ 포함 확인 (최소 4개)
GH_COUNT=$(unzip -l $ZIP | grep -c '\.github/workflows/')
echo "[3] .github/workflows/ 파일 수: $GH_COUNT"
[ "$GH_COUNT" -ge 4 ] && echo "    ✅ PASS" || echo "    ❌ FAIL — .github/workflows/ 누락"

# [4] .git/ 내부 파일 미포함 확인
GIT_INTERNAL=$(unzip -l $ZIP | grep -c ' \.git/')
echo "[4] .git/ 내부 파일 수: $GIT_INTERNAL (0이어야 함)"
[ "$GIT_INTERNAL" -eq 0 ] && echo "    ✅ PASS" || echo "    ❌ FAIL — .git/ 포함됨"

# [5] __pycache__ 미포함 확인
PYC_COUNT=$(unzip -l $ZIP | grep -c '__pycache__')
echo "[5] __pycache__ 파일 수: $PYC_COUNT (0이어야 함)"
[ "$PYC_COUNT" -eq 0 ] && echo "    ✅ PASS" || echo "    ❌ FAIL — __pycache__ 포함됨"

# [6] pyproject.toml 포함 확인
PY_COUNT=$(unzip -l $ZIP | grep -c 'pyproject.toml')
echo "[6] pyproject.toml: $PY_COUNT"
[ "$PY_COUNT" -ge 1 ] && echo "    ✅ PASS" || echo "    ❌ FAIL — pyproject.toml 누락"

# [7] tests/ 포함 확인
TEST_COUNT=$(unzip -l $ZIP | grep -c 'tests/')
echo "[7] tests/ 파일 수: $TEST_COUNT"
[ "$TEST_COUNT" -ge 100 ] && echo "    ✅ PASS" || echo "    ❌ FAIL — tests/ 부족"

echo ""
echo "=== 검증 완료. 모든 항목 PASS 시에만 인도 가능 ==="
```

---

## 4. 개발 완료 → 인도 표준 절차 (Phase C 기준)

```
[1] 개발 완료
    ├── pytest 전체 실행 → 60/60 Gates PASS + 신규 TC 33개 이상 PASS 확인
    ├── tools/generate_test_inventory.py 실행 → test_inventory.json 갱신
    └── run_release_gate.py 실행 → EA-1~EA-8 전 항목 PASS

[2] GitHub 배포
    ├── git add -A && git commit -m "VXXX: [설명]"
    ├── git push origin main
    └── gh release create vXX.X.X --title "vXX.X.X" --notes "[릴리즈 노트]"

[3] ZIP 패키징 (표준 명령어 사용 — 섹션 2.1)
    └── cd /tmp/repo_vXXX && zip -r ... --exclude ".git/*" ...

[4] ZIP 검증 (섹션 3의 7개 항목 전부 PASS 필수)

[5] C:\claude 복사 및 링크 제공
    └── cp /tmp/literary-os-vXXX.zip /sessions/.../mnt/claude/

[6] 메모리 업데이트
    ├── memory/project_vXXX_state.md 작성
    └── memory/MEMORY.md 인덱스 갱신
```

---

## 5. 개발 방식 및 형식 표준 프로토콜

### 5.1 버전 명명

| 항목 | 규칙 |
|------|------|
| 버전 번호 | `vMAJOR.MINOR.PATCH` (pyproject.toml 기준) |
| V번호 | 개발 이터레이션 번호 (V631, V632, ...) |
| 릴리즈 태그 | GitHub tag = pyproject.toml version |
| CHANGELOG 파일명 | `docs/changelog/CHANGELOG_VXXX.md` |
| MANIFEST 파일명 | `manifests/MANIFEST_VXXX.md` |

### 5.2 ADR 작성 표준

```markdown
# ADR-XXX: [제목]

## 상태
ACCEPTED

## 맥락
[왜 이 결정이 필요한가]

## 결정
[무엇을 결정했는가]

## 근거
[왜 이 결정이 최선인가]

## 결과
[긍정적/부정적 결과]

## 대안 검토
[검토한 다른 방안과 기각 이유]
```

### 5.3 테스트 파일 명명 규칙

- 파일명: `tests/unit/test_vXXX_[기능명].py`
- TC 명명: `TC-01` ~ `TC-33` (최소 33개, 기능당)
- 마커: `@pytest.mark.unit`
- LLM-0 원칙: 테스트 내 외부 LLM 호출 절대 금지

### 5.4 신규 파일 추가 시 필수 작업

1. 해당 패키지 `__init__.py`에 공개 심볼 추가
2. `tools/generate_test_inventory.py` 재실행 → `test_inventory.json` 갱신
3. `docs/adr/INDEX.md` 업데이트 (ADR 추가 시)

### 5.5 Phase C 절대 원칙 (불변)

| 원칙 | 내용 |
|------|------|
| **LLM-0** | `corpus/`, `constitution/`, `finetune/` 모듈에서 외부 LLM 호출 절대 금지 |
| **LLM-1** | PROMOTED 단계 모델만 서빙 (AutoPromotionGate G62 통과 필수) |
| **DEV_MODE** | 항상 `false` 기본값 유지 (ADR-034) |
| **경쟁 흡수** | 독립 재구현 원칙 — 경쟁사 코드/데이터 불사용 |
| **GPU SLO** | 재학습 최소 간격 7일, 월 최대 $200 |

---

## 6. 버전 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|-----------|
| v1.0 | 2026-05-26 | 최초 제정 (V633 ZIP 누락 사고 계기) |

