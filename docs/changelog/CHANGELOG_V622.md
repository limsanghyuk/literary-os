# CHANGELOG — V622 (v10.27.0)

**Release Date:** 2026-05-25  
**Base Version:** V621 (v10.26.0, 6,801 TC)  
**Release Version:** v10.27.0  
**TC Delta:** +60 (6,861 TC)

---

## Summary

V622 SP-B.3 retrofit: 기존 멀티워크 및 RLHF 레이어 3개 모듈에 핵심 추상화 후방 추가.
G58/G59 회귀 0건, 60/60 TC PASS.

---

## Changes

### New Features

#### §A — ConflictPolicy + CharacterConflictResolver (`shared_character_db_v2.py`)
- `ConflictPolicy(str, Enum)` 5종: RENAME / MERGE / FORK / BLOCK / ESCALATE
- `CharacterConflictResolver.resolve(conflict_id, policy)` — 정책별 핸들러 dispatch
  - `_resolve_rename`: cid + `_renamed` 신규 등록
  - `_resolve_merge`: traits union 병합 (resolved=True)
  - `_resolve_fork`: cid + `_fork` 파생 등록 (원본 보존)
  - `_resolve_block`: RuntimeError 발생 (수동 해결 강제)
  - `_resolve_escalate`: escalated 마킹, resolved=False

#### §B — WorkloadProfile + SLO + schedule() (`multi_work_orchestrator_v2.py`)
- `WorkloadProfile(str, Enum)`: SINGLE / DUAL / TRIPLE
- SLO 상수: `SLO_SINGLE_MS=3000`, `SLO_DUAL_MS=5000`, `SLO_TRIPLE_MS=8000`
- `classify_workload(project_ids)`: n≤1→SINGLE, n=2→DUAL, n≥3→TRIPLE
- `schedule(project_ids, scene_ms_each)` → `ScheduleResult`
  - SINGLE: 직렬, DUAL: 2-way 병렬, TRIPLE: ceil(N/2) 라운드로빈

#### §C — AdvSeed + RewardModelV2 (`reward_model.py`)
- `AdvSeed(NamedTuple)`: name / description / inject_fn / expected_drop
- `ADV_SEEDS_REQUIRED` 5종: marker_stuffing / length_inflation / repetition_pattern / extreme_emotion / genre_deviation
- `RewardModelV2(RewardModel)` VERSION="2.0.0"
  - `score_with_adv_seeds(text, seeds)` → {baseline, results, robustness, all_passed}
  - `robustness_score(text)` → float ∈ [0, 1]

### Bug Fixes
- `_resolve_merge`: `rec.conflicting_ids` AttributeError 수정 → 현재 traits 상태 기준 병합

### Tests
- `tests/unit/test_v622_sp_b3_retrofit.py`: 60 TC 신규 (§A TC-01~20, §B TC-21~40, §C TC-41~60)
- `tools/test_inventory.json`: 6,861 TC로 갱신
- G58/G59 회귀: 0건

### Documentation
- `docs/adr/ADR-089.md`: SP-B.3 retrofit 설계 결정 기록

---

## Test Results

| Suite       | PASS | SKIP | FAIL |
|-------------|------|------|------|
| unit        | 703  | 0    | 0    |
| integration | 31   | 3    | 0    |
| **Total**   | **734** | **3** | **0** |

**Total TC (inventory):** 6,861
