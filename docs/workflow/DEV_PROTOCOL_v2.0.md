# Literary OS 개발 통합 프로토콜 v2.0

**버전**: 2.0  
**제정일**: 2026-05-26  
**적용 대상**: Phase C V638 이후 **모든** 개발 이터레이션 (절대 필수)  
**대체 문서**: PACKAGING_PROTOCOL_v1.0.md (패키징 절차는 §5로 이관)

---

## ⚠️ 최우선 원칙

> **개발·설계·수정 착수 전 반드시 Preflight Guide v1.1 12단계를 실행한다.**  
> 이 원칙을 건너뛴 커밋은 릴리즈 승인 대상이 아니다.

---

## 근본 원인 기록 (v1.0 → v2.0 개정 이유)

| 결함 | 내용 | 영향 |
|---|---|---|
| ① 개발 전 단계 누락 | 구 프로토콜 §4는 "완료 후"만 기술 | V631~V636 Preflight 미실행 |
| ② 문서 분리 | PREFLIGHT_GUIDE_v1.1.md 별도 존재 | 연결 끊김, 참조 누락 |
| ③ 강제 메커니즘 없음 | "참조하라"만 명시, 실행 명령 없음 | 자동 건너뜀 |
| ④ 세션 초기화 취약 | AI 세션 시작 시 재확인 없음 | 매 세션 재교육 필요 |
| ⑤ 패키지 비교 없음 | 이전 버전과 크기·파일 수 비교 미실시 | 회귀 누락 가능 |

V637 Preflight 첫 정식 적용 결과 **EvalResult 클래스명 충돌**(G37 FAIL)을 
사전 감지하여 커밋 전 해소. Preflight 없이 진행했다면 Gate FAIL로만 발견됐을 버그.

---

## 전체 개발 흐름 (MUST FOLLOW)

```
┌─────────────────────────────────────────────────────────┐
│  [0] 세션 시작 — 메모리 로드 & 레포 클론                │  ← 필수
├─────────────────────────────────────────────────────────┤
│  [1] PREFLIGHT 12단계 실행 (아래 §1 참조)              │  ← 절대 필수
│      python3 tools/gitnexus_analyze.py                  │
│      + Step 3/5/7/8/9/10/11/12 순서대로 실행           │
├─────────────────────────────────────────────────────────┤
│  [2] 구현 (§2 개발 표준 준수)                           │
│      신규 파일 → 테스트(33 TC) → __init__ 공개          │
├─────────────────────────────────────────────────────────┤
│  [3] 검증 (§3)                                          │
│      pytest → generate_test_inventory → run_release_gate│
├─────────────────────────────────────────────────────────┤
│  [4] GitHub 배포 (§4)                                   │
│      commit → push → Release 태그                       │
├─────────────────────────────────────────────────────────┤
│  [5] ZIP 패키징 + 7/7 검증 + 이전 버전 비교 (§5)       │  ← 신규
├─────────────────────────────────────────────────────────┤
│  [6] 메모리 업데이트 (§6)                               │
└─────────────────────────────────────────────────────────┘
```

---

## §1. PREFLIGHT 12단계 (개발 착수 전 필수 실행)

> 참조 원문: `docs/workflow/PREFLIGHT_GUIDE_v1.1.md`  
> **각 Step의 출력을 확인한 뒤 다음 Step으로 넘어간다.**

### 1.1 실행 명령 (매 버전 시작 시)

```bash
# Step 1: 코드그래프 현황 파악
cd /tmp/repo_vXXX
python3 - << 'EOF'
import ast, os
from pathlib import Path
from collections import defaultdict

ROOT = Path(".")
SKIP = {"__pycache__", ".git", ".pytest_cache"}
symbols = {}

class V(ast.NodeVisitor):
    def __init__(self, m): self.m = m; self._c = []
    def visit_ClassDef(self, n):
        symbols[f"{self.m}.{n.name}"] = "class"; self._c.append(n.name)
        self.generic_visit(n); self._c.pop()
    def visit_FunctionDef(self, n):
        t = "method" if self._c else ("test_fn" if n.name.startswith("test_") else "function")
        symbols[f"{self.m}.{self._c[-1] if self._c else ''}.{n.name}" if self._c else f"{self.m}.{n.name}"] = t
        self.generic_visit(n)
    visit_AsyncFunctionDef = visit_FunctionDef

for f in ROOT.rglob("*.py"):
    if any(s in f.parts for s in SKIP): continue
    try:
        mod = str(f.relative_to(ROOT)).replace(os.sep,".").replace("/",".")[:-3]
        V(mod).visit(ast.parse(f.read_text("utf-8")))
    except: pass

print(f"모듈: {len(set(k.rsplit('.',2)[0] for k in symbols)):,}")
print(f"심볼: {len(symbols):,}  (클래스:{sum(1 for v in symbols.values() if v=='class'):,})")
EOF
```

### 1.2 Step별 확인 항목

