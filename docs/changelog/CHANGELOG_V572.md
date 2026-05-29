# CHANGELOG V572 — CI 강화 & Preflight 자동화

**버전**: v7.8.0-V572  
**날짜**: 2026-05-18  
**Phase**: Phase 6 Stage D  
**기반**: v7.7.1-V571 (5,456 PASS / 0 FAIL / 20 SKIP)

---

## 개요

V572는 Literary OS의 개발-CI 신뢰 루프를 강화하는 인프라 버전이다.  
V571 CI 안정화 과정에서 발견된 3개 구조적 문제(의존성 불일치, numpy 미명시, Survival Matrix 경로 오류)를 해결한다.

**핵심 목표**: "Preflight 통과 = CI 통과"를 보장하는 자동화 루프 완성.

---

## 신설 파일

### `tools/preflight_step13.py`
- **목적**: GitNexus Preflight Step 13 — CI 의존성 정합성 자동 검사
- **동작**: tests/**/*.py 전체 AST 파싱 → import 수집 → importlib.metadata 대조 → 불일치 리포트
- **모드**: 기본(경고), `--strict` (불일치 시 exit 1, CI 블로킹)
- **ADR**: ADR-032

### `tools/survival_matrix.py`
- **목적**: Survival Matrix V572 — 핵심 심볼 생존 확인 보조 스크립트
- **수정 내역**: V571 Preflight 경로 불일치 6건 전면 수정
  - `arc/NarrativeDebtDetector` → `graph_intelligence/asd/narrative_debt_detector`
  - `arc/StoryDoctorOrchestrator` → `graph_intelligence/asd/story_doctor_orchestrator`
  - `arc/AutoRepairExecutor` → `graph_intelligence/asd/auto_repair_executor`
  - `arc/AdapterContractV2` → `llm_bridge/adapter_contract` (AdapterContractV2)
  - `graph/NarrativeGraphStore` → `graph_intelligence/narrative_graph_store`
  - `CascadeRouter` → `CascadeOrchestrator` (실제 클래스명)
  - Corpus 4종: `corpus_ingestor`, `corpus_validator`, `bgem3_embedder`, `cim_bootstrap`
- **결과**: 16/16 REQUIRED LIVE, 4/4 OPTIONAL LIVE

### `CHANGELOG_V572.md`
- 이 파일

---

## 수정 파일

### `.github/workflows/ci.yml`
- **추가**: `preflight` 잡 신설
  - Python 3.11 단일 환경에서 `python tools/preflight_step13.py --strict` 실행
  - `test` 잡에 `needs: preflight` 추가 — Preflight 실패 시 전체 CI 블로킹
- **결과**: 3잡(test×2, integrity) → 4잡(preflight, test×2, integrity)

### `pyproject.toml`
- **추가**: `dev` extras에 `numpy>=1.24` 명시 추가
- **배경**: scikit-learn 전이 의존으로 우연히 통과 중이던 상태 → 독립 명시로 전환
- **영향**: test_v325_vector_retriever.py의 numpy import 안전 보장

---

## 해결된 구조적 문제

| 문제 | V571 상태 | V572 해결 |
|------|-----------|-----------|
| CI 의존성 불일치 | 수동 디버깅 필요 | Preflight Step 13 자동 탐지 |
| numpy 미명시 | 전이 의존 우연 통과 | dev extras 명시 추가 |
| Survival Matrix 경로 오류 | 6개 심볼 DEAD 판정 | 16/16 LIVE 달성 |
| CI 잡 수 | 3개 (test×2, integrity) | 4개 (preflight 추가) |

---

## 테스트 결과

```
5456 passed, 20 skipped in 29s
```

V571 대비 변동 없음 — 코드 로직 변경 없음, 인프라/툴링만 수정.

---

## ADR

- **ADR-032**: Preflight Step 13 신설 — tests/ import vs dev extras 자동 대조

---

## 다음 버전 (V573 예정)

V572로 CI-Preflight 신뢰 루프가 완성되었으므로, V573부터 새로운 기능 개발 재개 가능.
