# V574 — Bug Fix Release

**버전**: 7.9.0-V574  
**날짜**: 2026-05-19  
**기준**: V573 (7.8.1) + 회사 컴퓨터 실행 검증 결과 반영  
**테스트**: 5,471 PASS, 22 SKIPPED (V573 대비 +6)

---

## 수정된 버그

### Bug-1 (CRITICAL): AutoRepairExecutor 의존성 역전

- **파일**: `literary_system/graph_intelligence/asd/auto_repair_executor.py`
- **증상**: `SceneChangePreGate`에 `NarrativeGraphStore` 대신 `NarrativeImpactAnalyzer` 인스턴스가 전달되어 `get_node()` 호출 시 `AttributeError` 발생
- **원인**: `SceneChangePreGate.__init__`이 `store: NarrativeGraphStore`를 받아 내부에서 `NarrativeImpactAnalyzer`를 생성하는 구조인데, `AutoRepairExecutor`가 중간 단계로 `analyzer`를 직접 생성하여 전달
- **수정**:
  ```python
  # BEFORE (Bug):
  analyzer = NarrativeImpactAnalyzer(store)
  gate26   = SceneChangePreGate(analyzer)

  # AFTER (Fix):
  gate26   = SceneChangePreGate(store)  # store 직접 전달
  ```
- **제거**: 불필요해진 `from ..narrative_impact_analyzer import NarrativeImpactAnalyzer` import 삭제

### Bug-2 (ENVIRONMENT): analyze.py FastAPI 환경 의존

- **파일**: `apps/studio_api/routers/analyze.py`
- **증상**: FastAPI 미설치 환경(sandbox/CI)에서 `import analyze` 시 `ImportError` 발생 — `try/except` 가드를 뚫고 예외가 전파됨
- **원인**: `if not _FA: raise ImportError("FastAPI required")` 구문이 `try/except` 밖에 위치
- **수정**:
  ```python
  if not _FA:
      import types
      router = types.SimpleNamespace()
      router.post = lambda *a, **kw: (lambda f: f)
      router.get  = lambda *a, **kw: (lambda f: f)
  else:
      router = APIRouter(prefix="/api/v1", tags=["Analysis"])
  ```

### Bug-3 (NOT APPLICABLE): knowledge_access 필드 문제

- 회사 V571-dev 환경 특이 현상으로 확인
- V573 literary_system/ 코드베이스에는 해당 필드 미존재 → 수정 불필요

---

## 신규 테스트

- **파일**: `tests/test_v574_bug_fixes.py` (8개 테스트)
  - `TestBug1AutoRepairExecutor`: 4개 — 인스턴스화, gate26 타입, 의존성 역전 검증, dry_run ERROR 없음
  - `TestBug2StudioApiAnalyze`: 3개 — import 가능, router 존재, post/get 속성 보유
  - `TestBug3KnowledgeAccessScope`: 1개 — literary_system/ 내 knowledge_access 미존재 확인

---

## 검증

회사 컴퓨터(Claude Code + GPT + GitNexus) 실행 검증 결과를 `docs/sessions/2026-05-19_company_execution_validation.md`에 기록.  
홈 Cowork 환경에서 전체 테스트 재실행 후 5,471 PASS 확인.
