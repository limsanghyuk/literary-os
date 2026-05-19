# CHANGELOG — V575 (8.0.0)

> **릴리즈 날짜**: 2026-05-19  
> **버전**: 8.0.0  
> **분류**: Security & Hygiene  
> **테스트**: 5,483 PASS (V574 대비 +12)  
> **Gates**: 30/30 PASS  

---

## 개요

V575는 PE 보고서(V574 분석)에서 도출된 **Security & Hygiene** 릴리즈다.  
기능 추가 없이 보안 결함 수정, 코드 품질 정규화, CI 위생 게이트 신설에 집중.

---

## 변경 사항

### 🔴 CRITICAL — 보안 패치

#### FIX-1: DEV_MODE 기본값 `"true"` → `"false"`
- **파일**: `apps/studio_api/auth/middleware.py:29`
- **문제**: `os.environ.get("LITERARY_OS_DEV_MODE", "true")` — `LITERARY_OS_DEV_MODE` 환경변수가  
  설정되지 않은 모든 배포 환경에서 인증이 자동으로 bypass됨
- **수정**: 기본값을 `"false"` 로 변경 → 인증 bypass는 명시적 환경변수 설정 시에만 활성화

### 🟡 HIGH — 코드 품질

#### FIX-2: `print()` → `logging` 전환 (32건)
- 전환 대상 파일 (13개):
  - `orchestrators/e2e_loop_orchestrator.py` (21건)
  - `orchestrators/scene_generation_orchestrator.py`
  - `rag/retrieval_pipeline.py`
  - `graph_intelligence/sp2/stage_patch_impact_calculator.py`
  - `graph_intelligence/scene_change_pre_gate.py`
  - `graph_intelligence/sp3/scene_blast_radius_report.py`
  - `pipeline/pipeline_state.py`
  - `gates/gate24_slm_sp3.py`
  - `arc/series_arc_planner.py`
  - `arc/causal_plot_graph.py`
  - `gate/critic_comparison_gate.py`
  - `llm_bridge/cascade.py`
  - `quality/llm_judge.py`
  - `pipelines/drama_episode_generator.py`
- 모든 파일에 `import logging` + `logger = logging.getLogger(__name__)` 추가

#### FIX-3: bare `except:` → `except Exception:` (4건)
- `literary_system/schemas/scene_draft_output.py` (3건)
- `literary_system/emotion/emotional_momentum_tracker.py` (1건)

### 🟢 MEDIUM — 데드코드 / 문서

#### FIX-4: 데드코드 파일 제거
- `apps/studio_api/main_v316.py` 삭제 (V420부터 미사용)

#### FIX-5: `pyproject.toml` description 갱신
- `"Literary OS V571 — Phase6 MultiWork..."` → V575 현재 설명으로 수정

### 🔵 NEW — CI 위생 게이트

#### FEAT-1: `tools/preflight_step15.py` 신설 (ADR 제안 반영)
- Rule-1 (CRITICAL): DEV_MODE 기본값 `"true"` 금지
- Rule-2 (HIGH): `literary_system/` 내 `print()` 사용 금지
- Rule-3 (MEDIUM): bare `except:` 금지
- `--strict` 모드: CI 블로킹

#### FEAT-2: CI `preflight-step15` 잡 추가
- `.github/workflows/ci.yml`에 `preflight-step15` 잡 삽입
- Step14 → Step15 → test 순서로 체인
- `test` 잡은 모든 preflight 통과 후에만 실행

---

## 테스트

| 항목 | 결과 |
|------|------|
| 전체 테스트 | 5,483 PASS, 22 skip |
| V574 대비 | +12 (test_v575_hygiene.py 12건 추가) |
| Gates | 30/30 PASS |
| Preflight Step 13 | ALL CLEAR |
| Preflight Step 14 | ALL CLEAR (55 types, 0 mismatch) |
| Preflight Step 15 | ALL CLEAR (Rule-1/2/3 모두 0건) |

---

## 파일 변경 요약

| 분류 | 파일 수 | 내용 |
|------|---------|------|
| 수정 | 17 | middleware.py + 13 logging + 2 except + pyproject.toml + ci.yml |
| 신설 | 2 | tools/preflight_step15.py, tests/test_v575_hygiene.py |
| 삭제 | 1 | apps/studio_api/main_v316.py |

---

*Literary OS — V575 Security & Hygiene | 2026-05-19*
