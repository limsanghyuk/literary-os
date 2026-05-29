# CHANGELOG — V587 (v9.2.0)

**릴리즈 날짜**: 2026-05-20  
**버전**: v9.2.0  
**이전 버전**: v9.1.0-V586  
**게이트**: 45/45 PASS  
**테스트**: 5760+ PASS (e2e 포함)

---

## SP-α: 외부 신뢰 회복 + 문서 정합성 CI

- **ci.yml 44 Gates 버그 수정**: "39 Gates" 표기 → 45 Gates (V587 기준)
- **버전 정합성 CI 강화**: `pyproject.toml` / `README.md` / `MANIFEST.md` / `CHANGELOG.md` / `ci.yml` / `SESSION_INIT.md` 6파일 동시 검증 (`tools/check_version_consistency.py --strict`)
- **GitHub Releases 자동화**: `.github/workflows/release.yml` 신설, `v*.*.*` 태그 push 시 자동 릴리즈
- **CHANGELOG 소급 보완**: V572(v7.8.0) ~ V586(v9.1.0) 15버전 항목 정비
- **pyproject.toml / README / MANIFEST**: v9.2.0 일치
- **ADR-048**: Doc Consistency CI 정책 문서화

## SP-β: Gate G46 E2EProseGate + ADR-046 Gate 계층화

### Gate G46 — E2EProseGate (ADR-047)

신규 파일: `literary_system/gates/e2e_prose_gate.py` (333 lines)

6-checkpoint E2E 산문 파이프라인 검증:

| CP | 시스템 | 검증 |
|----|--------|------|
| CP-1 | NIE/NIL | `NILOrchestrator.process_scene()` + `NILResult` 필드 |
| CP-2 | ASD AutoRepair | `NarrativeDebtDetector` + `AutoRepairExecutor` 생성 가능 |
| CP-3 | GIG NarrativeGraph | `SceneChangePreGate.evaluate()` → `approved=True` |
| CP-4 | LOSDB QueryInterface | `check_all_connections()` ≤ 1000ms |
| CP-5 | Constitution | prose score ≥ 0.65 (MOCK: 0.70) |
| CP-6 | CLI generate | `SceneGenerationPipeline(gateway=MockGateway)` → ≥ 10자 |

- MOCK 모드 CI 기본 실행, `@pytest.mark.real_llm` 수동 분리
- `tests/e2e/test_e2e_prose.py` 20 PASS (non-real_llm)
- `pytest.ini` 마커 등록: `e2e`, `real_llm`

### ADR-046 — Gate 계층화 (CI 4-Tier)

`literary_system/gates/release_gate.py` 확장:

- `run_release_gate_tiered(tiers=['L0', 'L1'])` 신설
- `_GATE_TIER` 딕셔너리: L0(3), L1(7), L2(35) 분류
- `GateRegistryEntry.tier` 필드 추가 (`gate_registry.py`)

**실측 (V587 기준):**

| 티어 | 게이트 수 | 실측 시간 | 목표 |
|------|-----------|-----------|------|
| L0 | 3 | 54.3ms | ≤5s |
| L0+L1 | 10 | 1103.7ms | ≤30s |
| Full | 45 | ~120s | ≤5m |

`docs/perf/gate_timings_v587.json` 저장.

### ci.yml 4-Tier 분리

- `gate-l0`: L0 3게이트 (pre-commit)
- `gate-pr`: L0+L1 10게이트 (PR fast-path, PR 전용)
- `test`: Full 45게이트 + pytest (main push)
- `security-quick`: DEV_MODE 회귀 (PR 전용)

### ADR 신설

- `docs/adr/ADR-046-gate-hierarchy.md`
- `docs/adr/ADR-047-e2e-prose-policy.md`
- `docs/adr/INDEX.md` ADR-044~ADR-048 항목 추가

### 측정 도구

`tools/measure_gate_time.py` (244 lines):
- `--quick`: L0+L1 실측
- `--output`: JSON 결과 저장
- L0+L1 > 30s 시 exit code 1

---

## 게이트 현황 (V587 기준)

| 구분 | V586 | V587 |
|------|------|------|
| 총 게이트 | 44 | **45** |
| PASS | 44 | **45** |
| E2E 게이트 | 없음 | **G46 추가** |
| CI L0+L1 실측 | N/A | **1.1s** |

---

## 변경 파일 목록

```
literary_system/gates/e2e_prose_gate.py        (신규)
literary_system/gates/release_gate.py          (수정: G46 추가, tiered API)
literary_system/gates/gate_registry.py         (수정: tier 필드)
tests/e2e/__init__.py                          (신규)
tests/e2e/test_e2e_prose.py                    (신규)
pytest.ini                                     (수정: markers)
tools/measure_gate_time.py                     (신규)
docs/perf/gate_timings_v587.json               (신규)
docs/adr/ADR-046-gate-hierarchy.md             (신규)
docs/adr/ADR-047-e2e-prose-policy.md           (신규)
docs/adr/ADR-048-doc-consistency-ci.md         (SP-α 기작성)
docs/adr/INDEX.md                              (수정)
.github/workflows/ci.yml                       (수정: 4-tier jobs)
.github/workflows/release.yml                  (SP-α 기작성)
tools/check_version_consistency.py             (SP-α 기작성)
pyproject.toml                                 (v9.2.0)
README.md                                      (v9.2.0)
MANIFEST.md                                    (v9.2.0)
CHANGELOG.md                                   (V587 항목 추가)
SESSION_INIT.md                                (V587 기준 업데이트)
```
