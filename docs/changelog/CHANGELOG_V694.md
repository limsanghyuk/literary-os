# Changelog — V694

**Version:** 12.1.0
**Date:** 2026-05-28

## Added

- `literary_system/gates/spd1_exit_gate.py` (341 lines)
  - `ExitCheckpoint`, `SpD1ExitResult` 데이터 클래스
  - E1~E6 6축 검증 함수
  - `run_spd1_exit_gate()` — CLI 실행 지원
- `tests/unit/test_v694_spd1_exit_gate.py` — 33 TC ALL PASS
- `docs/adr/ADR-157.md`

## Changed

- `pyproject.toml` 버전 12.0.2 → 12.1.0 (SP-D.1 완료)
- `pyproject.toml` description SP-D.1 완료 반영
- `README.md` 버전 배지 갱신

## Test Results

- V694 신규: 33 PASS
- 누적 총계: 9,238 TC (9,205 + 33)
