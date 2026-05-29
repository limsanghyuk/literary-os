# CHANGELOG — V745

**Date**: 2026-05-30  
**Version**: 13.0.0 (Phase D Exit)  
**Gate**: G95 Phase D Exit (SC-1~SC-8 ALL PASS)  
**Commit**: V745: G95 Phase D Exit Gate (8축 SC-1~SC-8) + v13.0.0 릴리즈

## Summary

Phase D (V681~V745) final release. G95 certifies all Phase D success criteria.

## New Files

| File | Description |
|------|-------------|
| `literary_system/gates/phase_d_exit_gate.py` | G95 Phase D Exit Gate — 8-axis verification |
| `tests/unit/test_v745_phase_d_exit.py` | 72 TC (all PASS) |
| `docs/adr/ADR-208.md` | ADR for G95 |
| `docs/changelog/CHANGELOG_V745.md` | This file |

## Modified Files

| File | Change |
|------|--------|
| `literary_system/gates/release_gate.py` | Appended G95 (`phase_d_exit_g95`) — GATES: 96 → 97 |
| `tests/unit/test_v731_api_completeness.py` | Updated `len(GATES) == 96` → `== 97` |
| `tools/test_inventory.json` | Updated test_count: 8845 → 10716 |
| `pyproject.toml` | version: 12.6.0 → 13.0.0 |

## Gate Results

| Gate | Status | Detail |
|------|--------|--------|
| G95 SC-1 | PASS | gates_registered=97 ≥ 96 |
| G95 SC-2 | PASS | tests_collected=10,716 ≥ 10,000 |
| G95 SC-3 | PASS | StaticTypeSafetyReport + run_fn present |
| G95 SC-4 | PASS | PerformanceSLOGate + API_P99_SLO_MS=200ms |
| G95 SC-5 | PASS | ZeroTrustSecurityGate + TenantAuthority |
| G95 SC-6 | PASS | run_g87_gate + PluginWhitelist |
| G95 SC-7 | PASS | ChaosResilienceGate + 5 scenarios |
| G95 SC-8 | PASS | adr_files=192 ≥ 68 |

## Regression

- Unit tests: 4342 PASS, 20 FAIL (all pre-existing, confirmed from V744 baseline)
- V745-introduced failures: **0**

## Phase D Complete

| Metric | Value |
|--------|-------|
| V-versions | V681~V745 (65 versions) |
| New Gates | G81~G95 (15 gates, total 97) |
| TC collected | 10,716 |
| ADRs | 192 total (ADR-143~ADR-208 for Phase D) |
| Final version | 13.0.0 |