| Step | 확인 항목 | 실패 시 조치 |
|---|---|---|
| 1 | 모듈/심볼 수 이전 버전 대비 ± 확인 | 급격한 감소 시 파일 삭제 여부 점검 |
| 3 | 변경 예정 심볼의 현재 importer 목록 | 영향 범위 사전 파악 |
| 5 | depth-1/2/3 영향 계산 | High 위험 시 Step 1~12 전부 재실행 |
| 7 | LLM-0 위반 패턴 검사 | `grep -rn "openai\|anthropic\|requests.post" literary_system/constitution/ literary_system/finetune/ literary_system/corpus/` |
| 8 | 생존 매트릭스 — SP-C.1 핵심 클래스 전원 존재 | 누락 시 개발 중단 후 원인 파악 |
| 9 | Gate 연결 계보 (G62 → release_gate) | 단절 시 연결 복원 |
| 10 | `constitution/__init__.py` 공개 API 스키마 | 누락 심볼 추가 |
| 11 | 위험도 분류 (🔴/🟡/🟢) | 🔴 High 시 Step 1~12 전부 |
| 12 | `python3 tools/run_release_gate.py` | FAIL 시 개발 중단 |

### 1.3 위험도 분류 기준

| 위험도 | 해당 변경 | 필수 Step |
|---|---|---|
| 🔴 High | `release_gate.py` 수정, Gate 추가/삭제, `__init__.py` 대규모 변경 | Step 1~12 전부 |
| 🟡 Medium | 기존 모듈에 메서드 추가, `__init__.py` 소규모 export 추가 | Step 7~12 |
| 🟢 Low | 독립 신규 모듈 추가, 테스트 파일, 문서 | Step 10, 12 |

---

## §2. 구현 표준

### 2.1 버전 명명

| 항목 | 규칙 |
|---|---|
| 버전 번호 | `vMAJOR.MINOR.PATCH` (pyproject.toml 단일 소스) |
| V번호 | 개발 이터레이션 번호 (V638, V639, ...) |
| CHANGELOG | `docs/changelog/CHANGELOG_VXXX.md` |
| MANIFEST | `manifests/MANIFEST_VXXX.md` |

### 2.2 ADR 작성 표준

```markdown
# ADR-XXX: [제목]

**날짜**: YYYY-MM-DD
**상태**: Accepted
**구현**: VXXX (vXX.X.X)

## 컨텍스트
[왜 이 결정이 필요한가]

## 결정
[무엇을 결정했는가]

## 결과
[긍정적/부정적 결과]
```

### 2.3 테스트 파일 표준

- 파일명: `tests/unit/test_vXXX_[기능명].py`
- TC 수: **최소 33개** (TC-01~TC-33)
- 구성: 상수/초기화(5) + 핵심동작(10) + PASS/FAIL(5) + 영속화(3) + 엣지케이스(5) + 통합(5)
- LLM-0: 테스트 내 외부 LLM 호출 절대 금지

### 2.4 신규 파일 추가 시 필수 작업 체크리스트

```
[ ] 해당 패키지 __init__.py에 공개 심볼 추가 (__all__ 포함)
[ ] 클래스명 중복 없음 확인 (duplicate_zero G37)
[ ] LLM-0 원칙 준수 확인
[ ] tools/generate_test_inventory.py 실행
```

### 2.5 Phase C 절대 원칙 (불변)

| 원칙 | 내용 |
|---|---|
| **LLM-0** | `corpus/`, `constitution/`, `finetune/` 모듈에서 외부 LLM 호출 절대 금지 |
| **LLM-1** | PROMOTED 단계 모델만 서빙 (AutoPromotionGate G62 통과 필수) |
| **DEV_MODE** | 항상 `false` 기본값 유지 (ADR-034) |
| **GPU SLO** | 재학습 최소 간격 7일, 월 최대 $200 |

---

## §3. 검증 체크리스트 (커밋 전 필수)

```bash
# [1] 전체 테스트
cd /tmp/repo_vXXX
python3 -m pytest tests/unit/ -q --tb=short 2>&1 | tail -5

# [2] test_inventory 갱신
python3 tools/generate_test_inventory.py

# [3] Release Gate 61/61 확인
python3 tools/run_release_gate.py > /tmp/gate_result.json 2>/dev/null
python3 -c "import json; d=json.load(open('/tmp/gate_result.json')); print(d['summary'])"
```

**Gate FAIL 시 절대 커밋하지 않는다.**

---

## §4. GitHub 배포 절차

```bash
GH_TOKEN="[토큰]"
VNUM="638"       # V번호
SEMVER="11.8.0"  # pyproject.toml 버전

# [1] 커밋
git add [변경 파일 목록]
git commit -m "V${VNUM}: [핵심 변경 1줄 설명] (ADR-XXX)"

# [2] 푸시
git push https://${GH_TOKEN}@github.com/limsanghyuk/literary-os main

# [3] Release 태그 (GitHub API)
curl -s -X POST -H "Authorization: token ${GH_TOKEN}" \
  https://api.github.com/repos/limsanghyuk/literary-os/releases \
  -d "{\"tag_name\":\"v${SEMVER}\",\"name\":\"v${SEMVER} — V${VNUM} [제목]\",\"body\":\"[릴리즈 노트]\"}"
```

