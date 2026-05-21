# CHANGELOG — V595.3 (v10.0.3)

**날짜**: 2026-05-21  
**버전**: v10.0.3  
**분류**: Phase A Atomicity & Gate Freshness Final (Hotfix 릴리즈)  
**기반**: V595.2 (v10.0.2, commit 841561e1)

---

## 변경 요약

V595.2 Principal Engineering Audit에서 발견된 P1 결함 4종을 해결하는 필수 패치.
기능 추가 없음. 원자성·무결성·상태 전이 정합성 수정만 포함.

---

## FIX-A: SQLiteRealAdapter migration 원자성 (P0-1)

**파일**: `literary_system/db/sql_real_adapter.py`

`conn.executescript()`는 내부적으로 자동 COMMIT을 발행하므로 트랜잭션 경계를 제어할 수 없었음.
부분 실패 시 앞 SQL 구문이 DB에 잔류하고 migration_log에는 기록되지 않는 상태 불일치 발생.

**수정**: `executescript()` → `BEGIN IMMEDIATE` + 개별 `execute()` + `commit()`/`rollback()` 패턴으로 교체.
`rollback()` 메서드도 동일하게 수정.

---

## FIX-B: VectorRealAdapter 파일 rollback 누락 (P1-1)

**파일**: `literary_system/db/vector_real_adapter.py`

`apply()` 내부에서 `save` op가 mutation sequence 중간에 실행되어, 이후 op 실패 시
메모리는 롤백되지만 JSON 파일은 중간 상태를 유지하는 divergence 발생.

**수정**:
- `apply()` 진입 시 파일 바이트 스냅샷 저장
- `save` op를 mutation sequence에서 분리 → 모든 mutation 성공 후 마지막에만 실행
- 예외 발생 시 메모리 + 파일 모두 스냅샷으로 복원

---

## FIX-C: BackendHealthMonitor HALF_OPEN 상태 전이 오류 (P1-2)

**파일**: `literary_system/db/health_monitor.py`

`try_recover()`가 OPEN → HALF_OPEN 전이 시 `last_check_ok = True`를 설정하여,
실제 probe 없이 `get_available_backends()`가 해당 백엔드를 가용으로 반환했음.

**수정**: `try_recover()`에서 `last_check_ok = False`로 변경.
`get_available_backends()`는 `CLOSED + last_check_ok=True + last_error=''` 조건을 모두 요구하도록 보강.

---

## FIX-D: PhaseAExitGate EA-6 source_hash 미검증 (P1-3)

**파일**: `literary_system/gates/phase_a_exit_gate.py`

EA-6이 `test_inventory.json`의 `test_count >= 6000`만 검사하고 `source_hash`는 무시하여,
stale inventory로도 Gate가 PASS되는 문제.

**수정**: `tools.generate_test_inventory.source_hash()`를 임포트하여 현재 source_hash와
inventory source_hash 불일치 시 EA-6 FAIL + 명확한 오류 메시지 출력.

---

## 테스트

**신규 테스트**: `tests/unit/test_v595_3_fixes.py` (9개 TC)
- TC-A1: 부분 실패 migration 롤백 검증
- TC-A2: 정상 migration 원자 적용 검증
- TC-B1: save 후 실패 시 파일 롤백 검증
- TC-B2: 정상 ops 파일 보존 검증
- TC-C1: HALF_OPEN 상태에서 가용 불가 검증
- TC-C2: probe 성공 후 CLOSED + 가용 검증
- TC-D1: stale source_hash EA-6 FAIL 검증
- TC-D2: 일치 source_hash EA-6 PASS 검증
- TC-D3: test_count 부족 EA-6 FAIL 검증

---

## 수치 통일

| 항목 | V595.2 | V595.3 |
|------|--------|--------|
| pyproject version | 10.0.2 | **10.0.3** |
| README badge | 5897 PASS (구버전) | **6179 PASS** |
| pyproject description | 6182+ tests | **6179+ tests** |
| test_inventory.json | 6182 (stale) | **6188 (신규 9개 반영)** |
| release gate | 51/51 | **51/51** |

---

## 검증 명령

```bash
python -m compileall -q literary_system apps tools tests
python tools/check_version_consistency.py --strict
python tools/generate_test_inventory.py
python tools/run_release_gate.py
pytest tests/e2e/test_e2e_prose.py -q
pytest tests/unit/test_v595_3_fixes.py -v
sha256sum -c SHA256SUMS.txt | grep -c FAIL
```

---

## P2 이슈 (V596 이후 개선 권고 — 본 릴리즈 범위 외)

- **P2-1**: LOSConstitution 키워드 휴리스틱 — 마커 과밀 문장 점수 왜곡
- **P2-2**: LOSDBClient private fallback 경로 잔존