---

## §5. ZIP 패키징 + 이전 버전 비교 검증

### 5.1 표준 패키징 명령어 (절대 변경 금지)

```bash
cd /tmp/repo_vXXX
zip -r /tmp/literary-os-vXXX.zip . \
    --exclude ".git/*" \
    --exclude "*/__pycache__/*" \
    --exclude "*.pyc" \
    -q
```

### 5.2 7개 항목 검증 스크립트 (PACKAGING_PROTOCOL_v1.0 계승)

```bash
ZIP=/tmp/literary-os-vXXX.zip
check() {
  local desc="$1" count="$2" threshold="$3" op="$4"
  if [ "$op" = "ge" ]; then
    [ "$count" -ge "$threshold" ] && echo "✅ [$desc] $count" || echo "❌ [$desc] $count (≥$threshold 미달)"
  elif [ "$op" = "eq" ]; then
    [ "$count" -eq "$threshold" ] && echo "✅ [$desc] $count" || echo "❌ [$desc] $count (=$threshold 불일치)"
  fi
}

TOTAL=$(unzip -l $ZIP | tail -1 | awk '{print $2}')
check "[1] 총 파일 수" "$TOTAL"                                "1200" "ge"
check "[2] .gitignore"   "$(unzip -l $ZIP | grep -c '\.gitignore$' || true)" "1" "ge"
check "[3] .github/workflows" "$(unzip -l $ZIP | grep -c '\.github/workflows/.*\.yml$' || true)" "4" "ge"
check "[4] .git/ 없음"  "$(unzip -l $ZIP | grep -c '\.git/' || true)" "0" "eq"
check "[5] __pycache__ 없음" "$(unzip -l $ZIP | grep -c '__pycache__' || true)" "0" "eq"
check "[6] pyproject.toml" "$(unzip -l $ZIP | grep -c 'pyproject\.toml$' || true)" "1" "ge"
check "[7] tests/ 파일" "$(unzip -l $ZIP | grep -c 'tests/' || true)" "100" "ge"
```

### 5.3 이전 버전과의 비교 검증 (신규 필수 항목)

```bash
PREV_ZIP=/sessions/.../mnt/claude/literary-os-v[이전버전].zip
CURR_ZIP=/tmp/literary-os-vXXX.zip

PREV_COUNT=$(unzip -l $PREV_ZIP | tail -1 | awk '{print $2}')
CURR_COUNT=$(unzip -l $CURR_ZIP | tail -1 | awk '{print $2}')
DIFF=$((CURR_COUNT - PREV_COUNT))

PREV_SIZE=$(ls -lh $PREV_ZIP | awk '{print $5}')
CURR_SIZE=$(ls -lh $CURR_ZIP | awk '{print $5}')

echo "=== 이전 버전 대비 비교 ==="
echo "  이전: $PREV_COUNT 파일 / $PREV_SIZE"
echo "  현재: $CURR_COUNT 파일 / $CURR_SIZE"
echo "  증감: +$DIFF 파일"

# 이상 기준: 파일 수가 이전 버전보다 100개 이상 감소하면 경고
if [ $DIFF -lt -100 ]; then
  echo "⚠️  WARN: 파일 수 $DIFF 감소 — 의도치 않은 파일 삭제 여부 확인 필요"
else
  echo "✅ 파일 수 변화 정상 범위"
fi
```

### 5.4 C:\claude 복사

```bash
cp /tmp/literary-os-vXXX.zip /sessions/.../mnt/claude/literary-os-vXXX.zip
ls -lh /sessions/.../mnt/claude/literary-os-v*.zip | tail -5
```

---

## §6. 메모리 업데이트

```
[ ] memory/project_vXXX_state.md 작성 (핵심 지표 + 변경 요약 + Preflight 결과)
[ ] memory/MEMORY.md 인덱스 항목 추가
```

---

## §7. 프로토콜 준수 점검 체크리스트 (최종 인도 전)

```
개발 전
[ ] §1 Preflight 12단계 실행 완료
[ ] Step 11 위험도 분류 기록
[ ] Step 12 Release Gate PASS 확인

구현 중
[ ] LLM-0 원칙 준수
[ ] 클래스명 중복 없음 (duplicate_zero)
[ ] __init__.py 공개 API 추가

배포 전
[ ] 전체 pytest PASS
[ ] generate_test_inventory.py 실행
[ ] run_release_gate.py 61/61 PASS

패키징
[ ] 표준 명령어로 ZIP 생성
[ ] 7/7 검증 항목 PASS
[ ] 이전 버전 대비 파일 수 비교 정상
[ ] C:\claude 복사 완료

마무리
[ ] GitHub Release 생성
[ ] memory/ 업데이트
```

---

## §8. 버전 이력

| 버전 | 날짜 | 변경 내용 |
|---|---|---|
| v1.0 | 2026-05-26 | PACKAGING_PROTOCOL_v1.0 최초 제정 — ZIP 검증 7항목 |
| v2.0 | 2026-05-26 | **전면 개정** — Preflight §1 필수화, 이전 버전 비교 §5.3 추가, 결함 4종 해소 |
